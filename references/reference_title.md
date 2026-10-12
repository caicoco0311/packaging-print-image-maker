# Alibaba B2B title and keyword analysis

Run this file after three high-sales Alibaba products pass the research gates. Run it in parallel with `reference_image.md`; neither branch depends on the other.

Run `scripts/analyze_titles.py` on the validated title set, then review its deterministic hot terms and merge the approved output into `identity.json`.

## Input

Use the user's product, requested packaging type, explicit user attributes, and the three validated Alibaba titles.

## Analyze hot terms

- Tokenize the three titles into product, packaging category, material, structure, finish, application, customization, and buyer-intent phrases.
- Identify repeated and commercially relevant terms. Treat frequency as evidence, not permission to keyword-stuff.
- Exclude seller/source brands, unsupported claims, and irrelevant traffic terms.

## Create listing metadata

- Extract only product, packaging category, material, shape, structure, finish, and application facts.
- Remove seller and source brands, OEM or ODM wording, promotions, minimum-order language, model numbers, certifications, contacts, marketplace wording, and repeated keywords.
- Preserve the user's product, packaging type, and explicit attributes.
- Prefer facts shared by multiple validated titles; use a single-title fact only when the product page confirms it.

Create one readable Alibaba B2B product name and a deduplicated detail-page keyword list. Preserve the user's product, packaging type, and explicit attributes. Use natural buyer language and do not invent certifications, performance claims, or materials.

## Output

Create one descriptive English title of approximately 4–12 words:

```json
{
  "normalized_product_title": "Custom Textured Paper Wine Bottle Label",
  "detail_page_keywords": ["custom wine labels", "textured paper label", "gold foil label printing"],
  "title_attributes": {
    "product": "red wine",
    "packaging_type": "label",
    "materials": ["textured paper"],
    "finishes": []
  }
}
```

The title and keywords are listing metadata for filenames, reports, and Alibaba B2B detail-page copy. Never render them as visible package text. Only `Your Logo` and the role-2 title are required visible text.
