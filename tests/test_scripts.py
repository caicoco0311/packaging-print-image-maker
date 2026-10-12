from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


build_prompts = load_module("build_prompts", "build_prompts.py")
resize_outputs = load_module("resize_outputs", "resize_outputs.py")
validate_outputs = load_module("validate_outputs", "validate_outputs.py")


def identity(category: str, requested=True) -> dict:
    packaging_types = {"label": "Label", "sticker": "Sticker", "box": "Box", "other": "Pouch"}
    materials = ["cotton paper"] if requested else ["textured paper"]
    return {
        "schema_version": "4.1",
        "input_mode": "text",
        "reference_mode": "researched",
        "raw_input": f"test + {packaging_types[category]}",
        "product": "test product",
        "packaging_type": packaging_types[category],
        "normalized_category": category,
        "normalized_product_title": f"Custom Test Product {packaging_types[category]}",
        "detail_page_keywords": ["custom test packaging"],
        "requested_materials": ["cotton paper"] if requested else [],
        "material_source": "user" if requested else "research",
        "visual_identity": {
            "container_shape": "rectangular container",
            "closure": "sealed top",
            "materials": materials,
            "label_shape": "rectangle",
            "print_location": "front",
            "palette": ["ivory", "black"],
            "finishes": ["matte"],
            "physical_dimensions": "dimensions unknown; preserve reference proportions",
            "structure_states": ["assembled"],
        },
        "required_text": "Your Logo",
        "title_text": "customized Solution",
        "forbidden_content": ["seller identity", "watermark"],
        "selected_references": [
            {"title": "A", "url": "https://example.com/a", "sold_count": 1000, "sold_rank": 1, "title_valid": True, "image_valid": True, "role": "primary", "image_paths": ["a.png", "a-detail.png"]},
            {"title": "B", "url": "https://example.com/b", "sold_count": 500, "sold_rank": 2, "title_valid": True, "image_valid": True, "role": "secondary", "image_paths": ["b.png"]},
            {"title": "C", "url": "https://example.com/c", "sold_count": 100, "sold_rank": 3, "title_valid": True, "image_valid": True, "role": "tertiary", "image_paths": ["c.png"]},
        ],
    }


