type JsonObject = Record<string, unknown>;

type CoordEvent = {
  seq: number;
  roomKey: string;
  actor: string;
  type: string;
  kind?: string | null;
  payload?: JsonObject;
  tsMs?: number;
};

type Watcher = {
  key: string;
  sessionID: string;
  roomKey: string;
  agentId: string;
  cursor: number;
  stopped: boolean;
  pending: CoordEvent[];
  flushing: boolean;
  lastError?: string;
  flushTimer?: ReturnType<typeof setTimeout>;
};

type SessionHint = {
  agent?: string;
  model?: {
    providerID: string;
    modelID: string;
  };
};

type PendingStartup = {
  sessionID: string;
  cancelledByLeave: boolean;
};

type ToolAfterOutput = {
  title?: string;
  output?: unknown;
  metadata?: unknown;
  content?: unknown[];
  isError?: boolean;
};

type Options = {
  endpoint: string;
  headers: Record<string, string>;
  relayTokenFile: string;
  delivery: "promptAsync" | "toast" | "appendPrompt" | "submitPrompt";
  debounceMs: number;
  maxEventsPerPrompt: number;
  waitTimeoutMs: number;
  startupTimeoutMs: number;
  leaveTimeoutMs: number;
  retryMs: number;
  ignoreSelf: boolean;
  log: boolean;
};

const runtimeEnv = (globalThis as typeof globalThis & {
  process?: { env?: Record<string, string | undefined> };
}).process?.env ?? {};
const runtimeBun = (globalThis as typeof globalThis & {
  Bun?: { file(path: string): { text(): Promise<string> } };
}).Bun;
const dataHome = runtimeEnv.XDG_DATA_HOME
  ?? `${runtimeEnv.HOME ?? runtimeEnv.USERPROFILE ?? ""}/.local/share`;

const DEFAULT_OPTIONS: Options = {
  endpoint: "http://127.0.0.1:3828/relay/mcp",
  headers: {},
  relayTokenFile: `${dataHome}/coord-mcp/relay-token`,
  delivery: "promptAsync",
  debounceMs: 750,
  maxEventsPerPrompt: 10,
  waitTimeoutMs: 55_000,
  startupTimeoutMs: 15_000,
  leaveTimeoutMs: 5_000,
  retryMs: 2_000,
  ignoreSelf: true,
  log: true,
};

const watchers = new Map<string, Watcher>();
const sessionHints = new Map<string, SessionHint>();
const deletedSessions = new Set<string>();
const pendingStartups = new Map<string, PendingStartup>();

