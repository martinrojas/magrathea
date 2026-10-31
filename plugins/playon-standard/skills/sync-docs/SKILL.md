---
name: sync-docs
description: Use before opening a PR in a repo with a .sot-standard stamp when the change alters behavior, commands, paths, or boundaries that its grounding docs describe
---

# Sync grounding docs with a change

Rules: `skill://sot-standard/STANDARD.md` ("Seven rules"). Docs change in the same PR as the behavior they describe.

## Steps

1. Map the change to the docs that own it:
   `python3 skill://sot-standard/scripts/doc_map.py --root . [--base <base branch>]`
   Owners come from rules `paths:`, ARCHITECTURE.md boundaries, exact-file citations, and command files.
2. If `stale` is empty, say "No owned docs affected" and stop.
3. Dispatch one `drift-auditor` task per stale doc, all in a single `task` call. Each task text gives the doc path, its
   `via` list, its `paths`, and its `status` (from the matching `owners` entry).
4. Read each returned diff against the code, then apply it with `edit`.
   For a doc with `status: accepted`, never apply a diff: report the conflict and offer `record-decision` to
   supersede it. Relay each `Ask <owner>: …` line to the user; do not decide it.
5. Delete entries the code now makes obvious (rule 3).
6. Validate: `python3 skill://sot-standard/scripts/validate_standard.py .`
7. List `unowned` paths that look like domain logic and offer `domain-rules` for them.

## Never

Rewrite an accepted decision record.
