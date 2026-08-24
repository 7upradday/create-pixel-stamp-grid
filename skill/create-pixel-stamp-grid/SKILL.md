---
name: create-pixel-stamp-grid
description: Transform exactly four realistic photographs into two coordinated 2-by-2 flat pixel-art postage-stamp posters for vertical social media. Preserve generated tile colors by default, derive only the poster backgrounds from source-dominant color families, render a primary-color polka-dot version and a secondary-color exact 18-stripe version, infer a grounded three-word English theme, and typeset it deterministically. Use for four-photo pixel collages, pixel postage-stamp posters, social-media covers, source-matched backgrounds, or automatic theme-title generation.
---

# Create Pixel Stamp Grid

Use the deterministic three-stage pipeline below. Generate only the four tile illustrations; let scripts control background color ranking, geometry, typography, and validation. Produce flat digital pixel art only, never a physical-material simulation.

## Inputs and defaults

- Require exactly four images in top-left, top-right, bottom-left, bottom-right order.
- Accept crop focus `center`, `upper-third`, or focal coordinates.
- Output exactly two posters: first dominant color as polka dots, second dominant color as 18 vertical stripes.
- Include an inferred English theme by default. Omit it only when the user explicitly requests `theme: off`.
- Use a 2048 by 2732 canvas, 52 by 52 logical pixels, or 64 by 64 for all four tiles when any face or detailed product needs it.
- Preserve generated tile colors by default. Use local quantization only when a tile lacks a clean pixel grid, and shared quantization only when the user explicitly requests strong palette unification.

## SOP 1 — Analyze sources and transform

1. Inspect the correct orientation of every source.
2. Run `scripts/extract_palette.py --freshness 0.8` on the four original images before image generation. Treat `dominant_backgrounds[0]` as primary and `[1]` as secondary for poster backgrounds; do not force these hues into tile content.
3. Read `references/style-spec.md` and `references/prompt-template.md`. Record each subject, viewpoint, crop anchor, must-preserve details, removable clutter, and semantic accents.
4. Transform one source per image-generation call into one borderless square tile. Preserve viewpoint, silhouette, approximate scale, identity, source colors, semantic accents, and centered or upper-third placement. Remove UI, watermarks, accidental text, and clutter. Do not invent content.
5. Run `scripts/pixelize_tile.py --color-mode preserve` on each clean generated tile. If a tile lacks a coherent pixel grid, use `--color-mode local --local-colors 32 --logical-size 52|64`. Use `--color-mode shared --palette-json PALETTE.json` only on explicit request after checking that no semantic color shifts toward the dominant background hue.

## SOP 2 — Infer, typeset, and compose

1. Read `references/theme-title-spec.md`. Build evidence, generate three distinct candidates, validate them, and select the highest-scoring valid title without pausing.
2. Run `scripts/compose_post.py --palette-json PALETTE.json --title "Selected Three Words"`.
3. Let the script output only `pixel-stamp-primary-dots.png` and `pixel-stamp-secondary-stripes.png`, each with four independent stamps, exactly 12 scallops per side, an upper-middle grid, and deterministic typography.

## SOP 3 — Validate and revise

1. Read `references/acceptance-rubric.md`.
2. Run `scripts/validate_output.py --manifest composition-manifest.json --expect-title` on both posters.
3. Inspect subject identity, title spelling and clearance, tile-color fidelity, source-background agreement, 12-scallop borders, and exactly 18 stripes.
4. Revise only the earliest failing stage: transform for identity errors, pixelize for palette or grid errors, compose for geometry or typography errors.
5. Return both posters, palette preview and JSON, tile order and crop decisions, `composition-manifest.json`, validation report, selected title, and evidence.

## Stability rules

- Never generate the complete poster in one image-model call.
- Never ask the image model to draw the title; render it deterministically with `compose_post.py`.
- Treat dots and stripes as pattern types, never as fixed color presets.
- Derive background hue from the original photographs, not the generated tiles.
- Keep background palette and tile palette independent by default.
- Preserve natural skin, fur, metals, water, food, neutrals, and subject-specific accents.
- Convert the two detected source families to luminous macaron base/accent pairs without changing their hue family. Preserve the representative source hue for green and purple backgrounds and enforce the chroma floors in `references/style-spec.md`.
- In optional shared mode, reserve four palette slots for the first dominant hue and use at least 24 shared colors; reject the mode if unrelated subjects acquire that hue.
- Keep backgrounds high-key and luminous. Reject mustard, ochre, gray-beige, dusty mauve, or any preset that looks dim at thumbnail size.
- Apply only 2–3 percent subtle vintage mottling to the background; never let texture lower overall brightness.
- Do not add logos, copied package text, credits, signatures, shadows, inner outlines, or material textures.
