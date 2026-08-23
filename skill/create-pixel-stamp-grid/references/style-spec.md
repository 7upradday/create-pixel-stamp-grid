# Style specification

## Poster geometry

- Use a vertical 3:4 social-media canvas; default to 2048 by 2732 pixels.
- Center a two-by-two group horizontally.
- Place the group in the upper-middle, beginning near 9-12 percent of canvas height.
- Reserve 22-28 percent of canvas height below the group.
- Give every tile its own complete white scalloped postage-stamp border.
- Use exactly 12 large semicircular scallops per side. For a 720-pixel stamp, use approximately 60 pixels per scallop and a 30-pixel radius.
- Use a white border of approximately 40 pixels so the larger scallops remain legible at social-media size.
- Keep horizontal and vertical gutters equal.

## Pixel language

- Preserve the source subject, angle, large shapes, and major spatial relationships.
- Simplify photographic detail into deliberate square clusters.
- Use hard edges and nearest-neighbor enlargement.
- Avoid smooth curves, antialiasing, soft gradients, photographic noise, and dense random dithering.
- Use one common logical resolution. Default to 52 by 52; use 64 by 64 only when a face or detailed product needs it.
- Keep the subject readable at thumbnail size.

## Color language

- Extract colors from the four original inputs before generating tiles.
- Build a shared palette plus a protected four-step ramp for the first dominant source hue. Keep the shared palette at the requested limit by reserving four slots for this ramp; preserve the darkest and lightest source-derived neutrals before filling the remaining slots.
- Rank chromatic hue families by normalized pixel coverage across all four images plus cross-image support. Ignore near-white, very dark, and nearly neutral pixels for background ranking.
- Select two perceptually distinct families. Use the highest score as primary, then choose the highest remaining family whose representative hue is at least 45 degrees away; this prevents one yellow-green cluster from being counted as both yellow and green. If no qualifying source family exists, use the curated complementary fallback and record zero source support.
- Convert pink, yellow, and sky blue to the curated high-value macaron pairs. For green and purple, preserve the representative source hue and construct the background dynamically: green uses HSV saturation/value `10%/98%` for the base and `28%/93%` for the accent; purple uses `10%/99%` and `24%/94%`. This prevents gray mint and gray lavender without making the poster dark.
- Protect the first dominant hue inside tile content with four value steps. For green and purple, keep the darkest semantic step at no less than 42% saturation, then taper saturation toward the highlight. Do not apply this floor to skin, white surfaces, food, or neutral shadows; only the nearest palette mapping uses these reserved colors.
- Keep background value very high. Use cream lemon rather than beige, lemon rather than mustard, sky rather than gray-blue, and mint rather than gray-green.
- Freshen extracted content palettes at `0.8`: slightly raise saturation and value for chromatic midtones, make a smaller adjustment to skin and warm food colors, and preserve dark outlines and near-white highlights.
- Use low-frequency mottling at only 2–3 percent. Apply it only to the poster background and never allow it to create a gray veil.
- Preserve skin in a plausible range and do not force it into decorative palette colors.
- Use a dark neutral for separation when adjacent colors merge.

## Background outputs

Generate exactly two posters. Pattern and color are separate decisions.

- `pixel-stamp-primary-dots.png`: primary-family pale base with a darker same-family polka dot.
- `pixel-stamp-secondary-stripes.png`: secondary-family pair in exactly 18 full-height alternating stripes.

Keep dot diameter near 0.6-1.0 percent of canvas width and spacing near 3-4 percent. Keep both patterns subordinate to the stamps. Do not generate a solid-background version unless the user explicitly requests a later exception.

## Theme typography

- Render typography with `scripts/compose_post.py`, never with image generation.
- Use bundled `assets/Allura-Regular.ttf`, a thin connected calligraphic script matching the reference's elegant handwritten rhythm.
- Choose ink by background family using a soft decorative contrast band: minimum contrast against either background color must be at least 1.9:1; average contrast should remain between 1.9:1 and 3.6:1, targeting about 2.7:1. Warm yellow → fresh cyan blue `#239DBA`; sky blue → summer raspberry `#D9618D`; mint → soft coral pink `#DE6C96`; pink → cornflower blue `#4D94C6`; lavender → fresh teal `#2D9691`; neutral → cyan blue, berry, or cornflower sampled to harmonize with the image palette.
- Treat these as ordered candidates, not unconditional colors. Let `compose_post.py --title-color auto` calculate the decorative contrast band.
- Use two staggered lines: word one begins near the left of the lower title area; words two and three begin farther right on the next line.
- Dynamically reduce font size to fit each line without changing the wording.
- Keep generous surrounding whitespace. Do not add a subtitle, credit, logo, shadow, outline, or decorative icon.
