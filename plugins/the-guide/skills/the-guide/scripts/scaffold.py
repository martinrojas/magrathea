#!/usr/bin/env python3
"""Write the Source-of-Truth Standard's files into a repo.

Usage:
  scaffold.py init [root] --with <csv> [--size S]
      csv of: product architecture decisions ui review changelog (may be "")
      size: small | software | monorepo | docs (default: docs when product is
      absent, else software)
  scaffold.py package <pkgdir> [--root R] [--review]
  scaffold.py upgrade [root] [--finish] [--upgrades DIR]

Prints one JSON object. Exit 0 ok; 1 domain failure; 2 usage error.
Stdlib only.

init never overwrites: existing files are listed under "skipped". AGENTS.md
rows and sections for tokens you did not choose are removed so the router only
points at files that exist.

upgrade refreshes the vendored validator, applies the machine-readable `ops`
of every upgrade note between the repo's stamp and the plugin's (idempotent
line inserts and replacements), and lists the notes whose prose still needs an
agent. --finish writes the new stamp.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "templates"
UPGRADES = HERE.parent / "upgrades"
VALIDATOR = HERE / "validate_standard.py"
STAMP_FILE = ".the-guide"
TOKENS = {"product", "architecture", "decisions", "ui", "review", "changelog"}
SIZES = {"small", "software", "monorepo", "docs"}
VERSION = re.compile(r"^\d+\.\d+\.\d+$")

# Files each token adds, relative to the template root.
FILES = {
    "product": ["PRODUCT.md", "docs/rules/TEMPLATE.yaml"],
    "architecture": ["ARCHITECTURE.md"],
    "decisions": ["docs/decisions/README.md", "docs/decisions/0000-template.md"],
    "ui": ["DESIGN.md"],
    "review": ["REVIEW.md", "context.yaml"],
    "changelog": ["CHANGELOG.md"],
}
# AGENTS.md lines, by prefix, kept only when their token is present.
AGENTS_LINES = {
    "product": ["| [`PRODUCT.md`](./PRODUCT.md) |", "| `docs/rules/<domain>.yaml` |",
                "- Use glossary terms from `PRODUCT.md`",
                "- Behavior matches the domain's rules"],
    "ui": ["| [`DESIGN.md`](./DESIGN.md) |"],
    "architecture": ["| [`ARCHITECTURE.md`](./ARCHITECTURE.md) |"],
    "decisions": ["| [`docs/decisions/`](./docs/decisions/README.md) |"],
    "changelog": ["| [`CHANGELOG.md`](./CHANGELOG.md) |",
                  "- User-visible changes have an entry under `Unreleased`"],
}
# AGENTS.md sections (## heading) kept only when their token is present.
AGENTS_SECTIONS = {"review": "## Code Review"}

PKG_AGENTS = """@{up}AGENTS.md

# AGENTS.md — {pkg}

Only what differs from the root `AGENTS.md`; everything else is inherited.
Automated reviewers inject this file together with the root one for changes
under this directory, so review invariants specific to this package go here.

## Commands

- Test: `<command>`
"""

PKG_REVIEW = """@{up}REVIEW.md

# Code Review Policy — {pkg}

