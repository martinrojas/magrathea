---
name: upgrade-standard
description: Use when a repo's .sot-standard stamp is older than the installed slartibartfast plugin, or when asked to upgrade a repo to a new Source-of-Truth Standard version
---

# Upgrade a repo to the installed standard

Rules: `skill://sot-standard/STANDARD.md`. Work on a task branch.

## Steps

1. `python3 skill://sot-standard/scripts/scaffold.py upgrade .`
   It refreshes the vendored `scripts/validate_standard.py` and prints
   `{"from","to","notes","validator_refreshed"}`. It exits 1 if the repo is not adopted or is newer than the plugin.
2. If `notes` is empty and `from == to`, say the repo is current (mention a validator refresh if one happened) and stop.
3. Otherwise read each note in order and apply only its structural changes: headings, fixed lines, sections added from
   `skill://sot-standard/templates/`. Keep every filled-in value. If `notes` is empty but `from != to`, no structure
   changed: go straight to the next step.
4. Validate: `python3 skill://sot-standard/scripts/validate_standard.py .`
5. Stamp: `python3 skill://sot-standard/scripts/scaffold.py upgrade . --finish`
6. Validate again: `python3 skill://sot-standard/scripts/validate_standard.py .` as a backstop. Fix any error; a
   missing `CHANGELOG.md` means a note was skipped, so apply it.
7. Commit on the task branch; one PR for the owning team. Push only when asked.

## Never

Overwrite filled-in content.
Edit a released changelog section.
