# Alibaba research routing

## Candidate extraction

Before searching, run `scripts/research_cache.py get` for the normalized product and packaging category. Treat exit code 0 as a hit and 2 as a miss. Reuse only the returned primary image; the script rejects missing local images. Do not let color, finish, copy, or other presentation-only overrides trigger a new search. After fresh research and image download, run `scripts/research_cache.py put` with the completed identity.

1. Search Alibaba.com with the signed-in in-app browser for the parsed product and packaging type.
2. Extract at most 10 unique product-detail candidates with a stable URL, visible title, and directly readable numeric sold value.
3. Normalize the displayed sold value to an integer. Never estimate or invent a missing value.
4. Exclude duplicates, unusable URLs, missing numeric sales, and `sold_count < 100`.
5. Sort eligible candidates by `sold_count` descending. Do not calculate a composite, relevance, or clarity score.

## Simple title gate

Mark a candidate invalid when its title clearly describes the wrong product, wrong packaging category, printing equipment, raw material instead of finished packaging, an unrelated accessory, or a service without physical packaging. When ambiguous, inspect the product page. This gate returns only valid or invalid and never reorders valid products.

## Simple image gate

Require one clear packaging main image with visible structure and an identifiable material or printable surface. Reject severe blur, crop, unrelated imagery, or a page without usable packaging evidence. This gate returns only valid or invalid and never scores images.

## Selection and fallback

- Select the three highest-sold candidates that pass both gates.
- Replace a failed candidate with the next highest-sold eligible candidate.
- Stop before generation if fewer than three valid products remain.
- Record `sold_rank` 1–3 after final validation.

After extracting the three final links, run [reference_title.md](reference_title.md) and [reference_image.md](reference_image.md) in parallel, then join their structured outputs. For a valid same-product/category cache, skip candidate extraction and reuse the saved research. The image branch may select one cached primary image instead of downloading or screening more images.
