// OMP extension: forwards edit/write tool results to the shared Python hook.
// Declared in package.json under omp.extensions. The Python script decides
// whether a grounding doc in an adopted repo was touched and prints a JSON
// object with additionalContext only on validator errors.
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import * as path from "node:path";

const HOOK = path.join(import.meta.dir, "..", "validate_grounding.py");
const TOOLS = new Set(["edit", "write", "ast_edit", "multi_edit"]);

export default function (pi: ExtensionAPI) {
	pi.on("tool_result", async (event, ctx) => {
		try {
			if (event.isError || !TOOLS.has(event.toolName)) return undefined;
			const payload = JSON.stringify({ tool_name: event.toolName, tool_input: event.input, cwd: ctx.cwd });
			const run = Bun.spawnSync(["python3", HOOK], { stdin: new TextEncoder().encode(payload), timeout: 30000 });
			const out = run.stdout.toString().trim();
			if (!out) return undefined;
			const parsed = JSON.parse(out) as { hookSpecificOutput?: { additionalContext?: string } };
			const text = parsed.hookSpecificOutput?.additionalContext;
			return text ? { additionalContext: text } : undefined;
		} catch {
			return undefined;
		}
	});
}
