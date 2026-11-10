# Upgrade notes

Each release that changes template **structure** adds `upgrades/<version>.md`
(for example `1.1.0.md`). `scaffold.py upgrade` applies every note between the
repo's stamp and the plugin's, in version order, and ignores this README.

A note has up to two parts:

1. A fenced ```ops block holding a JSON list of idempotent line edits the
   script applies itself. Each op is `{"file", "op", "match", "line"}`:
   `insert_after` adds `line` after the first line starting with `match`
   (skipped if a line with the same first 24 characters already exists);
   `replace` replaces the first line starting with `match`. Files the repo
   never adopted are skipped.
2. A `## Manual` section listing moves an agent has to make (content
   relocated between files, sections merged). `upgrade-standard` reads only
   this section. Omit it when the ops cover everything.

Filled-in content is never described here; upgrades must keep it.

Example:

    ## Structural changes

    ```ops
    [{"file": "AGENTS.md", "op": "insert_after",
      "match": "| This file |",
      "line": "| [`CHANGELOG.md`](./CHANGELOG.md) | User-visible changes per release |"}]
    ```

    ## Manual

    - `DESIGN.md`: move hex colors stated in prose into the `colors:` front-matter group.
