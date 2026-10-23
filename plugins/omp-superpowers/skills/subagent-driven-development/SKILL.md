---
name: subagent-driven-development
description: Use when executing an approved implementation plan with mostly independent tasks by dispatching a fresh implementer agent per task with task-level and final reviews, instead of working through the plan inline
---

# Subagent-Driven Development

Execute plan by dispatching a fresh implementer subagent per task, a task review (spec compliance + code quality) after each, and a broad whole-branch review at the end.

**Why subagents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They never inherit your session's context, history, or AGENTS.md — the dispatch must be self-contained, so you construct exactly what they need. This also preserves your own context for coordination work.

**Core principle:** Fresh subagent per task + task review (spec + quality) + broad final review = high quality, fast iteration

User and repository instructions (AGENTS.md etc.) override this skill.

**Narration:** between tool calls, narrate at most one short line — the
ledger and the tool results carry the record.

**Continuous execution:** Do not pause to check in with your human partner between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are the four named below, or all tasks complete. "Should I continue?" prompts and progress summaries waste their time — they asked you to execute the plan, so execute it.

**Rulings, not stalls.** A running plan does not wait on a human. Conflicts,
ambiguities, plan defects, a cap you would have asked to exceed — decide
them. The spec is the binding authority, the plan is its argument, and your
judgment settles what neither answers. Record every decision in the ledger as
`Ruling: <what you decided> — <why> — <what it costs if wrong>`, and keep
going. A wrong ruling costs rework your human partner can see and undo; a
session parked on a question costs their whole day and buys nothing.

Four things stop you, and only these: an irreversible or destructive
operation; a security-sensitive action; a side effect outside this worktree
that norms say you ask about first (a merge, a push to a shared branch, a
publish); and a plan so broken that every path forward is a guess. For those,
stop and ask. Push, PR creation, merge, branch deletion, and worktree
removal always need separate explicit user approval. Local commits on the
plan's task branch follow user/repository instructions; where those are
silent, plan approval authorizes them.

## When to Use

```dot
digraph when_to_use {
    "Have implementation plan?" [shape=diamond];
    "Tasks mostly independent?" [shape=diamond];
    "Partner chose inline, or no task tool?" [shape=diamond];
    "subagent-driven-development" [shape=box];
    "executing-plans" [shape=box];
    "Manual execution or brainstorm first" [shape=box];

    "Have implementation plan?" -> "Tasks mostly independent?" [label="yes"];
    "Have implementation plan?" -> "Manual execution or brainstorm first" [label="no"];
    "Tasks mostly independent?" -> "Partner chose inline, or no task tool?" [label="yes"];
    "Tasks mostly independent?" -> "Manual execution or brainstorm first" [label="no - tightly coupled"];
    "Partner chose inline, or no task tool?" -> "executing-plans" [label="yes"];
    "Partner chose inline, or no task tool?" -> "subagent-driven-development" [label="no"];
}
```

**vs. Executing Plans (inline):**
- Fresh subagent per task (no context pollution) instead of one context doing every task
- Review after each task (spec compliance + code quality) instead of only at the end
- Costs a fresh context per task and per review; inline costs one context plus one final reviewer
- Both run in this session, share the same plan workspace and ledger, and never pause between tasks

## The Process

```dot
digraph process {
    rankdir=TB;

    subgraph cluster_per_task {
        label="Per Task";
        "Dispatch sp-implementer agent via task tool" [shape=box];
        "Implementer asks questions?" [shape=diamond];
        "Answer questions, provide context" [shape=box];
        "Implementer implements, tests, commits, self-reviews" [shape=box];
        "Generate review package, dispatch sp-task-reviewer" [shape=box];
        "Spec ✅ and quality approved?" [shape=diamond];
        "Fix loop: read references/fix-loop.md before every round" [shape=box];
        "Append completion to ledger, mark todo complete" [shape=box];
    }

    "Setup: task branch, ledger check, read plan, pre-flight review" [shape=box];
    "More tasks remain?" [shape=diamond];
    "Final review and finish: read references/final-review.md" [shape=box];
    "Final review clean: delete this plan's workspace" [shape=box];
    "Read skill://finishing-a-development-branch" [shape=box style=filled fillcolor=lightgreen];

    "Setup: task branch, ledger check, read plan, pre-flight review" -> "Dispatch sp-implementer agent via task tool";
    "Dispatch sp-implementer agent via task tool" -> "Implementer asks questions?";
    "Implementer asks questions?" -> "Answer questions, provide context" [label="yes"];
    "Answer questions, provide context" -> "Implementer implements, tests, commits, self-reviews";
    "Implementer asks questions?" -> "Implementer implements, tests, commits, self-reviews" [label="no"];
    "Implementer implements, tests, commits, self-reviews" -> "Generate review package, dispatch sp-task-reviewer";
    "Generate review package, dispatch sp-task-reviewer" -> "Spec ✅ and quality approved?";
    "Spec ✅ and quality approved?" -> "Append completion to ledger, mark todo complete" [label="yes"];
    "Spec ✅ and quality approved?" -> "Fix loop: read references/fix-loop.md before every round" [label="no"];
    "Fix loop: read references/fix-loop.md before every round" -> "Append completion to ledger, mark todo complete" [label="addressed, or parked at the cap"];
    "Append completion to ledger, mark todo complete" -> "More tasks remain?";
    "More tasks remain?" -> "Dispatch sp-implementer agent via task tool" [label="yes"];
    "More tasks remain?" -> "Final review and finish: read references/final-review.md" [label="no"];
    "Final review and finish: read references/final-review.md" -> "Final review clean: delete this plan's workspace";
    "Final review clean: delete this plan's workspace" -> "Read skill://finishing-a-development-branch";
}
```

