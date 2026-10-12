#!/usr/bin/env python3
"""Build six separate positive and negative packaging-image prompts from Markdown rules."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROLE_FILES = (
    (1, "hero", "01_hero.txt", "01-hero-native.png", "01-hero-950.png"),
    (2, "showcase", "02_showcase.txt", "02-showcase-native.png", "02-showcase-950.png"),
    (3, "details", "03_details.txt", "03-details-native.png", "03-details-950.png"),
    (4, "usage", "04_usage.txt", "04-usage-native.png", "04-usage-950.png"),
    (5, "artwork", "05_artwork.txt", "05-artwork-native.png", "05-artwork-950.png"),
    (6, "multi_angle", "06_multi_angle.txt", "06-multi-angle-native.png", "06-multi-angle-950.png"),
)

CATEGORY_FILES = {
    "label": "label.md",
    "sticker": "sticker.md",
    "box": "box.md",
    "other": "other_packaging.md",
}

IDENTITY_FIELDS = (
    "schema_version", "input_mode", "reference_mode", "raw_input", "product", "packaging_type",
    "normalized_category", "normalized_product_title", "detail_page_keywords", "requested_materials",
    "material_source", "visual_identity", "required_text", "title_text",
    "forbidden_content", "selected_references",
)

VISUAL_FIELDS = (
    "container_shape", "closure", "materials", "label_shape",
    "print_location", "palette", "finishes", "physical_dimensions", "structure_states",
)


def parse_text_blocks(path: Path, expected: list[str]) -> dict[str, str]:
    source = path.read_text(encoding="utf-8")
    found: dict[str, str] = {}
    for name in expected:
        heading_count = len(re.findall(rf"(?m)^## {re.escape(name)}\s*$", source))
        pattern = rf"(?ms)^## {re.escape(name)}\s*\n+```text\s*\n(.*?)\n```\s*(?=^## |\Z)"
        blocks = re.findall(pattern, source)
        if heading_count != 1 or len(blocks) != 1 or not blocks[0].strip():
            raise ValueError(f"block '{name}' in {path.name} must appear exactly once as a non-empty text code block")
        found[name] = " ".join(blocks[0].split())
    machine_headings = re.findall(r"(?m)^## (common|role_[1-6])\s*$", source)
    if sorted(machine_headings) != sorted(expected):
        raise ValueError(f"unexpected, missing, or duplicate machine-readable headings in {path.name}")
    return found


def load_rules(skill_root: Path, category: str) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    references = skill_root / "references"
    full = ["common", *(f"role_{number}" for number in range(1, 7))]
    category_blocks = ["common", "role_2", "role_4", "role_5", "role_6"]
    positive = parse_text_blocks(references / "image_construction.md", full)
    category_positive = parse_text_blocks(references / CATEGORY_FILES[category], category_blocks)
    negative = parse_text_blocks(references / "negative_prompt.md", full)
    return positive, category_positive, negative


def _require_list(data: dict, field: str) -> list:
    value = data.get(field)
    if not isinstance(value, list):
        raise ValueError(f"identity field '{field}' must be an array")
    return value


def load_identity(path: Path, category: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [field for field in IDENTITY_FIELDS if field not in data]
    if missing:
        raise ValueError(f"identity.json missing required fields: {', '.join(missing)}")
    if data["schema_version"] != "4.1":
        raise ValueError("schema_version must be '4.1'")
    if data["input_mode"] not in {"text", "image", "url"}:
        raise ValueError("input_mode must be text, image, or url")
    if data["reference_mode"] not in {"researched", "direct-link", "cache-reuse"}:
        raise ValueError("reference_mode must be researched, direct-link, or cache-reuse")
    if data["input_mode"] == "url" and data["reference_mode"] != "direct-link":
        raise ValueError("url input requires reference_mode direct-link")
    if data["normalized_category"] != category:
        raise ValueError("normalized_category does not match --category")
    if not str(data["normalized_product_title"]).strip():
        raise ValueError("normalized_product_title must be non-empty")
    requested = _require_list(data, "requested_materials")
    forbidden = _require_list(data, "forbidden_content")
    keywords = _require_list(data, "detail_page_keywords")
    refs = _require_list(data, "selected_references")
    if data["material_source"] not in {"user", "research", "inferred"}:
        raise ValueError("material_source must be user, research, or inferred")
    if requested and data["material_source"] != "user":
        raise ValueError("non-empty requested_materials requires material_source 'user'")
    if data["required_text"] != "Your Logo":
        raise ValueError("required_text must be exactly 'Your Logo'")
    if data["title_text"] != "customized Solution":
        raise ValueError("title_text must be exactly 'customized Solution'")
    if not forbidden:
        raise ValueError("forbidden_content must be non-empty")
    if not keywords:
        raise ValueError("detail_page_keywords must be non-empty")

    visual = data["visual_identity"]
    if not isinstance(visual, dict):
        raise ValueError("visual_identity must be an object")
    missing_visual = [field for field in VISUAL_FIELDS if field not in visual]
    if missing_visual:
        raise ValueError(f"visual_identity missing fields: {', '.join(missing_visual)}")
    for field in ("materials", "palette", "finishes", "structure_states"):
        if not isinstance(visual[field], list):
            raise ValueError(f"visual_identity.{field} must be an array")
    if requested:
        resolved = {str(item).strip().lower() for item in visual["materials"]}
        missing_requested = [item for item in requested if str(item).strip().lower() not in resolved]
        if missing_requested:
            raise ValueError("visual_identity.materials must preserve every requested material")

    mode = data["reference_mode"]
    expected_counts = {"researched": {3}, "direct-link": {1}, "cache-reuse": {1, 2, 3}}
    if len(refs) not in expected_counts[mode]:
        raise ValueError(f"selected_references count is invalid for reference_mode {mode}")
    required_ref = {"title", "url", "sold_count", "sold_rank", "title_valid", "image_valid", "role", "image_paths"}
    ranks, roles, image_paths = [], [], []
    for index, ref in enumerate(refs, 1):
        absent = sorted(required_ref - set(ref))
        if absent:
            raise ValueError(f"reference {index} missing fields: {', '.join(absent)}")
        minimum_sales = 100 if mode in {"researched", "cache-reuse"} else 0
        if not isinstance(ref["sold_count"], int) or ref["sold_count"] < minimum_sales:
            raise ValueError(f"reference {index} sold_count must be an integer >= {minimum_sales}")
        if not isinstance(ref["sold_rank"], int):
            raise ValueError(f"reference {index} sold_rank must be an integer")
        if ref["title_valid"] is not True or ref["image_valid"] is not True:
            raise ValueError(f"reference {index} must pass title and image gates")
        if not isinstance(ref["image_paths"], list) or not ref["image_paths"]:
            raise ValueError(f"reference {index} image_paths must be a non-empty array")
        ranks.append(ref["sold_rank"])
        roles.append(ref["role"])
        image_paths.extend(str(item) for item in ref["image_paths"])
    if mode == "researched" and sorted(ranks) != [1, 2, 3]:
        raise ValueError("researched reference sold_rank values must be exactly 1, 2, and 3")
    if mode == "researched" and set(roles) != {"primary", "secondary", "tertiary"}:
        raise ValueError("researched reference roles must be primary, secondary, and tertiary")
    if mode == "direct-link" and (ranks != [1] or roles != ["primary"]):
        raise ValueError("direct-link reference must be rank 1 with role primary")
    if len(set(image_paths)) > 5:
        raise ValueError("selected references exceed the five-image budget")
    return data


def compact(values: list) -> str:
    return ", ".join(str(value) for value in values) if values else "none"


def identity_text(identity: dict, role_number: int) -> str:
    visual = identity["visual_identity"]
    if role_number == 1:
        return "\n".join((
            f"Product identity: {identity['normalized_product_title']}",
            f"Packaging category: {identity['normalized_category']}",
            f"Container: {visual['container_shape']}",
            f"Closure or opening: {visual['closure']}",
            f"Resolved materials: {compact(visual['materials'])}",
            f"Label or print shape: {visual['label_shape']}",
            f"Print location: {visual['print_location']}",
            f"Palette: {compact(visual['palette'])}",
            f"Finishes: {compact(visual['finishes'])}",
            f"Physical dimensions or proportions: {visual['physical_dimensions']}",
            f"Physical structure states: {compact(visual['structure_states'])}",
        ))
    return (
        "Use Image 1, the approved hero, as the identity anchor. Preserve: "
        f"{visual['container_shape']}; {visual['closure']}; {compact(visual['materials'])}; "
        f"{visual['label_shape']} at {visual['print_location']}; {compact(visual['palette'])}; "
        f"{compact(visual['finishes'])}; {visual['physical_dimensions']}; {compact(visual['structure_states'])}."
    )


def unique_reference_paths(identity: dict) -> list[str]:
    return list(dict.fromkeys(str(path) for ref in identity["selected_references"] for path in ref["image_paths"]))


def asset_plan(identity: dict, role_number: int, skill_root: Path) -> list[dict[str, str]]:
    logo = str((skill_root / "assets" / "your-logo-text-lock.png").resolve())
    title = str((skill_root / "assets" / "customized-solution-text-lock.png").resolve())
    references = unique_reference_paths(identity)
    if role_number == 1:
        return [{"role": "alibaba_reference", "path": path} for path in references] + [{"role": "your_logo_asset", "path": logo}]
    plan = [{"role": "approved_hero", "path": "<task-output>/native/01-hero-native.png"}, {"role": "your_logo_asset", "path": logo}]
    if role_number == 2:
        plan.append({"role": "title_asset", "path": title})
    if role_number in {2, 5} and references:
        plan.append({"role": "primary_reference", "path": references[0]})
    return plan


def reference_text(plan: list[dict[str, str]]) -> str:
    labels = {
        "alibaba_reference": "Alibaba structure/material/print reference",
        "approved_hero": "approved hero identity anchor", "your_logo_asset": "neutral Your Logo spelling asset",
        "title_asset": "neutral customized Solution spelling asset",
        "primary_reference": "primary product reference; use print detail only when visibly supported",
    }
    return "\n".join(f"Image {index}: {labels[item['role']]} ({item['role']})." for index, item in enumerate(plan, 1))


def material_lock(identity: dict, role_number: int) -> str:
    if role_number != 3:
        return ""
    requested = identity["requested_materials"]
    if requested:
        return (
            "USER MATERIAL LOCK: At least one grid panel must clearly and recognizably show "
            f"the exact user-requested material: {compact(requested)}. Do not substitute a generic or similar material."
        )
    return f"MATERIAL DETAIL: At least one grid panel must clearly show the resolved material: {compact(identity['visual_identity']['materials'])}."


def text_locks(identity: dict, role_number: int) -> str:
    logo = (
        'Render exact case-sensitive text "Your Logo" at the visual center of every clearly visible main package presentation face. '
        "Keep it straight, legible, uncropped, and physically printed on the package; distant, rear, or severely foreshortened faces are exempt."
    )
    if role_number == 2:
        title = 'Render exact case-sensitive title "customized Solution" once in the clean top title zone without overlap.'
    else:
        title = "Add no headline or title text."
    return f"{logo}\n{title}"


def build_positive(identity: dict, category: str, role_number: int, positive: dict[str, str], category_rules: dict[str, str], plan: list[dict[str, str]]) -> str:
    category_role = category_rules.get(f"role_{role_number}", "")
    parts = [
        f"ROLE {role_number} OF 6: {ROLE_FILES[role_number - 1][1]}",
        "IDENTITY\n" + identity_text(identity, role_number),
        "INPUT IMAGE ROLES\n" + reference_text(plan),
        "POSITIVE IMAGE SPEC\n" + " ".join(filter(None, (positive["common"], category_rules["common"], positive[f"role_{role_number}"], category_role))),
    ]
    lock = material_lock(identity, role_number)
    if lock:
        parts.append(lock)
    parts.append("TEXT LOCKS\n" + text_locks(identity, role_number))
    parts.append("Output one 1:1 image intended for lossless resize to 950 × 950 PNG without cropping.")
    prompt = "\n\n".join(parts) + "\n"
    if "Your Logo" not in prompt:
        raise AssertionError("required logo text missing from positive prompt")
    if role_number == 2 and "customized Solution" not in prompt:
        raise AssertionError("role 2 title missing from positive prompt")
    if role_number == 3 and identity["requested_materials"]:
        for item in identity["requested_materials"]:
            if str(item) not in prompt:
                raise AssertionError("requested material missing from role 3 prompt")
    return prompt


def build_negative(identity: dict, role_number: int, negative: dict[str, str]) -> str:
    return f"{negative['common']}, {negative[f'role_{role_number}']}, {compact(identity['forbidden_content'])}\n"


def run(identity_path: Path, category: str, out_dir: Path, skill_root: Path, verify_reference_files: bool = False) -> Path:
    identity = load_identity(identity_path, category)
    positive, category_rules, negative = load_rules(skill_root, category)
    positive_dir, negative_dir = out_dir / "positive", out_dir / "negative"
    positive_dir.mkdir(parents=True, exist_ok=True)
    negative_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for number, role, filename, native_name, final_name in ROLE_FILES:
        plan = asset_plan(identity, number, skill_root)
        if verify_reference_files:
            missing = [item["path"] for item in plan if item["role"] not in {"approved_hero"} and not Path(item["path"]).is_file()]
            if missing:
                raise FileNotFoundError(f"missing input assets for role {number}: {', '.join(missing)}")
        (positive_dir / filename).write_text(build_positive(identity, category, number, positive, category_rules, plan), encoding="utf-8")
        (negative_dir / filename).write_text(build_negative(identity, number, negative), encoding="utf-8")
        reference_roles = [item["role"] for item in plan]
        rows.append({
            "role_number": number,
            "role": role,
            "positive_prompt_file": f"positive/{filename}",
            "negative_prompt_file": f"negative/{filename}",
            "native_file": native_name,
            "final_file": final_name,
            "reference_roles": reference_roles,
            "input_assets": plan,
            "requires_logo_text": True,
            "requires_title_text": number == 2,
            "max_retries": 2 if number in (1, 2) else 1,
        })
    manifest = {
        "schema_version": "2.0",
        "identity_file": str(identity_path.resolve()),
        "category": category,
        "prompt_count": 6,
        "positive_negative_separated": True,
        "prompts": rows,
    }
    manifest_path = out_dir / "prompt_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity", required=True, type=Path)
    parser.add_argument("--category", required=True, choices=tuple(CATEGORY_FILES))
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--verify-reference-files", action="store_true")
    args = parser.parse_args()
    print(run(args.identity, args.category, args.out_dir, args.skill_root, args.verify_reference_files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
