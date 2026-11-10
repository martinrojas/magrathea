import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "the-guide" / "scripts"


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd)


def validate(root):
    return run("validate_standard.py", root)

VALID_LOG = ("# Changelog\n\nPublic interface: the `tool` CLI.\n\n## [Unreleased]\n\n"
             "## [1.1.0] - 2026-02-01\n\n### Added\n\n- A flag.\n\n"
             "## [1.0.0] - 2026-01-01\n\nBaseline: changes before this changelog were not tracked.\n")


class TempRepo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def init(self, with_):
        r = run("scaffold.py", "init", self.root, "--with", with_)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                              check=True, capture_output=True)


class ChangelogTest(TempRepo):
    def check(self, log, files=None):
        self.write("AGENTS.md", "# AGENTS.md\n")
        self.write(".the-guide", "1.0.0\nsize: docs\n")
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

    def test_missing_changelog_is_fine(self):
        # CHANGELOG.md is an optional tier: checked only when present.
        r = self.check(None)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("CHANGELOG.md", r.stdout)

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


class InitTest(TempRepo):
    def test_empty_set_writes_minimal_repo(self):
        out = self.init("")
        files = {p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(files, {"AGENTS.md", "CLAUDE.md", ".the-guide",
                                 "scripts/validate_standard.py"})
        self.assertEqual(out["skipped"], [])
        self.assertEqual(out["size"], "docs")
        self.assertEqual((self.root / ".the-guide").read_text(), out["stamp"] + "\nsize: docs\n")
        text = (self.root / "AGENTS.md").read_text()
        rows = [l for l in text.splitlines() if l.startswith("| ")]
        for gone in ("PRODUCT.md", "DESIGN.md", "ARCHITECTURE.md", "docs/decisions", "docs/rules",
                     "CHANGELOG.md", "REVIEW.md", "context.yaml"):
            self.assertFalse([r for r in rows if gone in r], gone)
        self.assertNotIn("## Code Review", text)
        self.assertIn("## Definition of done", text)
        # the vendored copy, as CI in an adopting repo runs it
        r = subprocess.run([sys.executable, "scripts/validate_standard.py", "."], cwd=self.root,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("CHANGELOG.md", r.stdout)

    def test_full_software_set_validates(self):
        out = self.init("product,architecture,decisions")
        self.assertNotIn("CHANGELOG.md", out["created"])
        self.assertEqual(out["size"], "software")
        agents = (self.root / "AGENTS.md").read_text()
        self.assertNotIn("DESIGN.md`](./DESIGN.md)", agents)
        self.assertNotIn("## Code Review", agents)
        self.assertIn("list them here", (self.root / "ARCHITECTURE.md").read_text())
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)
        self.assertLessEqual(len(agents.splitlines()), 100)

    def test_review_token_writes_review_layer(self):
        out = self.init("product,architecture,decisions,review")
        self.assertIn("REVIEW.md", out["created"])
        self.assertIn("context.yaml", out["created"])
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("## Code Review", agents)
        self.assertIn("context.yaml", agents)
        self.assertIn("context.yaml", (self.root / "ARCHITECTURE.md").read_text())
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)
        self.assertNotIn("warning ", v.stdout)

    def test_review_without_bridge_is_reported(self):
        self.init("product,review")
        agents = self.root / "AGENTS.md"
        text = agents.read_text()
        agents.write_text(text.replace("## Code Review", "## Reviewing"))
        v = validate(self.root)
        self.assertIn("warning AGENTS.md: REVIEW.md exists but AGENTS.md has no 'Code Review' heading", v.stdout)
        (self.root / "REVIEW.md").unlink()
        agents.write_text(text)
        v = validate(self.root)
        self.assertEqual(v.returncode, 1)
        self.assertIn("ERROR   AGENTS.md: 'Code Review' heading points at a missing REVIEW.md", v.stdout)

    def test_context_yaml_schema(self):
        self.init("product,review")
        ctx = self.root / "context.yaml"
        ctx.write_text("version: 0\ncontext:\n  - name: wiki\n    repo: acme/wiki\n"
                       "    paths: [content/]\n    entry: content/_index.md\n    why: domain notes\n")
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)
        ctx.write_text("version: 1\ncontext:\n  - name: wiki\n    repo: not a slug\n    paths: []\n"
                       "    bogus: 1\n  - name: dup\n    repo: not a slug\n    paths: [x]\n")
        v = validate(self.root)
        self.assertEqual(v.returncode, 1)
        for msg in ("version must be 0", "repo must be org/name", "paths must be a non-empty list",
                    "unknown key 'bogus'", "duplicate repo"):
            self.assertIn(msg, v.stdout, msg)

    def test_product_required_unless_docs_size(self):
        self.write("AGENTS.md", "# AGENTS.md\n")
        v = validate(self.root)
        self.assertEqual(v.returncode, 1)
        self.assertIn("ERROR   PRODUCT.md: missing", v.stdout)
        self.write(".the-guide", "1.0.0\nsize: docs\n")
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)
        self.write(".the-guide", "1.0.0\nsize: huge\n")
        self.assertIn("size must be one of", validate(self.root).stdout)

    def test_changelog_token_adds_file_and_rows(self):
        out = self.init("product,changelog")
        self.assertIn("CHANGELOG.md", out["created"])
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("| [`CHANGELOG.md`](./CHANGELOG.md) |", agents)
        self.assertIn("entry under `Unreleased`", agents)
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)

    def test_changelog_template_is_flagged_as_unfilled_under_strict(self):
        self.init("changelog")
        v = run("validate_standard.py", self.root, "--strict")
        self.assertEqual(v.returncode, 1, v.stdout)
        self.assertRegex(v.stdout, r"ERROR\s+CHANGELOG\.md: 1 unfilled placeholder line\(s\) at 3\b")

    def test_existing_changelog_is_never_overwritten(self):
        log = self.write("CHANGELOG.md", "# mine\n")
        out = self.init("changelog")
        self.assertEqual(log.read_text(), "# mine\n")
        self.assertIn("CHANGELOG.md", out["skipped"])

    def test_ui_writes_design_template_and_keeps_row(self):
        out = self.init("product,ui")
        self.assertIn("DESIGN.md", out["created"])
        self.assertIn("DESIGN.md`](./DESIGN.md)", (self.root / "AGENTS.md").read_text())
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)
        self.assertNotIn("link target not found", v.stdout)

    def test_ui_template_is_flagged_as_unfilled_under_strict(self):
        self.init("product,ui")
        v = run("validate_standard.py", self.root, "--strict")
        self.assertEqual(v.returncode, 1, v.stdout)
        self.assertRegex(v.stdout, r"ERROR\s+DESIGN\.md: \d+ unfilled placeholder")

    def test_unknown_token_is_usage_error(self):
        self.assertEqual(run("scaffold.py", "init", self.root, "--with", "nope").returncode, 2)

    def test_existing_files_are_never_overwritten(self):
        agents = self.write("AGENTS.md", "# mine\n")
        out = self.init("product")
        self.assertEqual(agents.read_text(), "# mine\n")
        self.assertEqual(out["skipped"], ["AGENTS.md"])
        self.assertNotIn("AGENTS.md", out["created"])
        self.assertIn("PRODUCT.md", out["created"])


