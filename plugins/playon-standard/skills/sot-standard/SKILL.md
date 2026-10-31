---
name: sot-standard
description: Internal assets for the playon-standard skills — the standard's rules (STANDARD.md), templates, and scripts. Not for direct use.
hide: true
---

# sot-standard

Index of bundled files. Read them as `skill://sot-standard/<path>`.

- `STANDARD.md`: the seven rules, sizing, and formats. Skills point here and never restate it.
- `templates/`: what an adopting repo gets (`.sot-standard` there is the one owner of the standard version).
- `scripts/`: stdlib-only Python 3.9, terse output.
  - `detect.py [root]`: JSON facts about a repo (stack, commands, packages, UI, size).
  - `scaffold.py init [root] --with <csv>` / `package <dir> [--review]` / `upgrade [root] [--finish]`: write templates, add a package file, upgrade the stamp.
  - `validate_standard.py [root] [--strict]`: check a repo against the standard.
  - `next_id.py adr "<title>" [--supersedes ADR-NNNN]` / `br <domain>` / `sd <domain>`: allocate ids.
  - `doc_map.py [--root R] [--base REF] [paths]`: changed paths mapped to the grounding docs that own them.
- `upgrades/`: per-release structural notes.
