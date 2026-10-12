# Excel batch workflow

Read this file only for `.xlsx`, `.csv`, or `.tsv` input. Ask the user to save legacy `.xls` as `.xlsx` first.

## Row contract

Treat each enabled non-empty row as one isolated packaging task. Require unique `task_id` and non-empty `user_input`. Accept optional `enabled`, `material`, `palette`, `finish`, `notes`, and `output_name`.

- Ignore blank rows.
- Default missing `enabled` to true; skip explicit false.
- Block only the row with missing input, invalid enabled value, or duplicate task ID; continue unrelated rows.
- Preserve source row number and never overwrite the source workbook.
- Structured material, palette, and finish columns are explicit user overrides.

## Conversion and state

Run `scripts/workbook_to_batch_manifest.py`, then `scripts/prepare_batch_tasks.py`. Store every task under `batch-output/<task_id>/` with `row_input.json`, `identity.json`, prompts, native images, final images, and resumable state.

Statuses are `pending`, `researching`, `research_complete`, `prompt_ready`, `hero_generating`, `hero_passed`, `wave_2`, `validating`, `complete`, `blocked`, or `skipped`.

Do not restart a completed unchanged stage. A failed row must not stop others. Group rows by normalized product and packaging category before research. Search once per group when user overrides do not change the underlying product search; reuse the saved links, title evidence, and image evidence for the remaining rows. A reused row may attach only one validated cached reference image.

## Scheduling

- Process Alibaba research in an isolated queue to avoid page/source mixing.
- Build prompts for all research-complete rows cheaply.
- Run at most one task's five-call Wave 2 at a time unless the runtime explicitly permits more.
- Preserve passing images and checkpoint after every stage.

## Results

Use `scripts/update_batch_results.py` to save a new results workbook with task ID, status, stage, retries, output directory, error, and six image paths. Never overwrite the input workbook.
