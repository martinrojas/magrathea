---
name: domain-rules
description: Use when changing a domain's logic in a repo with PRODUCT.md §7 and you meet a business rule that is in neither the code nor docs/rules/<domain>.yaml
---

# Propose a domain rule

Rules: `skill://sot-standard/STANDARD.md` ("Product grounding at different sizes"). Rules files grow by demand: you
propose one rule you needed; the domain owner accepts it.

## Steps

1. Find the domain's row in PRODUCT.md §7. If it has no rules file, create `docs/rules/<domain>.yaml` from
   `skill://sot-standard/templates/docs/rules/TEMPLATE.yaml` with `domain`, `owner`, `system_of_record`,
   `last_reviewed`, and `paths:` filled. Put the path in the row's Rules file cell as a backticked
   `` `docs/rules/<domain>.yaml` `` (the validator's map check reads that form).
2. Allocate ids: `python3 skill://sot-standard/scripts/next_id.py br <domain>` (and `sd <domain>` for a decision).
3. Write the rule as `WHEN … THE SYSTEM SHALL …` with a `given`/`expect` example, a `source`, and a `priority`.
4. Add known unknowns under `gaps:` with the owner to ask.
5. Write the test for the example and set `evidence: <test path>#<test name>`.
6. Validate: `python3 skill://sot-standard/scripts/validate_standard.py .`
7. Propose the rule to the owner named in the row. The PR summary says "proposed BR-<domain>-N for <owner> to
   accept".

## Never

Accept a rule, or inventory a domain up front.
