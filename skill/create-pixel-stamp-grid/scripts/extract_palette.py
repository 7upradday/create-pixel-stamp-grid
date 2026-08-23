#!/usr/bin/env python3
"""Extract per-image and shared palettes from exactly four images."""

import argparse
import colorsys
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


BACKGROUND_BANK = {
    "pink-red": ((255, 227, 237), (248, 199, 217)),
    "yellow-warm": ((255, 243, 178), (255, 227, 113)),
    "mint-green": ((238, 249, 241), (191, 232, 208)),
    "sky-blue": ((227, 241, 251), (193, 228, 243)),
    "lavender-purple": ((246, 240, 250), (227, 210, 240)),
}

# Green and purple lose their identity quickly when a very pale fixed preset is
# used. Keep their source hue and impose a small chroma floor instead.
DYNAMIC_BACKGROUND = {
    "mint-green": {"base_saturation": 0.10, "base_value": 0.98, "accent_saturation": 0.28, "accent_value": 0.93},
    "lavender-purple": {"base_saturation": 0.10, "base_value": 0.99, "accent_saturation": 0.24, "accent_value": 0.94},
}

SECONDARY_FALLBACK = {
    "pink-red": "sky-blue",
    "yellow-warm": "sky-blue",
    "mint-green": "pink-red",
    "sky-blue": "pink-red",
    "lavender-purple": "mint-green",
}


def hex_color(rgb):
    return "#%02X%02X%02X" % tuple(rgb)


def distance(a, b):
    return sum((int(a[i]) - int(b[i])) ** 2 for i in range(3)) ** 0.5


def color_family(rgb):
    red, green, blue = (channel / 255 for channel in rgb)
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    degrees = hue * 360
    if saturation < 0.08 or value < 0.28:
        return None
    if degrees < 25 or degrees >= 315:
        return "pink-red"
    if degrees < 75:
        return "yellow-warm"
    if degrees < 175:
        return "mint-green"
    if degrees < 240:
        return "sky-blue"
    return "lavender-purple"


def hue_distance(first, second):
    first_hue = colorsys.rgb_to_hsv(*(channel / 255 for channel in first))[0] * 360
    second_hue = colorsys.rgb_to_hsv(*(channel / 255 for channel in second))[0] * 360
    delta = abs(first_hue - second_hue)
    return min(delta, 360 - delta)


def representative_color(entry):
    if not entry or entry[3] <= 0:
        return (128, 128, 128)
    return tuple(round(entry[channel] / entry[3]) for channel in range(3))


def hsv_color(hue, saturation, value):
    return tuple(round(channel * 255) for channel in colorsys.hsv_to_rgb(hue, saturation, value))


def background_pair(family, source):
    if family not in DYNAMIC_BACKGROUND:
        return BACKGROUND_BANK[family]
    hue = colorsys.rgb_to_hsv(*(channel / 255 for channel in source))[0]
    spec = DYNAMIC_BACKGROUND[family]
    return (
        hsv_color(hue, spec["base_saturation"], spec["base_value"]),
        hsv_color(hue, spec["accent_saturation"], spec["accent_value"]),
    )


def semantic_ramp(source, family):
    hue, source_saturation, _ = colorsys.rgb_to_hsv(*(channel / 255 for channel in source))
    floor = 0.42 if family in {"mint-green", "lavender-purple"} else 0.34
    steps = (
        (max(floor, source_saturation + 0.08), 0.42),
        (max(floor - 0.04, source_saturation), 0.58),
        (max(floor - 0.08, source_saturation * 0.90), 0.74),
        (max(0.22, source_saturation * 0.70), 0.88),
    )
    return [hsv_color(hue, saturation, value) for saturation, value in steps]


def protect_primary_palette(shared, primary, limit):
    ramp = semantic_ramp(parse_hex(primary["source_color"]), primary["family"])
    if limit <= len(ramp):
        return ramp[:limit], ramp[:limit]
    ranked = sorted(shared, key=lambda rgb: sum(rgb) / 3)
    preferred = [ranked[0], ranked[-1]] + shared
    kept = []
    for color in preferred:
        if any(distance(color, accent) < 22 for accent in ramp):
            continue
        if all(distance(color, old) >= 20 for old in kept):
            kept.append(color)
        if len(kept) == limit - len(ramp):
            break
    return (kept + ramp)[:limit], ramp


