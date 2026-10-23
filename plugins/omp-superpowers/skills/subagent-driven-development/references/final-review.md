# Final Review and Finish

Part of skill://subagent-driven-development. Every task in the plan is
complete.

The final whole-branch review gets a package too: run
`bash skill://subagent-driven-development/scripts/review-package PLAN_FILE MERGE_BASE HEAD` (MERGE_BASE = the commit the
branch started from, e.g. `git merge-base main HEAD`) and include the
printed path in the final review dispatch, so the final reviewer reads
one file instead of re-deriving the branch diff with git commands. Dispatch
the `sp-final-reviewer` agent (it runs on the `@slow` role; see SKILL.md's
Model Selection) via the `task` tool. Its dispatch carries the review package
path, the plan and spec paths, the git range `MERGE_BASE..HEAD`, the plan's
Review Focus verbatim (or "none"), and the ledger's deferred-minor and parked
lines so it can triage which must be fixed before merge. Every "Declined to
judge" line in its report becomes a ledger line
`Final: Ruling: <behavior> — <why> — <cost if wrong>`.

If the final whole-branch review returns findings, dispatch ONE fix agent (`sp-implementer`, or `sp-implementer-strong` when the findings need design judgment)
with the complete findings list — not one fixer per finding. Write the findings to
`<workspace>/final-fixes-brief.md`, name `<workspace>/final-fixes-report.md` as
the report file, and record FIX_BASE (`git rev-parse HEAD`) before dispatching.
The dispatch carries both paths, BASE (= FIX_BASE), the working directory, and
the plan's Global Constraints.
Per-finding fixers each rebuild context and re-run suites; a real
session's final-review fix wave cost more than all its tasks combined.
Then run exactly one scoped re-review of the fix wave
(`bash skill://subagent-driven-development/scripts/review-package PLAN_FILE FIX_BASE HEAD`
over the fix range, dispatched to `sp-re-reviewer` with the brief, report, FIX_BASE, HEAD, the
findings list, and the package path).
Adjudicate any residual findings as in the fix loop's breaker
(references/fix-loop.md): park with rulings, or rule on the load-bearing
ones and ledger what you decided. Only the four things that stop a running
plan (top of SKILL.md) stop you here. There is no second fix wave —
residual load-bearing findings surface to your human partner when
finishing-a-development-branch presents the options.

### Finish

Before you delete anything, collect every ledger line containing `Ruling:` —
preflight rulings, parked findings, breaker adjudications, all of them — into
your final message under "Rulings I made", in the order you made them, each
with what it costs if wrong. The list is exhaustive: if the ledger holds a
ruling, the list holds it. That list is the only place the decisions you
took on your human partner's behalf reach them — they read it and rework
whatever you got wrong. A ruling that dies with the workspace was a decision
made in secret.

When the final whole-branch review is clean and its fixes are committed,
delete this plan's workspace (`rm -rf <workspace>`) — the git history is
the record now. Sibling directories belong to other plans; leave them
alone.

Then read `skill://finishing-a-development-branch` and follow it. Push, merge and
publish need your human partner's explicit approval; commits on the task
branch were authorized by plan approval.