## Setup

Ensure you are on the plan's task branch (the `**Git:**` line in the plan
header names it); create it if missing. Never implement on the base or
protected branch. Create a worktree only when repo or user instructions call
for one or the current tree holds unrelated uncommitted work; otherwise work
in place without asking. Implementers run sequentially in the shared tree —
never use the `task` tool's `isolated` option for plan tasks. If the spec and
plan are not yet committed, commit them on the task branch.

Conversation memory does not survive compaction. In real sessions,
controllers that lost their place have re-dispatched entire completed task
sequences — the single most expensive failure observed. Track progress in
a ledger file, not only in todos.

- Each plan owns a workspace: at skill start, run this skill's
  `bash skill://subagent-driven-development/scripts/sdd-workspace PLAN_FILE` — it prints the plan's git-ignored
  directory (under `<repo-root>/.superpowers/sdd/`), home to
  every artifact for THIS plan: ledger, briefs, reports, review packages.
  Another plan's directory is never yours to read or write.
- Check for this plan's ledger at `<workspace>/progress.md`. If one exists,
  read [references/resuming.md](references/resuming.md) before anything
  else: it says whose ledger it is and where to resume.
- Create the ledger with its identity as the first line:
  `# SDD ledger — plan: <plan file path>`.
- The ledger is your recovery map: the commits it names exist in git even
  when your context no longer remembers creating them. After compaction,
  trust the ledger and `git log` over your own recollection.
