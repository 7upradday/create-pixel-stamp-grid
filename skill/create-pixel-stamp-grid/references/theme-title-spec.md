# Theme title specification

Generate a grounded three-word English display title from the combined evidence of all four images.

## Evidence schema

Create a JSON record with:

- `anchors`: shared objects, palette adjectives, materials, or setting cues
- `anchor_support`: map every anchor term to supporting image numbers
- `contexts`: supported mood, season, setting, or light terms
- `context_support`: map every context term to image numbers, or document `whole_set` evidence
- `endings`: approved experience nouns
- `unsupported`: tempting but unverified brands, places, seasons, activities, identities, and copied text

For heterogeneous subjects, prefer a shared palette or atmosphere instead of listing objects. Count a palette anchor only when it is visibly present in at least three images.

## Required form

- Use exactly three words.
- Use English ASCII letters and spaces only.
- Use Title Case.
- Keep 15-26 characters including spaces.
- Use `Shared Anchor + Supported Mood/Season + Experience Noun`.
- Require word one in `anchors` with support from at least two images; require three for palette anchors.
- Require word two in `contexts` with support from at least two images or documented whole-set evidence.
- Require word three in `endings`.
- Use a noun phrase, not a sentence, slogan, command, or caption.

Suggested ending vocabulary must still be added to the evidence record: `Escape`, `Daydream`, `Moments`, `Postcard`, `Interlude`, `Holiday`, or another concise experience noun grounded in the set.

## Reject

- punctuation, emoji, hashtags, numerals, possessives, articles, or connective filler
- brand names, personal names, precise locations, and copied package text
- unsupported weather, season, destination, activity, or identity claims
- promotional clichés such as `Amazing`, `Beautiful`, `Perfect`, `Magical`, `Unforgettable`, `Lifestyle`, `Aesthetic`, or `Vibes`
- titles that enumerate unrelated objects
- candidates differing by only one synonym

## Candidate procedure

1. Generate three structurally distinct candidates from the evidence record.
2. Explain each candidate in one short Chinese sentence tied to image numbers.
3. Validate every candidate with `scripts/validate_theme.py`.
4. Score valid candidates: evidence 40, cross-image coverage 25, cohesion 15, natural English 10, typographic fit 10.
5. Select the highest-scoring valid candidate. Do not pause for typography approval or generate alternates unless requested.
6. Pass the exact selected title to `scripts/compose_post.py --title` and include it in every requested poster variant.

## Reference-matched typography

- Use `assets/Allura-Regular.ttf`; do not substitute an image-generated approximation.
- Render with `--title-color auto`. Determine ink from the background family. Reject colors whose minimum contrast against either background is below 1.9:1 or whose average contrast is above 3.6:1; target an average near 2.7:1 so the title remains airy rather than reading like dark body text.
- Split after the first word: line one contains word one, line two contains words two and three.
- Use a large, airy, right-flowing calligraphic treatment inspired by the reference title `Lemon Summer Escape` without copying that wording.
- Keep the first line left-shifted and the second line slightly right-shifted.
- Fit by reducing font size only. Never abbreviate, wrap to three lines, add punctuation, outline, shadow, subtitle, credit, or logo.

For a set sharing pastel colors and summer light, a valid structural example is `Pastel Summer Daydream`; use it only when its three terms pass the actual evidence record.
