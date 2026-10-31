---
name: adopt-standard
description: Use when a repo adopts the Source-of-Truth Standard (AGENTS.md router, PRODUCT.md, ARCHITECTURE.md, docs/decisions, docs/rules) or a monorepo adds a package to it
---

# Adopt the Source-of-Truth Standard

Rules, sizing, and formats: `skill://sot-standard/STANDARD.md`. Read its "Seven rules" and "Sizing" first; this skill
only drives the scripts. Run everything from the repo root, on a task branch (never the base branch).

## Steps

1. Detect: `python3 skill://sot-standard/scripts/detect.py .`
   If `.sot-standard` is in `existing`, stop and use `upgrade-standard`.
2. Pick the lightest size and confirm it with the engineer (`ask`). `--with` per size:
   - `small` → `product`
   - `software` → `product,architecture,decisions`
   - `monorepo` → the software set at the root
   - `docs` → empty
   Add `ui` if `ui` is true: it writes a `DESIGN.md` template in the Google DESIGN.md format
   (https://github.com/google-labs-code/design.md). Fill tokens and components from the styles in code, keep the
   section order, and drop unknown groups into `omitted:`. Put anything undecided in prose rather than guessing.
3. Scaffold: `python3 skill://sot-standard/scripts/scaffold.py init . --with <csv>`
   - Monorepo: for each package the engineer selects, `scaffold.py package <dir>`.
   - `skipped` lists files that already existed. Reconcile a skipped `AGENTS.md`/`CLAUDE.md` by hand: move durable
     content into the template's sections and make `CLAUDE.md` exactly `@AGENTS.md`.
   - Before cutting any block from a skipped `AGENTS.md` (the validator's hard limit is 1.5× the 100-line target), write
     it into its owner file (`ARCHITECTURE.md`, `docs/decisions/`, `docs/rules/`, `docs/guides/`) in the same step. Drop
     only what the code now shows. List what moved and what was dropped in your summary.
4. Changelog: rules in `skill://sot-standard/STANDARD.md` ("Changelog and versions"). Fill the public-interface line
   from code and README; mark it "(inferred, not verified)" if not read in code.
   - `CHANGELOG.md` in `created` and `detect.git_has_commits` true: below `## [Unreleased]` add
     `## [1.0.0] - <today, YYYY-MM-DD>` and the line `Baseline: changes before this changelog were not tracked.` If
     `detect.manifest_version` is set and is not `1.0.0`, offer (`ask`) to set it to `1.0.0`, because the validator
     warns on a mismatch. No commits: keep only `## [Unreleased]`; the first release is `1.0.0`.
   - `CHANGELOG.md` in `skipped`: never replace or rewrite it. After validating, report each `CHANGELOG.md` finding,
     show a proposed diff (prepend `## [Unreleased]`, normalize version headings to `## [x.y.z] - YYYY-MM-DD` using
     only dates the file states; never invent a date), and apply it only after the engineer agrees (`ask`).
5. Fill commands, runtime, and layout from the `detect` output and the code. Compare every command and tool the
   existing `AGENTS.md` names against `detect.commands` and the repo's config files; fix a stale one, and list any drift
   you leave elsewhere (README, other docs) in your summary and as a Q-row in `PRODUCT.md` §8.
6. Product facts (PRODUCT.md §1–7: purpose, users, goals, non-goals, core terms, constraints, domain owners): ask the
   engineer in one batched `ask`, offering "I'll answer" and "Draft from README and code". A draft marks every claim
   you did not read in code "(inferred, not verified)" and adds a Q-row asking the owner to confirm it. Delete
   sections that do not apply.
7. Validate: `python3 skill://sot-standard/scripts/validate_standard.py .` for 0 errors, then again with `--strict`.
   The summary line counts the claims still marked "(inferred, not verified)"; report that number. A strict hit on
   text that is not a placeholder (a URL, a date format) is a validator bug: report it, do not rewrite the text.
   If `ui` is set and Node is available, also run `npx @google/design.md@0.4.0 lint DESIGN.md` (format is alpha; pin
   the version). Fix `broken-ref` errors; report warnings (contrast, section order, missing primary) without
   rewriting the design to silence them.
8. Offer to add `python3 scripts/validate_standard.py .` (and, with `ui`, the pinned `design.md lint` command, which
   needs Node and network) to the repo's lint or CI command; do not add either unasked.
   Commit on the task branch and offer to open the PR. Push only when asked.

## Never

Invent product facts or safeguards; mark behavior you have not read "(inferred, not verified)".
Rewrite or delete a released changelog section without the engineer's yes.