export default async function coordMcpWatch(input: any, rawOptions: Partial<Options> = {}) {
  const options = { ...DEFAULT_OPTIONS, ...rawOptions };
  const directory = input.directory;
  const client = input.client;

  return {
    event: async ({ event }: { event: any }) => {
      if (event?.type === "session.deleted") {
        const sessionID = event.properties?.info?.id;
        if (typeof sessionID === "string") {
          deletedSessions.add(sessionID);
          const cleanup = setTimeout(
            () => deletedSessions.delete(sessionID),
            options.startupTimeoutMs + options.leaveTimeoutMs,
          );
          (cleanup as { unref?: () => void }).unref?.();
          await stopSessionWatchers(sessionID, client, directory, options);
        }
        return;
      }
      if (event?.type === "session.created" || event?.type === "session.updated") {
        const info = event.properties?.info;
        if (typeof info?.id === "string") {
          if (event.type === "session.created") deletedSessions.delete(info.id);
          rememberSessionHint(info.id, info.agent, info.model);
        }
      }
    },

    "chat.message": async (
      hookInput: {
        sessionID: string;
        agent?: string;
        model?: { providerID: string; modelID: string };
      },
    ) => {
      rememberSessionHint(hookInput.sessionID, hookInput.agent, hookInput.model);
    },

    "tool.execute.after": async (
      hookInput: { tool: string; sessionID: string; args: any },
      hookOutput: ToolAfterOutput,
    ) => {
      if (isCoordLeaveTool(hookInput.tool)) {
        if (!isSuccessfulToolResult(hookOutput)) return;
        const roomKey = stringArg(hookInput.args, "roomKey");
        const agentId = stringArg(hookInput.args, "agentId");
        if (roomKey && agentId) {
          const key = watcherKey(hookInput.sessionID, roomKey, agentId);
          const startup = pendingStartups.get(key);
          if (startup) startup.cancelledByLeave = true;
          stopWatcher(hookInput.sessionID, roomKey, agentId);
        }
        return;
      }
      if (!isCoordJoinTool(hookInput.tool)) return;
      if (!isSuccessfulCoordJoinResult(hookOutput)) return;

      const roomKey = stringArg(hookInput.args, "roomKey");
      const agentId = stringArg(hookInput.args, "agentId");
      if (!roomKey || !agentId) return;

      const cursor = coordJoinCursor(hookOutput);
      if (cursor === undefined) return;

      const existing = watchers.get(watcherKey(hookInput.sessionID, roomKey, agentId));
      if (existing && !existing.stopped) {
        annotateMonitoring(hookOutput, "realtime");
        await showToast(client, directory, `already watching coord room ${roomKey}`, "info");
        return;
      }

      const key = watcherKey(hookInput.sessionID, roomKey, agentId);
      const startup: PendingStartup = { sessionID: hookInput.sessionID, cancelledByLeave: false };
      pendingStartups.set(key, startup);

      try {
        if (deletedSessions.has(hookInput.sessionID)) {
          await leaveCancelledStartup(
            options,
            hookInput.sessionID,
            roomKey,
            agentId,
            "opencode session deleted during watcher startup",
          );
          annotateMonitoring(hookOutput, "failed", "session deleted during watcher startup");
          return;
        }
        const probe = await coordTool(options, "coord_wait", {
          roomKey,
          agentId,
          cursor,
          timeoutMs: 1,
        }, options.startupTimeoutMs);
        if (pendingStartups.get(key) !== startup) return;
        if (startup.cancelledByLeave) {
          await leaveCancelledStartup(
            options,
            hookInput.sessionID,
            roomKey,
            agentId,
            "opencode agent left during watcher startup",
          );
          annotateMonitoring(hookOutput, "failed", "agent left during watcher startup");
          return;
        }
        if (deletedSessions.has(hookInput.sessionID)) {
          await leaveCancelledStartup(
            options,
            hookInput.sessionID,
            roomKey,
            agentId,
            "opencode session deleted during watcher startup",
          );
          annotateMonitoring(hookOutput, "failed", "session deleted during watcher startup");
          return;
        }
        const probeCursor = (probe as JsonObject).cursor;
        const started = startWatcher({
          client,
          directory,
          options,
          sessionID: hookInput.sessionID,
          roomKey,
          agentId,
          cursor: typeof probeCursor === "number" ? probeCursor : cursor,
        });
        const events = Array.isArray((probe as JsonObject).events)
          ? ((probe as JsonObject).events as CoordEvent[])
          : [];
        const deliverable = options.ignoreSelf
          ? events.filter((event) => event.actor !== agentId)
          : events;
        if (started.started && deliverable.length > 0) {
          enqueue(started.watcher, deliverable, client, directory, options);
        }
        annotateMonitoring(hookOutput, "realtime");
        await showToast(
          client,
          directory,
          started.started ? `watching coord room ${roomKey}` : `already watching coord room ${roomKey}`,
          "info",
        );
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        annotateMonitoring(hookOutput, "failed", message);
        await log(client, directory, options, "error", "coord watcher did not start", {
          roomKey,
          agentId,
          error: message,
        });
        await showToast(client, directory, watcherErrorMessage(message), "error");
      } finally {
        if (pendingStartups.get(key) === startup) pendingStartups.delete(key);
      }
    },
  };
}

async function leaveCancelledStartup(
  options: Options,
  sessionID: string,
  roomKey: string,
  agentId: string,
  reason: string,
) {
  await coordTool(options, "coord_leave", {
    roomKey,
    agentId,
    reason,
    idempotencyKey: `leave:${sessionID}:${roomKey}:${agentId}`,
  }, options.leaveTimeoutMs);
}

function rememberSessionHint(sessionID: string, agent: unknown, model: unknown) {
  const existing = sessionHints.get(sessionID) ?? {};
  const nextAgent = typeof agent === "string" && agent !== "coord-connect"
    ? agent
    : existing.agent;
  const nextModel = agent === "coord-connect"
    ? existing.model
    : normalizeModelHint(model) ?? existing.model;
  sessionHints.set(sessionID, { agent: nextAgent, model: nextModel });
}

