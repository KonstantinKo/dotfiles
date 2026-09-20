import { tool, type Plugin } from "@opencode-ai/plugin";
import { readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

type Level = "lite" | "full" | "ultra" | "off";

const stateFile = join(homedir(), ".config", "opencode", ".caveman-active");

const rules: Record<Exclude<Level, "off">, string> = {
  lite: "Caveman LITE active. Use tight professional sentences. Keep articles. Drop filler, hedging, pleasantries. Preserve required format, technical terms, code, API names, error strings. Only explicit user command `stop caveman` or `normal mode` disables it.",
  full: "Caveman FULL active. Use concise fragments. Drop articles, filler, hedging, pleasantries; prefer short words. Preserve required format, technical terms, code, API names, error strings. Only explicit user command `stop caveman` or `normal mode` disables it.",
  ultra: "Caveman ULTRA active. Max compression: drop articles, filler, hedging, pleasantries, avoidable conjunctions; fragments; abbreviate prose; use X -> Y; one word when enough. Never abbreviate code/API symbols; keep error strings exact; preserve required format/substance. Only explicit user command `stop caveman` or `normal mode` disables it.",
};

const aliases: Record<string, Level> = {
  caveman: "full",
  "caveman lite": "lite",
  "caveman full": "full",
  "caveman ultra": "ultra",
  "caveman-lite": "lite",
  "caveman-full": "full",
  "caveman-ultra": "ultra",
  "caveman-off": "off",
  "stop caveman": "off",
  "normal mode": "off",
};

function isLevel(value: string): value is Level {
  return ["lite", "full", "ultra", "off"].includes(value);
}

function loadLevel(): Level {
  try {
    const value = readFileSync(stateFile, "utf8").trim();
    return isLevel(value) ? value : "full";
  } catch {
    return "full";
  }
}

function saveLevel(level: Level) {
  writeFileSync(stateFile, level, "utf8");
  return level === "off" ? "Caveman mode disabled." : `Caveman mode set to ${level}.`;
}

const cavemanSetLevel = tool({
  description: "Set response compression when user requests caveman lite/full/ultra, stop caveman, or normal mode.",
  args: {
    level: tool.schema.enum(["lite", "full", "ultra", "off"]),
  },
  async execute({ level }) {
    return saveLevel(level);
  },
});

export default (async () => ({
  tool: {
    caveman_set_level: cavemanSetLevel,
  },
  "experimental.chat.system.transform": async (_input, output) => {
    const level = loadLevel();
    if (level !== "off") output.system.push(rules[level]);
  },
  "command.execute.before": async (input, output) => {
    const raw = input.arguments.trim()
      ? `${input.command} ${input.arguments.trim()}`
      : input.command;
    const level = aliases[raw.toLowerCase().trim()];
    if (!level) return;
    output.parts.push({
      type: "text",
      id: crypto.randomUUID(),
      sessionID: input.sessionID,
      messageID: "",
      text: saveLevel(level),
    });
  },
})) satisfies Plugin;