class PackageTest(TempRepo):
    def test_package_files_import_root_by_depth(self):
        self.init("")
        (self.root / "packages" / "api").mkdir(parents=True)
        r = run("scaffold.py", "package", "packages/api", "--root", self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.root / "packages/api/AGENTS.md").read_text().splitlines()[0], "@../../AGENTS.md")
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)

    def test_package_review_needs_root_review(self):
        self.init("")
        (self.root / "packages" / "api").mkdir(parents=True)
        self.assertEqual(run("scaffold.py", "package", "packages/api", "--root", self.root, "--review").returncode, 1)
        self.init("product,review")
        r = run("scaffold.py", "package", "packages/api", "--root", self.root, "--review")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.root / "packages/api/REVIEW.md").read_text().splitlines()[0], "@../../REVIEW.md")
        self.assertEqual(validate(self.root).returncode, 0)

    def test_package_outside_root_is_usage_error(self):
        self.init("")
        self.assertEqual(run("scaffold.py", "package", "..", "--root", self.root).returncode, 2)
        self.assertEqual(run("scaffold.py", "package", "missing", "--root", self.root).returncode, 2)


class StrictPlaceholderTest(TempRepo):
    def test_urls_and_date_formats_are_not_placeholders(self):
        self.write("AGENTS.md", "# AGENTS.md\n\nShare as `/about?key=<value>`; plans carry `Last updated: YYYY-MM-DD` "
                                "and live in `a/<domain>.yaml`.\n")
        self.write(".the-guide", "1.0.0\nsize: docs\n")
        r = run("validate_standard.py", self.root, "--strict")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_real_placeholders_are_flagged(self):
        self.write("AGENTS.md", "# AGENTS.md\n\n- Test: `<command>`\n- ok\n- Run: `<other>`\n")
        self.write("PRODUCT.md", "---\nname: x\nlast_reviewed: YYYY-MM-DD\n---\n\n# x\n")
        r = run("validate_standard.py", self.root, "--strict")
        self.assertEqual(r.returncode, 1)
        self.assertIn("2 unfilled placeholder line(s) at 3, 5", r.stdout)

    def test_summary_counts_inferred_claims(self):
        self.write("AGENTS.md", "# AGENTS.md\n\nA (inferred, not verified)\nB (inferred, not verified)\n")
        self.assertIn("2 unverified claim(s)", run("validate_standard.py", self.root).stdout)