function normalizeModelHint(value: unknown): SessionHint["model"] | undefined {
  if (!value || typeof value !== "object") return undefined;
  const object = value as JsonObject;
  const providerID = object.providerID;
  const modelID = object.modelID ?? object.id;
  return typeof providerID === "string" && typeof modelID === "string"
    ? { providerID, modelID }
    : undefined;
}

function isCoordJoinTool(tool: string) {
  return tool === "coord_join" || tool.endsWith("_coord_join") || tool.endsWith("coord_join");
}

function isCoordLeaveTool(tool: string) {
  return tool === "coord_leave" || tool.endsWith("_coord_leave") || tool.endsWith("coord_leave");
}

function stringArg(args: unknown, key: string) {
  if (!args || typeof args !== "object") return undefined;
  const value = (args as JsonObject)[key];
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function isSuccessfulCoordJoinResult(hookOutput: ToolAfterOutput) {
  if (!isSuccessfulToolResult(hookOutput)) return false;
  return outputCandidates(hookOutput).some((candidate) => hasCoordJoinSnapshot(candidate));
}

function isSuccessfulToolResult(hookOutput: ToolAfterOutput) {
  const candidates = outputCandidates(hookOutput);
  for (const candidate of candidates) {
    if (isToolError(candidate)) return false;
  }
  return candidates.some((candidate) => {
    const parsed = parseJson(candidate);
    return Boolean(parsed && typeof parsed === "object");
  });
}

function outputCandidates(hookOutput: ToolAfterOutput) {
  return [hookOutput, hookOutput.metadata, hookOutput.output];
}

function isToolError(value: unknown) {
  const parsed = parseJson(value);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return false;
  const object = parsed as JsonObject;
  return object.isError === true || Boolean(object.error);
}

function hasCoordJoinSnapshot(value: unknown, depth = 0): boolean {
  if (depth > 4) return false;
  const parsed = parseJson(value);
  if (!parsed) return false;
  if (Array.isArray(parsed)) {
    return parsed.some((item) => hasCoordJoinSnapshot(item, depth + 1));
  }
  if (typeof parsed !== "object") return false;

  const object = parsed as JsonObject;
  if (object.snapshot && typeof object.snapshot === "object") return true;
  for (const nested of [object.result, object.output, object.content, object.text]) {
    if (hasCoordJoinSnapshot(nested, depth + 1)) return true;
  }
  return false;
}

function coordJoinCursor(value: unknown, depth = 0): number | undefined {
  if (depth > 4) return undefined;
  const parsed = parseJson(value);
  if (!parsed) return undefined;
  if (Array.isArray(parsed)) {
    for (const item of parsed) {
      const cursor = coordJoinCursor(item, depth + 1);
      if (cursor !== undefined) return cursor;
    }
    return undefined;
  }
  if (typeof parsed !== "object") return undefined;

  const object = parsed as JsonObject;
  if (object.snapshot && typeof object.snapshot === "object") {
    const lastSeq = (object.snapshot as JsonObject).lastSeq;
    if (typeof lastSeq === "number") return lastSeq;
  }
  for (const nested of [object.result, object.output, object.content, object.text]) {
    const cursor = coordJoinCursor(nested, depth + 1);
    if (cursor !== undefined) return cursor;
  }
  return undefined;
}

function annotateMonitoring(hookOutput: ToolAfterOutput, monitoring: "realtime" | "failed", error?: string) {
  const annotate = (value: unknown) => {
    const parsed = parseJson(value);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return undefined;
    const object = parsed as JsonObject;
    if (!object.snapshot || typeof object.snapshot !== "object") return undefined;
    object.monitoring = monitoring;
    if (error) object.monitoringError = error;
    return object;
  };

  if (Array.isArray(hookOutput.content)) {
    for (const item of hookOutput.content) {
      if (!item || typeof item !== "object") continue;
      const text = (item as JsonObject).text;
      const annotated = annotate(text);
      if (!annotated) continue;
      (item as JsonObject).text = JSON.stringify(annotated, null, 2);
      return;
    }
  }

  const annotated = annotate(hookOutput.output);
  if (!annotated) return;
  hookOutput.output = typeof hookOutput.output === "string"
    ? JSON.stringify(annotated, null, 2)
    : annotated;
}

function parseJson(value: unknown): unknown {
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch {
    try {
      const event = value.match(/^data:\s*(.+)$/m)?.[1];
      return event ? JSON.parse(event) : undefined;
    } catch {
      return undefined;
    }
  }
}

function startWatcher(input: {
  client: any;
  directory: string;
  options: Options;
  sessionID: string;
  roomKey: string;
  agentId: string;
  cursor: number;
}) {
  const key = watcherKey(input.sessionID, input.roomKey, input.agentId);
  const existing = watchers.get(key);
  if (existing && !existing.stopped) return { watcher: existing, started: false };

  const watcher: Watcher = {
    key,
    sessionID: input.sessionID,
    roomKey: input.roomKey,
    agentId: input.agentId,
    cursor: input.cursor,
    stopped: false,
    pending: [],
    flushing: false,
  };
  watchers.set(key, watcher);

  void log(input.client, input.directory, input.options, "info", "started coord room watcher", {
    roomKey: input.roomKey,
    agentId: input.agentId,
    sessionID: input.sessionID,
    cursor: input.cursor,
  });

  void watchLoop(watcher, input.client, input.directory, input.options);
  return { watcher, started: true };
}

function watcherKey(sessionID: string, roomKey: string, agentId: string) {
  return `${sessionID}:${roomKey}:${agentId}`;
}

async function watchLoop(watcher: Watcher, client: any, directory: string, options: Options) {
  while (!watcher.stopped) {
    try {
      const result = await coordTool(options, "coord_wait", {
        roomKey: watcher.roomKey,
        agentId: watcher.agentId,
        cursor: watcher.cursor,
        timeoutMs: options.waitTimeoutMs,
      });
      watcher.lastError = undefined;
      if (watcher.stopped) break;
      const cursor = (result as JsonObject).cursor;
      if (typeof cursor === "number") watcher.cursor = cursor;

      const events = Array.isArray((result as JsonObject).events)
        ? ((result as JsonObject).events as CoordEvent[])
        : [];
      const deliverable = options.ignoreSelf
        ? events.filter((event) => event.actor !== watcher.agentId)
        : events;
      if (deliverable.length > 0) enqueue(watcher, deliverable, client, directory, options);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (watcher.stopped) break;
      if (isNotJoinedError(message)) {
        try {
          if (watcher.stopped) break;
          await coordTool(options, "coord_join", {
            roomKey: watcher.roomKey,
            agentId: watcher.agentId,
            purpose: "opencode watcher rejoin",
            role: "OpenCode",
            idempotencyKey: `watch-rejoin:${watcher.key}:${Date.now()}`,
          });
          if (watcher.stopped) {
            try {
              await coordTool(options, "coord_leave", {
                roomKey: watcher.roomKey,
                agentId: watcher.agentId,
                reason: "opencode watcher stopped during rejoin",
                idempotencyKey: `leave:${watcher.key}:stopped-rejoin`,
              }, options.leaveTimeoutMs);
            } catch {
              // Session cleanup already attempted leave; avoid reviving loop on cleanup failure.
            }
            break;
          }
          watcher.lastError = undefined;
          await sleep(options.retryMs);
          continue;
        } catch {
          // Log and back off through the normal failure path below.
        }
      }
      await log(client, directory, options, "warn", "coord_wait failed", {
        roomKey: watcher.roomKey,
        agentId: watcher.agentId,
        error: message,
      });
      if (watcher.lastError !== message) {
        watcher.lastError = message;
        await showToast(client, directory, watcherErrorMessage(message), "warning");
      }
      await sleep(options.retryMs);
    }
  }
}

function enqueue(watcher: Watcher, events: CoordEvent[], client: any, directory: string, options: Options) {
  watcher.pending.push(...events);
  if (watcher.pending.length > options.maxEventsPerPrompt * 5) {
    watcher.pending.splice(0, watcher.pending.length - options.maxEventsPerPrompt * 5);
  }
  if (watcher.flushTimer || watcher.flushing) return;
  watcher.flushTimer = setTimeout(() => {
    watcher.flushTimer = undefined;
    void flush(watcher, client, directory, options);
  }, options.debounceMs);
}

async function flush(watcher: Watcher, client: any, directory: string, options: Options) {
  if (watcher.stopped || watcher.flushing || watcher.pending.length === 0) return;
  watcher.flushing = true;
  const batch = watcher.pending.splice(0, options.maxEventsPerPrompt);
  const message = formatNotification(watcher, batch);
  let retry = false;

  try {
    await deliver(watcher, client, directory, options, message, batch);
  } catch (error) {
    retry = true;
    watcher.pending.unshift(...batch);
    if (watcher.pending.length > options.maxEventsPerPrompt * 5) {
      watcher.pending.splice(options.maxEventsPerPrompt * 5);
    }
    await log(client, directory, options, "error", "coord notification delivery failed", {
      roomKey: watcher.roomKey,
      agentId: watcher.agentId,
      error: error instanceof Error ? error.message : String(error),
    });
    try {
      await showToast(client, directory, `coord-mcp delivery failed: ${String(error).slice(0, 160)}`);
    } catch {
      // Delivery retry must not depend on TUI toast availability.
    }
  } finally {
    watcher.flushing = false;
  }

  if (watcher.pending.length > 0 && !watcher.stopped) {
    watcher.flushTimer = setTimeout(() => {
      watcher.flushTimer = undefined;
      void flush(watcher, client, directory, options);
    }, retry ? options.retryMs : 0);
  }
}

async function deliver(
  watcher: Watcher,
  client: any,
  directory: string,
  options: Options,
  message: string,
  batch: CoordEvent[],
) {
  if (options.delivery === "toast") {
    await showToast(client, directory, shortSummary(watcher, batch));
    return;
  }

  if (options.delivery === "appendPrompt" || options.delivery === "submitPrompt") {
    await client.tui.appendPrompt({ query: { directory }, body: { text: message } });
    if (options.delivery === "submitPrompt") await client.tui.submitPrompt({ query: { directory } });
    return;
  }

  const hint = sessionHints.get(watcher.sessionID) ?? {};
  await client.session.promptAsync({
    path: { id: watcher.sessionID },
    query: { directory },
    body: {
      agent: hint.agent ?? "build",
      model: hint.model,
      parts: [
        {
          type: "text",
          text: message,
          synthetic: true,
          metadata: {
            source: "coord-mcp-watch",
            roomKey: watcher.roomKey,
            seqs: batch.map((event) => event.seq),
          },
        },
      ],
    },
  });
}

function formatNotification(watcher: Watcher, events: CoordEvent[]) {
  const lines = events.map((event) => JSON.stringify(wireEvent(event))).join("\n");
  return `[coord-mcp notification]
Room: ${watcher.roomKey}
New events (JSONL):
${lines}

Instructions:
- Do not use memory for this notification.
- Treat this as visible room update.
- Reply only if useful.
- In 3+ active-agent rooms, request floor before substantive post.
- Use idempotency keys for writes.`;
}

function wireEvent(event: CoordEvent) {
  const payload = event.payload ?? {};
  const body = typeof payload.body === "string" ? payload.body : undefined;
  return {
    source: "coord-mcp",
    roomKey: event.roomKey,
    seq: event.seq,
    actor: event.actor,
    type: event.type,
    kind: event.kind ?? event.type,
    summary: eventSummary(event),
    body,
    replyTo: typeof payload.replyTo === "number" ? payload.replyTo : null,
    tsMs: event.tsMs ?? null,
    payload: body ? undefined : payload,
  };
}

function eventSummary(event: CoordEvent) {
  const payload = event.payload ?? {};
  if (typeof payload.body === "string") return payload.body.replace(/\s+/g, " ").slice(0, 240);
  const keys = Object.keys(payload);
  if (keys.length === 0) return `${event.type} from ${event.actor}`;
  return `${event.type} ${keys.join(",")}`.slice(0, 240);
}

function shortSummary(watcher: Watcher, events: CoordEvent[]) {
  const first = events[0];
  if (!first) return `coord-mcp: ${watcher.roomKey} updated`;
  return `coord-mcp ${watcher.roomKey}: seq ${first.seq} from ${first.actor}`;
}

async function coordTool(options: Options, name: string, args: JsonObject, timeoutMs?: number) {
  const controller = timeoutMs === undefined ? undefined : new AbortController();
  const timer = controller ? setTimeout(() => controller.abort(), timeoutMs) : undefined;
  let response: Response;
  try {
    response = await fetch(options.endpoint, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        accept: "application/json, text/event-stream",
        ...await requestHeaders(options),
      },
      redirect: "manual",
      signal: controller?.signal,
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: `${name}-${Date.now()}`,
        method: "tools/call",
        params: { name, arguments: args },
      }),
    });
  } finally {
    if (timer) clearTimeout(timer);
  }
  if (!response.ok && response.status !== 202) {
    const body = await response.text();
    const parsed = parseJson(body);
    const detail = parsed && typeof parsed === "object"
      ? (parsed as JsonObject).message ?? (parsed as JsonObject).error
      : undefined;
    throw new Error(`HTTP ${response.status}${detail ? `: ${String(detail)}` : ""}`);
  }
  if (response.status === 202) throw new Error("watcher request accepted without result");

  const outer = await response.json();
  if (outer.error) throw new Error(outer.error.message ?? JSON.stringify(outer.error));
  const result = outer.result;
  const text = result?.content?.[0]?.text;
  if (typeof text !== "string") throw new Error("missing MCP text result");
  const inner = JSON.parse(text);
  if (result.isError) throw new Error(inner.message ?? JSON.stringify(inner));
  return inner;
}

