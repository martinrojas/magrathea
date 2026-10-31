#!/usr/bin/env python3
"""Validate a project against the source-of-truth standard.

Usage: python3 scripts/validate_standard.py [root] [--budget N] [--strict]

Errors fail the run (exit 1). Warnings do not. --strict also fails on unfilled
template placeholders, for use once a project has filled its files in.

Stdlib only, except that full checking of docs/rules/*.yaml needs PyYAML
(pip install pyyaml). Without it, rules files get a reduced regex check.
"""
import argparse
import datetime
import os
import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

PREFIXES = "U|G|NG|C|SD|BR|K|CH|Q|BD|TC|F|GO|R"
# Plain IDs (G1, K2) in PRODUCT.md/ARCHITECTURE.md; domain-scoped IDs
# (BR-billing-3, SD-billing-1) in docs/rules/<domain>.yaml.
ID_TOKEN = rf"(?:{PREFIXES})(?:-[a-z][a-z0-9_]*)?-?\d+"
ID_REF = re.compile(rf"\b{ID_TOKEN}\b")
DEF_TABLE = re.compile(rf"^\|\s*({ID_TOKEN})\s*\|")
DEF_BULLET = re.compile(rf"^\s*-\s+({ID_TOKEN})(?=[:\s(])")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
IMPORT = re.compile(r"^@(\S+)\s*$")
LINE_CITE = re.compile(
    r"\b[\w./-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|rb|php|cs|swift|kt|md):\d+\b|#L\d+\b")
# A placeholder is `<name>` outside URL/path/generic positions, or a date field left as YYYY-MM-DD.
PLACEHOLDER = re.compile(r"(?<![=?&/\w])<[A-Za-z/][^<>\n]*>|:\s*YYYY-MM-DD\s*(?:#.*)?$")
INFERRED = "(inferred, not verified)"
RESOLUTIONS = {"unique", "first", "priority", "collect"}
PRIORITIES = {"must", "should"}
DOMAIN = re.compile(r"^[a-z][a-z0-9_]*$")
STATUSES = {"proposed", "accepted", "rejected", "superseded", "deprecated"}
OPTIONAL_TARGETS = {"DESIGN.md"}
SCAN_NAMES = {"AGENTS.md", "CLAUDE.md", "PRODUCT.md", "DESIGN.md", "ARCHITECTURE.md", "CHANGELOG.md"}
SCAN_DIRS = ("decisions", "rules", "guides")
STAMP = re.compile(r"^\d+\.\d+\.\d+$")
SEMVER_CORE = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
VERSION_HEADING = re.compile(rf"^## \[({SEMVER_CORE})\] - (\d{{4}}-\d{{2}}-\d{{2}})$")

errors, warnings = [], []


def err(f, msg):
    errors.append(f"ERROR   {f}: {msg}")


def warn(f, msg):
    warnings.append(f"warning {f}: {msg}")


def body_lines(text):
    """Yield (lineno, line) outside fenced code blocks."""
    fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence:
            yield i, line


def front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "#", "-")):
                k, v = line.split(":", 1)
                fm[k.strip()] = v.split("#")[0].strip()
    return fm


def walk_docs(root):
    found = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if not x.startswith(".")
                   and x not in {"node_modules", "venv", "dist", "build", "vendor"}]
        rel = Path(d).relative_to(root)
        for f in files:
            in_docs = rel.parts[:1] == ("docs",) and any(
                p in SCAN_DIRS for p in rel.parts[1:2])
            is_rules_yaml = rel.parts[:2] == ("docs", "rules") and f.endswith((".yaml", ".yml"))
            if f.endswith(".md") and (f in SCAN_NAMES or in_docs):
                found.append(Path(d) / f)
            elif is_rules_yaml:
                found.append(Path(d) / f)
    return sorted(found)


def is_template(p):
    return "template" in p.name.lower()


def check_links(root, files):
    for p in files:
        if p.suffix != ".md":
            continue
        rel = p.relative_to(root)
        text = p.read_text(encoding="utf-8")
        for n, line in body_lines(text):
            targets = [(m, "link") for m in LINK.findall(line)]
            im = IMPORT.match(line.strip())
            if im:
                targets.append((im.group(1), "import"))
            for t, kind in targets:
                if re.match(r"^(https?:|mailto:|#)", t):
                    continue
                path = (p.parent / t.split("#")[0]).resolve()
                if not path.exists():
                    msg = f"line {n}: {kind} target not found: {t}"
                    if Path(t).name in OPTIONAL_TARGETS and kind == "link":
                        warn(rel, msg + " (optional file; remove the row if unused)")
                    else:
                        err(rel, msg)
            if LINE_CITE.search(line):
                warn(rel, f"line {n}: cite code by path#symbol, not line number")


