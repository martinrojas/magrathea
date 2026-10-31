# playon-standard

The PlayOn Project Source-of-Truth Standard as an [OMP](https://github.com/can1357/oh-my-pi) plugin: adopt it in a repo,
keep its grounding docs in sync with the code, record decisions and domain rules, and upgrade it. The plugin owns the
standard's templates, rules (`STANDARD.md`) and scripts; adopting repos vendor only `scripts/validate_standard.py`.

## Install

```text
/marketplace add <owner>/<marketplace-repo>      # or a local path to the marketplace checkout
/marketplace install playon-standard@magrathea
```

CLI equivalent: `omp plugin marketplace add <source>` then `omp plugin install playon-standard@magrathea`.
Start a new session afterwards; skills, agents and hooks are discovered at startup.

## Skills

| Skill | Triggers when |
|---|---|
| `adopt-standard` | A repo adopts the PlayOn Source-of-Truth Standard (AGENTS.md router, PRODUCT.md, ARCHITECTURE.md, docs/decisions, docs/rules) or a monorepo adds a package to it. |
| `sync-docs` | Before opening a PR in a repo with a `.sot-standard` stamp when the change alters behavior, commands, paths, or boundaries that its grounding docs describe. |
| `record-decision` | A significant technical choice is made in a repo with `docs/decisions/`, or an accepted decision record must be superseded. |
| `domain-rules` | Changing a domain's logic in a repo with PRODUCT.md §7 and you meet a business rule that is in neither the code nor `docs/rules/<domain>.yaml`. |
| `upgrade-standard` | A repo's `.sot-standard` stamp is older than the installed plugin, or you ask to upgrade a repo to a new standard version. |

`sot-standard` is a hidden skill holding the shared assets (`STANDARD.md`, `templates/`, `scripts/`, `upgrades/`).

## Agent

| Agent | Model role | Used for |
|---|---|---|
| `drift-auditor` | `@smol` | Read-only check of one grounding doc against the code paths it owns; dispatched by `sync-docs`. |

Override with `task.agentModelOverrides`, for example `drift-auditor: "@task"`.

## Hook

`hooks/post/validate-grounding.ts` runs after `edit`, `write` and `ast_edit`. When the touched file is a grounding doc
inside a repo with a `.sot-standard` stamp, it runs the validator and, only on errors, adds them to the agent's context.
It prints nothing when checks pass and stays silent in repos that have not adopted the standard.

## Developing

- Templates validate: `cd skills/sot-standard/templates && python3 ../scripts/validate_standard.py .`
- Tests (from this directory): `python3 -m unittest discover -s tests`
- Scripts are stdlib-only and must run on Python 3.9.
- Version bump: change `skills/sot-standard/templates/.sot-standard` and the catalog `version` in
  `.omp-plugin/marketplace.json` together; add `skills/sot-standard/upgrades/<version>.md` when template structure changes.
- Marketplace installs run from a cached copy: after editing a local checkout run
  `omp plugin install --force playon-standard@magrathea` and start a new session.
