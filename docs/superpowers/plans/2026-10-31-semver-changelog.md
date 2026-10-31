# Semver Changelog in the Source-of-Truth Standard Implementation Plan

> **For agentic workers:** Use `skill://subagent-driven-development` (recommended) or `skill://executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `CHANGELOG.md` (Keep a Changelog layout, semantic versioning) a core file of the standard: scaffolded, routed from `AGENTS.md`, structurally validated offline, and brought into existing repos by the adopt and upgrade flows. Ships as slartibartfast 0.4.0.

**Architecture:** A new template is written by `scaffold.py init` for every adopter. `validate_standard.py` gains `check_changelog(root)` (errors for missing file and broken structure, warnings for content smells) and `manifest_version(root)`, which `detect.py` imports so the manifest parsing has one owner. The rules live once in `STANDARD.md` ("Changelog and versions"); the adopt, upgrade and sync-docs skills and the `0.4.0` upgrade note point to it.

**Tech Stack:** Python 3.9 stdlib (`re`, `json`, `datetime`, `subprocess`, `unittest`), Markdown skills/templates, one Bun/TypeScript hook.

**Spec:** `docs/superpowers/specs/2026-10-31-semver-changelog-design.md`

**Git:** Task branch `feature/semver-changelog`. Local commits on that branch (spec, plan, and task commits) follow user/repository instructions; where those are silent, approving this plan authorizes them. Push, PR creation, merge, branch deletion, and worktree removal need separate explicit approval.

All paths below are relative to the repo root; `P` = `plugins/slartibartfast`, `S` = `plugins/slartibartfast/skills/sot-standard`. Commands run from the repo root.

## Global Constraints

- Scripts are stdlib-only and must run on Python 3.9: no `tomllib`, no `X | Y` annotations (existing code has none; add none).
- `validate_standard.py` is vendored into adopters as a single file: it must stay offline and import nothing from sibling scripts. `detect.py` may import from it.
- Changelog layout: no front matter; `## [Unreleased]` first, then `## [x.y.z] - YYYY-MM-DD`, newest first; subsections from `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`; bottom link references allowed and not checked.
- Version headings accept core `x.y.z` only (no leading zeros, no pre-release/build suffix): the spec pins the heading as `## [x.y.z] - YYYY-MM-DD`.
- No `0.x`: the first recorded version is `1.0.0`.
- Baseline section, exact: heading `## [1.0.0] - <adoption date>` followed by the line `Baseline: changes before this changelog were not tracked.` Written only when git history has commits and no changelog existed.
- An existing `CHANGELOG.md` is never replaced or rewritten automatically; released history is edited only after the user says yes.
- The template points to the rules in plain text ("the standard's "Changelog and versions" section, in the slartibartfast plugin's `STANDARD.md`"), never a Markdown link: `STANDARD.md` is not vendored and `check_links` errors on missing local targets.
- Missing `CHANGELOG.md` is an error for every repo, with no stamp gate.
- `AGENTS.md` template: add exactly one row and one line (104 → 106 lines; target 100, hard limit 150).
- Version bump: `S/templates/.sot-standard` and the slartibartfast `version` in `.omp-plugin/marketplace.json` both go to `0.4.0` in the same commit, with `S/upgrades/0.4.0.md`.
- Tagging, pushing and publishing happen only when the user asks.
- Commit messages follow the repo's style: imperative sentence, no conventional-commit prefix.

## Review Focus

1. **An existing changelog in another shape** (`## v1.2.0 (2020-01-01)`, `## [1.0]`, a heading with no date): each bad heading gets its own error with a line number, no traceback; adopt proposes a diff and never applies it unasked. Pinned by `test_malformed_version_headings` (Task 2) and the adopt step (Task 7).
2. **A title-only or empty `CHANGELOG.md`** (no `##` heading at all): one "first ## heading must be [Unreleased]" error, not a crash or silence. Pinned by `test_first_heading_must_be_unreleased` (Task 2).
3. **Unreadable or version-less manifests** (malformed `package.json`, non-string `version`, top-level JSON array, `pyproject.toml` with no static version): no crash and no mismatch warning, in both the validator and `detect.py`. Pinned by `test_unreadable_manifests_are_ignored` (Task 3) and `test_malformed_package_json_is_reported_not_fatal` (Task 5).
4. **Headings inside fenced code, and bottom link references**: a fenced `## …` is not a heading; a release whose only following lines are link references still warns "no entries". Pinned by `test_headings_in_code_fences_are_ignored` (Task 2) and `test_release_without_entries_warns` (Task 3).
5. **Per-package `CHANGELOG.md` files in a monorepo** (a non-goal): `SCAN_NAMES` now link-scans them, but only the root file is structurally checked, so a package changelog in another format does not fail the repo. Pinned by `test_package_changelogs_are_not_structurally_checked` (Task 2).

