# Handling a Report That Isn't DONE

Part of skill://subagent-driven-development.

**DONE_WITH_CONCERNS:** The implementer completed the work but flagged doubts. Read the concerns before proceeding. If the concerns are about correctness or scope, address them before review. If they're observations (e.g., "this file is getting large"), note them and proceed to review.

**NEEDS_CONTEXT:** The implementer needs information that wasn't provided. Provide the missing context and re-dispatch (or, if the implementer is still resumable, `write agent://<implementer-id>` with the context).

**BLOCKED:** The implementer cannot complete the task. Assess the blocker:
1. If it's a context problem, provide more context and re-dispatch with the same agent variant
2. If the task requires more reasoning, re-dispatch with the next stronger variant (`sp-implementer-fast` → `sp-implementer` → `sp-implementer-strong`)
3. If the task is too large, break it into smaller pieces
4. If the plan itself is wrong, rule on the correction, ledger it, and re-dispatch with the ruling carried in the dispatch

**Never** ignore an escalation or force the same agent variant to retry without changes. If the implementer said it's stuck, something needs to change.
