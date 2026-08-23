#!/usr/bin/env python3
"""Render every curated background pair as a compact review board."""

import argparse

from PIL import Image, ImageDraw, ImageFont

from extract_palette import BACKGROUND_BANK, hex_color


def load_font(size):
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Pixel Stamp Background Bank")
    args = parser.parse_args()

    canvas = Image.new("RGB", (1200, 900), "#FFFDFB")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(44)
    label_font = load_font(28)
    hex_font = load_font(24)
    draw.text((70, 42), args.title, font=title_font, fill="#34343A")

    for row, (family, (base, accent)) in enumerate(BACKGROUND_BANK.items()):
        top = 125 + row * 145
        draw.text((70, top + 42), family, font=label_font, fill="#34343A")
        draw.rounded_rectangle((335, top, 690, top + 108), radius=26, fill=base)
        draw.rounded_rectangle((725, top, 1080, top + 108), radius=26, fill=accent)
        draw.text((455, top + 38), hex_color(base), font=hex_font, fill="#565B68")
        draw.text((845, top + 38), hex_color(accent), font=hex_font, fill="#565B68")

    canvas.save(args.output)


if __name__ == "__main__":
    main()