def parse_ids(files):
    defined, where = set(), {}
    for p in files:
        for n, line in body_lines(p.read_text(encoding="utf-8")):
            m = DEF_TABLE.match(line) or DEF_BULLET.match(line)
            if m:
                i = m.group(1)
                if i in where:
                    err(p.name, f"line {n}: duplicate ID {i} (also in {where[i]})")
                where[i] = f"{p.name}:{n}"
                defined.add(i)
    return defined


def check_ids(root, files, rules_ids):
    id_files = [p for p in files if p.name in {"PRODUCT.md", "ARCHITECTURE.md"}]
    defined = parse_ids(id_files) | rules_ids
    ref_files = id_files + [p for p in files if p.parent.name == "decisions"
                            and p.suffix == ".md" and p.name != "README.md"
                            and not is_template(p)]
    for p in ref_files:
        for n, line in body_lines(p.read_text(encoding="utf-8")):
            if DEF_TABLE.match(line) or DEF_BULLET.match(line):
                refs = ID_REF.findall(line)[1:]
            else:
                refs = ID_REF.findall(line)
            for r in refs:
                if r not in defined:
                    err(p.relative_to(root), f"line {n}: reference to undefined ID {r}")
    return defined


def _rules_regex_fallback(root, p, text):
    """Reduced check when PyYAML is missing: IDs, resolutions, priorities."""
    rel = p.relative_to(root)
    ids = re.findall(r"^\s*-\s*id:\s*([A-Za-z0-9-]+)", text, re.M)
    for i in ids:
        if not re.match(rf"^(SD|BR)-[a-z][a-z0-9_]*-\d+$", i):
            err(rel, f"id {i} must look like SD-<domain>-N or BR-<domain>-N")
    for m in re.finditer(r"^\s*resolution:\s*(\S+)", text, re.M):
        if m.group(1) not in RESOLUTIONS:
            err(rel, f"resolution {m.group(1)!r} must be one of {sorted(RESOLUTIONS)}")
    for m in re.finditer(r"^\s*priority:\s*(\S+)", text, re.M):
        if m.group(1) not in PRIORITIES:
            err(rel, f"priority {m.group(1)!r} must be one of {sorted(PRIORITIES)}")
    return set(ids)


