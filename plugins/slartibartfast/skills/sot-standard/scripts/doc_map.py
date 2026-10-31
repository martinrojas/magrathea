#!/usr/bin/env python3
"""Map changed paths to the grounding docs that own them.

Usage: doc_map.py [--root R] [--base REF] [paths ...]

Changed paths are the positional paths, else `git diff --name-only <base>` plus
untracked files (base: --base, else the merge-base with origin/HEAD, main,
master, then HEAD). Prints one JSON object: owners (doc, via, paths,
doc_changed, status), stale (owning docs not themselves changed), unowned.
Exit 0 ok; 2 usage error (not a git repo and no paths). Stdlib only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT_DOCS = ["AGENTS.md", "PRODUCT.md", "DESIGN.md", "ARCHITECTURE.md"]
DOC_DIRS = {"decisions", "rules", "guides"}
SKIP_DIRS = {"node_modules", "venv", "dist", "build", "vendor"}
COMMAND_FILES = {"package.json", "Makefile", "justfile", "Taskfile.yml", "pyproject.toml", "setup.cfg",
                 "Cargo.toml", "go.mod", ".nvmrc", ".node-version", ".python-version", ".tool-versions",
                 "pnpm-workspace.yaml"}
BD_ROW = re.compile(r"^\|\s*(BD\d+)\s*\|")
BACKTICK = re.compile(r"`([^`\n]+)`")
CITE = re.compile(r"(?<![\w./-])([\w./-]+\.[A-Za-z0-9]+)(?:#[^\s`)]*)?")
ADR_FILE = re.compile(r"^docs/decisions/\d{4}-.*\.md$")


def git(root, *args):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def norm(p, root):
    p = Path(p)
    if p.is_absolute():
        try:
            p = p.relative_to(root)
        except ValueError:
            pass
    return p.as_posix().removeprefix("./")


def changed_paths(root, base):
    if git(root, "rev-parse", "--git-dir") is None:
        return None, None
    if not base:
        for ref in ("origin/HEAD", "main", "master", "HEAD"):
            base = git(root, "merge-base", "HEAD", ref)
            if base:
                break
    paths = set(((git(root, "diff", "--name-only", base) if base else git(root, "ls-files")) or "").splitlines())
    paths |= set((git(root, "ls-files", "--others", "--exclude-standard") or "").splitlines())
    return base, sorted(paths)


def grounding_docs(root):
    docs = [d for d in ROOT_DOCS if (root / d).is_file()]
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x not in SKIP_DIRS]
        rel = Path(d).relative_to(root)
        for f in files:
            if "template" in f.lower():
                continue
            p = (rel / f).as_posix()
            in_docs = rel.parts[:1] == ("docs",) and rel.parts[1:2] and rel.parts[1] in DOC_DIRS
            is_rules_yaml = rel.parts[:2] == ("docs", "rules") and f.endswith((".yaml", ".yml"))
            if (f == "AGENTS.md" and rel.parts) or (in_docs and f.endswith(".md")) or is_rules_yaml:
                docs.append(p)
    return sorted(set(docs))


def glob_regex(glob):
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def rule_globs(text):
    globs, inside = [], False
    for line in text.splitlines():
        if re.match(r"^paths:\s*(#.*)?$", line):
            inside = True
            continue
        if not inside:
            continue
        m = re.match(r"^\s+-\s+(.*)$", line)
        if not m:
            break
        value = re.sub(r"\s+#.*$", "", m.group(1)).strip().strip("'\"")
        if value and not value.startswith("<"):
            globs.append(value.removeprefix("./"))
    return globs


def boundary_tokens(row):
    cells = row.split("|")
    if len(cells) < 3:
        return []
    cell = cells[2]
    tokens = BACKTICK.findall(cell)
    tokens += [t for t in re.split(r"[\s,;]+", BACKTICK.sub(" ", cell)) if "/" in t]
    out = []
    for t in tokens:
        t = t.strip()
        if not t or t.startswith("<"):
            continue
        t = t.replace("**", "")
        t = re.sub(r"^\./", "", t).rstrip("/")
        if t:
            out.append(t)
    return out


def cited_files(text):
    found = set()
    for span in BACKTICK.findall(text):
        span = span.strip()
        m = CITE.match(span)
        if m and span[m.end(1):m.end(1) + 1] in ("", "#"):
            found.add(m.group(1))
    found |= {m.group(1) for m in CITE.finditer(text) if "#" in m.group(0)}
    return {f.removeprefix("./") for f in found}


def status(text):
    m = re.search(r"^status:\s*(\w+)", text, re.M)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--base")
    ap.add_argument("paths", nargs="*")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    if a.paths:
        base, changed = None, sorted({norm(p, root) for p in a.paths})
    else:
        base, changed = changed_paths(root, a.base)
        if changed is None:
            print("not a git repository; pass changed paths explicitly", file=sys.stderr)
            sys.exit(2)

    docs = grounding_docs(root)
    doc_set, changed_set = set(docs), set(changed)
    code = [p for p in changed if p not in doc_set]
    texts = {d: (root / d).read_text(encoding="utf-8", errors="replace") for d in docs}

    owners = {}

    def own(doc, via, path):
        e = owners.setdefault(doc, {"via": [], "paths": []})
        if via not in e["via"]:
            e["via"].append(via)
        if path not in e["paths"]:
            e["paths"].append(path)

    for d in docs:
        if d.startswith("docs/rules/"):
            for glob in rule_globs(texts[d]):
                rx = glob_regex(glob)
                for p in code:
                    if rx.match(p):
                        own(d, f"paths: {glob}", p)
    if "ARCHITECTURE.md" in texts:
        for row in texts["ARCHITECTURE.md"].splitlines():
            m = BD_ROW.match(row)
            if not m:
                continue
            for token in boundary_tokens(row):
                for p in code:
                    if p == token or p.startswith(token + "/"):
                        own("ARCHITECTURE.md", m.group(1), p)
    for d in docs:
        for cited in cited_files(texts[d]) & set(code):
            own(d, f"cites {cited}", cited)
    for p in code:
        if Path(p).name in COMMAND_FILES:
            for parent in [Path(p).parent, *Path(p).parent.parents]:
                cand = (parent / "AGENTS.md").as_posix()
                if cand in doc_set:
                    own(cand, "commands", p)
                    break

    out = []
    for d in sorted(owners):
        out.append({"doc": d, "via": owners[d]["via"], "paths": sorted(owners[d]["paths"]),
                    "doc_changed": d in changed_set,
                    "status": status(texts[d]) if ADR_FILE.match(d) else None})
    owned = {p for e in owners.values() for p in e["paths"]}
    print(json.dumps({
        "base": base, "changed": changed, "owners": out,
        "stale": [o["doc"] for o in out if not o["doc_changed"]],
        "unowned": [p for p in code if p not in owned],
    }))


if __name__ == "__main__":
    main()
