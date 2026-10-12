# Input extraction and identity contract

## Parsing

- Set `input_mode` to `text` or `image`. URL input bypasses this file.
- Interpret every request by best effort as `product + packaging type`.
- Accept any language, length, word order, punctuation, or separator. Never run a character-count gate.
- Preserve the exact request in `raw_input`.
- Normalize the packaging type to `label`, `sticker`, `box`, or `other`.
- Preserve explicit user materials in `requested_materials`. Never replace them with research or inferred materials.
- Use `material_source: user` when `requested_materials` is non-empty; otherwise use `research` or `inferred` after evidence is collected.

## identity.json

Write UTF-8 JSON before prompt generation:

```json
{
  "schema_version": "4.1",
  "input_mode": "text",
  "reference_mode": "researched",
  "raw_input": "红酒 + 棉纸标签",
  "product": "red wine",
  "packaging_type": "Label",
  "normalized_category": "label",
  "normalized_product_title": "Custom Textured Paper Wine Bottle Label",
  "detail_page_keywords": ["custom wine labels", "textured paper label", "gold foil printing"],
  "requested_materials": ["cotton paper"],
  "material_source": "user",
  "visual_identity": {
    "container_shape": "750 ml dark glass wine bottle",
    "closure": "cork and capsule",
    "materials": ["cotton paper"],
    "label_shape": "large vertical rectangle",
    "print_location": "front bottle body",
    "palette": ["warm ivory", "burgundy", "antique gold"],
    "finishes": ["blind embossing", "gold foil"],
    "physical_dimensions": "750 ml bottle; label dimensions unknown",
    "structure_states": ["applied flat to bottle front"]
  },
  "required_text": "Your Logo",
  "title_text": "customized Solution",
  "forbidden_content": ["seller identity", "watermark", "contact information", "certification mark", "unsupported claim"],
  "selected_references": []
}
```

Every selected reference must contain:

```json
{
  "title": "Alibaba product title",
  "url": "https://www.alibaba.com/product-detail/...",
  "sold_count": 1000,
  "sold_rank": 1,
  "title_valid": true,
  "image_valid": true,
  "role": "primary",
  "image_paths": []
}
```

Use `reference_mode: researched` for a fresh three-product search, `cache-reuse` for a valid same-product/category cache, and `direct-link` only for URL input. Fresh research requires exactly three references with unique ranks 1–3 and `sold_count >= 100`. Cache reuse may retain one to three validated source records and may attach only one previously validated image. Keep no more than five unique image paths.

## Evidence priority

Apply evidence in this order:

1. explicit user input;
2. verified image evidence;
3. verified product-page facts;
4. normalized title facts;
5. reasonable inference.

After the hero passes, do not silently change the resolved container, closure, materials, label geometry, print location, palette, or finishes.