class UpgradeTest(TempRepo):
    def test_older_stamp_refreshes_validator_then_finish_stamps(self):
        self.init("product")
        (self.root / ".the-guide").write_text("0.0.9\nsize: software\n")
        (self.root / "scripts/validate_standard.py").write_text("# stale\n")
        r = run("scaffold.py", "upgrade", self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual((out["from"], out["validator_refreshed"]), ("0.0.9", True))
        self.assertEqual(out["manual_notes"], [])
        self.assertEqual((self.root / ".the-guide").read_text(), "0.0.9\nsize: software\n")
        current = (SCRIPTS.parent / "templates" / ".the-guide").read_text().strip()
        r = run("scaffold.py", "upgrade", self.root, "--finish")
        self.assertEqual(json.loads(r.stdout), {"stamp": current, "size": "software"})
        self.assertEqual((self.root / ".the-guide").read_text(), current + "\nsize: software\n")

    def test_ops_apply_idempotently_and_manual_notes_are_listed(self):
        self.init("product")
        (self.root / ".the-guide").write_text("0.0.1\n")
        current = (SCRIPTS.parent / "templates" / ".the-guide").read_text().strip()
        upgrades = self.root / "_upgrades"
        upgrades.mkdir()
        (upgrades / "0.0.1.md").write_text("## Structural changes\n\n- too old; must be skipped\n\n## Manual\n")
        (upgrades / f"{current}.md").write_text(
            "## Structural changes\n\n```ops\n"
            '[{"file": "AGENTS.md", "op": "insert_after", "match": "## Commands", '
            '"line": "- Deploy: `<command>`"},\n'
            ' {"file": "PRODUCT.md", "op": "replace", "match": "## 1. Purpose", "line": "## 1. Why"},\n'
            ' {"file": "MISSING.md", "op": "replace", "match": "x", "line": "y"}]\n'
            "```\n\n## Manual\n\n- Move things by hand.\n")
        out = json.loads(run("scaffold.py", "upgrade", self.root, "--upgrades", upgrades).stdout)
        self.assertEqual(len(out["applied"]), 2, out)
        self.assertEqual([Path(n).name for n in out["manual_notes"]], [f"{current}.md"])
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("## Commands\n- Deploy: `<command>`", agents)
        self.assertIn("## 1. Why", (self.root / "PRODUCT.md").read_text())
        out = json.loads(run("scaffold.py", "upgrade", self.root, "--upgrades", upgrades).stdout)
        self.assertEqual(out["applied"], [])
        self.assertEqual(agents, (self.root / "AGENTS.md").read_text())
        self.assertEqual(validate(self.root).returncode, 0)

    def test_newer_repo_stamp_fails(self):
        self.init("product")
        (self.root / ".the-guide").write_text("9.0.0\n")
        self.assertEqual(run("scaffold.py", "upgrade", self.root).returncode, 1)

    def test_not_adopted_fails(self):
        self.assertEqual(run("scaffold.py", "upgrade", self.root).returncode, 1)


class PlanTest(TempRepo):
    def plan(self, name, fm):
        self.write(f"docs/plans/{name}.md", f"---\n{fm}\n---\n\n# p\n")

    def test_plans_are_not_grounding_docs_and_hygiene_warns(self):
        self.init("product")
        import datetime
        today = datetime.date.today()
        old = (today - datetime.timedelta(days=45)).isoformat()
        self.plan("a-active", f"status: active\nopened: {today.isoformat()}\nserves: [G1]")
        self.plan("b-done", f"status: done\nopened: {today.isoformat()}")
        self.plan("c-old", f"status: active\nopened: {old}")
        self.plan("d-bad", "title: no status")
        self.write("docs/plans/TEMPLATE.md", "---\nstatus: active\nopened: YYYY-MM-DD\n---\n")
        r = validate(self.root)
        self.assertEqual(r.returncode, 0, r.stdout)  # warnings only, never errors
        self.assertNotIn("a-active", r.stdout)
        self.assertIn("warning docs/plans/b-done.md: plan is done; run close-plan and delete it", r.stdout)
        self.assertIn("warning docs/plans/c-old.md: plan opened 45 days ago (limit 30)", r.stdout)
        self.assertIn("warning docs/plans/d-bad.md: plan needs front matter status", r.stdout)
        self.assertIn("warning docs/plans/d-bad.md: plan needs front matter opened", r.stdout)
        self.assertNotIn("TEMPLATE", r.stdout)
        # plans are outside the grounding scan: an undefined ID in a plan is not an error
        self.plan("e-ids", f"status: active\nopened: {today.isoformat()}\n---\nserves BR-nope-9")
        self.assertEqual(validate(self.root).returncode, 0)
        r = run("validate_standard.py", self.root, "--plan-age", "60")
        self.assertNotIn("c-old", r.stdout)
        # doc_map does not treat a plan as an owner
        d = json.loads(run("doc_map.py", "--root", self.root, "docs/plans/a-active.md", "src/x.py").stdout)
        self.assertEqual(d["unowned"], ["docs/plans/a-active.md", "src/x.py"])


class HookTest(TempRepo):
    HOOK = SCRIPTS.parent.parent.parent / "hooks" / "validate_grounding.py"

    def fire(self, tool, rel):
        payload = json.dumps({"tool_name": tool, "tool_input": {"file_path": rel}, "cwd": str(self.root)})
        return subprocess.run([sys.executable, str(self.HOOK)], input=payload, capture_output=True, text=True)

    def test_silent_when_clean_or_not_adopted(self):
        self.write("AGENTS.md", "# x\n")
        self.assertEqual(self.fire("Edit", "AGENTS.md").stdout, "")  # no stamp: not adopted
        self.init("product")
        self.assertEqual(self.fire("Edit", "AGENTS.md").stdout, "")  # adopted and clean
        self.assertEqual(self.fire("Edit", "src/app.py").stdout, "")  # not a grounding doc

    def test_errors_are_returned_as_additional_context(self):
        self.init("product")
        (self.root / "CLAUDE.md").write_text("# not a shim\n")
        for tool in ("Edit", "write"):
            r = self.fire(tool, "CLAUDE.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)["hookSpecificOutput"]
            self.assertEqual(out["hookEventName"], "PostToolUse")
            self.assertIn("Automatic check, not a user message", out["additionalContext"])
            self.assertIn("ERROR   CLAUDE.md: must contain only the line: @AGENTS.md", out["additionalContext"])
            self.assertNotIn("warning", out["additionalContext"])

    def test_garbage_input_is_ignored(self):
        r = subprocess.run([sys.executable, str(self.HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


class DetectTest(TempRepo):
    def test_pnpm_react_monorepo(self):
        self.write("package.json", json.dumps({"dependencies": {"react": "18"},
                                              "workspaces": ["packages/*"]}))
        self.write("pnpm-lock.yaml", "")
        self.write("packages/a/index.ts", "")
        self.write("packages/b/index.ts", "")
        r = run("detect.py", self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertTrue(d["ui"])
        self.assertEqual(d["package_manager"], ["pnpm"])
        self.assertEqual(d["packages"], ["packages/a", "packages/b"])
        self.assertEqual(d["suggested_size"], "monorepo")

    def test_malformed_package_json_is_reported_not_fatal(self):
        self.write("package.json", "{nope")
        d = json.loads(run("detect.py", self.root).stdout)
        self.assertEqual(len(d["errors"]), 1)
        self.assertEqual(d["stack"], ["node"])
        self.assertIsNone(d["manifest_version"])

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


class NextIdTest(TempRepo):
    def adr(self, title, *extra):
        r = run("next_id.py", "adr", title, "--root", self.root, "--date", "2026-01-02", *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_adr_numbers_files_and_index(self):
        self.init("decisions")
        self.assertEqual(self.adr("Use Postgres"), {"id": "ADR-0001", "path": "docs/decisions/0001-use-postgres.md"})
        self.assertEqual(self.adr("Queue: SQS, not Kafka!")["id"], "ADR-0002")
        index = (self.root / "docs/decisions/README.md").read_text()
        self.assertNotIn("_none yet_", index)
        self.assertIn("| ADR-0001 | Use Postgres | proposed | 2026-01-02 |  |", index)
        self.assertTrue((self.root / "docs/decisions/0002-queue-sqs-not-kafka.md").exists())
        record = (self.root / "docs/decisions/0001-use-postgres.md").read_text()
        self.assertIn("status: proposed", record)
        self.assertIn("relates_to: []", record)
        self.assertNotIn("ADR-0000", record)

    def test_supersede_links_both_records_and_validates(self):
        self.init("product,decisions")
        self.adr("First")
        self.adr("Second")
        self.assertEqual(self.adr("Third", "--supersedes", "ADR-0001")["id"], "ADR-0003")
        old = (self.root / "docs/decisions/0001-first.md").read_text()
        self.assertIn("superseded_by: ADR-0003", old)
        self.assertIn("status: proposed", old)
        index = (self.root / "docs/decisions/README.md").read_text()
        self.assertIn("| ADR-0001 | First | proposed | 2026-01-02 | by ADR-0003 |", index)
        self.assertIn("supersedes ADR-0001 |", index)
        self.assertIn("supersedes: ADR-0001", (self.root / "docs/decisions/0003-third.md").read_text())
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)

    def test_unknown_superseded_record_writes_nothing(self):
        self.init("decisions")
        before = (self.root / "docs/decisions/README.md").read_text()
        r = run("next_id.py", "adr", "X", "--root", self.root, "--supersedes", "ADR-0009")
        self.assertEqual(r.returncode, 1)
        self.assertEqual((self.root / "docs/decisions/README.md").read_text(), before)
        self.assertEqual(len(list((self.root / "docs/decisions").glob("[0-9]*-*.md"))), 1)  # template only

    def test_requires_decisions_index(self):
        self.assertEqual(run("next_id.py", "adr", "X", "--root", self.root).returncode, 1)

    def test_rule_ids_count_comments_and_start_at_one(self):
        self.write("docs/rules/x.yaml", "decisions:\n  - id: SD-x-2\nrules:\n  - id: BR-x-1\n  - id: BR-x-3\n"
                                       "# supersedes: BR-x-4\n# BR-xy-9 is another domain\n")
        self.assertEqual(run("next_id.py", "br", "x", "--root", self.root).stdout.strip(), "BR-x-5")
        self.assertEqual(run("next_id.py", "sd", "x", "--root", self.root).stdout.strip(), "SD-x-3")
        self.assertEqual(run("next_id.py", "sd", "missing", "--root", self.root).stdout.strip(), "SD-missing-1")

    def test_bad_domain_is_usage_error(self):
        self.assertEqual(run("next_id.py", "br", "Bad-Domain", "--root", self.root).returncode, 2)


class DocMapTest(TempRepo):
    def setUp(self):
        super().setUp()
        self.write("AGENTS.md", "# AGENTS.md\n\n- Entry: `src/api/server.ts#start`\n- Layout: `src/` code\n")
        self.write("ARCHITECTURE.md", "| ID | Part | Owns |\n|----|------|------|\n"
                                      "| BD1 | `src/scanner/` | scanning |\n| BD2 | <module> | x |\n")
        self.write("docs/rules/admission.yaml", "domain: admission\npaths:   # owned\n"
                                                "  - src/admission/**\n  - <src/other/**>\nrules: []\n")
        self.write("docs/decisions/0001-accepted.md", "---\nid: ADR-0001\nstatus: accepted\n---\n"
                                                      "Applies to `src/queue/worker.ts`.\n")

    def doc_map(self, *paths):
        r = run("doc_map.py", "--root", self.root, *paths)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        return d, {o["doc"]: o for o in d["owners"]}

    def test_each_owner_kind(self):
        d, o = self.doc_map("src/admission/a/b.ts", "src/scanner/x.ts", "src/api/server.ts", "package.json",
                            "src/misc/x.ts")
        self.assertEqual(o["docs/rules/admission.yaml"]["via"], ["paths: src/admission/**"])
        self.assertEqual(o["docs/rules/admission.yaml"]["paths"], ["src/admission/a/b.ts"])
        self.assertEqual(o["ARCHITECTURE.md"]["via"], ["BD1"])
        self.assertEqual(o["ARCHITECTURE.md"]["paths"], ["src/scanner/x.ts"])
        self.assertEqual(o["AGENTS.md"]["via"], ["cites src/api/server.ts", "commands"])
        self.assertEqual(o["AGENTS.md"]["paths"], ["package.json", "src/api/server.ts"])
        self.assertEqual(d["unowned"], ["src/misc/x.ts"])
        self.assertEqual(sorted(d["stale"]), ["AGENTS.md", "ARCHITECTURE.md", "docs/rules/admission.yaml"])

    def test_check_mode_fails_only_when_owned_docs_are_stale(self):
        r = run("doc_map.py", "--root", self.root, "--check", "src/scanner/x.ts")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(json.loads(r.stdout)["stale"], ["ARCHITECTURE.md"])
        self.assertEqual(json.loads(r.stdout)["owners"][0]["path_count"], 1)
        r = run("doc_map.py", "--root", self.root, "--check", "src/scanner/x.ts", "ARCHITECTURE.md")
        self.assertEqual(r.returncode, 0, r.stdout)
        r = run("doc_map.py", "--root", self.root, "--check", "src/misc/x.ts")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_review_docs_are_owners_through_citations(self):
        self.write("REVIEW.md", "# R\n\nNever flag `src/gen/out.ts`.\n")
        self.write("context.yaml", "version: 0\ncontext: []\n")
        d, o = self.doc_map("src/gen/out.ts")
        self.assertEqual(o["REVIEW.md"]["via"], ["cites src/gen/out.ts"])
        self.assertIn("REVIEW.md", d["stale"])

    def test_directory_citations_do_not_own_code(self):
        d, o = self.doc_map("src/other.ts")
        self.assertEqual(d["unowned"], ["src/other.ts"])
        self.assertEqual(d["owners"], [])

    def test_changed_doc_is_not_stale_and_accepted_status_is_reported(self):
        d, o = self.doc_map("docs/rules/admission.yaml", "src/admission/x.ts", "src/queue/worker.ts")
        self.assertTrue(o["docs/rules/admission.yaml"]["doc_changed"])
        self.assertNotIn("docs/rules/admission.yaml", d["stale"])
        self.assertEqual(o["docs/decisions/0001-accepted.md"]["status"], "accepted")
        self.assertIn("docs/decisions/0001-accepted.md", d["stale"])
        self.assertNotIn("docs/rules/admission.yaml", d["unowned"])

    def test_nested_package_commands_go_to_nearest_agents_md(self):
        self.write("packages/api/AGENTS.md", "@../../AGENTS.md\n")
        d, o = self.doc_map("packages/api/package.json")
        self.assertEqual(list(o), ["packages/api/AGENTS.md"])

    def test_git_changes_are_used_without_paths(self):
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("commit", "-qm", "init")
        self.write("src/scanner/new.ts", "")
        d, o = self.doc_map()
        self.assertEqual(d["changed"], ["src/scanner/new.ts"])
        self.assertEqual(d["stale"], ["ARCHITECTURE.md"])

    def test_not_a_git_repo_without_paths_is_usage_error(self):
        self.assertEqual(run("doc_map.py", "--root", self.root).returncode, 2)


if __name__ == "__main__":
    unittest.main()
