# Generation gates and handoff

## Prompt submission

- Use the manifest's positive and negative files for each role; never hand-write shortened replacements.
- Keep positive and negative files separate on disk. At tool call time, submit the positive text followed by a clearly labeled `AVOID` section containing that role's negative text.
- Generate each role as a separate call and file. Never request a six-image contact sheet.

## Wave 1

Generate the hero with up to five Alibaba images and the `Your Logo` text asset. Check container, closure, resolved material, label or print geometry, print location, palette, finish, exact required text, seller-identity removal, product dimensions/proportions, apparent scale, and camera-angle plausibility. Retry only the failed requirement, at most twice. Do not start Wave 2 until the hero passes.

## Wave 2

- Launch roles 2–6 together; use roles 2–4 then 5–6 if five-way concurrency is unavailable.
- Use the approved hero and `Your Logo` asset for every role.
- Give role 2 the title asset and role 5 the primary print-detail reference.
- Retry role 2 at most twice and roles 3–6 at most once. Retain passing roles.

## Hard gates

All must pass:

- correct packaging category and shared product identity;
- exact required text on clearly visible main faces;
- role 2 contains exact `customized Solution` once in clean top space;
- no seller identity, watermark, contact, certification, unsupported claim, or unrelated text;
- role 3 is a strict four-panel grid and visibly demonstrates the resolved material;
- role 5 is readable print artwork;
- role 6 contains at least three consistent views;
- dimensions and relative proportions remain consistent across all six roles; never invent an exact measurement when the evidence provides none;
- object size is plausible relative to hands, containers, furniture, or other scale cues;
- perspective, camera angle, visible faces, edges, openings, and closures agree geometrically;
- folded, unfolded, flat, open, closed, assembled, and disassembled views preserve the same panel count, cut lines, hinges, seams, tabs, openings, wall thickness, and attachment points;
- no structure changes volume, material thickness, topology, or assembly logic between views;
- every native source is square;
- exactly six final 950 × 950 PNG files exist and match the manifest.

If required text fails visual self-check, read [text_repair.md](text_repair.md). If any other hard gate remains after its retry limit, preserve passing files and report the blocking role without delivering a complete set.

## Brief visual check

Confirm varied composition, plausible structure, recognizable materials, photographic lighting, grounded shadows, clean edges, consistent color and finish, stable dimensions/proportions, plausible scale, correct perspective, and physically reversible state transitions. Compare folded/unfolded or open/closed views side by side. Do not calculate a routine numeric score.

Create `physical_qa.json` with `scripts/physical_qa.py`, inspect all six roles, set every applicable gate to `pass` and top-level `passed` to true, then pass the record to `validate_outputs.py`. Never mark a gate passed without visual inspection.

## Handoff

Keep originals in `output/native/`. Resize square sources with LANCZOS to the six manifest names, run `validate_outputs.py`, and save a compact result containing pass status, waves, retries, failed gates, elapsed time, and output paths.
