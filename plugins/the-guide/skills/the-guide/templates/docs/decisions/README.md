# Decision Records

One file per significant decision: what was chosen, why, and what it costs.
Records explain **why**. `ARCHITECTURE.md` states **what holds now**.

## How agents must treat records

| Status | Meaning | Agent behavior |
|--------|---------|----------------|
| `accepted` | Current and binding | Follow it. If a task conflicts, stop and raise it; propose either changing the task or superseding the record. |
| `proposed` | Under discussion | Context only. Not binding. |
| `rejected` | Considered and declined | Do not re-propose without new information. |
| `superseded` | Replaced by a newer record | History only. Follow the record named in `superseded_by`. |
| `deprecated` | No longer applies, no replacement | History only. |

Additional rules:
- Check this index before proposing architectural or cross-cutting changes.
- If code visibly contradicts an `accepted` record, do not assume either is
  right. Report the drift and propose which one should change.
- Never edit an `accepted` record's decision in place. Supersede it with a new
  record. Typo and link fixes are fine; note them with an `updated` date.
- State each rule in one record only; cross-reference from others.
- Where code deliberately depends on a record, leave a one-line comment at the
  site, for example `// intentionally synchronous, see ADR-0007`.
- Draft a record while the context is fresh (at the time of the decision),
  mark it `proposed`, and let a human accept it.

## Conventions
- File name: `NNNN-short-slug.md` (zero-padded, never reused). Start from
  `0000-template.md`.
- Keep each record to about a page.
- Relate records to product IDs from `PRODUCT.md` in `relates_to`.
- Rewrite to current state; the exception is the decision history itself, which
  stays in the supersede chain.
- Cite code by `path#symbol`, never by line number.

## Index

| ID | Title | Status | Date | Supersedes / by |
|----|-------|--------|------|-----------------|
| _none yet_ | | | | |
