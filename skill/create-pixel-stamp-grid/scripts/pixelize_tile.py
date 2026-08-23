#!/usr/bin/env python3
"""Square-crop and enforce a true logical pixel grid and optional shared palette."""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps


def parse_hex(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def square_crop(image, focus_x, focus_y):
    width, height = image.size
    side = min(width, height)
    cx, cy = focus_x * width, focus_y * height
    left = max(0, min(width - side, round(cx - side / 2)))
    top = max(0, min(height - side, round(cy - side / 2)))
    return image.crop((left, top, left + side, top + side))


def palette_image(colors):
    pal = Image.new("P", (1, 1))
    flat = [channel for color in colors for channel in color]
    pal.putpalette(flat + [0] * (768 - len(flat)))
    return pal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--logical-size", type=int, default=52)
    parser.add_argument("--output-size", type=int, default=676)
    parser.add_argument("--focus-x", type=float, default=0.5)
    parser.add_argument("--focus-y", type=float, default=0.5)
    parser.add_argument("--palette-json")
    args = parser.parse_args()

    image = ImageOps.exif_transpose(Image.open(args.input)).convert("RGB")
    image = square_crop(image, args.focus_x, args.focus_y)
    logical = image.resize((args.logical_size, args.logical_size), Image.Resampling.LANCZOS)
    if args.palette_json:
        data = json.loads(Path(args.palette_json).read_text(encoding="utf-8"))
        colors = [parse_hex(value) for value in data["shared_palette"]]
        logical = logical.quantize(palette=palette_image(colors), dither=Image.Dither.NONE).convert("RGB")
    else:
        logical = logical.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    logical.resize((args.output_size, args.output_size), Image.Resampling.NEAREST).save(args.output)


if __name__ == "__main__":
    main()
