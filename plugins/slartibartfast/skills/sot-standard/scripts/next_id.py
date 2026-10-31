#!/usr/bin/env python3
"""Allocate the next decision-record or domain-rule id.

Usage:
  next_id.py adr "<title>" [--root R] [--supersedes ADR-NNNN] [--date YYYY-MM-DD]
      create docs/decisions/NNNN-slug.md (status: proposed) and its index row;
      prints {"id": ..., "path": ...}
  next_id.py br <domain> [--root R]    print the next BR-<domain>-N
  next_id.py sd <domain> [--root R]    print the next SD-<domain>-N

Numbers are never reused: the maximum is taken over files, the index, and, for
rules, every mention in the domain's rules file (comments included).
Exit 0 ok; 1 domain failure; 2 usage error. Stdlib only.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "docs" / "decisions" / "0000-template.md"
DOMAIN = re.compile(r"^[a-z][a-z0-9_]*$")
ADR_ID = re.compile(r"^ADR-(\d{4})$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NONE_ROW = "| _none yet_ |"


class Fail(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code


def set_front_matter(text, key, value):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise Fail("record has no front matter")
    block, line = m.group(1), f"{key}: {value}"
    pat = re.compile(rf"^{key}:.*$", re.M)
    block = pat.sub(lambda _: line, block, count=1) if pat.search(block) else block + "\n" + line
    return "---\n" + block + "\n---\n" + text[m.end():]


def split_row(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def join_row(cells):
    return "| " + " | ".join(cells) + " |"


def adr(a):
    root = Path(a.root).resolve()
    decisions = root / "docs" / "decisions"
    readme = decisions / "README.md"
    if not readme.exists() or "## Index" not in readme.read_text(encoding="utf-8"):
        raise Fail("docs/decisions/README.md with an ## Index section is required; "
                   "run adopt-standard with decisions")
    if a.supersedes and not ADR_ID.match(a.supersedes):
        raise Fail("--supersedes must look like ADR-0001", 2)
    if a.date and not DATE.match(a.date):
        raise Fail("--date must be YYYY-MM-DD", 2)
    slug = re.sub(r"[^a-z0-9]+", "-", a.title.lower()).strip("-")[:50].strip("-")
    if not slug:
        raise Fail("title must contain letters or digits", 2)
    today = a.date or date.today().isoformat()

    lines = readme.read_text(encoding="utf-8").split("\n")
    idx = lines.index("## Index")
    numbers = [int(p.name[:4]) for p in decisions.glob("[0-9][0-9][0-9][0-9]-*.md")
               if p.name != "0000-template.md"]
    numbers += [int(n) for line in lines[idx:] for n in re.findall(r"ADR-(\d{4})", line)]
    new_id = f"ADR-{max(numbers, default=0) + 1:04d}"
    path = decisions / f"{new_id[4:]}-{slug}.md"

    tpl = decisions / "0000-template.md"
    body = (tpl if tpl.exists() else TEMPLATE).read_text(encoding="utf-8")
    body = body.replace("ADR-0000", new_id).replace("<Short decision title>", a.title)
    body = re.sub(r"^relates_to:.*$", "relates_to: []", body, count=1, flags=re.M)
    body = re.sub(r"^date:.*$", lambda _: f"date: {today}", body, count=1, flags=re.M)
    if a.supersedes:
        body = re.sub(r"^supersedes:.*$", lambda _: f"supersedes: {a.supersedes}", body, count=1, flags=re.M)

    old_path = None
    if a.supersedes:
        matches = sorted(decisions.glob(f"{a.supersedes[4:]}-*.md"))
        if not matches:
            raise Fail(f"{a.supersedes} not found in docs/decisions/")
        old_path = matches[0]

    row = join_row([new_id, a.title, "proposed", today, f"supersedes {a.supersedes}" if a.supersedes else ""])
    none_at = next((i for i, l in enumerate(lines) if l.startswith(NONE_ROW)), None)
    if none_at is not None:
        lines[none_at] = row
    else:
        last = max((i for i in range(idx + 1, len(lines)) if lines[i].startswith("|")), default=idx)
        lines.insert(last + 1, row)
    if a.supersedes:
        for i, l in enumerate(lines):
            if l.startswith(f"| {a.supersedes} |"):
                cells = split_row(l)
                cells[-1] = f"{cells[-1]}; by {new_id}" if cells[-1] else f"by {new_id}"
                lines[i] = join_row(cells)
                break

    if old_path:
        old = old_path.read_text(encoding="utf-8")
        old = set_front_matter(set_front_matter(old, "superseded_by", new_id), "updated", today)
        old_path.write_text(old, encoding="utf-8")
    path.write_text(body, encoding="utf-8")
    readme.write_text("\n".join(lines), encoding="utf-8")
    return {"id": new_id, "path": path.relative_to(root).as_posix()}


def rule_id(kind, a):
    if not DOMAIN.match(a.domain):
        raise Fail("domain must match ^[a-z][a-z0-9_]*$", 2)
    f = Path(a.root).resolve() / "docs" / "rules" / f"{a.domain}.yaml"
    text = f.read_text(encoding="utf-8") if f.exists() else ""
    nums = [int(n) for n in re.findall(rf"\b{kind}-{re.escape(a.domain)}-(\d+)\b", text)]
    return f"{kind}-{a.domain}-{max(nums, default=0) + 1}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("adr")
    p.add_argument("title")
    p.add_argument("--supersedes")
    p.add_argument("--date")
    for kind in ("br", "sd"):
        p2 = sub.add_parser(kind)
        p2.add_argument("domain")
    for sp in sub.choices.values():
        sp.add_argument("--root", default=".")
    a = ap.parse_args()
    try:
        out = json.dumps(adr(a)) if a.cmd == "adr" else rule_id(a.cmd.upper(), a)
    except Fail as e:
        print(str(e), file=sys.stderr)
        sys.exit(e.code)
    print(out)


if __name__ == "__main__":
    main()
