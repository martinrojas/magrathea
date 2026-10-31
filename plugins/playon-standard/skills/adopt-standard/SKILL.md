---
name: adopt-standard
description: Use when a repo adopts the PlayOn Source-of-Truth Standard (AGENTS.md router, PRODUCT.md, ARCHITECTURE.md, docs/decisions, docs/rules) or a monorepo adds a package to it
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
   Add `review,context` if the engineer confirms playon-reviewer reviews the repo (`reviewed_evidence` is only a hint;
   enrolment is not visible in the repo) and a companion repo exists; just `review` if none does. Add `ui` if `ui` is
   true. There is no DESIGN.md template yet: say the AGENTS.md row is kept and the file is theirs to write.
3. Scaffold: `python3 skill://sot-standard/scripts/scaffold.py init . --with <csv>`
   - Monorepo: for each package the engineer selects, `scaffold.py package <dir> [--review]`.
   - `skipped` lists files that already existed. Reconcile a skipped `AGENTS.md`/`CLAUDE.md` by hand: move durable
     content into the template's sections and make `CLAUDE.md` exactly `@AGENTS.md`.
4. Fill commands, runtime, and layout from the `detect` output and the code. Ask the engineer for purpose, users,
   goals, non-goals, core terms, constraints, and domain owners (PRODUCT.md §1–7). Delete sections that do not apply.
5. If the repo is reviewed: write `context.yaml` entries (`git_remote` names this repo; ask for companion repos) and
   the AGENTS.md §7 invariants. Tell the engineer that enrolment is a PR to playon-reviewer's `config.toml`
   (`repo_allowlist`, `user_allowlist`) plus the GitHub App, done by an org owner, with nothing in this repo. Keep this
   step thin: the reviewer questions in `research/reviewer-audit.md` §7 are still open.
6. Validate: `python3 skill://sot-standard/scripts/validate_standard.py .` (0 errors; add `--strict` once
   placeholders are filled). Commit on the task branch and offer to open the PR. Push only when asked.

## Never

Invent product facts or safeguards; mark behavior you have not read "(inferred, not verified)".
