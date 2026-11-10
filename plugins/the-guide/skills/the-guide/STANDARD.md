# Project Source-of-Truth Standard

A small set of Markdown files that ground agents (and people) in what a
project is, what it must obey, and what code cannot tell them. This file is
for adopters; agents load `rules.md` (the seven rules) instead.

## Principle

Write only what an agent cannot infer from the code. Research on repository
context files found that generated or overlong files raise cost without
improving results, while short human-written files help modestly. So the set
is small, each file owns one kind of truth, and everything is lean.

## The files

| File | Tier | Owns |
|------|------|------|
| `AGENTS.md` | Core | Router: grounding docs and how to treat them, commands, layout, conventions, review invariants, done |
| `PRODUCT.md` | Core (not for docs-only repos) | Why: purpose, users, goals, non-goals, core terms, cross-domain constraints, and a map of where product truth lives per domain |
| `docs/rules/<domain>.yaml` | On demand | Business rules for one domain, written when agents change its logic and intent is not in the code |
| `DESIGN.md` | Core if UI | Visual system in the [Google DESIGN.md format](https://github.com/google-labs-code/design.md): YAML tokens plus rationale prose |
| `ARCHITECTURE.md` | As needed | Non-inferable technical context: boundaries, constraints, risky flows, oddities, risks |
| `docs/decisions/` | As needed | One record per significant choice, with status |
| `REVIEW.md` | If reviewed | Review-only policy of record, about 100 lines; never restates `AGENTS.md`. The invariants an automated reviewer must check are summarized in `AGENTS.md` §Code Review, the only file it injects |
| `context.yaml` | If reviewed | Companion repos (and which paths in them) a reviewer or coding agent needs; the one list, which `ARCHITECTURE.md` and `REVIEW.md` point to. Read by the automated reviewer |
| `CHANGELOG.md` | As needed | User-visible changes per release (see "Changelog and versions"); validated only when present |
| `docs/guides/` | On demand | Runbooks |
| `docs/plans/` | Ephemeral | Scaffolding for one change, with `status` and `opened` front matter; never a source of truth, excluded from the grounding scan, deleted by `close-plan` when the change lands |
| `CLAUDE.md` | Shim | Single line: `@AGENTS.md` |
| `.the-guide` | Stamp | Standard version adopted and the repo's size; read by the upgrade and validation tools |
| `scripts/validate_standard.py` | Vendored tool | The validator, refreshed by `upgrade-standard`; run it in CI |

## Seven rules

1. **One owner per fact.** Other files point to it; they do not restate it.
   This includes the agent rules themselves: `AGENTS.md` §Grounding documents
   states them once and the other files point back.
2. **`AGENTS.md` is a router**, about 100 lines. A link plus a one-line hook
   beats a summary, which drifts.
3. **Non-inferable only.** Delete entries the code now makes obvious.
4. **Code wins on current behavior.** Flag drift and propose a fix.
5. **Rewrite to current state; do not append.** Decision history lives in the
   supersede chain. `CHANGELOG.md` is the one file that is history, so it
   appends.
6. **Verify or label.** State code behavior only after reading code; mark the
   rest "(inferred, not verified)". Never invent safeguards.
7. **Cite IDs, and cite code by `path#symbol`**, never by line number. Inline
   review comments posted by a bot anchor to diff lines; that is the posting
   mechanism, not a citation.

## Product grounding at different sizes

`DESIGN.md` works because a design system is finite. A product's rules are
not, so `PRODUCT.md` is a map, not a rulebook: a page of purpose, users,
goals, non-goals, core terms, constraints, and a table of domains with their
owner, system of record, and rules file. A map can be complete; a rulebook
for production software cannot, and an incomplete source of truth misleads.

- **Greenfield or small:** one domain. `PRODUCT.md`'s map has one row and the
  rules file can be written up front, since the rules are few and known.
- **Production, many stakeholders:** many domains. Fill the map (within reach
  for any PM) and write a rules file only when agents start changing a
  domain's logic. Grow by demand: an agent that meets an unwritten rule
  proposes a row; the domain owner accepts it. Rules recoverable from code are
  not written down; `code wins on current behavior` handles those.
- **Feature-level detail** (user stories, acceptance criteria) stays in the
  system of record or a per-change spec that cites `PRODUCT.md` IDs.

## Code review

The standard's review audience is bot-first. The automated reviewer is
assumed to inject `AGENTS.md` (root and along the changed path) and its own rubric, and nothing
else, so the invariants the bot must check live in `AGENTS.md` §Code Review as
concrete statements ("Money is integer cents; a float in a payment path is a
defect"), never as rules about severity or output format, which the rubric
owns. `REVIEW.md` is the policy of record for people, coding agents, and
whole-repo reviews. Severities are the rubric's four (P0–P3) and a repo may
not redefine them. Companion repos go in `context.yaml`, which the reviewer
reads from the base branch so a PR cannot redirect its own review. Keep
`AGENTS.md`, `REVIEW.md`, `docs/rules/` and `context.yaml` under `CODEOWNERS`.

## Plans and sessions

Distill the diff, not the session. A transcript is noise next to the facts
that matter, and summarizing it into docs is how running logs and "context"
folders accumulate; the code already shows what changed. The one thing that
lives only in the conversation is the reasoning behind a choice, which goes
in a decision record at the moment of the decision. When a plan's change
lands, `close-plan` runs the mechanical check (`doc_map.py`: which grounding
docs own the touched paths and are stale), asks five routing questions (a
reasonable alternative rejected → decision record; an unwritten rule met →
rules file; something that now looks wrong on purpose → `ARCHITECTURE.md`
gotcha; a command, layout or reviewer invariant changed → `AGENTS.md`; an
open question → `PRODUCT.md` §8), and deletes the plan. Git history keeps
it. The validator warns on a plan marked `done` or older than 30 days, so
cleanup is a lint result, not a habit.

## Formats

Every grounding document is Markdown with YAML front matter: prose carries
intent, front matter carries the few fields tools validate. Rules files and
`context.yaml` are the exceptions and are always YAML: they hold records that
a tool reads, not prose. `DESIGN.md` carries its tokens in YAML front matter
for the same reason. `CHANGELOG.md` uses the Keep a Changelog layout and has
no front matter. No other format (JSON, TOON, XML) is used for context files.

## Changelog and versions

When a repo keeps `CHANGELOG.md`, it records user-visible change in the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) layout under
[semantic versioning](https://semver.org/spec/v2.0.0.html): `## [Unreleased]`
first, then `## [x.y.z] - YYYY-MM-DD` sections, newest first, with `Added`,
`Changed`, `Deprecated`, `Removed`, `Fixed` and `Security` subsections. One
root changelog and one version, in a monorepo too. Entries go under
`Unreleased` in the same PR as the change; refactors, tests and docs-only
changes get no entry. Released sections are immutable except for typo fixes.
The first recorded version is `1.0.0`; a repo with prior history records a
`1.0.0` baseline line. Cutting a release (renaming `Unreleased`, bumping the
manifest, tagging) is the team's release process, not this standard's.

## Sizing

| Project | Use |
|---------|-----|
| Small or personal | `AGENTS.md` + `PRODUCT.md` (one domain; rules inline or one rules file) |
| Software project | Core set + `ARCHITECTURE.md`, `docs/decisions/` as needed; rules files by demand; `REVIEW.md` and `context.yaml` if agents review code |
| Monorepo | One root set; each package gets an `AGENTS.md` opening with `@../../AGENTS.md` (and, if reviewed, a `REVIEW.md` opening with `@../../REVIEW.md`; one `../` per level of depth), adding only what differs. The `@` import is a Claude Code feature; automated reviewers inject the root file along with the package's, so the package file carries only deltas either way |
| Docs or data repo | `AGENTS.md` only, adapted to content conventions and freshness rules; the stamp records `size: docs` |

When unsure, choose the lighter option. Adding structure later is easier than
removing it.

## Where content goes when a file outgrows its budget

| Growing content | Moves to |
|-----------------|----------|
| Architecture detail | `ARCHITECTURE.md` |
| Rationale for a choice | `docs/decisions/` |
| Business rules for a domain | `docs/rules/<domain>.yaml` |
| Runbooks, long how-tos | `docs/guides/` |
| Deep review topics | `docs/reviews/` |
| A finished plan, a spec that died with its PR, "lessons learned" | Nowhere; delete it. Route any durable fact through `close-plan` first |

Move, do not delete: keep durable content, drop only what code now shows.

## Versions and upgrades

The plugin owns the templates, this file, and the scripts; an adopting repo
carries only the filled-in files, the `.the-guide` stamp and a vendored
`scripts/validate_standard.py`. The stamp's first line is the standard version
adopted; an optional `size: <size>` line records the sizing row. Each release
that changes template structure ships an upgrade note; `upgrade-standard`
applies the note's machine-readable line edits itself and hands an agent only
the moves it cannot do. Filled-in content is never overwritten.

## Adopting

1. Install the plugin and run `adopt-standard`; it detects the repo, picks the
   lightest size with you, writes the templates, and fills what the code can
   tell it. Manual fallback: copy the files you need from `templates/`, fill
   placeholders, delete sections that do not apply, and remove the `AGENTS.md`
   rows (and the Code Review section) for files you skip.
2. If the repo is reviewed by an automated reviewer, keep `REVIEW.md` and
   `context.yaml` (delete `context.yaml` if no companion repo exists; the
   reviewer then reads this repo only).
3. Run `python3 scripts/validate_standard.py .` from the repo root and add it
   to CI (`ci.md` in the plugin has the snippet, with `doc_map.py --check` as
   the stale-doc backstop). If you keep `DESIGN.md`, also run
   `npx @google/design.md lint DESIGN.md`; the validator stays offline and
   does not check design tokens.
4. Keep it current: change a file in the same PR as the behavior it describes.