---

### Task 1: Changelog template, scaffold, and AGENTS.md routing

**Files:**
- Create: `S/templates/CHANGELOG.md`
- Modify: `S/scripts/scaffold.py` (`cmd_init`: the `rels` list)
- Modify: `S/templates/AGENTS.md` (section 1 table, section 7 list)
- Modify: `S/scripts/validate_standard.py` (`SCAN_NAMES`)
- Test: `P/tests/test_scripts.py` (`InitTest`)

**Test command:** `python3 -m unittest discover -s plugins/slartibartfast/tests`

**Interfaces:**
- Consumes: nothing new.
- Produces: `S/templates/CHANGELOG.md` with the public-interface placeholder on line 3; `cmd_init` always lists `CHANGELOG.md` in `created` or `skipped`; `SCAN_NAMES` includes `"CHANGELOG.md"`.

- [ ] **Step 1: Write the failing tests** in `InitTest`

```python
# test_empty_set_writes_minimal_repo: new expected set, plus the row and a quiet validator
self.assertEqual(files, {"AGENTS.md", "CLAUDE.md", "CHANGELOG.md", ".sot-standard",
                         "scripts/validate_standard.py"})
self.assertTrue([r for r in rows if r.startswith("| [`CHANGELOG.md`](./CHANGELOG.md) |")])
# ...after the existing vendored-validator returncode assertion:
self.assertNotIn("CHANGELOG.md", r.stdout)

# test_full_software_set_validates: capture the output
out = self.init("product,architecture,decisions")
self.assertIn("CHANGELOG.md", out["created"])

def test_changelog_template_is_flagged_as_unfilled_under_strict(self):
    self.init("")
    v = run("validate_standard.py", self.root, "--strict")
    self.assertEqual(v.returncode, 1, v.stdout)
    self.assertRegex(v.stdout, r"ERROR\s+CHANGELOG\.md: 1 unfilled placeholder line\(s\) at 3\b")

def test_existing_changelog_is_never_overwritten(self):
    log = self.write("CHANGELOG.md", "# mine\n")
    out = self.init("")
    self.assertEqual(log.read_text(), "# mine\n")
    self.assertIn("CHANGELOG.md", out["skipped"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests -k InitTest`
Expected: FAIL — `test_empty_set_writes_minimal_repo`, `test_full_software_set_validates`, `test_changelog_template_is_flagged_as_unfilled_under_strict` and `test_existing_changelog_is_never_overwritten` fail (no template, not in `rels`).

- [ ] **Step 3: Create `S/templates/CHANGELOG.md`** with this exact content (line 3 is the placeholder the strict test pins):

```markdown
# Changelog

Public interface: <what users or operators depend on: API, CLI, config, data formats, documented behavior; for an app, user-visible behavior>

All notable changes to this project are recorded here, newest first. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). When and how to add an
entry or cut a release: the standard's "Changelog and versions" section, in the
slartibartfast plugin's `STANDARD.md`.

## [Unreleased]
```

- [ ] **Step 4: Scaffold it and route it**
  - `scaffold.py` `cmd_init`: `rels = ["AGENTS.md", "CLAUDE.md", "CHANGELOG.md"] + …`. It is not in `FILES`/`AGENTS_ROWS`, so no token and no transform.
  - `validate_standard.py`: add `"CHANGELOG.md"` to `SCAN_NAMES`.
  - `S/templates/AGENTS.md` section 1: insert directly above the `| This file |` row:
    ```
    | [`CHANGELOG.md`](./CHANGELOG.md) | User-visible changes per release, under semantic versioning | Any user-visible change: add its entry under `Unreleased` |
    ```
  - `S/templates/AGENTS.md` section 7: insert after `- Tests, lint, and typecheck pass.`:
    ```
    - User-visible changes have an entry under `Unreleased` in `CHANGELOG.md`; released sections are never edited.
    ```

