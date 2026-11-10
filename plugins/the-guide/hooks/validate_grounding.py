#!/usr/bin/env python3
"""Post-edit hook: run the validator when a grounding doc changes in an adopted repo.

Reads one JSON object on stdin from the OMP extension (tool_name,
tool_input.file_path | tool_input.path | tool_input.paths, cwd). Finds the nearest ancestor holding
`.the-guide` for each touched grounding doc, runs the vendored-or-bundled
validator there, and prints a JSON `hookSpecificOutput.additionalContext`
only when the run has ERROR lines. Prints nothing otherwise, so a passing edit
costs no context. Never fails the tool call. Stdlib only.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE.parent / "skills" / "the-guide" / "scripts" / "validate_standard.py"
STAMP = ".the-guide"
NAMES = {"AGENTS.md", "CLAUDE.md", "PRODUCT.md", "DESIGN.md", "ARCHITECTURE.md", "REVIEW.md",
         "CHANGELOG.md", "context.yaml", STAMP}
DOC_DIR = re.compile(r"(^|/)docs/(decisions|rules|guides|reviews)/")
TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "edit", "write", "ast_edit", "multi_edit"}


def adopted_root(file):
    for d in [file.parent, *file.parent.parents]:
        if (d / STAMP).exists():
            return d
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    if event.get("tool_name") not in TOOLS:
        return
    cwd = Path(event.get("cwd") or os.getcwd())
    ti = event.get("tool_input") or {}
    raw = [ti.get("file_path"), ti.get("path"), ti.get("notebook_path")]
    if isinstance(ti.get("paths"), list):
        raw += ti["paths"]
    roots = set()
    for p in raw:
        if not isinstance(p, str):
            continue
        file = (cwd / p).resolve()
        if file.name not in NAMES and not DOC_DIR.search(file.as_posix()):
            continue
        root = adopted_root(file)
        if root:
            roots.add(root)
    reports = []
    for root in sorted(roots):
        validator = root / "scripts" / "validate_standard.py"
        if not validator.exists():
            validator = VALIDATOR
        try:
            run = subprocess.run([sys.executable, str(validator), str(root)],
                                 capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        if run.returncode != 1:
            continue
        errors = [l for l in run.stdout.splitlines() if l.startswith("ERROR")]
        if errors:
            reports.append(
                "[the-guide hook] Automatic check, not a user message: "
                f"validate_standard.py found errors after you edited grounding docs in {root}:\n"
                + "\n".join(errors) + "\nFix them before continuing.")
    if reports:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                 "additionalContext": "\n\n".join(reports)}}))


if __name__ == "__main__":
    main()
