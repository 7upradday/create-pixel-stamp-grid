#!/usr/bin/env python3
"""Validate deterministic poster properties and emit a JSON report."""

import argparse
import colorsys
import json
from pathlib import Path

from PIL import Image, ImageStat


CANVAS = (2048, 2732)
STAMP_OUTER = 720
STAMP_BORDER = 40
GRID_GAP = 76
GRID_TOP = 270


def expected_positions():
    group = STAMP_OUTER * 2 + GRID_GAP
    left = (CANVAS[0] - group) // 2
    return [
        (left, GRID_TOP),
        (left + STAMP_OUTER + GRID_GAP, GRID_TOP),
        (left, GRID_TOP + STAMP_OUTER + GRID_GAP),
        (left + STAMP_OUTER + GRID_GAP, GRID_TOP + STAMP_OUTER + GRID_GAP),
    ]


def is_near_white(pixel):
    # Keep very pale macaron backgrounds (for example mint #EEF9F1) from
    # merging with the intentionally pure-white stamp border during run counts.
    return min(pixel[:3]) >= 250 and max(pixel[:3]) - min(pixel[:3]) <= 5


def count_white_runs(values):
    runs = 0
    active = False
    for value in values:
        white = is_near_white(value)
        if white and not active:
            runs += 1
        active = white
    return runs


def color_distance(a, b):
    return sum((a[index] - b[index]) ** 2 for index in range(3)) ** 0.5


def parse_hex(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def validate_source_background(image, spec):
    base = parse_hex(spec["base_color"])
    accent = parse_hex(spec["accent_color"])
    if spec["background"] == "stripes":
        expected = tuple((base[index] + accent[index]) / 2 for index in range(3))
    else:
        expected = tuple(base[index] * 0.96 + accent[index] * 0.04 for index in range(3))
    band = image.crop((0, 0, image.width, min(180, image.height))).convert("RGB")
    observed = ImageStat.Stat(band).mean[:3]
    return color_distance(observed, expected) <= 24


def validate_eighteen_stripes(image):
    width, height = image.size
    samples = []
    for index in range(18):
        left = round((index + 0.25) * width / 18)
        right = round((index + 0.75) * width / 18)
        crop = image.crop((left, round(height * 0.82), right, round(height * 0.9)))
        samples.append(tuple(round(value) for value in ImageStat.Stat(crop).mean[:3]))
    adjacent = [color_distance(samples[index], samples[index + 1]) for index in range(17)]
    return min(adjacent) > 12


def validate_title_region(image):
    region = image.crop((180, 1840, image.width - 180, 2510)).convert("RGB")
    pixels = region.get_flattened_data() if hasattr(region, "get_flattened_data") else region.getdata()
    title_pixels = sum(
        1 for red, green, blue in pixels
        if 0.2126 * red + 0.7152 * green + 0.0722 * blue < 155
    )
    return title_pixels >= 1200


def validate_luminous_background(image):
    band = image.crop((0, 0, image.width, min(180, image.height))).convert("RGB")
    red, green, blue = ImageStat.Stat(band).mean[:3]
    _, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
    channel_mean = (red + green + blue) / 3
    if saturation < 0.08:
        return value >= 0.94 and channel_mean >= 238
    return value >= 0.90 and channel_mean >= 210


def inspect_stamps(image):
    tile_checks = []
    for left, top in expected_positions():
        inner = image.crop((
            left + STAMP_BORDER,
            top + STAMP_BORDER,
            left + STAMP_OUTER - STAMP_BORDER,
            top + STAMP_OUTER - STAMP_BORDER,
        )).convert("RGB")
        stat = ImageStat.Stat(inner)
        content_variance = sum(stat.var) / 3

        samples = []
        inset = STAMP_BORDER + 18
        for x in range(left + inset, left + STAMP_OUTER - inset, 8):
            samples.append(image.getpixel((x, top + STAMP_BORDER - 4)))
            samples.append(image.getpixel((x, top + STAMP_OUTER - STAMP_BORDER + 4)))
        for y in range(top + inset, top + STAMP_OUTER - inset, 8):
            samples.append(image.getpixel((left + STAMP_BORDER - 4, y)))
            samples.append(image.getpixel((left + STAMP_OUTER - STAMP_BORDER + 4, y)))
        white_ratio = sum(is_near_white(pixel) for pixel in samples) / max(1, len(samples))
        top_runs = count_white_runs([image.getpixel((x, top + 4)) for x in range(left, left + STAMP_OUTER)])
        left_runs = count_white_runs([image.getpixel((left + 4, y)) for y in range(top, top + STAMP_OUTER)])
        tile_checks.append({
            "content_variance": round(content_variance, 2),
            "content_present": content_variance > 80,
            "white_border_ratio": round(white_ratio, 3),
            "white_border_present": white_ratio > 0.72,
            "top_scallop_count": top_runs,
            "left_scallop_count": left_runs,
            "twelve_scallops_per_side": top_runs == 12 and left_runs == 12,
        })
    return tile_checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs="+")
    parser.add_argument("--report", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-width", type=int, default=2048)
    parser.add_argument("--expected-height", type=int, default=2732)
    parser.add_argument("--expect-title", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    specs = {item["filename"]: item for item in manifest.get("outputs", [])}
    expected_pair = {
        "pixel-stamp-primary-dots.png": ("primary", "dots"),
        "pixel-stamp-secondary-stripes.png": ("secondary", "stripes"),
    }

    results = []
    for path in args.images:
        image = Image.open(path)
        rgb = image.convert("RGB")
        filename = Path(path).name
        spec = specs.get(filename)
        stamp_checks = inspect_stamps(rgb) if image.size == CANVAS else []
        checks = {
            "dimensions": image.size == (args.expected_width, args.expected_height),
            "rgb_or_rgba": image.mode in {"RGB", "RGBA"},
            "not_blank": rgb.getbbox() is not None,
            "four_content_tiles": len(stamp_checks) == 4 and all(item["content_present"] for item in stamp_checks),
            "four_white_stamp_borders": len(stamp_checks) == 4 and all(item["white_border_present"] for item in stamp_checks),
            "twelve_scallops_per_stamp_side": len(stamp_checks) == 4 and all(item["twelve_scallops_per_side"] for item in stamp_checks),
            "luminous_summer_background": validate_luminous_background(rgb),
            "expected_primary_secondary_variant": bool(
                spec and filename in expected_pair
                and (spec.get("color_rank"), spec.get("background")) == expected_pair[filename]
            ),
            "source_derived_background": bool(spec and validate_source_background(rgb, spec)),
        }
        if "stripes" in Path(path).stem:
            checks["eighteen_vertical_stripes"] = validate_eighteen_stripes(rgb)
        if args.expect_title:
            checks["theme_title_present"] = validate_title_region(rgb)
        results.append({"path": str(Path(path)), "size": list(image.size), "mode": image.mode, "checks": checks, "stamp_details": stamp_checks, "passed": all(checks.values())})
    pair_complete = len(results) == 2 and {Path(item["path"]).name for item in results} == set(expected_pair)
    report = {"passed": pair_complete and all(item["passed"] for item in results), "two_expected_variants": pair_complete, "outputs": results}
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