- [ ] **Step 5: Run tests and the template self-check**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests`
Expected: PASS, 30 tests (28 + 2 new).
Run: `cd plugins/slartibartfast/skills/sot-standard/templates && python3 ../scripts/validate_standard.py .`
Expected: `0 error(s)`; the only warning is `AGENTS.md: 106 lines; target is about 100`.

- [ ] **Step 6: Commit**

```bash
git add plugins/slartibartfast/skills/sot-standard/templates/CHANGELOG.md plugins/slartibartfast/skills/sot-standard/templates/AGENTS.md plugins/slartibartfast/skills/sot-standard/scripts/scaffold.py plugins/slartibartfast/skills/sot-standard/scripts/validate_standard.py plugins/slartibartfast/tests/test_scripts.py
git commit -m "Scaffold CHANGELOG.md for every adopter and route it from AGENTS.md"
```

### Task 2: Validator — missing file and structural errors

**Files:**
- Modify: `S/scripts/validate_standard.py` (new constants, new `check_changelog`, call in `main`)
- Test: `P/tests/test_scripts.py` (module constant `VALID_LOG`, new `ChangelogTest`, `StrictPlaceholderTest` fixture)

**Test command:** `python3 -m unittest discover -s plugins/slartibartfast/tests`

**Interfaces:**
- Consumes: `SCAN_NAMES` containing `CHANGELOG.md` (Task 1); existing `err`, `warn`, `body_lines`.
- Produces: `check_changelog(root: Path) -> None`, called in `main` right after `check_basics`. It only checks `root / "CHANGELOG.md"`. Error messages (file label `CHANGELOG.md`):
  - `missing (core file)`
  - `first ## heading must be [Unreleased]`
  - `line {n}: version heading must be '## [x.y.z] - YYYY-MM-DD'`
  - `line {n}: invalid date {date}`
  - `line {n}: duplicate version {v}`
  - `line {n}: {v} is not below {prev}; versions must be newest first`
- Produces for Task 3: a parsed list of released sections (heading line number, version tuple, the lines up to the next `## ` heading) inside `check_changelog`, which Task 3 extends with warnings.
- Produces for tests: `VALID_LOG` and `ChangelogTest.check(log, files=None)`, used again in Task 3.

- [ ] **Step 1: Write the failing tests**

Add at module level (after `validate`), and give `StrictPlaceholderTest.test_urls_and_date_formats_are_not_placeholders` a `self.write("CHANGELOG.md", VALID_LOG)` before its validator run so it keeps exit 0:

```python
VALID_LOG = ("# Changelog\n\nPublic interface: the `tool` CLI.\n\n## [Unreleased]\n\n"
             "## [1.1.0] - 2026-02-01\n\n### Added\n\n- A flag.\n\n"
             "## [1.0.0] - 2026-01-01\n\nBaseline: changes before this changelog were not tracked.\n")


class ChangelogTest(TempRepo):
    def check(self, log, files=None):
        self.write("AGENTS.md", "# AGENTS.md\n")
        if log is not None:
            self.write("CHANGELOG.md", log)
        for rel, text in (files or {}).items():
            self.write(rel, text)
        r = validate(self.root)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def test_valid_changelog_passes(self):
        r = self.check(VALID_LOG)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("CHANGELOG.md", r.stdout)

    def test_missing_changelog_errors_at_any_stamp(self):
        for stamp in (None, "0.3.0\n"):  # no stamp gate: below 0.4.0 still errors
            if stamp:
                self.write(".sot-standard", stamp)
            r = self.check(None)
            self.assertEqual(r.returncode, 1)
            self.assertIn("ERROR   CHANGELOG.md: missing (core file)", r.stdout)

    def test_first_heading_must_be_unreleased(self):
        for log in ("# Changelog\n", "# Changelog\n\n## [1.0.0] - 2026-01-01\n\n- x\n"):
            r = self.check(log)
            self.assertEqual(r.returncode, 1)
            self.assertIn("ERROR   CHANGELOG.md: first ## heading must be [Unreleased]", r.stdout)

    def test_malformed_version_headings(self):
        r = self.check("# C\n\n## [Unreleased]\n\n## v1.2.0 (2020-01-01)\n\n- a\n\n## [1.0] - 2020-01-01\n\n- b\n\n"
                       "## [01.0.0] - 2020-01-01\n\n- c\n\n## [1.0.0]\n\n- d\n")
        self.assertEqual(r.returncode, 1)
        for n in (5, 9, 13, 17):
            self.assertIn(f"CHANGELOG.md: line {n}: version heading must be '## [x.y.z] - YYYY-MM-DD'", r.stdout)

    def test_invalid_calendar_date(self):
        r = self.check("# C\n\n## [Unreleased]\n\n## [1.0.0] - 2026-02-30\n\n- x\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("CHANGELOG.md: line 5: invalid date 2026-02-30", r.stdout)

    def test_duplicate_version(self):
        r = self.check("# C\n\n## [Unreleased]\n\n## [1.0.0] - 2026-01-02\n\n- x\n\n## [1.0.0] - 2026-01-01\n\n- y\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("CHANGELOG.md: line 9: duplicate version 1.0.0", r.stdout)
        self.assertNotIn("newest first", r.stdout)

    def test_versions_must_descend(self):
        r = self.check("# C\n\n## [Unreleased]\n\n## [1.0.0] - 2026-01-01\n\n- x\n\n## [1.1.0] - 2026-02-01\n\n- y\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("CHANGELOG.md: line 9: 1.1.0 is not below 1.0.0; versions must be newest first", r.stdout)

    def test_headings_in_code_fences_are_ignored(self):
        r = self.check(VALID_LOG.replace("- A flag.\n", "- A flag:\n\n```\n## not a heading\n```\n"))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_package_changelogs_are_not_structurally_checked(self):
        r = self.check(VALID_LOG, {"packages/a/CHANGELOG.md": "# a\n\n## 1.0\n"})
        self.assertEqual(r.returncode, 0, r.stdout)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests -k ChangelogTest`
Expected: FAIL — every test except `test_valid_changelog_passes`, `test_headings_in_code_fences_are_ignored` and `test_package_changelogs_are_not_structurally_checked` fails on a missing message.

- [ ] **Step 3: Implement `check_changelog(root)` in `validate_standard.py`**

Walk `body_lines` of `root / "CHANGELOG.md"` (so fenced lines are skipped) and treat lines starting with `## ` as section headings. The first must equal `## [Unreleased]` (trailing whitespace ignored); every later one must match a version-heading regex with semver core components `(0|[1-9]\d*)` and a `\d{4}-\d{2}-\d{2}` date. Validate the date with `datetime.date.fromisoformat`. Compare versions as int tuples: a version already seen is a duplicate (report only that); otherwise it must be lower than the previous valid version. Headings that fail the regex take no part in the duplicate/order checks.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests`
Expected: PASS, 39 tests.

