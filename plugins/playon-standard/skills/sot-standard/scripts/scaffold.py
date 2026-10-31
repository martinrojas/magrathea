#!/usr/bin/env python3
"""Write the Source-of-Truth Standard's files into a repo.

Usage:
  scaffold.py init [root] --with <csv>        csv of: product architecture decisions review context ui (may be "")
  scaffold.py package <pkgdir> [--root R] [--review]
  scaffold.py upgrade [root] [--finish]

Prints one JSON object. Exit 0 ok; 1 domain failure; 2 usage error.
Stdlib only.
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
TOKENS = {"product", "architecture", "decisions", "review", "context", "ui"}
VERSION = re.compile(r"^\d+\.\d+\.\d+$")

# Files each token adds, relative to the template root.
FILES = {
    "product": ["PRODUCT.md", "docs/rules/TEMPLATE.yaml"],
    "architecture": ["ARCHITECTURE.md"],
    "decisions": ["docs/decisions/README.md", "docs/decisions/0000-template.md"],
    "review": ["REVIEW.md"],
    "context": ["context.yaml"],
    "ui": [],
}
# AGENTS.md section 1 rows, by line prefix, kept only when their token is present.
AGENTS_ROWS = {
    "product": ["| [`PRODUCT.md`](./PRODUCT.md) |", "| `docs/rules/<domain>.yaml` |"],
    "ui": ["| [`DESIGN.md`](./DESIGN.md) |"],
    "architecture": ["| [`ARCHITECTURE.md`](./ARCHITECTURE.md) |"],
    "decisions": ["| [`docs/decisions/`](./docs/decisions/README.md) |"],
}
REVIEW_HEADING = "## 7. Code Review"
DONE_HEADING = "## 8. Definition of done"
AGENTS_CONTEXT_LINE = "Companion repos a reviewer needs: `context.yaml`."
REVIEW_CONTEXT = ["Companion repos a reviewer needs open to judge a change (and why) are listed",
                  "once, in [`context.yaml`](./context.yaml); do not restate them here."]
ARCH_CONTEXT = ["Related repos a change here can break are listed once, in `context.yaml`",
                "(repo, paths, why). Do not restate them here; add a row there."]

PKG_AGENTS = """@{up}AGENTS.md

# AGENTS.md — {pkg}

Only what differs from the root `AGENTS.md`; everything else is inherited.

## Commands

- Test: `<command>`
"""
PKG_AGENTS_REVIEW = """
## Code Review

- <invariant that applies only to this package>
"""
PKG_REVIEW = """@{up}REVIEW.md

# Code Review Policy — {pkg}

Only what differs from the root `REVIEW.md`.
"""


class Fail(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code


def marker_missing(marker):
    return Fail(f"template marker not found: {marker}")


def find_line(lines, prefix):
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            return i
    raise marker_missing(prefix)


def drop_paragraph(lines, pair):
    """Delete the two consecutive lines starting with `pair` and the blank line before them."""
    i = find_line(lines, pair[0])
    if i == 0 or lines[i - 1].strip() or i + 1 >= len(lines) or not lines[i + 1].startswith(pair[1]):
        raise marker_missing(pair[0])
    del lines[i - 1:i + 2]


def transform_agents(text, tokens):
    lines = text.split("\n")
    for token, prefixes in AGENTS_ROWS.items():
        for prefix in prefixes:
            i = find_line(lines, prefix)
            if token not in tokens:
                del lines[i]
    if "review" not in tokens:
        start, end = find_line(lines, REVIEW_HEADING), find_line(lines, DONE_HEADING)
        lines[start:end] = []
        lines[start] = "## 7. Definition of done"
    elif "context" not in tokens:
        if AGENTS_CONTEXT_LINE not in lines:
            raise marker_missing(AGENTS_CONTEXT_LINE)
        lines.remove(AGENTS_CONTEXT_LINE)
    return "\n".join(lines)


def transform_review(text, tokens):
    lines = text.split("\n")
    if "context" not in tokens:
        drop_paragraph(lines, REVIEW_CONTEXT)
    return "\n".join(lines)


def transform_architecture(text, tokens):
    lines = text.split("\n")
    if "context" not in tokens:
        drop_paragraph(lines, ARCH_CONTEXT)
    return "\n".join(lines)


TRANSFORMS = {"AGENTS.md": transform_agents, "REVIEW.md": transform_review,
              "ARCHITECTURE.md": transform_architecture}


def template_stamp():
    return (TEMPLATES / ".sot-standard").read_text(encoding="utf-8").strip()


def cmd_init(a):
    root = Path(a.root).resolve()
    tokens = {t for t in a.with_.split(",") if t}
    unknown = tokens - TOKENS
    if unknown:
        raise Fail(f"unknown --with token(s): {', '.join(sorted(unknown))}", 2)
    if "context" in tokens and "review" not in tokens:
        raise Fail("context requires review", 2)

    rels = ["AGENTS.md", "CLAUDE.md"] + [f for t in sorted(tokens) for f in FILES[t]]
    created, skipped, writes = [], [], []
    for rel in rels + [".sot-standard", "scripts/validate_standard.py"]:
        (skipped if (root / rel).exists() else created).append(rel)
    # Build every file before writing any, so a missing marker leaves the repo untouched.
    for rel in created:
        if rel == ".sot-standard":
            data = (template_stamp() + "\n").encode()
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
    return {"created": created, "skipped": skipped, "stamp": template_stamp()}


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
    if a.review and not (root / "REVIEW.md").exists():
        raise Fail("root REVIEW.md missing; run init with review first")
    pkg, up = "/".join(parts), "../" * len(parts)
    files = {"AGENTS.md": PKG_AGENTS.format(up=up, pkg=pkg) + (PKG_AGENTS_REVIEW if a.review else "")}
    if a.review:
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


def cmd_upgrade(a):
    root = Path(a.root).resolve()
    stamp_file = root / ".sot-standard"
    if not stamp_file.exists():
        raise Fail("not adopted: no .sot-standard; use adopt-standard")
    repo, current = stamp_file.read_text(encoding="utf-8").strip(), template_stamp()
    if not VERSION.match(repo):
        raise Fail(f"invalid .sot-standard {repo!r}; expected a version like {current}")
    if vtuple(repo) > vtuple(current):
        raise Fail(f"repo stamp {repo} is newer than the plugin's {current}; update the plugin")
    if a.finish:
        stamp_file.write_text(current + "\n", encoding="utf-8")
        return {"stamp": current}
    refreshed = False
    target = root / "scripts" / "validate_standard.py"
    if not target.exists() or target.read_bytes() != VALIDATOR.read_bytes():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(VALIDATOR.read_bytes())
        refreshed = True
    notes = sorted(
        (vtuple(p.stem), str(p)) for p in UPGRADES.glob("*.md")
        if VERSION.match(p.stem) and vtuple(repo) < vtuple(p.stem) <= vtuple(current))
    return {"from": repo, "to": current, "notes": [p for _, p in notes],
            "validator_refreshed": refreshed}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--with", dest="with_", required=True, help="csv of tokens; may be empty")
    p.set_defaults(fn=cmd_init)
    p = sub.add_parser("package")
    p.add_argument("pkgdir")
    p.add_argument("--root", default=".")
    p.add_argument("--review", action="store_true")
    p.set_defaults(fn=cmd_package)
    p = sub.add_parser("upgrade")
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--finish", action="store_true")
    p.set_defaults(fn=cmd_upgrade)
    a = ap.parse_args()
    try:
        print(json.dumps(a.fn(a)))
    except Fail as e:
        print(str(e), file=sys.stderr)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
