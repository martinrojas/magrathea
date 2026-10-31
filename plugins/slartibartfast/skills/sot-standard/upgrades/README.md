# Upgrade notes

Each release that changes template **structure** adds `upgrades/<version>.md`
(for example `0.2.0.md`).

Each such file is a `## Structural changes` list. Each item names a file, a
section heading, and the change: add, rename, or remove a section, or change a
fixed line.

`scaffold.py upgrade` ignores this `README.md`.

Filled-in content is never described here; upgrades must keep it.
