---
name: packaging-print-image-maker
description: Accept text, image, Alibaba product-link, XLSX, CSV, or TSV packaging requests; research or reuse sold-ranked Alibaba.com references when needed; create B2B listing titles and keywords; and generate a consistent six-image 950 x 950 ecommerce set. Use for labels, stickers, boxes, bottles, tubes, pouches, bags, cans, jars, printed packaging, finishing concepts, and OEM or ODM imagery.
---

# Packaging Print Image Maker

Create exactly six independent 950 x 950 PNG images per task.

## Route the input

- For text, read [extract.md](references/extract.md), then use research unless a matching cache is valid.
- For an uploaded image, read [extract.md](references/extract.md), treat visible image evidence as the identity anchor, then use research unless a matching cache is valid.
- For a product-page URL, skip `extract.md` and `research.md`. Enter the image-construction stage directly, derive the minimum `identity.json` fields from the linked page and explicit user instructions, and use that page's usable images as direct references.
- For `.xlsx`, `.csv`, or `.tsv`, read [batch_excel.md](references/batch_excel.md) and use the spreadsheet workflow. Treat each enabled row as an isolated single task.

## Single-task workflow

1. Follow the input route above and create task-local `identity.json` with `input_mode` and `reference_mode`.
   Assemble the final contract with `scripts/prepare_identity.py`; for URL input, pass the linked-page evidence JSON and do not run extraction or research.
2. For uncached text or image input, read [research.md](references/research.md). Extract at most 10 candidates, require numeric `sold_count >= 100`, and keep the three highest-sold title-valid and image-valid products. Reuse a valid same-product/category cache instead of repeating the full search.
   Query and update the persistent cache with `scripts/research_cache.py get|put`.
3. After research, run [reference_title.md](references/reference_title.md) and [reference_image.md](references/reference_image.md) in parallel. The title branch produces an Alibaba B2B product name and detail-page keywords; the image branch resolves generation evidence. A cache-reuse task may attach only one previously validated local reference image. Join both outputs before prompt construction. For URL input, bypass these research branches and construct directly from the supplied page.
   Build deterministic title metadata with `scripts/analyze_titles.py` and merge its output into the identity evidence before assembly.
4. Build deterministic positive and negative prompt files. The script parses [image_construction.md](references/image_construction.md), exactly one category file—[label.md](references/label.md), [sticker.md](references/sticker.md), [box.md](references/box.md), or [other_packaging.md](references/other_packaging.md)—and [negative_prompt.md](references/negative_prompt.md). Do not manually load those prompt-rule files during normal execution.

```powershell
python scripts/build_prompts.py --identity <task-dir>/identity.json --category <label|sticker|box|other> --out-dir <task-dir>/prompts --verify-reference-files
```

5. Read [generation_rules.md](references/generation_rules.md) immediately before generation. Run the hero gate, then roles 2–6 in one five-call wave or a 3+2 fallback.
6. Read [text_repair.md](references/text_repair.md) only after visual self-check finds a required-text failure. Do not load Alibaba references for a text-only repair.
7. Keep native square sources, resize without cropping, complete the physical-consistency QA record, and validate:

```powershell
python scripts/resize_outputs.py --native-dir <task-dir>/output/native --out-dir <task-dir>/output
python scripts/physical_qa.py --identity <task-dir>/identity.json --record <task-dir>/physical_qa.json
python scripts/validate_outputs.py --output-dir <task-dir>/output --prompt-manifest <task-dir>/prompts/prompt_manifest.json --physical-qa <task-dir>/physical_qa.json
```

Use the built-in image-generation tool. Scripts validate deterministic prompt, identity, batch, file, and dimension contracts; the Agent performs visual inspection without claiming OCR.
