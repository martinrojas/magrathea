# the-guide

My personal **Project Source-of-Truth Standard** as an [OMP](https://github.com/can1357/oh-my-pi) plugin:
adopt it in a repo, keep its grounding docs in sync with the code, record decisions and domain rules, set up
code review, and upgrade. The plugin owns the standard's templates, rules (`STANDARD.md`) and scripts; an
adopting repo carries only its filled-in files, a `.the-guide` stamp and a vendored
`scripts/validate_standard.py`.

Objective: projects that keep a small, clean context so agents spend fewer tokens and invent less. Every
deterministic step (detection, scaffolding, id allocation, path-to-doc mapping, validation, upgrades) runs as
a stdlib Python script whose only output is one JSON object or error lines. Skills are short and point at
`rules.md` rather than restating it. The drift check runs in a read-only subagent on a small model and
returns only a diff. The hook is silent when checks pass.

## Install

```text
/marketplace add <owner>/<marketplace-repo>      # or a local path to the marketplace checkout
/marketplace install the-guide@magrathea
```

CLI equivalent: `omp plugin marketplace add <source>` then `omp plugin install the-guide@magrathea`.
Start a new session afterwards; skills, agents and the extension are discovered at startup. The scripts need
Python 3.9+; full checking of `docs/rules/*.yaml` and `context.yaml` needs PyYAML (`pip install pyyaml`),
otherwise those files get a reduced check.

## Skills

| Skill | Triggers when |
|---|---|
| `adopt-standard` | A repo adopts the standard (`AGENTS.md` router, `PRODUCT.md`, `ARCHITECTURE.md`, `REVIEW.md`, `context.yaml`, `docs/decisions`, `docs/rules`) or a monorepo adds a package. Includes reviewer setup. |
| `sync-docs` | Before opening a PR in an adopted repo when the change alters behavior, commands, paths, boundaries, or review invariants its grounding docs describe. |
| `close-plan` | A plan or spec has been implemented: runs `sync-docs`, asks five routing questions (decision record, rule, gotcha, `AGENTS.md` line, open question), deletes the plan. Distills the diff, never the session. |
| `record-decision` | A significant technical choice is made in a repo with `docs/decisions/`, or an accepted record must be superseded. |
| `domain-rules` | Changing a domain's logic and meeting a business rule that is in neither the code nor `docs/rules/<domain>.yaml`. |
| `upgrade-standard` | A repo's `.the-guide` stamp is older than the installed plugin. |

`the-guide` holds the shared assets (`rules.md`, `STANDARD.md`, `ci.md`, `templates/`, `scripts/`,
`upgrades/`), reachable as `skill://the-guide/<path>`. It is hidden.

## Agent

`drift-auditor`: read-only check of one grounding doc against the code paths it owns; returns a unified
diff or `No drift.`; dispatched by `sync-docs`. Runs on the `@smol` model role.

## Hook

`hooks/validate_grounding.py` runs after an edit or write. When the touched file is a grounding doc inside a
repo with a `.the-guide` stamp, it runs the repo's vendored validator (falling back to the bundled one)
and, only on errors, adds them to the agent's context. It prints nothing when checks pass and stays silent
in repos that have not adopted the standard.

OMP wires it through the extension `hooks/omp/validate-grounding.ts`, declared in `package.json` under
`omp.extensions`; it forwards `tool_result` events for `edit`/`write`/`ast_edit` to the Python script.

## What an adopting repo gets

See `skills/the-guide/STANDARD.md` for the file set, tiers and rules. In short: `AGENTS.md` (router,
about 100 lines, with the Code Review invariants a bot injects), `PRODUCT.md` (map of where product truth
lives), `ARCHITECTURE.md`, `docs/decisions/`, `docs/rules/<domain>.yaml` on demand, `REVIEW.md` and
`context.yaml` if reviewed, `DESIGN.md` if UI, `CHANGELOG.md` only if asked, `CLAUDE.md` as `@AGENTS.md`,
the stamp and the vendored validator. `docs/plans/` is ephemeral: outside the grounding scan, and the
validator warns on a plan marked `done` or older than 30 days (`--plan-age`). CI runs the validator and `doc_map.py --check` (`ci.md`).

## Developing

- Templates validate: `python3 skills/the-guide/scripts/validate_standard.py skills/the-guide/templates`
- Tests (from this directory): `python3 -m unittest discover -s tests` (60 tests, stdlib only, Python 3.9+)
- Version bump: change `skills/the-guide/templates/.the-guide`, `package.json` and the `version` in the
  magrathea `.omp-plugin/marketplace.json` together; add `skills/the-guide/upgrades/<version>.md`
  when template structure changes (format in `upgrades/README.md`).
- After editing a local checkout, reinstall with `--force` and start a new session.

## Lineage

A personal fork of an earlier Source-of-Truth Standard plugin, on the same principles: one template set,
review layer included, agent rules stated once in `AGENTS.md`, changelog optional, deterministic upgrades,
CI backstop.
