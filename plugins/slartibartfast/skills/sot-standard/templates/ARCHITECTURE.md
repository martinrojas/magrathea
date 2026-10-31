---
name: <Product name> architecture
version: 0.1.0
last_reviewed: YYYY-MM-DD
owner: <person or team>
---

# Architecture — Non-Inferable Technical Context

> **For agents:** This file holds only what you cannot learn by reading the
> code: boundaries that must not be crossed, constraints, and deliberate
> oddities. It is not a tour of the codebase. If this file and the code
> disagree, trust the code, then flag the drift and propose a fix.
> Product intent → `PRODUCT.md`. Reasons behind choices → `docs/decisions/`.
>
> **Keep it short.** Add an entry only if a competent engineer (or agent) would
> otherwise get it wrong. Delete entries the code now makes obvious. Rewrite
> to current state; do not append history. Mark non-applicable sections
> `N/A — <reason>`. Cite code by `path#symbol`, never by line number, and
> state a safeguard exists only after reading the code that implements it.

## 1. System shape
Two to five sentences: the major parts, how they talk, and where it runs.
Link a diagram in `docs/` if one exists; do not inline a file-by-file map.

## 2. Boundaries and responsibilities
Parts of the system with a hard rule about what they may and may not do.

| ID | Part | Owns | Must not | Notes |
|----|------|------|----------|-------|
| BD1 | <module / service / layer> | <responsibility> | <forbidden dependency or action> | <ADR-xxxx if relevant> |

## 3. Technical constraints and invariants
Non-negotiables on the technical side: performance budgets, compatibility,
data integrity, security, deployment, platform limits.
- TC1: <constraint> — <reason>; serves <PRODUCT.md K#/BR# if applicable>

## 4. Data and flows that cross boundaries
Only flows where mistakes are costly (money, identity, permissions,
irreversible writes, external systems).
- F1: <flow in one line> — <what must always hold>

## 5. Integration points
External systems, what we depend on, and the failure behavior we expect.
| System | Used for | On failure | Quirks and limits (pagination, rate limits, delays, auth) |
|--------|----------|------------|------------------------------------------------------------|
| <service/API> | <purpose> | <retry / degrade / stop> | <what surprises people> |

Related repos a change here can break are listed once, in `context.yaml`
(repo, paths, why). Do not restate them here; add a row there.

## 6. Deliberate oddities and gotchas
Code that looks wrong but is intentional, and traps that have burned us.
Each points to the decision or incident that explains it.
- GO1: <oddity> — see ADR-<nnnn>

## 7. Risks
Project-specific, evidence-based risks only (not generic). Label each
DOCUMENTED or INFERRED.

| ID | Risk | Evidence | Mitigation | Basis |
|----|------|----------|------------|-------|
| R1 | <what could go wrong> | `<path>#<symbol>` or incident | <what limits it> | DOCUMENTED |

## 8. Where decisions live
- Reasoning for architectural choices: `docs/decisions/` (see its `README.md`
  for status rules).
- Product-level choices: `PRODUCT.md` §11.