async function requestHeaders(options: Options) {
  if (!isLoopbackRelayEndpoint(options.endpoint)) {
    throw new Error("watcher endpoint must be local Coord MCP relay");
  }
  if (Object.keys(options.headers).some((name) => name.toLowerCase() === "authorization")) {
    return options.headers;
  }
  if (!runtimeBun) throw new Error("Bun file API unavailable for watcher relay token");
  const token = (await runtimeBun.file(options.relayTokenFile).text()).trim();
  if (!token) throw new Error("watcher relay token is empty");
  return { ...options.headers, authorization: `Bearer ${token}` };
}

function isLoopbackRelayEndpoint(endpoint: string) {
  try {
    const url = new URL(endpoint);
    return url.protocol === "http:"
      && ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)
      && url.pathname === "/relay/mcp";
  } catch {
    return false;
  }
}

function isNotJoinedError(message: string) {
  return /must call coord_join|not joined/i.test(message);
}

function stopWatcher(sessionID: string, roomKey: string, agentId: string) {
  const key = watcherKey(sessionID, roomKey, agentId);
  const watcher = watchers.get(key);
  if (!watcher) return;
  watcher.stopped = true;
  if (watcher.flushTimer) clearTimeout(watcher.flushTimer);
  watchers.delete(key);
}

