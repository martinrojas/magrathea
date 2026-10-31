---
id: ADR-0000
title: <Short decision title>
status: proposed          # proposed | accepted | rejected | superseded | deprecated
date: YYYY-MM-DD
updated:                  # only if edited after acceptance (typo/link fixes)
deciders: <who was involved>
supersedes:               # ADR-nnnn, if this replaces one
superseded_by:            # ADR-nnnn, set when replaced
relates_to: []            # PRODUCT.md / ARCHITECTURE.md IDs, e.g. [BR3, TC1, BD2]
---

# ADR-0000: <Short decision title>

## Context
What situation forces a choice? Include only the facts an agent or new
engineer could not infer from the code.

## Options considered
1. **<Option A>** — <one line, including its main cost>
2. **<Option B>** — <one line, including its main cost>

## Decision
State the choice in one or two sentences, in the active voice
("We will use ...").

## Consequences
- **Gains:** <what gets better>
- **Costs:** <what gets worse or harder>
- **Follow-ups:** <work, rules, or ARCHITECTURE.md entries this creates>

## Notes for agents
- Rule this record owns (state it once, here): <rule>
- Where code depends on it: <path or "see comment `ADR-0000` at call sites">
- Revisit if: <condition that would make this stale>
