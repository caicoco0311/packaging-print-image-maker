#!/usr/bin/env python3
"""Route text, image, or URL input and assemble a prompt-ready identity.json."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse


URL_RE = re.compile(r"^https?://", re.I)
CATEGORY_ALIASES = {
    "label": ("label", "标签", "標籤"),
    "sticker": ("sticker", "贴纸", "貼紙"),
    "box": ("box", "carton", "盒", "箱"),
    "other": ("pouch", "bag", "bottle", "tube", "jar", "can", "袋", "瓶", "管", "罐"),
}


def detect_input_mode(raw_input: str, image_path: Path | None = None) -> str:
    if image_path is not None:
        return "image"
    if URL_RE.match(raw_input.strip()):
        return "url"
    return "text"


def normalize_category(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in CATEGORY_ALIASES:
        return lowered
    for category, aliases in CATEGORY_ALIASES.items():
        if any(alias.lower() in lowered for alias in aliases):
            return category
    raise ValueError("cannot normalize packaging category; provide normalized_category in evidence JSON")


def _list(evidence: dict, name: str, default=None) -> list:
    value = evidence.get(name, [] if default is None else default)
    if not isinstance(value, list):
        raise ValueError(f"evidence field {name} must be an array")
    return value


def assemble(raw_input: str, evidence: dict, image_path: Path | None = None) -> dict:
    mode = detect_input_mode(raw_input, image_path)
    if image_path is not None:
        image_path = image_path.resolve()
        if not image_path.is_file():
            raise FileNotFoundError(f"input image does not exist: {image_path}")
    if mode == "url":
        parsed = urlparse(raw_input.strip())
        if not parsed.netloc:
            raise ValueError("URL input must contain a host")

    category = normalize_category(str(evidence.get("normalized_category") or evidence.get("packaging_type", "")))
    requested = _list(evidence, "requested_materials")
    references = _list(evidence, "selected_references")
    reference_mode = "direct-link" if mode == "url" else str(evidence.get("reference_mode", "researched"))
    if mode == "url" and not references:
        image_paths = _list(evidence, "image_paths")
        references = [{
            "title": str(evidence.get("source_title", evidence.get("normalized_product_title", "Direct product link"))),
            "url": raw_input.strip(), "sold_count": int(evidence.get("sold_count", 0)), "sold_rank": 1,
            "title_valid": True, "image_valid": bool(image_paths), "role": "primary", "image_paths": image_paths,
        }]
    visual = evidence.get("visual_identity")
    if not isinstance(visual, dict):
        raise ValueError("evidence.visual_identity must be an object")
    if image_path is not None:
        visual = {**visual, "input_image_path": str(image_path)}

    return {
        "schema_version": "4.1", "input_mode": mode, "reference_mode": reference_mode,
        "raw_input": raw_input, "product": str(evidence.get("product", "")).strip(),
        "packaging_type": str(evidence.get("packaging_type", category)).strip(),
        "normalized_category": category,
        "normalized_product_title": str(evidence.get("normalized_product_title", "")).strip(),
        "detail_page_keywords": _list(evidence, "detail_page_keywords"),
        "requested_materials": requested,
        "material_source": "user" if requested else str(evidence.get("material_source", "research" if references else "inferred")),
        "visual_identity": visual, "required_text": "Your Logo", "title_text": "customized Solution",
        "forbidden_content": _list(evidence, "forbidden_content", ["seller identity", "watermark", "contact information", "certification mark", "unsupported claim"]),
        "selected_references": references,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    identity = assemble(args.input, evidence, args.image)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