function watcherErrorMessage(message: string) {
  const recoveryCommand = message.match(/\brun (.+)$/i)?.[1];
  if (recoveryCommand) return `coord watcher sign-in required; run ${recoveryCommand}`;
  if (/HTTP 401|HTTP 403|sign-in|authentication|token/i.test(message)) {
    return `coord watcher sign-in required; run "${dataHome}/coord-mcp/bin/coord-mcp" relay login`;
  }
  return `coord watcher relay unavailable: ${message.slice(0, 120)}`;
}

async function showToast(
  client: any,
  directory: string,
  message: string,
  variant: "info" | "warning" | "error" = "info",
) {
  await client.tui.showToast({
    query: { directory },
    body: { title: "coord-mcp", message, variant, duration: 5_000 },
  });
}

async function log(
  client: any,
  directory: string,
  options: Options,
  level: "debug" | "info" | "warn" | "error",
  message: string,
  extra?: JsonObject,
) {
  if (!options.log) return;
  try {
    await client.app.log({
      query: { directory },
      body: { service: "coord-mcp-watch", level, message, extra },
    });
  } catch {
    // Logging must never break watcher delivery.
  }
}

async function stopSessionWatchers(sessionID: string, client: any, directory: string, options: Options) {
  const leaving: Watcher[] = [];
  for (const watcher of watchers.values()) {
    if (watcher.sessionID !== sessionID) continue;
    watcher.stopped = true;
    if (watcher.flushTimer) clearTimeout(watcher.flushTimer);
    watchers.delete(watcher.key);
    leaving.push(watcher);
  }
  sessionHints.delete(sessionID);

  await Promise.all(leaving.map(async (watcher) => {
    try {
      await coordTool(options, "coord_leave", {
        roomKey: watcher.roomKey,
        agentId: watcher.agentId,
        reason: "opencode session deleted",
        idempotencyKey: `leave:${sessionID}:${watcher.roomKey}:${watcher.agentId}`,
      }, options.leaveTimeoutMs);
      await log(client, directory, options, "info", "left coord room", {
        roomKey: watcher.roomKey,
        agentId: watcher.agentId,
        sessionID,
      });
    } catch (error) {
      await log(client, directory, options, "warn", "coord_leave failed", {
        roomKey: watcher.roomKey,
        agentId: watcher.agentId,
        sessionID,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }));
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
