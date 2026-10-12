from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_markdown_links_resolve(self):
        missing = []
        for markdown in ROOT.rglob("*.md"):
            source = markdown.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", source):
                if "://" in target or target.startswith("#") or target.startswith("<"):
                    continue
                clean = target.split("#", 1)[0]
                if clean and not (markdown.parent / clean).is_file():
                    missing.append(f"{markdown.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])

    def test_required_v4_references_exist(self):
        for filename in ("reference_title.md", "reference_image.md", "text_repair.md", "batch_excel.md"):
            self.assertTrue((ROOT / "references" / filename).is_file(), filename)

    def test_legacy_and_composite_score_rules_are_absent(self):
        for filename in ("composition.md", "product_type.md", "usage_scene.md", "research-and-generation.md"):
            self.assertFalse((ROOT / "references" / filename).exists(), filename)
        research = (ROOT / "references" / "research.md").read_text(encoding="utf-8")
        generation = (ROOT / "references" / "generation_rules.md").read_text(encoding="utf-8")
        self.assertNotIn("composite_score =", research)
        self.assertNotIn("100-point", generation)
        self.assertIn("Do not calculate a routine numeric score", generation)

    def test_prompt_rules_are_not_duplicated_in_python(self):
        source = (ROOT / "scripts" / "build_prompts.py").read_text(encoding="utf-8")
        self.assertNotIn("ROLE_INSTRUCTIONS", source)
        self.assertNotIn("CATEGORY_RULES", source)
        self.assertIn("image_construction.md", source)
        self.assertIn("negative_prompt.md", source)

    def test_batch_runtime_has_one_implementation(self):
        self.assertTrue((ROOT / "scripts" / "workbook_to_batch_manifest.py").is_file())
        self.assertTrue((ROOT / "scripts" / "update_batch_results.py").is_file())
        self.assertFalse((ROOT / "scripts" / "workbook_to_batch_manifest.mjs").exists())
        self.assertFalse((ROOT / "scripts" / "update_batch_results.mjs").exists())
        repair = (ROOT / "references" / "text_repair.md").read_text(encoding="utf-8")
        self.assertIn("only after", repair.lower())
        self.assertIn("Do not reload Alibaba", repair)

    def test_openai_yaml_and_compact_entry(self):
        source = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        match = re.search(r'short_description: "([^"]+)"', source)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(len(match.group(1)), 25)
        self.assertLessEqual(len(match.group(1)), 64)
        self.assertIn("$packaging-print-image-maker", source)
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(skill.splitlines()), 100)
        self.assertIn("batch_excel.md", skill)


if __name__ == "__main__":
    unittest.main()