- [ ] **Step 5: Commit**

```bash
git add plugins/slartibartfast/skills/sot-standard/scripts/validate_standard.py plugins/slartibartfast/tests/test_scripts.py
git commit -m "Validate CHANGELOG.md presence and structure"
```

### Task 3: Validator — changelog warnings and manifest version

**Files:**
- Modify: `S/scripts/validate_standard.py` (`check_changelog`, new `manifest_version`, constants)
- Test: `P/tests/test_scripts.py` (`ChangelogTest`)

**Test command:** `python3 -m unittest discover -s plugins/slartibartfast/tests`

**Interfaces:**
- Consumes: `check_changelog` and its parsed released sections (Task 2); `VALID_LOG`, `ChangelogTest.check` (Task 2).
- Produces: `manifest_version(root: Path)` → `(file_name, version)` tuple of `str`, or `None`. Checks, in order, `package.json` (top-level JSON object with a string `version`), `pyproject.toml` (`version = "…"` inside `[project]` or `[tool.poetry]`), `Cargo.toml` (inside `[package]`), and returns the first file that declares a version. Unreadable or malformed files are skipped silently. TOML is read with a line scan that tracks the current `[table]` header; no TOML parser. Task 5 imports this function.
- Produces warning messages (file label `CHANGELOG.md`; warnings never change the exit code):
  - `line {n}: unknown subsection '{name}'` (any `### ` heading not in `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`; checked in every section, `Unreleased` included)
  - `line {n}: release {v} has no entries`: a released section with no line other than blanks, `### ` headings and link references (`[label]: target`)
  - `line {n}: {v} is a 0.x version; the first recorded version is 1.0.0`
  - `top release {v} differs from {file} version {mv}`: only when a released version exists and `manifest_version` is not `None`

- [ ] **Step 1: Write the failing tests** in `ChangelogTest`

