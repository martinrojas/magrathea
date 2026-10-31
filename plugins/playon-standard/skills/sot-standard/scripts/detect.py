#!/usr/bin/env python3
"""Print one JSON object of facts about a repo, for adopt-standard.

Usage: python3 detect.py [root]

Exit 0 always for a readable root; parse problems go in the "errors" list.
Stdlib only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "dist", "build", "vendor", "venv", ".venv"}
CODE_EXTS = {"py", "js", "ts", "tsx", "jsx", "go", "rs", "java", "kt", "rb", "php",
             "cs", "swift", "tf", "vue", "svelte"}
UI_FILE_EXTS = {"tsx", "jsx", "vue", "svelte"}
UI_DEPS = ["react", "react-dom", "vue", "svelte", "@angular/core", "next", "nuxt",
           "solid-js", "preact", "astro", "react-native", "expo"]
STACK_MARKERS = [
    ("node", ["package.json"]),
    ("python", ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"]),
    ("go", ["go.mod"]),
    ("rust", ["Cargo.toml"]),
    ("jvm", ["pom.xml", "build.gradle", "build.gradle.kts"]),
    ("ruby", ["Gemfile"]),
    ("php", ["composer.json"]),
]
LOCKFILES = [
    ("pnpm", ["pnpm-lock.yaml"]),
    ("yarn", ["yarn.lock"]),
    ("bun", ["bun.lock", "bun.lockb"]),
    ("npm", ["package-lock.json"]),
    ("poetry", ["poetry.lock"]),
    ("uv", ["uv.lock"]),
    ("pipenv", ["Pipfile.lock"]),
]
RUNTIME_FILES = [".nvmrc", ".node-version", ".python-version", ".tool-versions"]
EXISTING = ["AGENTS.md", "CLAUDE.md", "PRODUCT.md", "DESIGN.md", "ARCHITECTURE.md",
            "REVIEW.md", "context.yaml", ".sot-standard",
            "scripts/validate_standard.py", "docs/decisions/README.md"]
SOURCE_CAP = 5000
MAKE_TARGET = re.compile(r"^([A-Za-z0-9_.-]+):(?!=)")
REVIEW_HEADING = re.compile(r"^##\s+(?:\d+\.\s*)?Code Review", re.M)
REMOTE = re.compile(r"[:/]([^/:]+/[^/]+?)(?:\.git)?/?$")


def read_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        errors.append(f"{path.name}: {e}")
        return {}


def git_remote(root):
    try:
        out = subprocess.run(["git", "-C", str(root), "config", "--get", "remote.origin.url"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    m = REMOTE.search(out)
    return m.group(1) if m else None


def walk(root):
    """One pass: (terraform at depth <= 1, source file count, first UI file)."""
    tf, count, ui_file = False, 0, None
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x not in SKIP_DIRS]
        depth = len(Path(d).relative_to(root).parts)
        for f in files:
            ext = f.rsplit(".", 1)[-1] if "." in f else ""
            if ext == "tf" and depth <= 1:
                tf = True
            if ext in CODE_EXTS and count < SOURCE_CAP:
                count += 1
            if ext in UI_FILE_EXTS and ui_file is None:
                ui_file = str((Path(d) / f).relative_to(root))
        if count >= SOURCE_CAP and ui_file is not None:
            break
    return tf, count, ui_file


def expand(root, patterns):
    found = set()
    for pat in patterns:
        pat = pat.strip().strip("'\"")
        if not pat or pat.startswith("!"):
            continue
        pat = pat[2:] if pat.startswith("./") else pat
        pat = pat.rstrip("/")
        if not pat or pat.startswith("/") or ".." in Path(pat).parts:
            continue
        for p in root.glob(pat):
            rel = p.relative_to(root)
            if p.is_dir() and "node_modules" not in rel.parts:
                found.add(rel.as_posix())
    return sorted(found)


def yaml_list(text, key):
    """Items of a top-level `key:` block list, without a YAML parser."""
    items, inside = [], False
    for line in text.splitlines():
        if re.match(rf"^{key}\s*:\s*$", line):
            inside = True
        elif inside:
            m = re.match(r"^\s+-\s+(.+?)\s*(?:#.*)?$", line)
            if m:
                items.append(m.group(1))
            elif line.strip() and not line.lstrip().startswith("#"):
                break
    return items


def workspace_patterns(root, pkg):
    pats = []
    ws = root / "pnpm-workspace.yaml"
    if ws.exists():
        pats += yaml_list(ws.read_text(encoding="utf-8"), "packages")
    w = pkg.get("workspaces")
    if isinstance(w, dict):
        w = w.get("packages")
    if isinstance(w, list):
        pats += [x for x in w if isinstance(x, str)]
    gw = root / "go.work"
    if gw.exists():
        text = gw.read_text(encoding="utf-8")
        for m in re.finditer(r"^use\s*\((.*?)^\)", text, re.M | re.S):
            pats += [x.strip() for x in m.group(1).splitlines()
                     if x.strip() and not x.strip().startswith("//")]
        pats += re.findall(r"^use\s+([^\s(]+)", text, re.M)
    cargo = root / "Cargo.toml"
    if cargo.exists():
        m = re.search(r"^members\s*=\s*\[(.*?)\]", cargo.read_text(encoding="utf-8"), re.M | re.S)
        if m:
            pats += re.findall(r"[\"']([^\"']+)[\"']", m.group(1))
    return pats


def make_targets(root):
    mk = root / "Makefile"
    if not mk.exists():
        return None
    targets = []
    for line in mk.read_text(encoding="utf-8", errors="replace").splitlines():
        m = MAKE_TARGET.match(line)
        if m and not m.group(1).startswith(".") and m.group(1) not in targets:
            targets.append(m.group(1))
    return targets


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", nargs="?", default=".")
    root = Path(ap.parse_args().root).resolve()
    errors = []

    pkg = read_json(root / "package.json", errors) if (root / "package.json").exists() else {}
    if not isinstance(pkg, dict):
        pkg = {}
    tf, source_files, ui_file = walk(root)

    stack = {name for name, marks in STACK_MARKERS if any((root / m).exists() for m in marks)}
    if tf:
        stack.add("terraform")

    runtime = {}
    for f in RUNTIME_FILES:
        if (root / f).exists():
            runtime[f] = (root / f).read_text(encoding="utf-8", errors="replace").strip()
    if isinstance(pkg.get("engines"), dict):
        runtime["engines"] = pkg["engines"]

    commands = {}
    if isinstance(pkg.get("scripts"), dict):
        commands["package.json"] = pkg["scripts"]
    targets = make_targets(root)
    if targets is not None:
        commands["make"] = targets

    deps = {}
    for k in ("dependencies", "devDependencies"):
        if isinstance(pkg.get(k), dict):
            deps.update(pkg[k])
    ui_deps = [d for d in UI_DEPS if d in deps]
    ui_evidence = ui_deps or ([ui_file] if ui_file else None)

    packages = expand(root, workspace_patterns(root, pkg))

    reviewed = [f for f in ("REVIEW.md", "context.yaml") if (root / f).exists()]
    agents = root / "AGENTS.md"
    if agents.exists() and REVIEW_HEADING.search(agents.read_text(encoding="utf-8", errors="replace")):
        reviewed.append("AGENTS.md Code Review section")

    existing = [f for f in EXISTING if (root / f).exists()]
    rules = sorted((root / "docs" / "rules").glob("*.yaml")) if (root / "docs" / "rules").is_dir() else []
    existing += [p.relative_to(root).as_posix() for p in rules]
    claude = root / "CLAUDE.md"
    shim = claude.exists() and claude.read_text(encoding="utf-8", errors="replace").strip() == "@AGENTS.md"

    if len(packages) >= 2:
        size = "monorepo"
    elif not stack and source_files == 0:
        size = "docs"
    elif source_files < 50:
        size = "small"
    else:
        size = "software"

    print(json.dumps({
        "root": str(root),
        "git_remote": git_remote(root),
        "stack": sorted(stack),
        "package_manager": [n for n, marks in LOCKFILES if any((root / m).exists() for m in marks)],
        "runtime": runtime,
        "commands": commands,
        "packages": packages,
        "ui": bool(ui_evidence),
        "ui_evidence": ui_evidence,
        "reviewed_evidence": reviewed,
        "existing": existing,
        "claude_md_is_shim": shim,
        "source_files": source_files,
        "suggested_size": size,
        "errors": errors,
    }))


if __name__ == "__main__":
    sys.exit(main())
