---
name: adopt-standard
description: Use when a repo adopts the Source-of-Truth Standard (AGENTS.md router, PRODUCT.md, ARCHITECTURE.md, REVIEW.md, context.yaml, docs/decisions, docs/rules) or a monorepo adds a package to it
---

# Adopt the Source-of-Truth Standard

`<std>` is `skill://the-guide`.
Read `<std>/rules.md` first; this skill only drives the scripts. Run everything from the repo root, on a
task branch (never the base branch).

## Steps

1. Detect: `python3 <std>/scripts/detect.py .` If `.the-guide` is in `existing`, stop and use
   `upgrade-standard`.
2. Pick the lightest size and confirm it with the engineer in one question. `--with` per size:
   - `small` → `product`
   - `software` → `product,architecture,decisions`
   - `monorepo` → the software set at the root
   - `docs` → empty (`--size docs`)
   Add `ui` if `detect.ui` is true: it writes a `DESIGN.md` in the Google DESIGN.md format. Fill tokens
   and components from the styles in code, keep the section order, and list token groups you cannot
   read from code under `omitted:` with a reason; never invent a value.
   Add `review` if the repo is (or will be) reviewed by an automated reviewer: it writes `REVIEW.md` and
   `context.yaml` and keeps the Code Review section of `AGENTS.md`.
   Add `changelog` only if the team asks for one; it is not part of the core set.
3. Scaffold: `python3 <std>/scripts/scaffold.py init . --with <csv> [--size S]`
   - Monorepo: for each package the engineer selects, `scaffold.py package <dir> [--review]`.
   - `skipped` lists files that already existed. Reconcile a skipped `AGENTS.md`/`CLAUDE.md` by hand:
     move durable content into the template's sections and make `CLAUDE.md` exactly `@AGENTS.md`.
   - Before cutting any block from a skipped `AGENTS.md` (the validator's hard limit is 150 lines), write
     it into its owner file (`ARCHITECTURE.md`, `docs/decisions/`, `docs/rules/`, `docs/guides/`) in the
     same step. Drop only what the code now shows. List what moved and what was dropped in your summary.
4. Fill commands, runtime, and layout in `AGENTS.md` from `detect.commands`, `detect.runtime` and the
   repo's config files. Compare every command an existing `AGENTS.md` or README names against them; fix a
   stale one and list drift you leave elsewhere as a Q-row in `PRODUCT.md` §8.
5. Product facts (`PRODUCT.md` §1–7): ask the engineer in one batched question, offering "I'll answer" and
   "Draft from README and code". A draft marks every claim you did not read in code
   "(inferred, not verified)" and adds a Q-row asking the owner to confirm it. Delete sections that do not
   apply.
6. Review setup (only with `review`): fill `AGENTS.md` §Code Review with the repo's invariants as concrete
   statements ("Money is integer cents; a float in a payment path is a defect") and its never-flag list;
   never write rules about severity or output format there, the reviewer's rubric owns those. Fill
   `context.yaml` with companion repos the engineer names, or delete it if there are none. Fill the two
   boundary lines in `REVIEW.md`. Remind the engineer that enrolment is out-of-repo (GitHub App install
   and the reviewer's allowlist) and recommend `CODEOWNERS` on `AGENTS.md`, `REVIEW.md`, `docs/rules/`,
   `context.yaml`.
7. Changelog (only with `changelog`): fill the public-interface line from code and README, marked
   "(inferred, not verified)" if not read in code. With `detect.git_has_commits` true add
   `## [1.0.0] - <today>` and `Baseline: changes before this changelog were not tracked.` below
   `## [Unreleased]`. A skipped `CHANGELOG.md` is never rewritten: report validator findings on it, show a
   diff, apply only after the engineer agrees.
8. Validate: `python3 <std>/scripts/validate_standard.py .` for 0 errors, then again with `--strict`.
   Report the count of claims still marked "(inferred, not verified)". A strict hit on text that is not a
   placeholder (a URL, a date format) is a validator bug: report it, do not rewrite the text. With `ui`
   and Node available, also run `npx @google/design.md@0.4.0 lint DESIGN.md`; fix `broken-ref` errors and
   report the rest without rewriting the design to silence them.
9. Offer to add the CI check from `<std>/ci.md` (validator plus `doc_map.py --check`); do not add it
   unasked. Commit on the task branch and offer to open the PR. Push only when asked.

## Never

Invent product facts, safeguards, or design tokens; mark behavior you have not read "(inferred, not verified)".
Write severity or format rules into `AGENTS.md` §Code Review.
Rewrite or delete a released changelog section without the engineer's yes.
