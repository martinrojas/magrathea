# CI check for an adopting repo

Two commands, no LLM, seconds to run. The validator is the gate for the
grounding docs themselves; `doc_map.py --check` is the backstop that fails a
PR when owned code changed and its doc did not. Run them as a required
check so an automated reviewer that waits on checks sees them.

`doc_map.py` is not vendored; CI gets it by cloning the plugin at a pinned
tag or by copying `skills/the-guide/scripts/doc_map.py` next to the
vendored validator (then `upgrade-standard` refreshes both).

## GitHub Actions

```yaml
name: grounding-docs
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pyyaml
      - run: python3 scripts/validate_standard.py . --strict
      - run: python3 scripts/doc_map.py --root . --base origin/${{ github.base_ref }} --check
```

## CircleCI

```yaml
  grounding-docs:
    docker: [{ image: cimg/python:3.12 }]
    steps:
      - checkout
      - run: pip install pyyaml
      - run: python3 scripts/validate_standard.py . --strict
      - run: python3 scripts/doc_map.py --root . --base origin/main --check
```

Drop `--strict` until the repo's placeholders are filled. With `DESIGN.md`,
add `npx @google/design.md@0.4.0 lint DESIGN.md` (needs Node and network).
