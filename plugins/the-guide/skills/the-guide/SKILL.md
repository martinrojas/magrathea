---
name: the-guide
description: Internal assets of the the-guide plugin (the standard's rules, templates, scripts, upgrade notes). Used by the adopt-standard, sync-docs, close-plan, record-decision, domain-rules and upgrade-standard skills; not for direct use.
hide: true
---

# the-guide

Index of bundled files: `skill://the-guide/<path>`.

- `rules.md`: the seven rules, for agents. Read this, not `STANDARD.md`.
- `STANDARD.md`: the full standard, for adopters (files, tiers, review, sizing, versions).
- `ci.md`: CI snippet (validator + stale-doc backstop) for adopting repos.
- `templates/`: what an adopting repo gets; `.the-guide` there is the one owner of the standard version. `docs/plans/TEMPLATE.md` is copied on demand, never scaffolded.
- `scripts/`: stdlib-only Python 3.9, one JSON object or error lines out.
  - `detect.py [root]`: repo facts (stack, commands, packages, UI, CI, existing standard files, size, manifest version).
  - `scaffold.py init [root] --with <csv> [--size S]` / `package <dir> [--review]` / `upgrade [root] [--finish]`.
  - `validate_standard.py [root] [--strict] [--plan-age DAYS]`: check a repo against the standard.
  - `next_id.py adr "<title>" [--supersedes ADR-NNNN]` / `br <domain>` / `sd <domain>`: allocate ids.
  - `doc_map.py [--root R] [--base REF] [--check] [paths]`: changed paths → the grounding docs that own them.
- `upgrades/`: per-release notes with an `ops` block the upgrade script applies and a `## Manual` section for the rest.