```python
def test_unknown_subsection_warns(self):
    r = self.check(VALID_LOG.replace("### Added", "### Misc"))
    self.assertEqual(r.returncode, 0, r.stdout)
    self.assertIn("warning CHANGELOG.md: line 9: unknown subsection 'Misc'", r.stdout)

def test_release_without_entries_warns(self):
    r = self.check("# C\n\n## [Unreleased]\n\n## [1.0.0] - 2026-01-01\n\n### Added\n\n"
                   "[1.0.0]: https://example.com/v1.0.0\n")
    self.assertEqual(r.returncode, 0, r.stdout)
    self.assertIn("warning CHANGELOG.md: line 5: release 1.0.0 has no entries", r.stdout)

def test_zero_major_warns(self):
    r = self.check("# C\n\n## [Unreleased]\n\n## [0.3.0] - 2026-01-01\n\n- x\n")
    self.assertEqual(r.returncode, 0, r.stdout)
    self.assertIn("warning CHANGELOG.md: line 5: 0.3.0 is a 0.x version; the first recorded version is 1.0.0",
                  r.stdout)

def test_manifest_version_mismatch_warns(self):
    r = self.check(VALID_LOG, {"package.json": '{"version": "0.9.0"}'})
    self.assertIn("warning CHANGELOG.md: top release 1.1.0 differs from package.json version 0.9.0", r.stdout)
    self.write("package.json", '{"version": "1.1.0"}')
    self.assertNotIn("differs from", validate(self.root).stdout)

def test_manifest_is_first_that_declares_a_version(self):
    files = {"package.json": '{"name": "x"}',
             "pyproject.toml": '[tool.other]\nversion = "9.9.9"\n\n[project]\nname = "x"\nversion = "2.0.0"\n',
             "Cargo.toml": '[package]\nversion = "3.0.0"\n'}
    self.assertIn("differs from pyproject.toml version 2.0.0", self.check(VALID_LOG, files).stdout)
    (self.root / "pyproject.toml").unlink()
    self.assertIn("differs from Cargo.toml version 3.0.0", validate(self.root).stdout)

def test_unreleased_only_has_no_manifest_warning(self):
    r = self.check("# C\n\n## [Unreleased]\n", {"package.json": '{"version": "0.1.0"}'})
    self.assertEqual(r.returncode, 0, r.stdout)
    self.assertNotIn("CHANGELOG.md", r.stdout)

def test_unreadable_manifests_are_ignored(self):
    for text in ("{nope", '{"version": 1}', "[1, 2]"):
        r = self.check(VALID_LOG, {"package.json": text})
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("differs from", r.stdout)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests -k ChangelogTest`
Expected: FAIL — the five warning tests fail on missing messages; `test_unreleased_only_has_no_manifest_warning` and `test_unreadable_manifests_are_ignored` pass already.

- [ ] **Step 3: Implement `manifest_version(root)` and the four warnings** as specified in Interfaces. Use the top (first) released version for the manifest comparison, compared as the `x.y.z` string.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests`
Expected: PASS, 46 tests.

- [ ] **Step 5: Commit**

```bash
git add plugins/slartibartfast/skills/sot-standard/scripts/validate_standard.py plugins/slartibartfast/tests/test_scripts.py
git commit -m "Warn on changelog subsections, empty releases, 0.x and manifest drift"
```

### Task 4: Edit hook validates on CHANGELOG.md edits

**Files:**
- Modify: `P/hooks/post/validate-grounding.ts` (`NAMES`)

**Test command:** the smoke script in Step 1 (Bun; there is no TS test suite).

**Interfaces:**
- Consumes: the Task 2 error `first ## heading must be [Unreleased]`.
- Produces: `NAMES` includes `"CHANGELOG.md"`.

- [ ] **Step 1: Run the smoke check to verify it fails**

Run from the repo root:

```bash
bun -e '
const fs = require("node:fs"), os = require("node:os"), path = require("node:path");
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "hook-"));
fs.writeFileSync(path.join(dir, ".sot-standard"), "0.4.0\n");
fs.writeFileSync(path.join(dir, "AGENTS.md"), "# AGENTS.md\n");
fs.writeFileSync(path.join(dir, "CHANGELOG.md"), "# Changelog\n\n## [1.0.0] - 2026-01-01\n\n- x\n");
const hook = (await import("./plugins/slartibartfast/hooks/post/validate-grounding.ts")).default;
let fn; hook({ on: (_e, f) => { fn = f; } });
const out = await fn({ isError: false, toolName: "edit", input: { path: "CHANGELOG.md" } }, { cwd: dir });
console.log(out?.additionalContext ?? "NO REPORT");
'
```

Expected: `NO REPORT` (the hook ignores `CHANGELOG.md` edits today).

- [ ] **Step 2: Add `"CHANGELOG.md"` to `NAMES`** in `validate-grounding.ts`.

- [ ] **Step 3: Re-run the smoke check and a bundle check**

Run: the Step 1 command.
Expected: the output starts with `[slartibartfast hook] Automatic check` and contains `ERROR   CHANGELOG.md: first ## heading must be [Unreleased]`.
Run: `bun build plugins/slartibartfast/hooks/post/validate-grounding.ts --target=bun --external '@oh-my-pi/pi-coding-agent' --outfile /tmp/slarti-hook-smoke.js`
Expected: `Bundled 1 module`, exit 0.

- [ ] **Step 4: Commit**

```bash
git add plugins/slartibartfast/hooks/post/validate-grounding.ts
git commit -m "Run the grounding hook on CHANGELOG.md edits"
```

### Task 5: detect.py reports changelog, manifest version and git history

