---
name: domain-rules
description: Use when changing a domain's logic in a repo with PRODUCT.md §7 and you meet a business rule that is in neither the code nor docs/rules/<domain>.yaml
---

# Propose a domain rule

`<std>` is `skill://the-guide`.
Rules: `<std>/rules.md`. Rules files grow by demand: you propose the one rule you needed; the domain
owner accepts it.

## Steps

1. Find the domain's row in `PRODUCT.md` §7. If it has no rules file, create `docs/rules/<domain>.yaml`
   from `<std>/templates/docs/rules/TEMPLATE.yaml` with `domain`, `owner`, `system_of_record`,
   `last_reviewed`, and `paths:` filled. Put the path in the row's Rules file cell as a backticked
   `` `docs/rules/<domain>.yaml` `` (the validator's map check reads that form).
2. Allocate ids: `python3 <std>/scripts/next_id.py br <domain>` (and `sd <domain>` for a decision).
3. Write the rule as `WHEN … THE SYSTEM SHALL …` with a `given`/`expect` example, a `source`, and a
   `priority`.
4. Add known unknowns under `gaps:` with the owner to ask.
5. Write the test for the example and set `evidence: <test path>#<test name>`.
6. If the repo has `AGENTS.md` §Code Review and the rule is a must-rule a reviewer could check from a diff,
   propose (do not add) a one-line invariant for that section in your summary.
7. Validate: `python3 <std>/scripts/validate_standard.py .`
8. Propose the rule to the owner named in the row. The PR summary says "proposed BR-<domain>-N for <owner>
   to accept".

## Never

Accept a rule, or inventory a domain up front.
