# Project Source-of-Truth Standard

A small set of Markdown files that ground agents (and people) in what a
project is, what it must obey, and what code cannot tell them. This file is
for adopters; it is not loaded into agent context.

## Principle

Write only what an agent cannot infer from the code. Research on repository
context files found that generated or overlong files raise cost without
improving results, while short human-written files help modestly. So the set
is small, each file owns one kind of truth, and everything is lean.

## The files

| File | Tier | Owns |
|------|------|------|
| `AGENTS.md` | Core | Router: grounding docs, precedence, commands, conventions, done |
| `PRODUCT.md` | Core | Why: purpose, users, goals, non-goals, core terms, cross-domain constraints, and a map of where product truth lives per domain |
| `docs/rules/<domain>.yaml` | On demand | Business rules for one domain, written when agents change its logic and intent is not in the code |
| `DESIGN.md` | Core if UI | Visual system, in the [Google DESIGN.md format](https://github.com/google-labs-code/design.md): YAML tokens plus rationale prose |
| `ARCHITECTURE.md` | As needed | Non-inferable technical context: boundaries, constraints, risky flows, oddities, risks |
| `docs/decisions/` | As needed | One record per significant choice, with status |
| `docs/guides/` | On demand | Runbooks |
| `CLAUDE.md` | Shim | Single line: `@AGENTS.md` |

## Seven rules

1. **One owner per fact.** Other files point to it; they do not restate it.
2. **`AGENTS.md` is a router**, about 100 lines. A link plus a one-line hook
   beats a summary, which drifts.
3. **Non-inferable only.** Delete entries the code now makes obvious.
4. **Code wins on current behavior.** Flag drift and propose a fix.
5. **Rewrite to current state; do not append.** Decision history lives in the
   supersede chain.
6. **Verify or label.** State code behavior only after reading code; mark the
   rest "(inferred, not verified)". Never invent safeguards.
7. **Cite IDs, and cite code by `path#symbol`**, never by line number.

## Product grounding at different sizes

`DESIGN.md` works because a design system is finite. A product's rules are
not, so `PRODUCT.md` is a map, not a rulebook: a page of purpose, users,
goals, non-goals, core terms, constraints, and a table of domains with their
owner, system of record, and rules file. A map can be complete; a rulebook
for production software cannot, and an incomplete source of truth misleads.

- **Greenfield or small:** one domain. `PRODUCT.md`'s map has one row and the
  rules file can be written up front, since the rules are few and known.
- **Production, many stakeholders:** many domains. Fill the map (that is
  within reach for any PM) and write a rules file only when agents start
  changing a domain's logic. Grow by demand: an agent that meets an unwritten
  rule proposes a row; the domain owner accepts it. Rules recoverable from
  code are not written down; `code wins on current behavior` handles those.
- **Feature-level detail** (user stories, acceptance criteria) stays in the
  system of record or a per-change spec that cites `PRODUCT.md` IDs. It does
  not move into the standard.

## Formats

Every grounding document is Markdown with YAML front matter: prose carries
intent, front matter carries the few fields tools validate. Rules files are
the exception and are always YAML: they hold records that a tool reads, not
prose. YAML
matched Markdown on accuracy in file-native agent studies while costing far
fewer tokens for tabular data, and a fixed schema lets tools validate IDs and
generate tests from examples. No other format (JSON, TOON, XML) is used for
context files; the evidence favors none of them for agent reading.

## Sizing

| Project | Use |
|---------|-----|
| Small or personal | `AGENTS.md` + `PRODUCT.md` (one domain; rules inline or one rules file) |
| Software project | Core set + `ARCHITECTURE.md`, `docs/decisions/` as needed; rules files by demand |
| Monorepo | One root set; each package gets an `AGENTS.md` opening with `@../../AGENTS.md` (one `../` per level of depth), adding only what differs. The `@` import is a Claude Code feature; tools that inject the root file along with the package's make the package file carry only deltas either way |
| Docs or data repo | `AGENTS.md` only, adapted to content conventions and freshness rules |

When unsure, choose the lighter option. Adding structure later is easier than
removing it.

## Where content goes when a file outgrows its budget

| Growing content | Moves to |
|-----------------|----------|
| Architecture detail | `ARCHITECTURE.md` |
| Rationale for a choice | `docs/decisions/` |
| Business rules for a domain | `docs/rules/<domain>.yaml` |
| Runbooks, long how-tos | `docs/guides/` |

Move, do not delete: keep durable content, drop only what code now shows.

## Adopting

1. Copy the files you need; fill placeholders; delete sections that do not apply.
2. Remove the `AGENTS.md` rows for files you skip.
3. Run `python3 scripts/validate_standard.py` from the repo root. If you keep `DESIGN.md`, also run
   `npx @google/design.md lint DESIGN.md`: the standard's validator stays offline and does not check design tokens.
4. Keep it current: change a file in the same PR as the behavior it describes.
