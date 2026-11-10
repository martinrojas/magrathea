---
name: <Product name>
version: 0.1.0
status: draft            # draft | active | frozen
last_reviewed: YYYY-MM-DD
owner: <person or team>
type: <web app | API | internal tool | library | ...>
---

# <Product name> — Product Grounding

> **For agents:** This page grounds you in why the product exists and tells you
> where its rules live. It is a map, not the rulebook: rules for a domain live
> in that domain's file (§7) or in the system of record it names. How to treat
> this file (precedence, code wins, verify or label, cite IDs, propose rather
> than edit) is stated once, in `AGENTS.md` §Grounding documents.
> Look and feel → `DESIGN.md`. Technical constraints → `ARCHITECTURE.md`.
> Why past choices were made → `docs/decisions/`.

## 1. Purpose
One or two sentences: what this is, for whom, and why it exists.

## 2. Users
| ID | User | Primary need |
|----|------|--------------|
| U1 | <role> | <what they must accomplish> |

## 3. Goals and how we measure them
| ID | Goal | Signal |
|----|------|--------|
| G1 | <outcome> | <metric or observable result> |

## 4. Non-goals
Deliberately **not** done. Agents must not add these, even if helpful.
- NG1: <excluded capability> — <why>

## 5. Core terms
Only terms whose misuse would cause a wrong change (ten or fewer). Use them
exactly in code, UI, and copy. Domain-specific terms go in the domain's file.

| Term | Definition | Not to be confused with |
|------|------------|-------------------------|
| <Term> | <one sentence> | <similar term> |

## 6. Constraints
Non-negotiables that cut across domains: legal, privacy, security, money,
platform. Technical ones live in `ARCHITECTURE.md`.
- K1: <constraint> — <reason / source>

## 7. Where product truth lives
One row per domain. The rules file is written only when agents work in that
domain and the rules are not recoverable from code. Until then, the system of
record is the source and the owner is who to ask.

| Domain | Owner | System of record (PRDs, tickets, policies) | Rules file |
|--------|-------|--------------------------------------------|------------|
| <billing> | <team or person> | <link to where decisions get made> | `docs/rules/<billing>.yaml` |
| <permissions> | <team or person> | <link> | — (ask owner) |

Rules files are YAML (schema: `docs/rules/TEMPLATE.yaml`) so tools can
validate them and generate tests from their examples.

## 8. Open questions
Cross-domain items agents must not guess on.
- Q1: <question> — owner: <who>, needed by: <when>

## 9. Maintaining this file
- Write only what code cannot tell you; mark sections that do not apply
  `N/A — <reason>`; rewrite to current state, do not append history.
- **Grow by demand.** When an agent meets a rule that is in neither code nor a
  rules file, it proposes a row in the domain's file (created from
  `docs/rules/TEMPLATE.yaml`); the owner accepts it. Never inventory a domain
  up front.
- Changes: propose as a diff; on approval bump `version` and `last_reviewed`.
