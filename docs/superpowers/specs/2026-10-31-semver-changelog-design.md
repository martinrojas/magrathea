# Semver changelog in the Source-of-Truth Standard

Plugin: `plugins/slartibartfast`. Branch: `feature/semver-changelog`, based on `main` after PR #1 (0.3.0) merged, so the 0.4.0 stamp, catalog bump and upgrade-note sequence build on 0.3.0. Target release: 0.4.0.

## Intent

Every project that adopts the standard keeps a `CHANGELOG.md` that records user-visible change under semantic versioning, with written rules for when and how. A project that already has history and no changelog gets that history recorded as `1.0.0`, and tracking starts from there.

## Goals, non-goals, anti-goals

Goals
- `CHANGELOG.md` is a core file: scaffolded for every adopter, routed from `AGENTS.md`, part of the definition of done.
- `STANDARD.md` states the semver and entry rules once; other files point to it.
- `validate_standard.py` checks changelog structure offline, stdlib only, Python 3.9.
- Adopt and upgrade flows bring existing projects onto the changelog without losing anything.

Non-goals
- Generating entries from commits, conventional-commit enforcement, release automation, tagging, publishing.
- Judging whether an entry is accurate or complete (people do that, as with every other grounding doc).
- Per-package changelogs in a monorepo: one root changelog, one version.

Anti-goals (failure even if it "works")
- An agent rewriting or deleting a released section.
- Upgrade breaking an adopter midway: the vendored validator only changes at `scaffold.py upgrade` step 1, and the 0.4.0 note creates `CHANGELOG.md` before the validation step, so a repo that follows the upgrade skill never sees a spurious missing-file error.
- A baseline `1.0.0` that claims history the project does not have.

## Constraints

- Validator is stdlib-only and offline; no network, no `npx`.
- `AGENTS.md` template is 104 lines today (target about 100, hard limit 150): add at most a row and a line.
- Standard rule 5 (rewrite to current state, do not append) does not apply to a changelog, which is history by nature. `STANDARD.md` must say so.
- Git rules: scaffolding commits on the task branch; tagging, pushing and publishing happen only when the user asks.

## Approaches considered

| | Adds | Trade-off |
|---|---|---|
| A. Docs only | Template, scaffold, `AGENTS.md` row, rules in `STANDARD.md`; validator checks existence | Cheapest; a malformed changelog passes |
| B. Docs plus structural checks | A, plus structure validation, manifest-version warning, baseline in adopt, upgrade note | Catches drift offline; cannot judge accuracy |
| C. B plus change enforcement | B, plus "code changed, changelog did not" check | Noisy on refactors and docs-only PRs |

Chosen by the user: **B**. The "was an entry added" nudge from C goes into the `sync-docs` skill, not the validator.

## Decided by the user

- Core for every adopter.
- A project with prior history and no tracking: record what existed as `1.0.0`, start from there.

## Design (my calls unless marked above)

**File and format.** Root `CHANGELOG.md`, [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) layout, no front matter (it is a community format; `last_reviewed` adds nothing). Top `## [Unreleased]`, then `## [x.y.z] - YYYY-MM-DD`, newest first. Subsections drawn from `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. Bottom link references are allowed and not checked.

**Semver rules (go in `STANDARD.md`, short section "Changelog and versions").**
- The public interface is whatever users or operators depend on: API, CLI, config, data formats, documented behavior; for an app, user-visible behavior. The project names it in one line at the top of its changelog.
- MAJOR: breaking change to it. MINOR: backward-compatible addition. PATCH: backward-compatible fix.
- No `0.x`: the first recorded version is `1.0.0`.
- Entry goes under `Unreleased` in the same PR as the change. Refactors, tests, and docs-only changes get no entry.
- Cutting a release: rename `Unreleased` to the version and date, add a fresh empty `Unreleased`, bump the manifest version, in one commit. Tagging is the user's call.
- Released sections are immutable except for typo fixes. A mistake is corrected by a new entry.

**Template.** `templates/CHANGELOG.md`: title, a public-interface placeholder line, a plain-text pointer to the rules ("the standard's 'Changelog and versions' section, in the slartibartfast plugin's `STANDARD.md`"; no Markdown link, because `STANDARD.md` is not vendored into adopters and `check_links` errors on missing local targets), links to keepachangelog.com and semver.org, and an empty `## [Unreleased]`. It always scaffolds (like `AGENTS.md`, no `--with` token). `AGENTS.md` template gets a static row in section 1 and one definition-of-done line; no transform needed.

**Validator (`validate_standard.py`).**
- Missing `CHANGELOG.md`: error, for every repo, with no stamp gate (core means core; the user chose this). A repo below 0.4.0 that runs the plugin's validator (the edit hook does) is told to upgrade; repos using their older vendored validator are unaffected until they upgrade. `upgrade-standard` also re-runs the validator after `--finish` as a backstop.
- Errors: first `##` heading is not `[Unreleased]`; a version heading that is not valid semver or not `## [x.y.z] - YYYY-MM-DD`; invalid calendar date; duplicate version; versions not strictly descending.
- Warnings: unknown subsection name; a released version with no entries; top released version differs from the manifest version (`package.json`, `pyproject.toml`, `Cargo.toml`, first found); a `0.x` version.
- Unfilled public-interface placeholder is caught by existing `--strict`.
- `CHANGELOG.md` joins `SCAN_NAMES` in the validator (so link and `--strict` placeholder checks cover it) and the names in `validate-grounding.ts` that trigger validation.

**Adopt and detect.** `detect.py` adds `CHANGELOG.md` to `existing` and reports `manifest_version` and whether the git history has commits. After scaffold, if the repo has history and no changelog existed, `adopt-standard` writes `## [1.0.0] - <adoption date>` with one line: "Baseline: changes before this changelog were not tracked." It then offers to set the manifest version to `1.0.0`, because the validator warns on a mismatch. A greenfield repo keeps only `Unreleased`; its first release is `1.0.0`. An existing `CHANGELOG.md` is never replaced or rewritten automatically. If it fails the structural checks, `adopt-standard` reports each failure, shows a proposed diff (prepend `## [Unreleased]`, normalize version headings, no invented dates), and applies it only after the user agrees; released history is never edited without that yes.

**Upgrade.** `upgrades/0.4.0.md` instructs: create `CHANGELOG.md` from the template (baseline `1.0.0` as above if there is history; for an existing one, report failures and propose a diff as above), add the `AGENTS.md` row and definition-of-done line. Stamp and catalog bump to `0.4.0` together, on top of 0.3.0. `upgrade-standard` re-runs the validator after `scaffold.py upgrade . --finish` as a backstop.

**sync-docs.** One new step: if the change is user-visible and `Unreleased` has no matching entry, draft one and apply it; list it in the summary.

**Tests.** Update the empty-set init test (file list now includes `CHANGELOG.md`). New validator tests: each error and warning above, the stamp gate, and a valid changelog passing. Scaffold tests: `CHANGELOG.md` always created; a fresh scaffold validates clean without `--strict`; under `--strict` it is flagged for the unfilled public-interface placeholder (same shape as `test_ui_template_is_flagged_as_unfilled_under_strict`).

## Left to the builder

Exact regexes and manifest parsing; message wording; whether the baseline step is a script helper or skill prose; structure of the new tests.

## Risks

- Repos on `0.3.0` with no changelog fail the plugin's validator until upgraded. Intended: the changelog is core.
- A manifest at `0.1.0` plus a baseline `1.0.0` warns until the manifest is bumped; the adopt step offers the bump.
- `AGENTS.md` template grows to about 106 lines, above the 100 target but under the 150 limit; it warns today already.
