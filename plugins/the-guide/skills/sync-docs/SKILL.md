---
name: sync-docs
description: Use before opening a PR in a repo with a .the-guide stamp when the change alters behavior, commands, paths, boundaries, or review invariants that its grounding docs describe
---

# Sync grounding docs with a change

`<std>` is `skill://the-guide`.
Rules: `<std>/rules.md`. Docs change in the same PR as the behavior they describe.

## Steps

1. Map the change to the docs that own it:
   `python3 <std>/scripts/doc_map.py --root . [--base <base branch>]`
   Owners come from rules `paths:`, `ARCHITECTURE.md` boundaries, `path#symbol` citations in any grounding
   doc (including `REVIEW.md` and `context.yaml`), and command files → the nearest `AGENTS.md`.
2. If `stale` is empty, say "No owned docs affected" and go to step 6.
3. Dispatch one `drift-auditor` subagent per stale doc, all in parallel. Each task text gives the doc path,
   its `via` list, its `paths`, and its `status` (from the matching `owners` entry). If an owner's
   `path_count` is above 20, pass the auditor only the paths whose diff hunks touch a symbol the doc cites,
   and say so in your summary; a full re-read is the owner's call, not yours.
4. Read each returned diff against the code, then apply it.
   For a doc with `status: accepted`, never apply a diff: report the conflict and offer `record-decision`
   to supersede it. Relay each `Ask <owner>: …` line to the user; do not decide it.
5. Delete entries the code now makes obvious (rule 3).
6. If `CHANGELOG.md` exists and the change is user-visible, draft an entry under `## [Unreleased]` in the
   matching subsection and apply it. Never edit a released section.
7. Validate: `python3 <std>/scripts/validate_standard.py .`
8. List `unowned` paths that look like domain logic and offer `domain-rules` for them. An unowned path is
   not proof that no doc is affected: `PRODUCT.md` and `DESIGN.md` are owners only through citations.

## Never

Rewrite an accepted decision record. Apply an auditor diff you have not checked against the code.
