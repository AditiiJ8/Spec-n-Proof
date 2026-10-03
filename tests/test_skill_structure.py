"""Structural tests for the spec-and-proof skills. Standard library only.

Run from the repository root:
    python3 -m unittest discover -s tests -v

These tests check structure and consistency. They cannot show that an agent
behaves well when it follows the skills. See README.md, "What the tests do not cover".
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_skills as vs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
SKILL_NAMES = ["spec-sprint", "proof-build"]
EXAMPLES = ["sample-project-idea.md", "sample-spec.md", "sample-plan.md", "sample-verification-report.md"]


def read(path):
    return Path(path).read_text(encoding="utf-8")


class RealSkillTests(unittest.TestCase):
    def test_skill_files_exist(self):
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                self.assertTrue((SKILLS / name / "SKILL.md").is_file())

    def test_no_unexpected_skill_directories(self):
        found = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
        self.assertEqual(found, sorted(SKILL_NAMES))

    def test_each_skill_validates_cleanly(self):
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                report = vs.validate_skill(SKILLS / name)
                self.assertEqual(report.errors, [])
                self.assertEqual(report.warnings, [])

    def test_frontmatter_values(self):
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                block, _ = vs.split_frontmatter(read(SKILLS / name / "SKILL.md"))
                meta = vs.parse_frontmatter(block)
                self.assertEqual(meta["name"], name)
                self.assertTrue(meta["description"].strip())
                self.assertLessEqual(len(meta["description"]), 1024)
                self.assertEqual(meta["license"], "MIT")
                self.assertIsInstance(meta["metadata"]["version"], str)

    def test_descriptions_say_when_to_use(self):
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                block, _ = vs.split_frontmatter(read(SKILLS / name / "SKILL.md"))
                self.assertIn("Use when", vs.parse_frontmatter(block)["description"])

    def test_workflow_stages_present_and_ordered(self):
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                _, body = vs.split_frontmatter(read(SKILLS / name / "SKILL.md"))
                missing = vs.missing_stages(vs.headings(body), vs.WORKFLOWS[name]["stages"])
                self.assertEqual(missing, [])

    def test_body_length_within_recommendation(self):
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                _, body = vs.split_frontmatter(read(SKILLS / name / "SKILL.md"))
                self.assertLess(len(body.splitlines()), vs.MAX_BODY_LINES)

    def test_internal_references_resolve(self):
        expected = {
            "spec-sprint": ["assets/SPEC.template.md", "assets/PLAN.template.md"],
            "proof-build": ["assets/REPORT.template.md"],
        }
        for name, refs in expected.items():
            with self.subTest(skill=name):
                text = read(SKILLS / name / "SKILL.md")
                found = vs.referenced_paths(text)
                for ref in refs:
                    self.assertIn(ref, found)
                    self.assertTrue((SKILLS / name / ref).is_file())
                self.assertEqual(
                    vs.check_links(SKILLS / name / "SKILL.md", boundary=SKILLS / name, bare_paths=True), []
                )

    def test_skills_are_self_contained(self):
        # Installing one skill alone must work, so no reference may leave the skill folder.
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                for ref in vs.referenced_paths(read(SKILLS / name / "SKILL.md")):
                    self.assertFalse(ref.startswith(".."), ref)

    def test_command_line_validator_passes(self):
        self.assertEqual(vs.main([str(SKILLS)]), 0)


class CrossSkillConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.spec = read(SKILLS / "spec-sprint" / "SKILL.md")
        self.proof = read(SKILLS / "proof-build" / "SKILL.md")

    def test_plan_fields_are_shared_vocabulary(self):
        plan_template = read(SKILLS / "spec-sprint" / "assets" / "PLAN.template.md")
        for label in ("Done when", "Verify with"):
            with self.subTest(label=label):
                self.assertIn(label, plan_template)
                self.assertIn(label, self.spec)
                self.assertIn(label, self.proof)

    def test_checkbox_format_matches_between_skills(self):
        # spec-sprint writes "- [ ] T1: title"; proof-build must tell the agent to tick "[x]".
        self.assertIn("- [ ] T1:", self.spec)
        self.assertIn("- [ ] T1:", read(SKILLS / "spec-sprint" / "assets" / "PLAN.template.md"))
        self.assertIn("`[x]`", self.proof)

    def test_status_vocabulary_matches_report_template(self):
        template = read(SKILLS / "proof-build" / "assets" / "REPORT.template.md")
        for status in ("PASS", "FAIL", "NOT RUN", "BLOCKED"):
            with self.subTest(status=status):
                self.assertIn(status, self.proof)
                self.assertIn(status, template)

    def test_neither_skill_commits_on_its_own(self):
        self.assertIn("Do not commit", self.spec)
        self.assertIn("Do not commit, push, tag, or publish on your own", self.proof)

    def test_spec_sprint_does_not_implement(self):
        self.assertIn("does not write application code", self.spec)

    def test_hand_off_points_to_the_other_skill(self):
        self.assertIn("proof-build", self.spec)
        self.assertIn("spec-sprint", self.proof)

    def test_names_and_descriptions_are_distinct(self):
        metas = []
        for name in SKILL_NAMES:
            block, _ = vs.split_frontmatter(read(SKILLS / name / "SKILL.md"))
            metas.append(vs.parse_frontmatter(block))
        self.assertNotEqual(metas[0]["name"], metas[1]["name"])
        self.assertNotEqual(metas[0]["description"], metas[1]["description"])


class ValidatorRejectsBadSkillsTests(unittest.TestCase):
    """The validator must fail on broken input, otherwise a passing run means little."""

    def make(self, dirname, frontmatter, body="# Title\n\nSome instructions.\n"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill_dir = Path(tmp.name) / dirname
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
        return skill_dir

    def errors(self, skill_dir):
        return "\n".join(vs.validate_skill(skill_dir).errors)

    def test_valid_minimal_skill_passes(self):
        d = self.make("demo-skill", "name: demo-skill\ndescription: Does a thing. Use when needed.")
        self.assertTrue(vs.validate_skill(d).ok)

    def test_missing_skill_md(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        (Path(tmp.name) / "empty").mkdir()
        self.assertIn("SKILL.md is missing", self.errors(Path(tmp.name) / "empty"))

    def test_no_frontmatter(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name) / "x"
        d.mkdir()
        (d / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
        self.assertIn("frontmatter", self.errors(d))

    def test_unclosed_frontmatter(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name) / "x"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: x\ndescription: y\n", encoding="utf-8")
        self.assertIn("never closed", self.errors(d))

    def test_uppercase_name(self):
        d = self.make("Demo", "name: Demo\ndescription: A thing.")
        self.assertIn("lowercase", self.errors(d))

    def test_name_must_match_directory(self):
        d = self.make("demo-skill", "name: other-name\ndescription: A thing.")
        self.assertIn("must match its directory name", self.errors(d))

    def test_consecutive_hyphens(self):
        d = self.make("a--b", "name: a--b\ndescription: A thing.")
        self.assertIn("consecutive hyphens", self.errors(d))

    def test_leading_and_trailing_hyphen(self):
        for bad in ("-abc", "abc-"):
            with self.subTest(name=bad):
                d = self.make(bad, f"name: {bad}\ndescription: A thing.")
                self.assertIn("hyphen", self.errors(d))

    def test_name_too_long(self):
        long_name = "a" * 65
        d = self.make(long_name, f"name: {long_name}\ndescription: A thing.")
        self.assertIn("1-64", self.errors(d))

    def test_underscore_in_name(self):
        d = self.make("my_skill", "name: my_skill\ndescription: A thing.")
        self.assertIn("lowercase letters, digits and hyphens", self.errors(d))

    def test_missing_description(self):
        d = self.make("demo", "name: demo")
        self.assertIn("description is required", self.errors(d))

    def test_blank_description(self):
        d = self.make("demo", 'name: demo\ndescription: "   "')
        self.assertIn("description is required", self.errors(d))

    def test_description_too_long(self):
        d = self.make("demo", "name: demo\ndescription: " + "x" * 1025)
        self.assertIn("1025 characters", self.errors(d))

    def test_unknown_field(self):
        d = self.make("demo", "name: demo\ndescription: A thing.\ntags: nope")
        self.assertIn("unknown frontmatter field 'tags'", self.errors(d))

    def test_unquoted_colon_in_description_is_rejected(self):
        d = self.make("demo", "name: demo\ndescription: Steps: one, two")
        self.assertIn("unquoted value", self.errors(d))

    def test_numeric_metadata_must_be_quoted(self):
        d = self.make("demo", "name: demo\ndescription: A thing.\nmetadata:\n  version: 1.0")
        self.assertIn("quotes", self.errors(d))

    def test_quoted_metadata_is_accepted(self):
        d = self.make("demo", 'name: demo\ndescription: A thing.\nmetadata:\n  version: "1.0"')
        self.assertTrue(vs.validate_skill(d).ok)

    def test_block_scalar_is_reported_not_guessed(self):
        d = self.make("demo", "name: demo\ndescription: >\n  folded text")
        self.assertIn("unsupported YAML", self.errors(d))

    def test_compatibility_too_long(self):
        d = self.make("demo", "name: demo\ndescription: A thing.\ncompatibility: " + "y" * 501)
        self.assertIn("compatibility", self.errors(d))

    def test_broken_reference(self):
        d = self.make("demo", "name: demo\ndescription: A thing.", "See [guide](references/GUIDE.md).\n")
        self.assertIn("does not exist", self.errors(d))

    def test_bare_asset_path_must_exist(self):
        d = self.make("demo", "name: demo\ndescription: A thing.", "Start from assets/template.md.\n")
        self.assertIn("assets/template.md", self.errors(d))

    def test_reference_that_escapes_the_skill_directory(self):
        d = self.make("demo", "name: demo\ndescription: A thing.", "See [x](../outside.md).\n")
        (d.parent / "outside.md").write_text("hi", encoding="utf-8")
        self.assertIn("outside", self.errors(d))

    def test_valid_reference_is_accepted(self):
        d = self.make("demo", "name: demo\ndescription: A thing.", "See [guide](references/GUIDE.md).\n")
        (d / "references").mkdir()
        (d / "references" / "GUIDE.md").write_text("guide", encoding="utf-8")
        self.assertTrue(vs.validate_skill(d).ok)

    def test_urls_and_anchors_are_not_treated_as_files(self):
        body = "[site](https://example.com/assets/x.md) and [top](#top).\n"
        d = self.make("demo", "name: demo\ndescription: A thing.", body)
        self.assertTrue(vs.validate_skill(d).ok)

    def test_long_body_warns(self):
        d = self.make("demo", "name: demo\ndescription: A thing.", "line\n" * 501)
        report = vs.validate_skill(d)
        self.assertTrue(report.ok)
        self.assertTrue(report.warnings)

    def test_known_skill_missing_workflow_stages_fails(self):
        d = self.make("spec-sprint", "name: spec-sprint\ndescription: A thing.", "## Only one heading\n")
        text = self.errors(d)
        self.assertIn("workflow stage missing", text)
        self.assertIn("expected phrase not found", text)

    def test_stage_order_matters(self):
        self.assertEqual(vs.missing_stages(["Alpha", "Beta"], ["alpha", "beta"]), [])
        self.assertEqual(vs.missing_stages(["Beta", "Alpha"], ["alpha", "beta"]), ["beta"])

    def test_headings_inside_code_fences_are_ignored(self):
        body = "## Real\n```\n## Fake\n```\n"
        self.assertEqual(vs.headings(body), ["Real"])


class RepositoryFileTests(unittest.TestCase):
    def test_top_level_files_exist(self):
        for name in ("README.md", "DEMO.md", "LICENSE", ".gitignore"):
            with self.subTest(file=name):
                self.assertTrue((ROOT / name).is_file())

    def test_license_is_mit(self):
        text = read(ROOT / "LICENSE")
        self.assertIn("MIT License", text)
        self.assertIn("Permission is hereby granted, free of charge", text)

    def test_examples_exist_and_are_readable(self):
        for name in EXAMPLES:
            with self.subTest(example=name):
                path = ROOT / "examples" / name
                self.assertTrue(path.is_file())
                self.assertGreater(len(read(path).strip()), 100)

    def test_demo_target_files_exist(self):
        for name in ("expenses.py", "test_expenses.py"):
            with self.subTest(file=name):
                self.assertTrue((ROOT / "examples" / "expense-tracker" / name).is_file())

    def test_markdown_links_resolve(self):
        files = [ROOT / "README.md", ROOT / "DEMO.md"] + sorted((ROOT / "examples").glob("*.md"))
        for path in files:
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertEqual(vs.check_links(path), [])

    def test_readme_documents_install_and_validation(self):
        text = read(ROOT / "README.md")
        for needle in (".claude/skills", "python3 -m unittest discover -s tests", "Limitations"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_gitignore_covers_python_caches(self):
        self.assertIn("__pycache__", read(ROOT / ".gitignore"))

    def test_report_example_labels_its_provenance(self):
        text = read(ROOT / "examples" / "sample-verification-report.md")
        self.assertIn("captured", text.lower())
        self.assertIn("Not verified", text)
        for status in ("PASS", "NOT RUN", "BLOCKED"):
            self.assertIn(status, text)


if __name__ == "__main__":
    unittest.main()
