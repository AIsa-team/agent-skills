from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[3] / "scripts/validate_connect_paths.py"
spec = importlib.util.spec_from_file_location("connect_paths", MODULE_PATH)
assert spec and spec.loader
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)


class ConnectPathTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        category = root / "AIsa-connect"
        skill = category / "weekly-report"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: weekly-report\ndescription: test\n---\n")
        entry = {"slug": "weekly-report", "path": "AIsa-connect/weekly-report/SKILL.md", "url": paths.URL_PREFIX + "AIsa-connect/weekly-report/SKILL.md"}
        (category / "paths.json").write_text(json.dumps({"schema_version": 1, "skills": [entry]}))
        website = root / "en.json"
        website.write_text(json.dumps({"workflows": {"weekly-report": {
            "skill": {"markdownUrl": entry["url"], "githubUrl": paths.TREE_PREFIX + "AIsa-connect/weekly-report"},
            "prompt": "Set up AIsa; follow [SKILL.md URL]", "prompts": [{"text": "Follow [SKILL.md URL] for this task"}]
        }}}))
        return website

    def test_website_prompts_and_local_files_agree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            website = self.fixture(root)
            self.assertEqual(paths.validate(root, [website]), [])

    def test_url_case_mismatch_fails_even_on_case_insensitive_filesystems(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            p = root / "AIsa-connect/paths.json"
            data = json.loads(p.read_text())
            data["skills"][0]["url"] = data["skills"][0]["url"].replace("AIsa-connect", "aisa-connect")
            p.write_text(json.dumps(data))
            self.assertTrue(paths.validate(root))

    def test_missing_file_is_not_a_published_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            p = root / "AIsa-connect/weekly-report/SKILL.md"
            p.rename(p.with_name("skill.md"))
            self.assertTrue(paths.validate(root))

    def test_stale_website_url_and_omitted_copy_payload_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            website = self.fixture(root)
            data = json.loads(website.read_text())
            w = data["workflows"]["weekly-report"]
            w["skill"]["markdownUrl"] = w["skill"]["markdownUrl"].replace("weekly-report", "old-report")
            w["prompts"][0]["text"] = "A task without its installer/Skill"
            website.write_text(json.dumps(data))
            errors = paths.validate(root, [website])
            self.assertTrue(any("markdownUrl" in e for e in errors))
            self.assertTrue(any("copied prompt" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