def check_rules_yaml(root, files):
    """Validate docs/rules/<domain>.yaml against the TEMPLATE schema.

    Returns the set of SD/BR ids defined, so Markdown files can reference them.
    """
    defined = set()
    rules_files = [p for p in files if p.suffix in (".yaml", ".yml")
                   and p.parent.name == "rules" and not is_template(p)]
    for p in rules_files:
        rel = p.relative_to(root)
        text = p.read_text(encoding="utf-8")
        if yaml is None:
            warn(rel, "PyYAML not installed; reduced check only (pip install pyyaml)")
            defined |= _rules_regex_fallback(root, p, text)
            continue
        try:
            doc = yaml.safe_load(text) or {}
        except yaml.YAMLError as e:  # type: ignore[attr-defined]
            err(rel, f"YAML parse error: {str(e).splitlines()[0]}")
            continue
        if not isinstance(doc, dict):
            err(rel, "top level must be a mapping")
            continue
        domain = str(doc.get("domain", ""))
        if not DOMAIN.match(domain):
            err(rel, f"domain {domain!r} must be lowercase letters, digits, underscore")
        if p.stem != domain:
            err(rel, f"file name should be {domain}.yaml to match domain")
        for key in ("owner", "system_of_record", "last_reviewed"):
            if not doc.get(key):
                warn(rel, f"missing {key}")
        decisions = doc.get("decisions") or []
        rules = doc.get("rules") or []
        if not isinstance(decisions, list) or not isinstance(rules, list):
            err(rel, "decisions and rules must be lists")
            continue
        local, sd_ids = {}, set()

        def define(i, what):
            if not isinstance(i, str) or not re.match(
                    rf"^{what}-{re.escape(domain)}-\d+$", i):
                err(rel, f"{what} id {i!r} must look like {what}-{domain}-N")
                return
            if i in local or i in defined:
                err(rel, f"duplicate id {i}")
            local[i] = True
            defined.add(i)

        for d in decisions:
            if not isinstance(d, dict):
                err(rel, f"decision entry is not a mapping: {d!r}")
                continue
            i = d.get("id")
            define(i, "SD")
            sd_ids.add(i)
            for key in ("decision", "inputs", "outcomes", "resolution", "default"):
                if key not in d or d[key] in (None, "", []):
                    err(rel, f"{i}: missing {key}")
            if d.get("resolution") not in RESOLUTIONS:
                err(rel, f"{i}: resolution must be one of {sorted(RESOLUTIONS)}")
            outs = d.get("outcomes") or []
            if isinstance(outs, list) and d.get("default") not in (None, "") \
                    and d["default"] not in outs and not str(d["default"]).startswith("<"):
                warn(rel, f"{i}: default {d['default']!r} is not one of outcomes {outs}")
        for d in decisions:
            if isinstance(d, dict):
                for dep in d.get("depends_on") or []:
                    if dep not in sd_ids:
                        err(rel, f"{d.get('id')}: depends_on {dep} is not defined here")
        for r in rules:
            if not isinstance(r, dict):
                err(rel, f"rule entry is not a mapping: {r!r}")
                continue
            i = r.get("id")
            define(i, "BR")
            for key in ("rule", "example", "source", "priority"):
                if key not in r or r[key] in (None, ""):
                    err(rel, f"{i}: missing {key}")
            dec = r.get("decision")
            if dec not in (None, "", "—") and dec not in sd_ids:
                err(rel, f"{i}: decision {dec} is not defined in this file")
            if r.get("priority") not in PRIORITIES:
                err(rel, f"{i}: priority must be one of {sorted(PRIORITIES)}")
            ex = r.get("example")
            if isinstance(ex, dict) and not (ex.get("given") and ex.get("expect")):
                err(rel, f"{i}: example needs given and expect")
            elif ex is not None and not isinstance(ex, dict):
                err(rel, f"{i}: example must be a mapping with given and expect")
            ev = r.get("evidence")
            if isinstance(ev, str) and LINE_CITE.search(ev):
                warn(rel, f"{i}: cite evidence by path#symbol, not line number")
            sup = r.get("supersedes")
            if sup and sup not in local:
                warn(rel, f"{i}: supersedes {sup}, which is not in this file")
    return defined


def check_rules_map(root):
    """PRODUCT.md §7 rules-file references must exist; rules files should be mapped."""
    prod = root / "PRODUCT.md"
    if not prod.exists():
        return
    text = prod.read_text(encoding="utf-8")
    referenced = set()
    for m in re.finditer(r"`(docs/rules/[^`<>]+\.ya?ml)`", text):
        referenced.add(m.group(1))
        if "TEMPLATE" in m.group(1):
            continue
        if not (root / m.group(1)).exists():
            err("PRODUCT.md", f"rules file {m.group(1)} is referenced but does not exist")
    rdir = root / "docs" / "rules"
    if rdir.is_dir():
        for p in sorted(rdir.glob("*.y*ml")):
            if is_template(p):
                continue
            rel = p.relative_to(root).as_posix()
            if rel not in referenced:
                warn(rel, "not listed in PRODUCT.md §7 map")


def check_adrs(root, files):
    ddir = root / "docs" / "decisions"
    if not ddir.is_dir():
        return
    readme = ddir / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    # Only the Index section counts, so a passing mention elsewhere cannot hide a gap.
    index = text.split("## Index", 1)[1] if "## Index" in text else ""
    if not readme.exists():
        err("docs/decisions", "README.md (index and status rules) is missing")
    for p in sorted(ddir.glob("[0-9][0-9][0-9][0-9]-*.md")):
        if is_template(p):
            continue
        fm = front_matter(p.read_text(encoding="utf-8"))
        adr = "ADR-" + p.name[:4]
        rel = p.relative_to(root)
        if fm.get("status") not in STATUSES:
            err(rel, f"status must be one of {sorted(STATUSES)}")
        if fm.get("status") == "superseded" and not fm.get("superseded_by"):
            err(rel, "superseded record needs superseded_by")
        if adr not in index and p.name not in index:
            err(rel, f"not listed in docs/decisions/README.md index ({adr})")


