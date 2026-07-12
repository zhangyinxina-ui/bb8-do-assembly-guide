#!/usr/bin/env python3
"""Build the BB-8 dimension sheet from the current orthographic renders."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "blender" / "output"
SOURCE_FILES = ("front.png", "side.png", "back.png")
TARGET = OUTPUT / "BB8_three_view_dimension_sheet.png"
LABELS = (
    "FRONT / BODY 508 mm",
    "SIDE / HEAD 295 mm",
    "BACK / HEIGHT 670 mm",
)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    images = [Image.open(OUTPUT / name).convert("RGB") for name in SOURCE_FILES]
    if any(image.size != (900, 1100) for image in images):
        sizes = ", ".join(f"{name}={image.size}" for name, image in zip(SOURCE_FILES, images))
        raise SystemExit(f"Unexpected render size; expected 900x1100: {sizes}")

    border = 8
    header_height = 64
    column_gap = 6
    width = border * 2 + 900 * 3 + column_gap * 2
    height = border * 2 + header_height + 1100
    sheet = Image.new("RGB", (width, height), "#111617")
    draw = ImageDraw.Draw(sheet)
    draw.rectangle((0, 0, width - 1, height - 1), outline="#ff4b13", width=border)
    draw.rectangle(
        (border, border, width - border - 1, border + header_height - 1),
        fill="#121718",
    )

    font = load_font(25)
    for index, (image, label) in enumerate(zip(images, LABELS)):
        x = border + index * (900 + column_gap)
        y = border + header_height
        sheet.paste(image, (x, y))
        box = draw.textbbox((0, 0), label, font=font)
        text_width = box[2] - box[0]
        draw.text(
            (x + (900 - text_width) / 2, border + 17),
            label,
            fill="#f2f2ef",
            font=font,
        )

    sheet.save(TARGET, optimize=True)
    print(f"PASS three_view_sheet={TARGET} size={sheet.width}x{sheet.height}")


if __name__ == "__main__":
    main()
