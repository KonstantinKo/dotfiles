# Cold critic selection

At each gate, identify the vendor of the actual material authors: plan authors for the plan gate, implementation authors for the diff gate. The orchestrator’s vendor alone does not establish authorship.

- OpenAI authors → Anthropic Claude critic.
- Anthropic authors → OpenAI Codex critic.
- Mixed or unknown authors → fresh independent reviewer; label it an independent fallback, without claiming cross-vendor review.

Prefer a supported native mechanism that can select the other vendor in a fresh read-only session. Otherwise inspect installed CLI help and use supported read-only/plan mode, such as Codex `exec --sandbox read-only` or Claude `-p --permission-mode plan --tools "Read,Glob,Grep" --strict-mcp-config` with an empty MCP configuration. Restrict CLI mutation tools and external connectors; inspect help to pass the empty configuration in the supported format. Use supported configured models; avoid pinned model versions. Give the critic access to the exact worktree/material under existing permissions. Start a new session without resume/continue flags. Never reuse an authoring session, weaken read-only restrictions, or alter trust settings to launch it.

If the other provider is unavailable, fails, or cannot safely read the target, use a fresh independent read-only reviewer and explicitly report the fallback as not cross-vendor.

Supply a bounded packet: exact plan or comparison base/head and scoped diff (including relevant uncommitted changes), acceptance criteria/validation contract, relevant project constraints, and access to necessary source. Ask the critic to challenge the weakest assumptions and give specific evidence for objections; “no substantive objections” is valid. The primary agent verifies every claim against the current material, handles confirmed issues, and repeats affected review/checks before passing the gate.
