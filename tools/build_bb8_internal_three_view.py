#!/usr/bin/env python3
"""Build a labelled internal front/side/top sheet from current Blender renders."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "blender" / "output"
SOURCES = ("internal_front.png", "internal_side.png", "internal_top.png")
LABELS = ("INTERNAL FRONT", "INTERNAL SIDE", "INTERNAL TOP")
TARGET = OUTPUT / "BB8_internal_three_view.png"


def font(size):
    for candidate in ("/System/Library/Fonts/Helvetica.ttc",
                      "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


images = [Image.open(OUTPUT / source).convert("RGB") for source in SOURCES]
if any(image.size != (900, 900) for image in images):
    raise SystemExit(f"Expected three 900x900 renders, got {[image.size for image in images]}")

border, header, gap = 8, 64, 6
width = border * 2 + 900 * 3 + gap * 2
height = border * 2 + header + 900
sheet = Image.new("RGB", (width, height), "#111617")
draw = ImageDraw.Draw(sheet)
draw.rectangle((0, 0, width - 1, height - 1), outline="#ff4b13", width=border)
label_font = font(25)
for index, (image, label) in enumerate(zip(images, LABELS)):
    x = border + index * (900 + gap)
    sheet.paste(image, (x, border + header))
    bounds = draw.textbbox((0, 0), label, font=label_font)
    draw.text((x + (900 - (bounds[2] - bounds[0])) / 2, border + 17),
              label, fill="#f2f2ef", font=label_font)
sheet.save(TARGET, optimize=True)
print(f"PASS internal_three_view={TARGET} size={sheet.width}x{sheet.height}")