- `git clean -fdx` will destroy the workspace (it's git-ignored scratch); if
  that happens, recover from `git log`.

Read the plan once, note its context and Global Constraints, and create a
todo per task with the `todo` tool. If the plan names a Spec, read that too: the spec is the
authority the plan argues from, and conflicts inside the plan resolve
against it. A plan with no reachable spec gets a ledger note saying so —
rulings made without one are provisional.

Before dispatching Task 1, read [references/preflight.md](references/preflight.md)
and run the conflict scan it describes. Its table and rulings go in the
ledger.

## Model Selection

Models are not chosen per dispatch. Each tier is an agent variant, and each
variant's model comes from the user's own OMP model roles (`@smol`, `@task`,
`@slow`), so pick the variant, not a model. Use the least powerful variant
that can handle each role.

| Role | Agent | Model role | Use when |
|---|---|---|---|
| Implementer, mechanical | `sp-implementer-fast` | `@smol` | The task's plan text contains the complete code to write (transcription plus testing), or it is a single-file mechanical fix |
| Implementer, default | `sp-implementer` | `@task` | Prose-specified tasks, multi-file coordination, integration, pattern matching, debugging |
| Implementer, strong | `sp-implementer-strong` | `@slow` | Design judgment or broad codebase understanding; fix-loop rounds 4-5 escalation |
| Task review | `sp-task-reviewer` | `@task` | Every per-task spec + quality review |
| Scoped re-review | `sp-re-reviewer` | `@task` | Every fix-round re-review |
| Final review | `sp-final-reviewer` | `@slow` | The one whole-branch review |

**Turn count beats token price.** Wall-clock and context cost scale with how
many turns a subagent takes, and the cheapest models routinely take 2-3× the
turns on multi-step work — costing more overall. Use `sp-implementer` as the
floor for implementers working from prose descriptions; reserve
`sp-implementer-fast` for transcription and single-file mechanical work.

**Task complexity signals (implementation tasks):**
- Plan text contains the complete code, or a single-file mechanical fix → `sp-implementer-fast`
- Touches multiple files with integration concerns → `sp-implementer`
- Requires design judgment or broad codebase understanding → `sp-implementer-strong`

**Fix-loop escalation (rounds 4-5):** `sp-implementer-strong`, at least one
tier above the implementer that got stuck.

## The Task Loop

**Small same-shape work:** when the plan lists several small edits of the
same kind across files, read [references/batching.md](references/batching.md)
before dispatching them.

Everything you paste into a dispatch prompt — and everything a subagent
prints back — stays resident in your context for the rest of the session
and is re-read on every later turn. Hand artifacts over as files.

**Waiting on dispatched subagents:** results auto-deliver as follow-up
messages. Never poll, and never sit in a wait while you have local work —
ledger updates, packaging the next review, reading reports. Call `wait` only
when you are genuinely idle and blocked on a result. If a child seems lost or
stuck, reconcile: `read proc://` lists live jobs, `read proc://<id>` shows
status and output, and `read agent://<id>` returns a finished agent's output.
Chase any child that finished without reporting.

### 1. Dispatch the implementer

Record BASE (`git rev-parse HEAD`) before dispatching — the review package
and fix-round diffs need it.

- **Task brief:** before dispatching an implementer, run
  `bash skill://subagent-driven-development/scripts/task-brief PLAN_FILE N` — it extracts the task's full text to a
  uniquely named file and prints the path. Compose the dispatch so the
  brief stays the single source of requirements.
- **Dispatch via the `task` tool:** `{context, tasks:[{agent, name, task,
  solutionSpace}]}` with `agent` set to the variant from Model Selection. The
  static role instructions (no-subagents rule, report contract, self-review,
  TDD) already live in the agent body and the autoloaded
  `sp-implementer-contract` skill, so the dispatch carries only per-task
  values: (1) one line on where this task fits in the project; (2) the brief
  path, introduced as "read this first — it is your requirements, with the
  exact values to use verbatim"; (3) interfaces and decisions from earlier
  tasks that the brief cannot know; (4) your resolution of any ambiguity you
  noticed in the brief; (5) the report-file path; (6) BASE and the working
  directory; (7) the plan's Global Constraints, verbatim (task-brief extracts
  only the Task section; the plan's `**Test command:**` line for the task is
  in the brief). Exact values (numbers, magic strings, signatures, test cases)
  appear only in the brief. Never make a subagent read the whole plan file.
  Subagents do not see this conversation, so anything they need that is not
  in a file must be in the dispatch.
- **Report file:** name the implementer's report file after the brief
  (brief `…/task-N-brief.md` → report `…/task-N-report.md`) and put it in
  the dispatch. The implementer writes the full report there and
  returns only status, commits, a one-line test summary, and concerns.
- A dispatch describes one task, not the session's history. Do not
  paste accumulated prior-task summaries ("state after Tasks 1-3") into
  later dispatches — a real session's dispatch hit 42k chars of which 99%
  was pasted history. A fresh subagent needs its task, the interfaces it
  touches, and the global constraints. Nothing else.
- The implementer contract forbids spawning subagents: the implementer
  never dispatches helpers, and never a reviewer. Review arrives from you,
  after the report. In real sessions, every reviewer a worker spawned
  duplicated the task review the controller dispatched anyway — a full
  extra review seat per task.
- If an earlier task parked a finding in the area this task touches, carry
  a pointer to that ledger entry in the dispatch.
- Record the implementer's agent id from the dispatch result — fix-loop
  rounds 1-3 resume this agent with `write agent://<id>`.
- Never dispatch multiple implementation subagents in parallel (conflicts).

### 2. Handle the report

Implementer subagents report one of four statuses. Handle each appropriately:

**DONE:** Generate the review package (`bash skill://subagent-driven-development/scripts/review-package PLAN_FILE BASE HEAD` — it prints the unique file path it wrote; BASE is the commit you recorded before dispatching the implementer — never `HEAD~1`, which silently drops all but the last commit of a multi-commit task), then dispatch `sp-task-reviewer` with the printed path.

**Any other status** (DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED): read
[references/handling-reports.md](references/handling-reports.md) and follow
it, every time you get one.

If the implementer asks questions — before starting or mid-task (it
reports NEEDS_CONTEXT, or messages you) — answer via `write agent://<id>`
clearly and completely, provide additional context if needed, and don't
rush it into implementation.