**Files:**
- Modify: `S/scripts/detect.py` (`EXISTING`, new `git_has_commits`, two output keys, import)
- Modify: `S/SKILL.md` (the `detect.py` index line)
- Test: `P/tests/test_scripts.py` (`TempRepo`, `DetectTest`, `DocMapTest`)

**Test command:** `python3 -m unittest discover -s plugins/slartibartfast/tests`

**Interfaces:**
- Consumes: `manifest_version(root)` from Task 3, via `from validate_standard import manifest_version` (the script's own directory is on `sys.path` when run).
- Produces (used by the adopt skill and upgrade note in Task 7):
  - `"CHANGELOG.md"` in `EXISTING`, so it appears in `existing`.
  - `"manifest_version"`: `{"file": str, "version": str}` or `null`.
  - `"git_has_commits"`: `bool`, from `git_has_commits(root) -> bool` (`git -C <root> rev-parse --verify --quiet HEAD` exits 0; `False` on `OSError`/`SubprocessError`, same guard as `git_remote`).
  - `TempRepo.git(self, *args)`: runs `git -C <root> -c user.name=t -c user.email=t@t …` with `check=True, capture_output=True`. Replaces the lambda in `DocMapTest.test_git_changes_are_used_without_paths`.

- [ ] **Step 1: Write the failing tests**

```python
# DetectTest
def test_changelog_manifest_version_and_history(self):
    self.write("CHANGELOG.md", "# C\n")
    self.write("package.json", '{"version": "0.2.0"}')
    d = json.loads(run("detect.py", self.root).stdout)
    self.assertIn("CHANGELOG.md", d["existing"])
    self.assertEqual(d["manifest_version"], {"file": "package.json", "version": "0.2.0"})
    self.assertFalse(d["git_has_commits"])
    self.git("init", "-q", "-b", "main")
    self.assertFalse(json.loads(run("detect.py", self.root).stdout)["git_has_commits"])
    self.git("add", "-A")
    self.git("commit", "-qm", "init")
    self.assertTrue(json.loads(run("detect.py", self.root).stdout)["git_has_commits"])

# test_malformed_package_json_is_reported_not_fatal: add
self.assertIsNone(d["manifest_version"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests -k DetectTest`
Expected: FAIL — `KeyError: 'manifest_version'` in both tests.

- [ ] **Step 3: Implement** `TempRepo.git`, switch `DocMapTest` to it, then the `detect.py` changes in Interfaces. Update the `S/SKILL.md` line to: `` - `detect.py [root]`: JSON facts about a repo (stack, commands, packages, UI, size, existing standard files, manifest version, whether git has commits). ``

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests`
Expected: PASS, 47 tests.

- [ ] **Step 5: Commit**

```bash
git add plugins/slartibartfast/skills/sot-standard/scripts/detect.py plugins/slartibartfast/skills/sot-standard/SKILL.md plugins/slartibartfast/tests/test_scripts.py
git commit -m "Report changelog, manifest version and git history from detect.py"
```

### Task 6: STANDARD.md rules for changelog and versions

**Files:**
- Modify: `S/STANDARD.md` ("The files" table, rule 5, "Formats", new section, "Sizing")

**Test command:** `grep -n -e '^## Changelog and versions$' -e 'CHANGELOG.md' plugins/slartibartfast/skills/sot-standard/STANDARD.md`

**Interfaces:**
- Consumes: the heading name the Task 1 template cites ("Changelog and versions").
- Produces: section `## Changelog and versions`, the single owner of the semver and entry rules; Task 7 skills and the Task 8 note point to it.

- [ ] **Step 1: Run the check to verify it fails**

Run: the test command.
Expected: no output, exit 1.

- [ ] **Step 2: Edit `STANDARD.md`**
  - "The files" table: add above the `CLAUDE.md` row:
    `` | `CHANGELOG.md` | Core | User-visible changes per release, under semantic versioning (see "Changelog and versions") | ``
  - Rule 5: append the sentence `` `CHANGELOG.md` is the exception: it is history, so it appends (see "Changelog and versions"). ``
  - "Formats": after the first sentence add `` `CHANGELOG.md` uses the community Keep a Changelog layout and has no front matter. ``
  - "Sizing": Small row becomes `` `AGENTS.md` + `PRODUCT.md` + `CHANGELOG.md` (one domain; rules inline or one rules file) ``; Docs row becomes `` `AGENTS.md` and `CHANGELOG.md` only, adapted to content conventions and freshness rules ``.
  - Insert this section between "Formats" and "Sizing", verbatim:

```markdown
## Changelog and versions

`CHANGELOG.md` records user-visible change in the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) layout under
[semantic versioning](https://semver.org/spec/v2.0.0.html): `## [Unreleased]`
first, then `## [x.y.z] - YYYY-MM-DD` sections, newest first, with `Added`,
`Changed`, `Deprecated`, `Removed`, `Fixed` and `Security` subsections. One
root changelog and one version, in a monorepo too.

- **Public interface:** whatever users or operators depend on: API, CLI,
  config, data formats, documented behavior; for an app, user-visible
  behavior. Name it in one line at the top of the changelog.
- **MAJOR** for a breaking change to it, **MINOR** for a backward-compatible
  addition, **PATCH** for a backward-compatible fix.
- **No `0.x`.** The first recorded version is `1.0.0`. A project adopting the
  standard with prior history records it as a `1.0.0` baseline and tracks
  from there.
- **Entries** go under `Unreleased` in the same PR as the change. Refactors,
  tests, and docs-only changes get no entry.
- **Cutting a release:** rename `Unreleased` to the version and date, add a
  fresh empty `Unreleased`, and bump the manifest version, in one commit.
  Tagging and publishing are the user's call.
- **Released sections are immutable** except for typo fixes. Correct a
  mistake with a new entry.

Rule 5 does not apply here: a changelog is history, so it appends.
```

- [ ] **Step 3: Run the check to verify it passes**

Run: the test command.
Expected: the `## Changelog and versions` heading line plus at least the files-table, rule-5, Formats and Sizing lines naming `CHANGELOG.md`.

- [ ] **Step 4: Commit**

```bash
git add plugins/slartibartfast/skills/sot-standard/STANDARD.md
git commit -m "State changelog and semver rules in STANDARD.md"
```

### Task 7: Adopt, upgrade and sync-docs skill flows

**Files:**
- Modify: `P/skills/adopt-standard/SKILL.md`
- Modify: `P/skills/upgrade-standard/SKILL.md`
- Modify: `P/skills/sync-docs/SKILL.md`

**Test command:** `grep -n -e 'Baseline: changes before this changelog were not tracked.' -e 'git_has_commits' -e 'manifest_version' -e 'Unreleased' -e 'Validate again' -e 'go to step 6' plugins/slartibartfast/skills/adopt-standard/SKILL.md plugins/slartibartfast/skills/upgrade-standard/SKILL.md plugins/slartibartfast/skills/sync-docs/SKILL.md`

**Interfaces:**
- Consumes: `detect.py` keys `existing`, `manifest_version`, `git_has_commits` (Task 5); `scaffold.py init` `created`/`skipped` (Task 1); the "Changelog and versions" section (Task 6); validator messages (Tasks 2–3).
- Produces: adopt-standard's changelog step, which the Task 8 upgrade note refers to by name ("as `adopt-standard` describes").

- [ ] **Step 1: Run the check to verify it fails**

Run: the test command.
Expected: no match for the baseline line, `git_has_commits` or `manifest_version`.

- [ ] **Step 2: adopt-standard.** Insert a new step 4 after "Scaffold" and renumber the later steps (4→5 … 7→8). Content to convey, in the file's terse style:
  - Rules: `skill://sot-standard/STANDARD.md` "Changelog and versions".
  - `CHANGELOG.md` in `created` and `detect.git_has_commits` true: below `## [Unreleased]` add `## [1.0.0] - <today, YYYY-MM-DD>` and the line `Baseline: changes before this changelog were not tracked.` If `detect.manifest_version` is set and is not `1.0.0`, offer (`ask`) to set it to `1.0.0`, because the validator warns on a mismatch. No commits: keep only `## [Unreleased]`; the first release is `1.0.0`.
  - `CHANGELOG.md` in `skipped`: never replace or rewrite it. After validating, report each `CHANGELOG.md` finding, show a proposed diff (prepend `## [Unreleased]`, normalize version headings to `## [x.y.z] - YYYY-MM-DD` using only dates the file states; never invent a date), and apply it only after the engineer agrees (`ask`).
  - Fill the public-interface line from code and README; mark it "(inferred, not verified)" if not read in code.
  - "Never" section: add "Rewrite or delete a released changelog section without the engineer's yes."

- [ ] **Step 3: upgrade-standard.** After step 5 (Stamp) add: "Validate again: `python3 skill://sot-standard/scripts/validate_standard.py .` as a backstop. Fix any error; a missing `CHANGELOG.md` means a note was skipped, so apply it." Renumber Commit to 7. Add to "Never": "Edit a released changelog section."

- [ ] **Step 4: sync-docs.** Step 2 becomes: if `stale` is empty, say "No owned docs affected" and go to step 6. Insert step 6: "Changelog: if the change is user-visible (`STANDARD.md` "Changelog and versions") and `## [Unreleased]` in `CHANGELOG.md` has no entry for it, draft one under the matching subsection and apply it with `edit`. List it in your summary. Never edit a released section." Renumber Validate to 7 and the `unowned` step to 8.

- [ ] **Step 5: Run the check to verify it passes**

Run: the test command.
Expected: matches in all three files: adopt has the baseline line, `git_has_commits`, `manifest_version`, `Unreleased`; upgrade has `Validate again` (step 6, after the `--finish` step); sync-docs has `go to step 6` and `Unreleased`.

- [ ] **Step 6: Commit**

```bash
git add plugins/slartibartfast/skills/adopt-standard/SKILL.md plugins/slartibartfast/skills/upgrade-standard/SKILL.md plugins/slartibartfast/skills/sync-docs/SKILL.md
git commit -m "Bring CHANGELOG.md into the adopt, upgrade and sync-docs flows"
```

### Task 8: 0.4.0 upgrade note and version bump

**Files:**
- Create: `S/upgrades/0.4.0.md`
- Modify: `S/templates/.sot-standard` (`0.3.0` → `0.4.0`)
- Modify: `.omp-plugin/marketplace.json` (slartibartfast `version` → `0.4.0`)
- Test: `P/tests/test_scripts.py` (`UpgradeTest`)

**Test command:** `python3 -m unittest discover -s plugins/slartibartfast/tests`

**Interfaces:**
- Consumes: adopt-standard's changelog step (Task 7); the template `AGENTS.md` row and definition-of-done line (Task 1).
- Produces: `scaffold.py upgrade` lists `0.4.0.md` for repos stamped below `0.4.0`.

- [ ] **Step 1: Write the failing tests** in `UpgradeTest`

```python
# test_older_stamp_refreshes_validator_then_finish_stamps
self.assertEqual([Path(n).name for n in out["notes"]], ["0.3.0.md", "0.4.0.md"])

def test_0_3_0_repo_gets_changelog_note(self):
    self.init("")
    (self.root / ".sot-standard").write_text("0.3.0\n")
    out = json.loads(run("scaffold.py", "upgrade", self.root).stdout)
    self.assertEqual((out["to"], [Path(n).name for n in out["notes"]]), ("0.4.0", ["0.4.0.md"]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests -k UpgradeTest`
Expected: FAIL — notes are `["0.3.0.md"]` and `to` is `0.3.0`.

- [ ] **Step 3: Create `S/upgrades/0.4.0.md`** (format per `S/upgrades/README.md`):

```markdown
## Structural changes

`CHANGELOG.md` is a new core file; its rules are in the standard's "Changelog and versions" section. Apply this note before validating: the validator now fails when `CHANGELOG.md` is missing.

- `CHANGELOG.md`, absent: copy `skill://sot-standard/templates/CHANGELOG.md` to the repo root and fill its public-interface line. If the git history has commits, add the `1.0.0` baseline section and offer the manifest bump as `adopt-standard` describes; with no commits keep only `## [Unreleased]`.
- `CHANGELOG.md`, present: never replace or rewrite it. Report each validator finding on it, propose a diff (prepend `## [Unreleased]`, normalize version headings, no invented dates), and apply it only after the user agrees.
- `AGENTS.md` section `## 1. Grounding documents`: add the `CHANGELOG.md` row from `skill://sot-standard/templates/AGENTS.md`, above the `| This file |` row.
- `AGENTS.md` section `## 7. Definition of done`: add the `CHANGELOG.md` line from the same template, after the tests-pass line.
```

- [ ] **Step 4: Bump** `S/templates/.sot-standard` to `0.4.0` and the slartibartfast `"version"` in `.omp-plugin/marketplace.json` to `"0.4.0"` (leave omp-superpowers untouched).

- [ ] **Step 5: Run tests and checks**

Run: `python3 -m unittest discover -s plugins/slartibartfast/tests`
Expected: PASS, 48 tests.
Run: `cd plugins/slartibartfast/skills/sot-standard/templates && python3 ../scripts/validate_standard.py .`
Expected: `0 error(s)`.
Run: `grep -n '"version"' .omp-plugin/marketplace.json && cat plugins/slartibartfast/skills/sot-standard/templates/.sot-standard`
Expected: slartibartfast `"version": "0.4.0"`, omp-superpowers still `"0.1.0"`, stamp `0.4.0`.

- [ ] **Step 6: Commit**

```bash
git add plugins/slartibartfast/skills/sot-standard/upgrades/0.4.0.md plugins/slartibartfast/skills/sot-standard/templates/.sot-standard .omp-plugin/marketplace.json plugins/slartibartfast/tests/test_scripts.py
git commit -m "Bump slartibartfast to 0.4.0 with CHANGELOG.md upgrade note"
```
