# Image transformation prompt template

Use one source image per transformation call.

```text
Use case: style-transfer
Asset type: one square tile for a four-panel social-media pixel-stamp poster
Primary request: Transform the source photograph into authentic retro pixel art.
Input image: the attached image is the sole content and composition reference.
Subject lock: Preserve [subject], [viewpoint], [silhouette], [relative scale], and [must-preserve details].
Composition: Square crop; keep the subject [centered / near the upper third] as in the source. Use large readable shapes suitable for a [52x52 / 64x64] logical grid.
Style: Hard square pixel clusters, simplified geometric forms, limited palette, crisp edges, no antialiasing, no smooth gradients, restrained dithering; use clear high-key summer light rather than a gray or sepia cast.
Palette: Preserve the source image's own colors and [semantic accent colors]. Use the supplied background families only as a loose harmony reference; do not recolor the subject toward either poster-background hue. Preserve dark separation, natural skin or fur, metal, water, warm food colors, and near-white highlights.
Output: One clean borderless square tile only.
Constraints: No stamp border, no poster background, no title, no watermark, no added props, no extra people, no copied objects from unrelated references.
```

Render the selected theme later with `compose_post.py`; never ask the image model to draw title lettering.