### 3. Review the task

Per-task reviews are task-scoped gates. The broad review happens once, at the
final whole-branch review. Never skip the task review, and never accept a
report missing either verdict — spec compliance AND task quality are both
required. Implementer self-review never replaces the task review; both are
needed.

- Hand the reviewer its diff as a file: run
  `bash skill://subagent-driven-development/scripts/review-package PLAN_FILE BASE HEAD` and pass the reviewer the file path
  it prints. The output never enters your own context, and the reviewer sees
  the commit list, stat summary, and full diff with context in one `read`
  call. Use the BASE you recorded before dispatching the implementer —
  never `HEAD~1`, which silently truncates multi-commit tasks. Never
  dispatch a task reviewer without a diff file.
- **Reviewer inputs:** the `sp-task-reviewer` dispatch carries three paths —
  the same brief file, the report file, and the review package — plus BASE,
  HEAD, and the global constraints that bind the task.
- The global-constraints block you hand the reviewer is its attention
  lens. Copy the binding requirements verbatim from the plan's Global
  Constraints section or the spec: exact values, exact formats, and the
  stated relationships between components ("same layout as X", "matches
  Y"). The reviewer agent's body already carries the process rules (YAGNI,
  test hygiene, review method) — the constraints block is for what THIS
  project's spec demands.
- Do not add open-ended directives like "check all uses" or "run race tests
  if useful" without a concrete, task-specific reason
- Do not ask a reviewer to re-run tests the implementer already ran on the
  same code — the implementer's report carries the test evidence
- Do not pre-judge findings for the reviewer — never instruct a reviewer to
  ignore or not flag a specific issue. If you believe a finding would be a
  false positive, let the reviewer raise it and adjudicate it in the review
  loop. If the prompt you are writing contains "do not flag," "don't treat X
  as a defect," "at most Minor," or "the plan chose" — stop: you are
  pre-judging, usually to spare yourself a review loop.
If the reviewer reports "⚠️ Cannot verify from diff" items, read
[references/cannot-verify.md](references/cannot-verify.md) before you mark
the task complete.

### 4. The fix loop

The loop triggers when the review reports spec ❌, any Critical or Important
finding, or a ⚠️ item you confirmed as a real gap.

When it triggers, read [references/fix-loop.md](references/fix-loop.md) and
follow it. Read it again before every round, even if you read it earlier in
this session: it holds the round cap, the breaker, and the ledger line each
round writes, and your memory of it does not survive compaction.

### 5. Complete the task

When the review comes back clean — or every open finding is parked with a
ruling at the cap — append the completion line to the ledger in the same
message as your other bookkeeping:

- `Task <N>: complete (commits <base7>..<head7>, review clean)`
- `Task <N>: complete (commits <base7>..<head7>, <K> parked)` after a
  tripped breaker

Then mark the todo complete and move on. Before claiming a task or the
plan done, the evidence must be fresh: the implementer's report shows the
test command and its output for the final code, and any claim you pass on is
backed by that output, not by recollection. Never move to the next task while
the review has open Critical/Important issues that are neither fixed nor
parked-with-ruling at the cap.

## Final Review

When every task is complete, read
[references/final-review.md](references/final-review.md) and follow it. It
covers the whole-branch review, its single fix wave, and how you finish.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Close enough on spec compliance" | Reviewer found spec gaps = not done. Fix or hit the cap and adjudicate — those are the only exits. |
| "I'll fix it myself, dispatching is overhead" | Controller fixes pollute your context and skip review. Resume the implementer with `write agent://<id>`. |
| "One more round will converge" | Past the cap, rounds don't converge — the failure is structural. Adjudicate and route. |
| "The reviewer will just find something new anyway" | Scoped re-reviews verify fixes; they cannot wander. New findings on untouched code go to the ledger, not the loop. |
| "This finding is obviously wrong, I'll drop it" | You adjudicate only at the cap, and every ruling is a ledger entry. Silent discards are forbidden. |
| "The fix was small, skip the re-review" | Unreviewed fixes are how regressions land. Every round ends with a scoped re-review. |
| "Reviews slow the loop down" | The loop without reviews is just unverified churn. Reviews are the loop's brakes and steering. |
| "Ledger bookkeeping is overhead" | The ledger is what survives compaction. Controllers without one have re-dispatched entire completed task sequences. |
| "The implementer spawned its own reviewer — free extra assurance" | It's a duplicate seat reviewing the same diff; the task review is the gate. A worker-spawned reviewer is a defect to flag, not rigor. |
