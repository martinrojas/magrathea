---
status: active            # active | done — close-plan deletes a done plan
opened: YYYY-MM-DD
owner: <person>
serves: []                # PRODUCT.md / ARCHITECTURE.md IDs this plan serves, e.g. [G1, BR-billing-2]
---

# <Plan title>

Disposable: this file is scaffolding for one change and is deleted by
`close-plan` when the change lands. Nothing here is a source of truth; cite
the IDs in `serves` instead of restating the documents.

## Goal
One or two sentences.

## Steps
- [ ] <step>

## Open questions
- <question> — owner: <who>
