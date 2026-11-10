# The seven rules

Loaded by agents working on grounding docs. Everything else about the
standard (files, tiers, sizing, review, formats) is in `STANDARD.md`, for
adopters.

1. **One owner per fact.** Other files point to it; they do not restate it.
   The agent rules live in `AGENTS.md` §Grounding documents and nowhere else.
2. **`AGENTS.md` is a router**, about 100 lines (hard limit 150). A link plus
   a one-line hook beats a summary, which drifts.
3. **Non-inferable only.** Delete entries the code now makes obvious.
4. **Code wins on current behavior.** Flag drift and propose a fix.
5. **Rewrite to current state; do not append.** Decision history lives in the
   supersede chain. Only `CHANGELOG.md` appends.
6. **Verify or label.** State code behavior only after reading code; mark the
   rest "(inferred, not verified)". Never invent safeguards.
7. **Cite IDs, and cite code by `path#symbol`**, never by line number.

Where content goes when a file outgrows its budget: architecture detail →
`ARCHITECTURE.md`; rationale → `docs/decisions/`; business rules →
`docs/rules/<domain>.yaml`; runbooks → `docs/guides/`; deep review topics →
`docs/reviews/`. Move, do not delete. Plans and sessions go nowhere: distill
the diff through `close-plan`, then delete the plan.