class BuildPromptsTests(unittest.TestCase):
    def build(self, temp_path: Path, category: str, data=None, skill_root=ROOT):
        identity_path = temp_path / f"{category}.json"
        identity_path.write_text(json.dumps(data or identity(category), ensure_ascii=False), encoding="utf-8")
        out_dir = temp_path / f"out-{category}"
        manifest_path = build_prompts.run(identity_path, category, out_dir, skill_root)
        return out_dir, json.loads(manifest_path.read_text(encoding="utf-8"))

    def test_all_four_categories_and_separate_prompt_files(self):
        with tempfile.TemporaryDirectory() as temp:
            for category in ("label", "sticker", "box", "other"):
                out_dir, manifest = self.build(Path(temp), category)
                self.assertEqual(manifest["prompt_count"], 6)
                self.assertTrue(manifest["positive_negative_separated"])
                self.assertEqual(sum(row["requires_title_text"] for row in manifest["prompts"]), 1)
                for row in manifest["prompts"]:
                    positive = (out_dir / row["positive_prompt_file"]).read_text(encoding="utf-8")
                    negative = (out_dir / row["negative_prompt_file"]).read_text(encoding="utf-8")
                    self.assertIn("Your Logo", positive)
                    self.assertNotIn("NEGATIVE PROMPT", positive)
                    self.assertIn("seller", negative)
                self.assertIn("customized Solution", (out_dir / "positive" / "02_showcase.txt").read_text(encoding="utf-8"))

    def test_requested_material_is_hard_locked_in_four_grid(self):
        with tempfile.TemporaryDirectory() as temp:
            out_dir, _ = self.build(Path(temp), "label")
            details = (out_dir / "positive" / "03_details.txt").read_text(encoding="utf-8")
            self.assertIn("USER MATERIAL LOCK", details)
            self.assertIn("cotton paper", details)
            self.assertIn("strict four-panel", details)

    def test_wave_two_identity_is_compressed(self):
        with tempfile.TemporaryDirectory() as temp:
            out_dir, _ = self.build(Path(temp), "label")
            hero = (out_dir / "positive" / "01_hero.txt").read_text(encoding="utf-8")
            usage = (out_dir / "positive" / "04_usage.txt").read_text(encoding="utf-8")
            self.assertIn("Product identity:", hero)
            self.assertIn("approved hero", usage)
            self.assertNotIn("Product identity:", usage)
            self.assertLess(len(usage), len(hero))

    def test_markdown_is_the_positive_source_of_truth(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            skill_root = temp_path / "skill"
            shutil.copytree(ROOT / "references", skill_root / "references")
            image_rules = skill_root / "references" / "image_construction.md"
            source = image_rules.read_text(encoding="utf-8").replace("Create the commercial hero", "Create the TEST-SENTINEL commercial hero")
            image_rules.write_text(source, encoding="utf-8")
            out_dir, _ = self.build(temp_path, "label", skill_root=skill_root)
            self.assertIn("TEST-SENTINEL", (out_dir / "positive" / "01_hero.txt").read_text(encoding="utf-8"))

    def test_malformed_positive_or_negative_blocks_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rules.md"
            original = (ROOT / "references" / "negative_prompt.md").read_text(encoding="utf-8")
            expected = ["common", *(f"role_{i}" for i in range(1, 7))]
            path.write_text(original.replace("## role_6", "## omitted_role_6"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "role_6"):
                build_prompts.parse_text_blocks(path, expected)
            path.write_text(original + "\n## common\n\n```text\nduplicate\n```\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "common"):
                build_prompts.parse_text_blocks(path, expected)

    def test_identity_rejects_old_score_contract_and_low_sales(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "identity.json"
            data = identity("label")
            data["selected_references"][2]["sold_count"] = 99
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, ">= 100"):
                build_prompts.load_identity(path, "label")

    def test_direct_link_and_single_image_cache_modes(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            direct = identity("label")
            direct.update({"input_mode": "url", "reference_mode": "direct-link"})
            direct["selected_references"] = [{"title": "Direct", "url": "https://example.com/direct", "sold_count": 0, "sold_rank": 1, "title_valid": True, "image_valid": True, "role": "primary", "image_paths": ["direct.png"]}]
            direct_out, direct_manifest = self.build(temp_path, "label", direct)
            hero_assets = direct_manifest["prompts"][0]["input_assets"]
            self.assertEqual([asset["role"] for asset in hero_assets], ["alibaba_reference", "your_logo_asset"])
            self.assertIn("Image 2: neutral Your Logo", (direct_out / "positive" / "01_hero.txt").read_text(encoding="utf-8"))

            cached = identity("label")
            cached["reference_mode"] = "cache-reuse"
            cached["selected_references"] = [cached["selected_references"][0]]
            cached["selected_references"][0]["image_paths"] = ["cached-primary.png"]
            _, cached_manifest = self.build(temp_path, "label", cached)
            self.assertEqual([asset["role"] for asset in cached_manifest["prompts"][4]["input_assets"]], ["approved_hero", "your_logo_asset", "primary_reference"])

    def test_requested_five_input_dry_runs(self):
        examples = (
            ("红酒 + Label", "red wine", "Label", "label"),
            ("肽 + Label", "peptide", "Label", "label"),
            ("香水 + Sticker", "perfume", "Sticker", "sticker"),
            ("咖啡 + Box", "coffee", "Box", "box"),
            ("护肤品 + Pouch", "skincare", "Pouch", "other"),
        )
        with tempfile.TemporaryDirectory() as temp:
            for index, (raw_input, product, packaging_type, category) in enumerate(examples, 1):
                data = identity(category, requested=index % 2 == 0)
                data.update({"raw_input": raw_input, "product": product, "packaging_type": packaging_type})
                data["normalized_product_title"] = f"Custom {product} {packaging_type}"
                out_dir, manifest = self.build(Path(temp), category, data)
                self.assertEqual(manifest["category"], category)
                self.assertEqual(len(list((out_dir / "positive").glob("0*.txt"))), 6)
                self.assertEqual(len(list((out_dir / "negative").glob("0*.txt"))), 6)


class ResizeAndValidateTests(unittest.TestCase):
    @staticmethod
    def make_native_set(native_dir: Path, dimensions=(64, 64)):
        native_dir.mkdir(parents=True)
        for native_name, _ in resize_outputs.FILE_PAIRS:
            Image.new("RGB", dimensions, "white").save(native_dir / native_name, format="PNG")

    @staticmethod
    def make_prompt_manifest(path: Path):
        rows = []
        for number, (native_name, final_name) in enumerate(resize_outputs.FILE_PAIRS, 1):
            positive_name = f"positive/{number:02d}.txt"
            negative_name = f"negative/{number:02d}.txt"
            (path.parent / "positive").mkdir(exist_ok=True)
            (path.parent / "negative").mkdir(exist_ok=True)
            positive = 'Render exact "Your Logo".'
            if number == 2:
                positive += ' Render exact "customized Solution".'
            (path.parent / positive_name).write_text(positive, encoding="utf-8")
            (path.parent / negative_name).write_text("seller brand, watermark", encoding="utf-8")
            rows.append({
                "role_number": number,
                "native_file": native_name,
                "final_file": final_name,
                "positive_prompt_file": positive_name,
                "negative_prompt_file": negative_name,
            })
        path.write_text(json.dumps({
            "schema_version": "2.0",
            "positive_negative_separated": True,
            "prompt_count": 6,
            "prompts": rows,
        }), encoding="utf-8")

    def test_square_resize_and_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            native = output / "native"
            self.make_native_set(native)
            before = (native / resize_outputs.FILE_PAIRS[0][0]).read_bytes()
            resize_outputs.resize_all(native, output)
            self.assertEqual(before, (native / resize_outputs.FILE_PAIRS[0][0]).read_bytes())
            prompts = Path(temp) / "prompt_manifest.json"
            self.make_prompt_manifest(prompts)
            self.assertTrue(validate_outputs.validate(output, prompts)["valid"])

    def test_non_square_input_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            native = output / "native"
            self.make_native_set(native)
            Image.new("RGB", (80, 64), "white").save(native / resize_outputs.FILE_PAIRS[2][0])
            with self.assertRaisesRegex(ValueError, "non-square source rejected"):
                resize_outputs.resize_all(native, output)
            self.assertFalse(any(output.glob("*-950.png")))

    def test_missing_wrong_size_and_extra_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            native = output / "native"
            self.make_native_set(native)
            resize_outputs.resize_all(native, output)
            prompts = Path(temp) / "prompt_manifest.json"
            self.make_prompt_manifest(prompts)
            (output / "06-multi-angle-950.png").unlink()
            with self.assertRaisesRegex(ValueError, "final PNG set mismatch"):
                validate_outputs.validate(output, prompts)
            Image.new("RGB", (800, 800), "white").save(output / "06-multi-angle-950.png")
            with self.assertRaisesRegex(ValueError, "wrong size"):
                validate_outputs.validate(output, prompts)
            Image.new("RGB", (950, 950), "white").save(output / "extra.png")
            with self.assertRaisesRegex(ValueError, "final PNG set mismatch"):
                validate_outputs.validate(output, prompts)


if __name__ == "__main__":
    unittest.main()
