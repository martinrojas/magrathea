---
name: record-decision
description: Use when a significant technical choice is made in a repo with docs/decisions/, or when an accepted decision record must be superseded
---

# Record a decision

Rules: `skill://sot-standard/STANDARD.md`. Status rules and conventions: the repo's `docs/decisions/README.md`.
Draft the record while the context is fresh; a human accepts it.

## Steps

1. Create the record and its index row (new number, never reused):
   `python3 skill://sot-standard/scripts/next_id.py adr "<title>" [--supersedes ADR-NNNN]`
   It prints `{"id","path"}`. With `--supersedes` it also links the old record and index row.
2. Fill the created file: Context, Options considered (each with its main cost), Decision (active voice),
   Consequences, Notes for agents. About one page. Set `relates_to` to IDs defined in PRODUCT.md/ARCHITECTURE.md and
   `deciders` to the people involved.
3. Add a one-line `see ADR-NNNN` comment at the code sites that depend on it.
4. If ARCHITECTURE.md states the "what", update its entry to point at the record.
5. Validate: `python3 skill://sot-standard/scripts/validate_standard.py .`
6. Tell the user the deciders set `status: accepted`. When superseding, they also set the old record's status to
   `superseded`; the script has only filled `superseded_by`.

## Never

Mark a record accepted.
