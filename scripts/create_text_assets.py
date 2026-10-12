#!/usr/bin/env python3
"""Create neutral spelling-reference assets for the two required text locks."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_asset(path: Path, text: str, font_path: str, font_size: int) -> None:
    image = Image.new("RGB", (1200, 600), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    x = (image.width - (right - left)) / 2 - left
    y = (image.height - (bottom - top)) / 2 - top
    draw.text((x, y), text, font=font, fill="black")
    image.save(path, format="PNG", optimize=True)


def main() -> None:
    assets = Path(__file__).resolve().parents[1] / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    create_asset(assets / "your-logo-text-lock.png", "Your Logo", r"C:\Windows\Fonts\arialbd.ttf", 170)
    create_asset(assets / "customized-solution-text-lock.png", "customized Solution", r"C:\Windows\Fonts\arial.ttf", 108)


if __name__ == "__main__":
    main()
