# Upstream

Adapted from [obra/superpowers](https://github.com/obra/superpowers) at commit
[`2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`](https://github.com/obra/superpowers/tree/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b)
(v7.0.1, 2026-10-21), MIT. When syncing, diff upstream `skills/` from this commit and re-apply the deviations below.

## File map

| Upstream | Here |
|---|---|
| `skills/brainstorming/SKILL.md` | `skills/brainstorming/SKILL.md` |
| `skills/brainstorming/builder-check-prompt.md` | `agents/sp-builder-check.md` |
| `skills/writing-plans/SKILL.md` | `skills/writing-plans/SKILL.md`, planner role in `agents/sp-planner.md` |
| `skills/subagent-driven-development/{SKILL.md,references/*,scripts/*}` | same paths (scripts verbatim) |
| `skills/subagent-driven-development/implementer-prompt.md` | `skills/sp-implementer-contract/SKILL.md` (hidden) + `agents/sp-implementer{,-fast,-strong}.md` |
| `skills/subagent-driven-development/task-reviewer-prompt.md` | `agents/sp-task-reviewer.md` |
| `skills/subagent-driven-development/re-review-prompt.md` | `agents/sp-re-reviewer.md` |
| `skills/executing-plans/{SKILL.md,scripts/*}` | same paths |
| `skills/requesting-code-review/code-reviewer.md` | `skills/sp-final-review-contract/SKILL.md` (hidden) + `agents/sp-final-reviewer.md` |
| `skills/finishing-a-development-branch/SKILL.md` | same path |
| `skills/systematic-debugging/{SKILL.md,root-cause-tracing.md,defense-in-depth.md,condition-based-waiting.md,condition-based-waiting-example.ts,find-polluter.sh}` | same paths |
| `skills/receiving-code-review/SKILL.md` | same path |
| `skills/test-driven-development/{SKILL.md,writing-good-tests.md}` | same paths |

## Not shipped

| Upstream | Reason |
|---|---|
| `using-superpowers` + session-start hook | OMP already puts skill names and descriptions in the system prompt and instructs the model to read matching skills on demand; the "1% chance, must invoke" bootstrap would add interruptions. |
| `using-git-worktrees` | Overlaps OMP task isolation and user/repo worktree rules; setup now only ensures a task branch. |
| `verification-before-completion` | Duplicates OMP's verification rules; its evidence rule is inlined where completion is claimed. |
| `dispatching-parallel-agents` | Duplicates OMP's delegation guidance. |
| `requesting-code-review/SKILL.md` | Replaced by the `sp-final-reviewer` agent. |
| `writing-skills`, `diagnosing-superpowers` | Upstream-maintenance tooling; OMP has `manage_skill`. |
| Brainstorming visual companion (`scripts/`, `visual-companion.md`) | Replaced by inline mermaid/svg or a static HTML mockup opened with OMP's browser tool; no server, no telemetry. |
| `systematic-debugging/{CREATION-LOG.md,test-*.md}` | Upstream eval fixtures. |

## Cross-cutting deviations

- Cross-references use `skill://<name>`; harness-specific tool names map to OMP tools (`task`, `todo`, `read`/`edit`/`write`,
  `bash`, `ask`, `write agent://<id>`). Scripts run as `bash skill://…/scripts/<name>`; `executing-plans` scripts call the
  SDD scripts through `"${BASH:-bash}"` instead of relying on exec bits.
- Per-call model selection is replaced by agent variants bound to OMP model roles (`@smol`, `@task`, `@slow`, `@plan`).
  Static prompt templates live in agent bodies or hidden contract skills; dispatches carry only per-task values.
- Waiting guidance: OMP delivers subagent results automatically; no polling or bounded waits.
- Git: plan headers carry a `**Git:**` line; plan approval authorizes local commits on the task branch only (spec, plan, task
  commits). Push/PR/merge/branch deletion/worktree removal need explicit user choice. `git merge --no-ff`, `git pull --ff-only`
  only when the base has an upstream, never force-push.
- Precedence line added: user and repository instructions override the skills. "Announce at start" lines removed.

## Per-skill deviations

- **brainstorming:** description scoped to larger work or an explicit brainstorm/design request (no "before any creative work",
  no non-software scope); hard gate applies only to triggered work; builder check dispatches `sp-builder-check`; recon may use
  OMP's `scout`; spec path fixed to `docs/superpowers/specs/`, written but committed only with authorization; spikes use a `spike/` branch.
- **writing-plans:** description scoped to an approved design/spec or an explicit plan request; project-sized plans are written
  by `sp-planner` (main session reviews against the spec); `**Git:**` and `**Test command:**` lines added to the templates;
  after approval the controller commits spec + plan; "Native" execution option renamed "Inline"; code-simplicity bullet added.
- **subagent-driven-development:** tier table maps tasks to `sp-implementer-fast` / `sp-implementer` / `sp-implementer-strong`;
  implementer dispatch includes Global Constraints; fix-loop rounds 1-3 resume the implementer via `write agent://<id>`,
  rounds 4-5 use `sp-implementer-strong`; BLOCKED escalation steps up the variant; NEEDS_CONTEXT replaces live questions
  (subagents cannot wait for answers); final review uses `sp-final-reviewer` with Review Focus and range, declined-to-judge
  lines become ledger rulings; batched dispatch defines brief/report file names; no "without bash" fallback.
- **executing-plans:** OMP tool table; final review dispatches `sp-final-reviewer` (no-subagent fallback reads
  `skill://sp-final-review-contract`); `task-done` uses the task's `**Test command:**`; pre-flight rulings use `Preflight: Ruling:`.
- **finishing-a-development-branch:** merge flow `pull --ff-only` (when upstream exists) then `merge --no-ff`; PR via OMP's
  GitHub tool or `gh`; cleanup only for worktrees under `.worktrees/`/`worktrees/`, OMP task-isolation workspaces left alone;
  force-push never.
- **test-driven-development:** scoped to bug fixes and approved-plan tasks (autoloaded by implementers); outside that scope the
  harness's normal test policy applies; during plan execution, "ask your human partner" becomes a BLOCKED/NEEDS_CONTEXT report
  or a ledger ruling.
- **systematic-debugging:** verification rule inlined; supporting-file references use `skill://`; same plan-execution note for
  the 3-failed-fixes discussion.
- **receiving-code-review:** "instruction-file violation" parenthetical dropped; GitHub thread replies via OMP's GitHub tool or `gh api`.
- **Reviewer contracts:** read-only, never edit product code; plan-mandated findings are ruled on by the controller;
  the final reviewer inspects historical files with `git show <sha>:<path>` instead of creating worktrees.
