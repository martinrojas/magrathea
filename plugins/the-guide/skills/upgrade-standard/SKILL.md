---
name: upgrade-standard
description: Use when a repo's .the-guide stamp is older than the installed the-guide plugin, or when asked to upgrade a repo to a new Source-of-Truth Standard version
---

# Upgrade a repo to the installed standard

`<std>` is `skill://the-guide`.
Rules: `<std>/rules.md`. Work on a task branch.

## Steps

1. `python3 <std>/scripts/scaffold.py upgrade .`
   It refreshes the vendored `scripts/validate_standard.py`, applies every upgrade note's machine-readable
   line edits (idempotent), and prints `{"from","to","applied","manual_notes","validator_refreshed"}`.
   It exits 1 if the repo is not adopted or is newer than the plugin.
2. If `applied` and `manual_notes` are empty and `from == to`, say the repo is current (mention a
   validator refresh if one happened) and stop.
3. For each path in `manual_notes`, in order, read only its `## Manual` section and apply those moves:
   headings, sections added from `<std>/templates/`, content relocated between files. Keep every
   filled-in value.
4. Validate: `python3 <std>/scripts/validate_standard.py .`
5. Stamp: `python3 <std>/scripts/scaffold.py upgrade . --finish`
6. Validate again as a backstop. Fix any error.
7. Commit on the task branch; one PR for the owning team. Push only when asked.

## Never

Overwrite filled-in content. Re-apply an `ops` edit by hand; the script already did or skipped it.
Edit a released changelog section.