Only what differs from the root `REVIEW.md`.
"""


class Fail(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code


def find_line(lines, prefix):
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            return i
    raise Fail(f"template marker not found: {prefix}")


def drop_section(lines, heading):
    start = find_line(lines, heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    del lines[start:end]
    return lines


def transform_agents(text, tokens):
    lines = text.split("\n")
    for token, prefixes in AGENTS_LINES.items():
        for prefix in prefixes:
            i = find_line(lines, prefix)
            if token not in tokens:
                del lines[i]
    for token, heading in AGENTS_SECTIONS.items():
        find_line(lines, heading)
        if token not in tokens:
            drop_section(lines, heading)
    if "review" not in tokens:
        i = find_line(lines, "| This file |")
        lines[i] = lines[i].replace("conventions, review, done", "conventions, done")
    return "\n".join(lines)


def transform_architecture(text, tokens):
    if "review" in tokens:
        return text
    # Without a review layer there is no context.yaml to point at.
    return text.replace(
        "Related repos a change here can break are listed once, in `context.yaml`\n"
        "(repo, paths, why). Do not restate them here; add a row there.\n",
        "Related repos a change here can break: list them here (repo, paths, why),\n"
        "or add `context.yaml` and point at it once the repo is reviewed.\n")


TRANSFORMS = {"AGENTS.md": transform_agents, "ARCHITECTURE.md": transform_architecture}


def template_stamp():
    return (TEMPLATES / STAMP_FILE).read_text(encoding="utf-8").strip().splitlines()[0]


def read_stamp(root):
    p = root / STAMP_FILE
    lines = [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    version = lines[0] if lines else ""
    size = next((m.group(1) for m in (re.match(r"^size:\s*(\w+)$", x) for x in lines[1:]) if m), None)
    return version, size


def write_stamp(root, version, size):
    text = version + "\n" + (f"size: {size}\n" if size else "")
    (root / STAMP_FILE).write_text(text, encoding="utf-8")


def cmd_init(a):
    root = Path(a.root).resolve()
    tokens = {t for t in a.with_.split(",") if t}
    unknown = tokens - TOKENS
    if unknown:
        raise Fail(f"unknown --with token(s): {', '.join(sorted(unknown))}", 2)
    size = a.size or ("docs" if "product" not in tokens else "software")
    if size not in SIZES:
        raise Fail(f"unknown --size {size!r}; one of {sorted(SIZES)}", 2)

    rels = ["AGENTS.md", "CLAUDE.md"] + [f for t in sorted(tokens) for f in FILES[t]]
    created, skipped, writes = [], [], []
    for rel in rels + [STAMP_FILE, "scripts/validate_standard.py"]:
        (skipped if (root / rel).exists() else created).append(rel)
    # Build every file before writing any, so a missing marker leaves the repo untouched.
    for rel in created:
        if rel == STAMP_FILE:
            data = (template_stamp() + "\n" + f"size: {size}\n").encode()
        elif rel == "scripts/validate_standard.py":
            data = VALIDATOR.read_bytes()
        elif rel in TRANSFORMS:
            data = TRANSFORMS[rel]((TEMPLATES / rel).read_text(encoding="utf-8"), tokens).encode()
        else:
            data = (TEMPLATES / rel).read_bytes()
        writes.append((root / rel, data))
    for path, data in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return {"created": created, "skipped": skipped, "stamp": template_stamp(), "size": size}


def cmd_package(a):
    root = Path(a.root).resolve()
    pkg_path = (root / a.pkgdir).resolve()
    if Path(a.pkgdir).is_absolute() or not pkg_path.is_dir():
        raise Fail("pkgdir must be an existing directory relative to root", 2)
    try:
        parts = pkg_path.relative_to(root).parts
    except ValueError:
        raise Fail("pkgdir must be inside root", 2)
    if not parts:
        raise Fail("pkgdir must not be the root", 2)
    pkg, up = "/".join(parts), "../" * len(parts)
    files = {"AGENTS.md": PKG_AGENTS.format(up=up, pkg=pkg)}
    if a.review:
        if not (root / "REVIEW.md").exists():
            raise Fail("--review needs a root REVIEW.md (init with the review token)")
        files["REVIEW.md"] = PKG_REVIEW.format(up=up, pkg=pkg)
    created, skipped = [], []
    for name, text in files.items():
        target = pkg_path / name
        rel = f"{pkg}/{name}"
        if target.exists():
            skipped.append(rel)
        else:
            target.write_text(text, encoding="utf-8")
            created.append(rel)
    return {"created": created, "skipped": skipped}


def vtuple(v):
    return tuple(int(x) for x in v.split("."))


def note_ops(path):
    """Parse the optional ```ops json block of an upgrade note."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^```ops\n(.*?)\n```", text, re.S | re.M)
    if not m:
        return []
    try:
        ops = json.loads(m.group(1))
    except ValueError as e:
        raise Fail(f"{path.name}: ops block is not valid JSON: {e}")
    if not isinstance(ops, list):
        raise Fail(f"{path.name}: ops block must be a JSON list")
    return ops


def apply_ops(root, ops):
    """Apply idempotent line edits. Each op: {file, op, match, line}.

    op "insert_after": add `line` after the first line starting with `match`,
        unless a line starting with `line`'s first 24 chars already exists.
    op "replace": replace the first line starting with `match` with `line`.
    Files that do not exist are skipped (the repo did not adopt them).
    Returns the list of ops applied.
    """
    applied = []
    for op in ops:
        for key in ("file", "op", "match", "line"):
            if key not in op:
                raise Fail(f"upgrade op missing {key!r}: {op}")
        p = root / op["file"]
        if not p.exists():
            continue
        lines = p.read_text(encoding="utf-8").split("\n")
        idx = next((i for i, l in enumerate(lines) if l.startswith(op["match"])), None)
        if idx is None:
            continue
        if op["op"] == "insert_after":
            key = op["line"][:24]
            if any(l.startswith(key) for l in lines):
                continue
            lines.insert(idx + 1, op["line"])
        elif op["op"] == "replace":
            if lines[idx] == op["line"]:
                continue
            lines[idx] = op["line"]
        else:
            raise Fail(f"unknown upgrade op {op['op']!r}")
        p.write_text("\n".join(lines), encoding="utf-8")
        applied.append(f"{op['file']}: {op['op']} {op['match'][:40]}")
    return applied


def cmd_upgrade(a):
    root = Path(a.root).resolve()
    if not (root / STAMP_FILE).exists():
        raise Fail(f"not adopted: no {STAMP_FILE}; use adopt-standard")
    repo, size = read_stamp(root)
    current = template_stamp()
    if not VERSION.match(repo):
        raise Fail(f"invalid {STAMP_FILE} {repo!r}; expected a version like {current}")
    if vtuple(repo) > vtuple(current):
        raise Fail(f"repo stamp {repo} is newer than the plugin's {current}; update the plugin")
    if a.finish:
        write_stamp(root, current, size)
        return {"stamp": current, "size": size}
    refreshed = False
    target = root / "scripts" / "validate_standard.py"
    if not target.exists() or target.read_bytes() != VALIDATOR.read_bytes():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(VALIDATOR.read_bytes())
        refreshed = True
    upgrades = Path(a.upgrades) if a.upgrades else UPGRADES
    notes = sorted(
        (vtuple(p.stem), p) for p in upgrades.glob("*.md")
        if VERSION.match(p.stem) and vtuple(repo) < vtuple(p.stem) <= vtuple(current))
    applied, manual = [], []
    for _, p in notes:
        applied += apply_ops(root, note_ops(p))
        text = p.read_text(encoding="utf-8")
        if re.search(r"^## Manual", text, re.M):
            manual.append(str(p))
    return {"from": repo, "to": current, "applied": applied, "manual_notes": manual,
            "validator_refreshed": refreshed}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--with", dest="with_", required=True, help="csv of tokens; may be empty")
    p.add_argument("--size", help="small | software | monorepo | docs")
    p.set_defaults(fn=cmd_init)
    p = sub.add_parser("package")
    p.add_argument("pkgdir")
    p.add_argument("--root", default=".")
    p.add_argument("--review", action="store_true", help="also write a package REVIEW.md")
    p.set_defaults(fn=cmd_package)
    p = sub.add_parser("upgrade")
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--finish", action="store_true")
    p.add_argument("--upgrades", help="directory of upgrade notes (default: the plugin's)")
    p.set_defaults(fn=cmd_upgrade)
    a = ap.parse_args()
    try:
        print(json.dumps(a.fn(a)))
    except Fail as e:
        print(str(e), file=sys.stderr)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
