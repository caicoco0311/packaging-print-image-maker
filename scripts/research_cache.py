#!/usr/bin/env python3
"""Store and retrieve validated Alibaba research by normalized product and category."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def normalize(value: str) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", " ", value.lower()).strip()


def cache_key(product: str, category: str) -> str:
    normalized = f"{normalize(product)}|{normalize(category)}"
    if normalized == "|":
        raise ValueError("product and category cannot both be empty")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]


def _valid_images(references: list[dict]) -> list[str]:
    paths = []
    for ref in references:
        for value in ref.get("image_paths", []):
            path = Path(value)
            if path.is_file() and path.stat().st_size > 0:
                paths.append(str(path.resolve()))
    return list(dict.fromkeys(paths))


def put(cache_dir: Path, payload: dict) -> Path:
    refs = payload.get("selected_references")
    if not isinstance(refs, list) or not refs:
        raise ValueError("cache payload requires selected_references")
    images = _valid_images(refs)
    if not images:
        raise ValueError("cache payload has no existing local reference image")
    key = cache_key(str(payload.get("product", "")), str(payload.get("normalized_category", "")))
    record = {
        "schema_version": "1.0", "cache_key": key,
        "product": payload.get("product", ""), "normalized_category": payload.get("normalized_category", ""),
        "normalized_product_title": payload.get("normalized_product_title", ""),
        "detail_page_keywords": payload.get("detail_page_keywords", []),
        "visual_identity": payload.get("visual_identity", {}), "selected_references": refs,
        "valid_image_paths": images, "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    cache_dir.mkdir(parents=True, exist_ok=True)
    destination = cache_dir / f"{key}.json"
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def get(cache_dir: Path, product: str, category: str, output: Path | None = None) -> dict | None:
    path = cache_dir / f"{cache_key(product, category)}.json"
    if not path.is_file():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    images = [value for value in record.get("valid_image_paths", []) if Path(value).is_file() and Path(value).stat().st_size > 0]
    if not images:
        return None
    refs = record.get("selected_references", [])
    if not refs:
        return None
    primary = dict(refs[0])
    primary["image_paths"] = [images[0]]
    result = {**record, "reference_mode": "cache-reuse", "selected_references": [primary], "valid_image_paths": [images[0]]}
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    put_parser = sub.add_parser("put")
    put_parser.add_argument("--cache-dir", required=True, type=Path); put_parser.add_argument("--identity", required=True, type=Path)
    get_parser = sub.add_parser("get")
    get_parser.add_argument("--cache-dir", required=True, type=Path); get_parser.add_argument("--product", required=True); get_parser.add_argument("--category", required=True); get_parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "put":
        print(put(args.cache_dir, json.loads(args.identity.read_text(encoding="utf-8"))))
        return 0
    result = get(args.cache_dir, args.product, args.category, args.output)
    print(json.dumps({"hit": result is not None, "cache_key": cache_key(args.product, args.category)}, ensure_ascii=False))
    return 0 if result is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
