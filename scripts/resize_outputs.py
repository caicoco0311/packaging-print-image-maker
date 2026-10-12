#!/usr/bin/env python3
"""Resize six square native images to 950 x 950 PNG without cropping."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


FILE_PAIRS = (
    ("01-hero-native.png", "01-hero-950.png"),
    ("02-showcase-native.png", "02-showcase-950.png"),
    ("03-details-native.png", "03-details-950.png"),
    ("04-usage-native.png", "04-usage-950.png"),
    ("05-artwork-native.png", "05-artwork-950.png"),
    ("06-multi-angle-native.png", "06-multi-angle-950.png"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resize_all(native_dir: Path, out_dir: Path, size: int = 950) -> Path:
    if size <= 0:
        raise ValueError("size must be positive")
    missing = [name for name, _ in FILE_PAIRS if not (native_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing native images: {', '.join(missing)}")
    inspections = []
    for native_name, final_name in FILE_PAIRS:
        source = native_dir / native_name
        with Image.open(source) as image:
            image.load()
            if image.width != image.height:
                raise ValueError(f"non-square source rejected without cropping: {native_name} is {image.width}x{image.height}")
            inspections.append((source, final_name, image.width, image.height))
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for source, final_name, width, height in inspections:
        destination = out_dir / final_name
        with Image.open(source) as image:
            converted = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            resized = converted.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(destination, format="PNG", optimize=True)
        entries.append({
            "native_file": str(source.resolve()),
            "native_dimensions": [width, height],
            "native_sha256": sha256(source),
            "final_file": final_name,
            "final_dimensions": [size, size],
            "final_format": "PNG",
            "final_sha256": sha256(destination),
        })
    manifest = {"schema_version": "1.0", "resize_filter": "LANCZOS", "cropping": False, "outputs": entries}
    manifest_path = out_dir / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--size", type=int, default=950)
    args = parser.parse_args()
    print(resize_all(args.native_dir, args.out_dir, args.size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
