import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import * as fs from "node:fs";
import * as path from "node:path";

const VALIDATOR = path.join(import.meta.dir, "..", "..", "skills", "sot-standard", "scripts", "validate_standard.py");
const NAMES = new Set(["AGENTS.md", "CLAUDE.md", "PRODUCT.md", "DESIGN.md", "ARCHITECTURE.md", ".sot-standard"]);
const DOC_DIR = /(^|\/)docs\/(decisions|rules|guides)\//;

/** Nearest ancestor directory holding `.sot-standard`, or undefined when the repo has not adopted the standard. */
function adoptedRoot(file: string): string | undefined {
	for (let dir = path.dirname(file); ; dir = path.dirname(dir)) {
		if (fs.existsSync(path.join(dir, ".sot-standard"))) return dir;
		if (dir === path.dirname(dir)) return undefined;
	}
}

export default function (pi: ExtensionAPI) {
	pi.on("tool_result", async (event, ctx) => {
		try {
			if (event.isError || !["edit", "write", "ast_edit"].includes(event.toolName)) return undefined;
			const input = event.input as { path?: unknown; paths?: unknown };
			const raw = [input.path, ...(Array.isArray(input.paths) ? input.paths : [])];
			const roots = new Set<string>();
			for (const p of raw) {
				if (typeof p !== "string") continue;
				const file = path.resolve(ctx.cwd, p);
				if (!NAMES.has(path.basename(file)) && !DOC_DIR.test(file)) continue;
				const root = adoptedRoot(file);
				if (root) roots.add(root);
			}
			const reports: string[] = [];
			for (const root of roots) {
				const run = Bun.spawnSync(["python3", VALIDATOR, root], { timeout: 20000 });
				if (run.exitCode !== 1) continue;
				const errors = run.stdout.toString().split("\n").filter(line => line.startsWith("ERROR"));
				if (errors.length) {
					reports.push(`[slartibartfast hook] Automatic check, not a user message: validate_standard.py found errors after you edited grounding docs in ${root}:\n${errors.join("\n")}\nFix them before continuing.`);
				}
			}
			return reports.length ? { additionalContext: reports.join("\n\n") } : undefined;
		} catch {
			return undefined;
		}
	});
}
