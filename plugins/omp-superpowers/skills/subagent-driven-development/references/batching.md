# Batching Small Same-Shape Work

Part of skill://subagent-driven-development.

**Batch small same-shape work.** When the plan lists several tasks that are
each a small, independent edit of the same kind — the same one-line fix,
constant change, or field addition repeated across files — do not dispatch
one subagent per task. Compose ONE dispatch brief listing every file and
its change, send the whole batch to a single implementer agent, and review its diff
as one unit. Concatenate the per-task `task-brief` outputs into
`<workspace>/tasks-A-B-brief.md`, use `<workspace>/tasks-A-B-report.md` as the
report file, and append one `Task N: complete` ledger line per task when the
batch review is clean. Reserve one-dispatch-per-task for work that needs its own
judgment, its own tests, or its own review surface.
