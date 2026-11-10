---
name: close-plan
description: Use when a plan or spec has been implemented in a repo with a .the-guide stamp, to decide what (if anything) the grounding docs must absorb and then delete the plan
---

# Close out a plan

`<std>` is `skill://the-guide`.
Rules: `<std>/rules.md`. Distill the diff, not the session: the code already shows what changed, and
the only thing that lives solely in the conversation is the reasoning behind a choice, which belongs in
a decision record. Nothing from a plan is copied into a grounding doc.

## Steps

1. Read the plan (`docs/plans/<file>.md`, or the file the user names) and the branch diff
   (`git diff --stat <base>...HEAD`). Note the plan's `serves` IDs.
2. Run `sync-docs` (it runs `doc_map.py --check` and audits the stale owners). That handles every doc
   the code mechanically touches.
3. Answer these five questions against the plan and diff. Each "yes" routes to exactly one owner; a "no"
   writes nothing anywhere:
   - A choice someone could reasonably have made differently, with options rejected → `record-decision`.
   - A business rule met that was in neither code nor `docs/rules/<domain>.yaml` → `domain-rules`.
   - Something that now looks wrong but is intentional, or a trap that bit → one `GO` line in
     `ARCHITECTURE.md`, citing the record or incident.
   - A command, layout entry, or reviewer invariant changed → the matching line in `AGENTS.md`.
   - An open question still unresolved → a Q-row in `PRODUCT.md` §8 with an owner. Everything else is
     inferable from the code and is not written down.
4. Delete the plan file. Git history keeps it; the PR description cites the IDs created or changed.
   Delete any spec that died with the change too; a spec that would outlive it is a `PRODUCT.md` row or a
   rules file that has not been written yet, so route it through step 3 instead.
5. Validate: `python3 <std>/scripts/validate_standard.py .` (it warns on plans marked `done` or past
   their age limit, so a forgotten plan fails lint rather than relying on habit).
6. Summary: IDs created or changed, docs updated, plan deleted, and the questions answered "no".

## Never

Summarize the session or the plan into a grounding doc. Archive a plan instead of deleting it. Add a
"lessons learned" section anywhere.
