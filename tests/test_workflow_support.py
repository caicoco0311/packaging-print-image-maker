from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
    return module


prepare_identity = load("prepare_identity")
research_cache = load("research_cache")
analyze_titles = load("analyze_titles")
physical_qa = load("physical_qa")


def evidence(image_path: str) -> dict:
    return {
        "product": "red wine", "packaging_type": "label", "normalized_category": "label",
        "normalized_product_title": "Custom Wine Bottle Label", "detail_page_keywords": ["custom wine label"],
        "requested_materials": [], "material_source": "research",
        "visual_identity": {"container_shape": "750 ml bottle", "closure": "cork", "materials": ["paper"], "label_shape": "rectangle", "print_location": "front", "palette": ["ivory"], "finishes": ["foil"], "physical_dimensions": "750 ml; preserve proportions", "structure_states": ["applied"]},
        "selected_references": [{"title": "Wine Label", "url": "https://example.com/p", "sold_count": 500, "sold_rank": 1, "title_valid": True, "image_valid": True, "role": "primary", "image_paths": [image_path]}],
    }


class WorkflowSupportTests(unittest.TestCase):
    def test_url_routes_directly_and_builds_reference(self):
        data = evidence("ref.png"); data["selected_references"] = []; data["image_paths"] = ["ref.png"]
        result = prepare_identity.assemble("https://www.alibaba.com/product-detail/123.html", data)
        self.assertEqual(result["input_mode"], "url"); self.assertEqual(result["reference_mode"], "direct-link")
        self.assertEqual(len(result["selected_references"]), 1)

    def test_image_input_requires_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.png"; path.write_bytes(b"image")
            result = prepare_identity.assemble("wine label", evidence("ref.png"), path)
            self.assertEqual(result["input_mode"], "image"); self.assertEqual(result["visual_identity"]["input_image_path"], str(path.resolve()))

    def test_cache_returns_one_existing_primary_image(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); image = root / "ref.png"; image.write_bytes(b"image")
            payload = prepare_identity.assemble("wine label", evidence(str(image)))
            research_cache.put(root / "cache", payload)
            hit = research_cache.get(root / "cache", "red wine", "label")
            self.assertIsNotNone(hit); self.assertEqual(hit["reference_mode"], "cache-reuse")
            self.assertEqual(len(hit["selected_references"]), 1); self.assertEqual(len(hit["valid_image_paths"]), 1)

    def test_title_analysis_is_deduplicated_and_excludes_sales_noise(self):
        result = analyze_titles.analyze(["Hot Sale Custom Gold Foil Wine Label", "Factory Custom Gold Wine Bottle Label", "OEM Gold Foil Wine Label"], "Wine", "Label")
        self.assertIn("gold", result["hot_terms"]); self.assertNotIn("factory", result["hot_terms"])
        self.assertEqual(len(result["detail_page_keywords"]), len({item.lower() for item in result["detail_page_keywords"]}))

    def test_physical_qa_requires_every_gate(self):
        record = physical_qa.create(prepare_identity.assemble("wine label", evidence("ref.png")))
        with self.assertRaises(ValueError): physical_qa.validate(record)
        for gate in record["gates"].values(): gate["status"] = "pass"
        record["passed"] = True
        self.assertTrue(physical_qa.validate(record)["valid"])


if __name__ == "__main__":
    unittest.main()
