#!/usr/bin/env python3
"""Compose four square tiles into deterministic 3:4 pixel-stamp posters."""

import argparse
import colorsys
import json
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


DEFAULT_TITLE_FONT = Path(__file__).resolve().parent.parent / "assets" / "Allura-Regular.ttf"


def parse_hex(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def background_specs(palette_json):
    data = json.loads(Path(palette_json).read_text(encoding="utf-8"))
    dominant = data.get("dominant_backgrounds", [])
    if len(dominant) < 2:
        raise ValueError("Palette JSON must contain primary and secondary dominant backgrounds")
    by_role = {item["role"]: item for item in dominant}
    if "primary" not in by_role or "secondary" not in by_role:
        raise ValueError("Palette JSON must label dominant backgrounds as primary and secondary")
    return [
        {**by_role["primary"], "mode": "dots", "filename": "pixel-stamp-primary-dots.png"},
        {**by_role["secondary"], "mode": "stripes", "filename": "pixel-stamp-secondary-stripes.png"},
    ]


def relative_luminance(rgb):
    channels = []
    for value in rgb:
        channel = value / 255
        channels.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(first, second):
    light, dark = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def background_family(base, accent):
    mixed = tuple(round((base[i] + accent[i]) / 2) for i in range(3))
    hue, saturation, _ = colorsys.rgb_to_hsv(*(value / 255 for value in mixed))
    degrees = hue * 360
    if saturation < 0.08:
        return "neutral"
    if degrees < 25 or degrees >= 315:
        return "pink-red"
    if degrees < 75:
        return "yellow-warm"
    if degrees < 175:
        return "mint-green"
    if degrees < 240:
        return "sky-blue"
    return "lavender-purple"


def choose_title_color(base, accent, requested="auto", floor=1.9, target=2.7, ceiling=3.6):
    family = background_family(base, accent)
    candidates = {
        "yellow-warm": ["#239DBA", "#2AA8C4", "#2492AE"],
        "sky-blue": ["#D9618D", "#C96B8D", "#DE6C96"],
        "mint-green": ["#DE6C96", "#D9618D", "#C96B8D"],
        "pink-red": ["#4D94C6", "#438BBC", "#239DBA"],
        "lavender-purple": ["#2D9691", "#3B9D98", "#239DBA"],
        "neutral": ["#239DBA", "#C96B8D", "#4D94C6"],
    }[family]
    if requested != "auto":
        candidates = [requested]
    scored = []
    for value in candidates:
        rgb = parse_hex(value)
        base_ratio = contrast_ratio(rgb, base)
        accent_ratio = contrast_ratio(rgb, accent)
        minimum_ratio = min(base_ratio, accent_ratio)
        average_ratio = (base_ratio + accent_ratio) / 2
        scored.append((minimum_ratio, average_ratio, base_ratio, accent_ratio, value, rgb))
    passing = [item for item in scored if item[0] >= floor and item[1] <= ceiling]
    if requested != "auto" and not passing:
        item = scored[0]
        raise ValueError(
            f"Requested title color {requested} is outside the decorative contrast band: "
            f"minimum {item[0]:.2f}, average {item[1]:.2f}; expected minimum >= {floor:.1f} "
            f"and average <= {ceiling:.1f}"
        )
    if passing:
        # Family ordering carries the intended hue relationship; the band only
        # rejects ink that is too faint or too visually heavy.
        minimum_ratio, average_ratio, base_ratio, accent_ratio, value, rgb = passing[0]
    else:
        # Custom backgrounds may fall outside the curated high-key palette.
        # Pick the candidate nearest the visual target instead of forcing black.
        minimum_ratio, average_ratio, base_ratio, accent_ratio, value, rgb = min(
            scored, key=lambda item: abs(item[1] - target) + abs(item[2] - item[3]) * 0.2
        )
    contrast = {
        "base": round(base_ratio, 2),
        "accent": round(accent_ratio, 2),
        "minimum": round(minimum_ratio, 2),
        "average": round(average_ratio, 2),
        "mode": "soft-decorative",
    }
    return rgb, value.upper(), contrast, family


def add_vintage_texture(image, strength, seed=20260821):
    if strength <= 0:
        return image
    rng = random.Random(seed)
    low_size = (max(24, image.width // 24), max(24, image.height // 24))
    noise = Image.new("L", low_size)
    noise.putdata([rng.randint(112, 144) for _ in range(low_size[0] * low_size[1])])
    noise = noise.resize(image.size, Image.Resampling.BICUBIC).convert("RGB")
    textured = ImageChops.soft_light(image, noise)
    return Image.blend(image, textured, min(max(strength, 0), 0.3))


def background(size, mode, base, accent, stripe_count=18, texture_strength=0.025):
    image = Image.new("RGB", size, base)
    draw = ImageDraw.Draw(image)
    width, height = size
    if mode == "dots":
        radius, spacing = max(7, width // 180), max(52, width // 28)
        for row, y in enumerate(range(spacing // 2, height, spacing)):
            shift = spacing // 2 if row % 2 else 0
            for x in range(spacing // 2 + shift, width, spacing):
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=accent)
    elif mode == "stripes":
        for index in range(stripe_count):
            left = round(index * width / stripe_count)
            right = round((index + 1) * width / stripe_count)
            draw.rectangle((left, 0, right, height), fill=accent if index % 2 else base)
    return add_vintage_texture(image, texture_strength)


def make_stamp(tile, outer=720, border=40, scallop_count=12):
    tile_size = outer - border * 2
    source = ImageOps.fit(Image.open(tile).convert("RGB"), (tile_size, tile_size), method=Image.Resampling.NEAREST)
    mask = Image.new("L", (outer, outer), 0)
    draw = ImageDraw.Draw(mask)
    diameter = outer / scallop_count
    radius = diameter / 2
    draw.rectangle((radius, radius, outer - radius, outer - radius), fill=255)
    for index in range(scallop_count):
        center = (index + 0.5) * diameter
        box_top = (center - radius, 0, center + radius, radius * 2)
        box_bottom = (center - radius, outer - radius * 2, center + radius, outer)
        box_left = (0, center - radius, radius * 2, center + radius)
        box_right = (outer - radius * 2, center - radius, outer, center + radius)
        draw.ellipse(tuple(round(value) for value in box_top), fill=255)
        draw.ellipse(tuple(round(value) for value in box_bottom), fill=255)
        draw.ellipse(tuple(round(value) for value in box_left), fill=255)
        draw.ellipse(tuple(round(value) for value in box_right), fill=255)
    stamp = Image.new("RGBA", (outer, outer), (255, 255, 255, 0))
    white = Image.new("RGBA", (outer, outer), "white")
    stamp.paste(white, mask=mask)
    stamp.paste(source, (border, border))
    return stamp


def fit_font(text, font_path, max_width, start_size):
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    for size in range(start_size, 71, -4):
        font = ImageFont.truetype(str(font_path), size)
        box = probe.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= max_width:
            return font
    return ImageFont.truetype(str(font_path), 72)


def draw_theme_title(poster, title, font_path, color):
    words = title.split()
    if len(words) != 3:
        raise ValueError("Theme title must contain exactly three words")
    if not font_path.exists():
        raise FileNotFoundError(f"Title font not found: {font_path}")

    draw = ImageDraw.Draw(poster)
    lines = (words[0], " ".join(words[1:]))
    specs = (
        (285, 1910, 980, 250),
        (470, 2125, 1400, 225),
    )
    for text, (x, y, max_width, start_size) in zip(lines, specs):
        font = fit_font(text, font_path, max_width, start_size)
        box = draw.textbbox((0, 0), text, font=font)
        draw.text((x - box[0], y - box[1]), text, font=font, fill=color)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tiles", nargs=4)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--palette-json", required=True, help="Palette report containing primary and secondary background colors")
    parser.add_argument("--scallops-per-side", type=int, default=12)
    parser.add_argument("--stripe-count", type=int, default=18)
    parser.add_argument("--texture-strength", type=float, default=0.025)
    parser.add_argument("--title", help="Validated three-word English display title")
    parser.add_argument("--title-font", default=str(DEFAULT_TITLE_FONT))
    parser.add_argument("--title-color", default="auto", help="auto selects a harmonious ink in the soft decorative contrast band")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    specs = background_specs(args.palette_json)
    stamps = [make_stamp(path, scallop_count=args.scallops_per_side) for path in args.tiles]
    canvas_size = (2048, 2732)
    outer, gap, top = 720, 76, 270
    group = outer * 2 + gap
    left = (canvas_size[0] - group) // 2
    positions = [(left, top), (left + outer + gap, top), (left, top + outer + gap), (left + outer + gap, top + outer + gap)]

    manifest = []
    for spec in specs:
        mode = spec["mode"]
        base = parse_hex(spec["base_color"])
        accent = parse_hex(spec["accent_color"])
        poster = background(
            canvas_size,
            mode,
            base,
            accent,
            stripe_count=args.stripe_count,
            texture_strength=args.texture_strength,
        ).convert("RGBA")
        for stamp, position in zip(stamps, positions):
            poster.alpha_composite(stamp, position)
        title_color = None
        title_contrast = None
        family = background_family(base, accent)
        if args.title:
            rgb, title_color, title_contrast, family = choose_title_color(base, accent, args.title_color)
            draw_theme_title(poster, args.title, Path(args.title_font), rgb)
        poster.convert("RGB").save(output_dir / spec["filename"], quality=95)
        manifest.append({
            "filename": spec["filename"],
            "background": mode,
            "color_rank": spec["role"],
            "source_color": spec["source_color"],
            "source_color_score": spec["score"],
            "source_image_support": spec["image_support"],
            "base_color": "#%02X%02X%02X" % base,
            "accent_color": "#%02X%02X%02X" % accent,
            "background_family": family,
            "title": args.title,
            "title_color": title_color,
            "title_contrast": title_contrast,
        })
    (output_dir / "composition-manifest.json").write_text(json.dumps({"outputs": manifest}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