def check_basics(root, budget):
    agents = root / "AGENTS.md"
    if not agents.exists():
        err("AGENTS.md", "missing (core file)")
    else:
        n = len(agents.read_text(encoding="utf-8").splitlines())
        if n > int(budget * 1.5):
            err("AGENTS.md", f"{n} lines; hard limit {int(budget * 1.5)}. Move detail out")
        elif n > budget:
            warn("AGENTS.md", f"{n} lines; target is about {budget}")
    claude = root / "CLAUDE.md"
    if claude.exists() and claude.read_text(encoding="utf-8").strip() != "@AGENTS.md":
        err("CLAUDE.md", "must contain only the line: @AGENTS.md")
    for name in ("PRODUCT.md", "ARCHITECTURE.md"):
        p = root / name
        if p.exists() and "last_reviewed" not in front_matter(p.read_text(encoding="utf-8")):
            warn(name, "front matter has no last_reviewed")


def check_changelog(root):
    path = root / "CHANGELOG.md"
    if not path.exists():
        err("CHANGELOG.md", "missing (core file)")
        return
    text = path.read_text(encoding="utf-8")
    sections = []
    for n, line in body_lines(text):
        if line.startswith("## "):
            sections.append([n, line, []])
        elif sections:
            sections[-1][2].append((n, line))
    if not sections:
        err("CHANGELOG.md", "first ## heading must be [Unreleased]")
        return
    if sections[0][1].rstrip() != "## [Unreleased]":
        err("CHANGELOG.md", "first ## heading must be [Unreleased]")
    seen_versions = set()
    prev_ver = None
    prev_ver_str = None
    released_sections = []
    for n, line, body in sections[1:]:
        m = VERSION_HEADING.match(line.rstrip())
        if not m:
            err("CHANGELOG.md", f"line {n}: version heading must be '## [x.y.z] - YYYY-MM-DD'")
            continue
        ver_str, date_str = m.group(1), m.group(2)
        try:
            datetime.date.fromisoformat(date_str)
        except ValueError:
            err("CHANGELOG.md", f"line {n}: invalid date {date_str}")
        ver_tuple = tuple(int(x) for x in ver_str.split("."))
        if ver_tuple in seen_versions:
            err("CHANGELOG.md", f"line {n}: duplicate version {ver_str}")
        elif prev_ver is not None and ver_tuple >= prev_ver:
            err("CHANGELOG.md", f"line {n}: {ver_str} is not below {prev_ver_str}; versions must be newest first")
        else:
            prev_ver = ver_tuple
            prev_ver_str = ver_str
        seen_versions.add(ver_tuple)
        released_sections.append((n, ver_str, ver_tuple, body))


def check_stamp(root):
    p = root / ".sot-standard"
    if not p.exists():
        warn(".sot-standard", "missing version stamp; adopt-standard writes it")
        return
    text = p.read_text(encoding="utf-8").strip()
    if not STAMP.match(text):
        err(".sot-standard", f"must hold one version like 0.1.0 (got {text!r})")


def check_placeholders(root, files):
    for p in files:
        if is_template(p) or p.name == "README.md":
            continue
        # Blank comments but keep their newlines so reported line numbers stay true.
        text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group().count("\n"),
                      p.read_text(encoding="utf-8"), flags=re.S)
        hits = [n for n, line in body_lines(text) if PLACEHOLDER.search(line)]
        if hits:
            err(p.relative_to(root), f"{len(hits)} unfilled placeholder line(s) at "
                                     f"{', '.join(map(str, hits))}")


def count_inferred(files):
    return sum(p.read_text(encoding="utf-8").count(INFERRED)
               for p in files if not is_template(p) and p.name != "README.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--budget", type=int, default=100, help="AGENTS.md line target")
    ap.add_argument("--strict", action="store_true", help="fail on unfilled placeholders")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    files = walk_docs(root)
    check_basics(root, a.budget)
    check_changelog(root)
    check_stamp(root)
    check_links(root, files)
    rules_ids = check_rules_yaml(root, files)
    ids = check_ids(root, files, rules_ids)
    check_rules_map(root)
    check_adrs(root, files)
    if a.strict:
        check_placeholders(root, files)
    for line in warnings + errors:
        print(line)
    print(f"\n{len(files)} files scanned, {len(ids)} IDs defined, "
          f"{len(errors)} error(s), {len(warnings)} warning(s), "
          f"{count_inferred(files)} unverified claim(s) marked {INFERRED}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
