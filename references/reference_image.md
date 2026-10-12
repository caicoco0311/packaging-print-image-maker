# Reference image analysis

Run this file after three products pass research. Run it in parallel with `reference_title.md`; do not wait for title output. Use this branch only for product-image generation evidence.

## Five-image budget

- Keep one clear main image from each selected product.
- From `sold_rank: 1` only, keep at most two additional material, print, finish, die-cut, closure, edge, or structure images.
- Keep no more than five unique local images and download only images used by generation.
- For a valid same-product/category cache, prefer one previously validated primary image. Do not download or screen additional images unless that image is missing, corrupted, or insufficient to resolve required physical structure.

## Analyze visible evidence

Record container shape, closure, silhouette, materials, label or print shape, print location, palette, finishes, thickness, edge, seam, fold, die-cut, internal structure, visible dimensions or proportions, scale cues, camera angle, and folded/assembled versus unfolded/flat states. Do not infer invisible structure or fabricate exact dimensions.

Explicit user materials, shapes, colors, finishes, and structures override image evidence. Complete missing information without replacing user input.

Do not transfer seller logos, source brands, watermarks, contacts, certifications, QR codes, promotional claims, or source package wording.

## Output

Write the resolved `visual_identity` and local reference paths into `identity.json`. Keep analysis structured and do not paste its explanation into image prompts.
