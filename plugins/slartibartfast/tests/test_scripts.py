import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "sot-standard" / "scripts"


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd)


def validate(root):
    return run("validate_standard.py", root)


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


class InitTest(TempRepo):
    def test_empty_set_writes_minimal_repo(self):
        out = self.init("")
        files = {p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(files, {"AGENTS.md", "CLAUDE.md", "CHANGELOG.md", ".sot-standard",
                                 "scripts/validate_standard.py"})
        self.assertEqual(out["skipped"], [])
        text = (self.root / "AGENTS.md").read_text()
        rows = [l for l in text.splitlines() if l.startswith("| ")]
        self.assertTrue([r for r in rows if r.startswith("| [`CHANGELOG.md`](./CHANGELOG.md) |")])
        for gone in ("PRODUCT.md", "DESIGN.md", "ARCHITECTURE.md", "docs/decisions", "docs/rules"):
            self.assertFalse([r for r in rows if gone in r], gone)
        self.assertIn("## 7. Definition of done", text)
        self.assertNotIn("## 8.", text)
        # the vendored copy, as CI in an adopting repo runs it
        r = subprocess.run([sys.executable, "scripts/validate_standard.py", "."], cwd=self.root,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("CHANGELOG.md", r.stdout)

    def test_full_software_set_validates(self):
        out = self.init("product,architecture,decisions")
        self.assertIn("CHANGELOG.md", out["created"])
        agents = (self.root / "AGENTS.md").read_text()
        self.assertNotIn("DESIGN.md`](./DESIGN.md)", agents)
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)

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

    def test_ui_writes_design_template_and_keeps_row(self):
        out = self.init("ui")
        self.assertIn("DESIGN.md", out["created"])
        self.assertIn("DESIGN.md`](./DESIGN.md)", (self.root / "AGENTS.md").read_text())
        v = validate(self.root)
        self.assertEqual(v.returncode, 0, v.stdout)
        self.assertNotIn("link target not found", v.stdout)

    def test_ui_template_is_flagged_as_unfilled_under_strict(self):
        self.init("ui")
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

    def test_package_outside_root_is_usage_error(self):
        self.init("")
        self.assertEqual(run("scaffold.py", "package", "..", "--root", self.root).returncode, 2)
        self.assertEqual(run("scaffold.py", "package", "missing", "--root", self.root).returncode, 2)


class StrictPlaceholderTest(TempRepo):
    def test_urls_and_date_formats_are_not_placeholders(self):
        self.write("AGENTS.md", "# AGENTS.md\n\nShare as `/about?key=<value>`; plans carry `Last updated: YYYY-MM-DD` "
                                "and live in `a/<domain>.yaml`.\n")
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
        self.init("")
        (self.root / ".sot-standard").write_text("0.0.9\n")
        (self.root / "scripts/validate_standard.py").write_text("# stale\n")
        r = run("scaffold.py", "upgrade", self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual((out["from"], out["validator_refreshed"]), ("0.0.9", True))
        self.assertEqual([Path(n).name for n in out["notes"]], ["0.3.0.md"])
        self.assertEqual((self.root / ".sot-standard").read_text(), "0.0.9\n")
        current = (SCRIPTS.parent / "templates" / ".sot-standard").read_text().strip()
        r = run("scaffold.py", "upgrade", self.root, "--finish")
        self.assertEqual(json.loads(r.stdout), {"stamp": current})
        self.assertEqual((self.root / ".sot-standard").read_text(), current + "\n")

    def test_newer_repo_stamp_fails(self):
        self.init("")
        (self.root / ".sot-standard").write_text("9.0.0\n")
        self.assertEqual(run("scaffold.py", "upgrade", self.root).returncode, 1)

    def test_not_adopted_fails(self):
        self.assertEqual(run("scaffold.py", "upgrade", self.root).returncode, 1)


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
        git = lambda *a: subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                        check=True, capture_output=True)
        git("init", "-q", "-b", "main")
        git("add", "-A")
        git("commit", "-qm", "init")
        self.write("src/scanner/new.ts", "")
        d, o = self.doc_map()
        self.assertEqual(d["changed"], ["src/scanner/new.ts"])
        self.assertEqual(d["stale"], ["ARCHITECTURE.md"])

    def test_not_a_git_repo_without_paths_is_usage_error(self):
        self.assertEqual(run("doc_map.py", "--root", self.root).returncode, 2)


if __name__ == "__main__":
    unittest.main()