def parse_hex(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def dominant_backgrounds(paths):
    family_scores = Counter()
    family_support = Counter()
    family_rgb = {}

    for path in paths:
        image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        image.thumbnail((256, 256))
        quantized = image.quantize(colors=24, method=Image.Quantize.MEDIANCUT)
        colors = quantized.getcolors()
        palette = quantized.getpalette()
        total = sum(count for count, _ in colors)
        per_image = Counter()
        for count, index in colors:
            rgb = tuple(palette[index * 3:index * 3 + 3])
            family = color_family(rgb)
            if not family:
                continue
            _, saturation, value = colorsys.rgb_to_hsv(*(channel / 255 for channel in rgb))
            share = count / total
            weight = share * (0.35 + 0.65 * saturation) * (0.75 + 0.25 * value)
            per_image[family] += share
            family_scores[family] += weight
            rgb_entry = family_rgb.setdefault(family, [0.0, 0.0, 0.0, 0.0])
            rgb_weight = count * (0.35 + 0.65 * saturation)
            for channel in range(3):
                rgb_entry[channel] += rgb[channel] * rgb_weight
            rgb_entry[3] += rgb_weight
        for family, share in per_image.items():
            if share >= 0.06:
                family_support[family] += 1

    ranked = sorted(
        BACKGROUND_BANK,
        key=lambda family: (family_scores[family] + family_support[family] * 0.08, family_support[family]),
        reverse=True,
    )
    primary = ranked[0]
    primary_color = representative_color(family_rgb.get(primary))
    secondary = next(
        (
            family for family in ranked[1:]
            if family_scores[family] > 0
            and hue_distance(primary_color, representative_color(family_rgb.get(family))) >= 45
        ),
        SECONDARY_FALLBACK[primary],
    )
    ranked = [primary, secondary]
    results = []
    for rank, family in enumerate(ranked[:2], start=1):
        source = representative_color(family_rgb.get(family))
        base, accent = background_pair(family, source)
        results.append({
            "rank": rank,
            "role": "primary" if rank == 1 else "secondary",
            "family": family,
            "source_color": hex_color(source),
            "base_color": hex_color(base),
            "accent_color": hex_color(accent),
            "score": round(family_scores[family] + family_support[family] * 0.08, 4),
            "image_support": family_support[family],
        })
    return results


def freshen_color(rgb, amount):
    if amount <= 0:
        return rgb
    red, green, blue = (channel / 255 for channel in rgb)
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    hue_degrees = hue * 360
    if value < 0.24 or value > 0.96:
        return rgb
    skin_or_warm_food = 8 <= hue_degrees <= 42 and 0.14 <= saturation <= 0.68
    if skin_or_warm_food:
        saturation = min(0.78, saturation * (1 + 0.025 * amount))
        value = min(0.98, value + 0.025 * amount)
    elif saturation < 0.08:
        value = min(0.97, value + 0.035 * amount)
    else:
        saturation = min(0.86, saturation * (1 + 0.14 * amount))
        value = min(0.98, value + 0.065 * amount)
    return tuple(round(channel * 255) for channel in colorsys.hsv_to_rgb(hue, saturation, value))


def palette_for(path, colors):
    image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    image.thumbnail((320, 320))
    quantized = image.quantize(colors=max(colors * 2, 16), method=Image.Quantize.MEDIANCUT)
    raw = sorted(quantized.getcolors(), reverse=True)
    palette = quantized.getpalette()
    candidates = []
    total = sum(count for count, _ in raw)
    for count, index in raw:
        rgb = tuple(palette[index * 3:index * 3 + 3])
        value = sum(rgb) / 3
        chroma = max(rgb) - min(rgb)
        if value < 18 or value > 246:
            weight = count * 0.25
        else:
            weight = count * (1 + min(chroma / 255, 0.55))
        candidates.append((weight, count / total, rgb))
    selected = []
    for _, share, rgb in sorted(candidates, reverse=True):
        if all(distance(rgb, old) >= 28 for old in selected):
            selected.append(rgb)
        if len(selected) == colors:
            break
    return selected, image.size


def merge_shared(palettes, limit):
    weighted = Counter()
    for palette in palettes:
        for rank, rgb in enumerate(palette):
            weighted[rgb] += max(1, len(palette) - rank)
    selected = []
    for rgb, _ in weighted.most_common():
        if all(distance(rgb, old) >= 24 for old in selected):
            selected.append(rgb)
        if len(selected) == limit:
            break
    return selected


def draw_preview(per_image, shared, dominant, output):
    width, swatch, margin = 960, 64, 24
    height = margin * 8 + swatch * 7
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    rows = per_image + [shared]
    for row, colors in enumerate(rows):
        y = margin + row * (swatch + margin)
        for col, rgb in enumerate(colors):
            x = 180 + col * (swatch + 8)
            draw.rectangle((x, y, x + swatch, y + swatch), fill=rgb)
        draw.text((24, y + 20), "shared" if row == 4 else f"image {row + 1}", fill=(30, 30, 30))
    for offset, item in enumerate(dominant):
        y = margin + (5 + offset) * (swatch + margin)
        draw.text((24, y + 20), item["role"], fill=(30, 30, 30))
        draw.rectangle((180, y, 180 + swatch, y + swatch), fill=item["base_color"])
        draw.rectangle((252, y, 252 + swatch, y + swatch), fill=item["accent_color"])
        draw.text((332, y + 20), f'{item["family"]} from {item["source_color"]}', fill=(30, 30, 30))
    canvas.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs=4)
    parser.add_argument("--colors-per-image", type=int, default=8)
    parser.add_argument("--shared-colors", type=int, default=16)
    parser.add_argument("--freshness", type=float, default=0.8, help="0 disables; 0.8 is the bright summer default")
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--preview-out", required=True)
    args = parser.parse_args()

    results = [palette_for(path, args.colors_per_image) for path in args.images]
    source_palettes = [item[0] for item in results]
    palettes = [[freshen_color(color, args.freshness) for color in palette] for palette in source_palettes]
    dominant = dominant_backgrounds(args.images)
    raw_shared = merge_shared(palettes, args.shared_colors)
    shared, primary_ramp = protect_primary_palette(raw_shared, dominant[0], args.shared_colors)
    report = {
        "images": [
            {
                "path": str(Path(path)),
                "sample_size": list(results[i][1]),
                "source_palette": [hex_color(c) for c in source_palettes[i]],
                "palette": [hex_color(c) for c in palettes[i]],
            }
            for i, path in enumerate(args.images)
        ],
        "shared_palette": [hex_color(c) for c in shared],
        "raw_shared_palette": [hex_color(c) for c in raw_shared],
        "semantic_primary_ramp": [hex_color(c) for c in primary_ramp],
        "dominant_backgrounds": dominant,
        "freshness": args.freshness,
    }
    Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    draw_preview(palettes, shared, dominant, args.preview_out)


if __name__ == "__main__":
    main()
