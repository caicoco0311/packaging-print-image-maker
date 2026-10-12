#!/usr/bin/env python3
"""Extract repeated Alibaba title terms and emit clean B2B listing metadata."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


STOP = {"oem", "odm", "new", "hot", "sale", "wholesale", "factory", "supplier", "manufacturer", "moq", "free", "shipping", "customized"}


def tokens(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 1 and word not in STOP]


def analyze(titles: list[str], product: str, packaging_type: str, attributes: list[str] | None = None) -> dict:
    clean_titles = [title.strip() for title in titles if title.strip()]
    if not clean_titles:
        raise ValueError("at least one non-empty title is required")
    counts = Counter(word for title in clean_titles for word in set(tokens(title)))
    ranked = sorted(counts, key=lambda word: (-counts[word], word))
    hot = [word for word in ranked if counts[word] >= 2][:12]
    explicit = [str(value).strip() for value in attributes or [] if str(value).strip()]
    title_words = ["Custom", *explicit[:3], product.strip(), packaging_type.strip()]
    listing_title = " ".join(dict.fromkeys(word for word in title_words if word)).strip()
    keywords = []
    bases = [listing_title, f"custom {product} {packaging_type}", *(f"{word} {packaging_type}" for word in hot)]
    for value in bases:
        normalized = " ".join(value.split()).strip()
        if normalized and normalized.lower() not in {item.lower() for item in keywords}:
            keywords.append(normalized)
    return {"normalized_product_title": listing_title, "detail_page_keywords": keywords[:12], "hot_terms": hot, "term_frequency": {word: counts[word] for word in ranked[:20]}, "source_title_count": len(clean_titles)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--titles", required=True, type=Path, help="JSON array or selected_references object")
    parser.add_argument("--product", required=True); parser.add_argument("--packaging-type", required=True)
    parser.add_argument("--attributes", nargs="*", default=[]); parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source = json.loads(args.titles.read_text(encoding="utf-8"))
    if isinstance(source, dict):
        source = [row.get("title", "") for row in source.get("selected_references", [])]
    result = analyze(source, args.product, args.packaging_type, args.attributes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
