#!/usr/bin/env python3
"""Validate the deterministic six-image delivery contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


EXPECTED = (
    ("01-hero-native.png", "01-hero-950.png"),
    ("02-showcase-native.png", "02-showcase-950.png"),
    ("03-details-native.png", "03-details-950.png"),
    ("04-usage-native.png", "04-usage-950.png"),
    ("05-artwork-native.png", "05-artwork-950.png"),
    ("06-multi-angle-native.png", "06-multi-angle-950.png"),
)


def validate(output_dir: Path, prompt_manifest_path: Path, physical_qa_path: Path | None = None) -> dict:
    errors: list[str] = []
    native_dir = output_dir / "native"
    prompt_manifest = json.loads(prompt_manifest_path.read_text(encoding="utf-8"))
    output_manifest_path = output_dir / "output_manifest.json"
    if not output_manifest_path.is_file():
        errors.append("missing output_manifest.json")
        output_manifest = {"outputs": []}
    else:
        output_manifest = json.loads(output_manifest_path.read_text(encoding="utf-8"))

    prompt_rows = prompt_manifest.get("prompts", [])
    if prompt_manifest.get("schema_version") != "2.0" or prompt_manifest.get("positive_negative_separated") is not True:
        errors.append("prompt manifest must use separated positive/negative schema 2.0")
    if prompt_manifest.get("prompt_count") != 6 or len(prompt_rows) != 6:
        errors.append("prompt manifest must contain exactly six roles")
    actual_finals = sorted(path.name for path in output_dir.glob("*.png"))
    expected_finals = [final for _, final in EXPECTED]
    if actual_finals != sorted(expected_finals):
        errors.append(f"final PNG set mismatch: {actual_finals}")

    manifest_pairs = {(row.get("native_file"), row.get("final_file")) for row in prompt_rows}
    for row in prompt_rows:
        role_number = row.get("role_number")
        positive_name = row.get("positive_prompt_file")
        negative_name = row.get("negative_prompt_file")
        for label, filename in (("positive", positive_name), ("negative", negative_name)):
            if not isinstance(filename, str) or not filename:
                errors.append(f"role {role_number} missing {label} prompt mapping")
                continue
            path = prompt_manifest_path.parent / filename
            if not path.is_file() or not path.read_text(encoding="utf-8").strip():
                errors.append(f"role {role_number} missing or empty {label} prompt file: {filename}")
        if isinstance(positive_name, str) and (prompt_manifest_path.parent / positive_name).is_file():
            positive_text = (prompt_manifest_path.parent / positive_name).read_text(encoding="utf-8")
            if "Your Logo" not in positive_text:
                errors.append(f"role {role_number} positive prompt missing Your Logo lock")
            if role_number == 2 and "customized Solution" not in positive_text:
                errors.append("role 2 positive prompt missing customized Solution lock")
    output_rows = output_manifest.get("outputs", [])
    output_final_names = [row.get("final_file") for row in output_rows]
    if len(output_rows) != 6 or sorted(output_final_names) != sorted(expected_finals):
        errors.append("output manifest must map exactly six final files")

    for native_name, final_name in EXPECTED:
        if (native_name, final_name) not in manifest_pairs:
            errors.append(f"prompt manifest missing mapping {native_name} -> {final_name}")
        native_path = native_dir / native_name
        final_path = output_dir / final_name
        if not native_path.is_file():
            errors.append(f"missing native image: {native_name}")
        if not final_path.is_file():
            errors.append(f"missing final image: {final_name}")
            continue
        try:
            with Image.open(final_path) as image:
                image.load()
                if image.format != "PNG":
                    errors.append(f"wrong format: {final_name} is {image.format}")
                if image.size != (950, 950):
                    errors.append(f"wrong size: {final_name} is {image.width}x{image.height}")
        except Exception as exc:  # Pillow supplies useful corruption details.
            errors.append(f"cannot read {final_name}: {exc}")

    if physical_qa_path is not None:
        if not physical_qa_path.is_file():
            errors.append("missing physical QA record")
        else:
            qa = json.loads(physical_qa_path.read_text(encoding="utf-8"))
            pending = [name for name, gate in qa.get("gates", {}).items() if gate.get("status") not in {"pass", "not_applicable"}]
            if pending or qa.get("passed") is not True:
                errors.append(f"physical QA not passed: {pending}")

    result = {
        "valid": not errors,
        "checked_roles": 6,
        "prompt_text_contract_checked": True,
        "automated_image_text_check": False,
        "visual_qc_required": physical_qa_path is None,
        "physical_qa_checked": physical_qa_path is not None,
        "errors": errors,
    }
    if errors:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--prompt-manifest", required=True, type=Path)
    parser.add_argument("--physical-qa", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.output_dir, args.prompt_manifest, args.physical_qa), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
