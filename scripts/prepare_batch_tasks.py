#!/usr/bin/env python3
"""Prepare isolated, resumable task directories from a batch manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9._-]+$")
STATUSES = {
    "pending", "researching", "research_complete", "prompt_ready",
    "hero_generating", "hero_passed", "wave_2", "validating",
    "complete", "blocked", "skipped",
}


def stable_hash(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def research_key(raw_input: str) -> str:
    normalized = raw_input.lower()
    normalized = re.sub(r"https?://\S+", " url ", normalized)
    category = "other"
    category_patterns = (("label", r"\blabel\b|标签|標籤"), ("sticker", r"\bsticker\b|贴纸|貼紙"), ("box", r"\bbox\b|\bcarton\b|盒|箱"), ("other", r"\b(pouch|bag|bottle|tube|jar|can)\b|袋|瓶|管|罐"))
    for name, pattern in category_patterns:
        if re.search(pattern, normalized):
            category = name
            break
    normalized = re.sub(r"\b(label|sticker|box|carton|pouch|bag|bottle|tube|jar|can)\b|标签|標籤|贴纸|貼紙|盒|箱|袋|瓶|管|罐", " ", normalized)
    normalized = re.sub(r"[^0-9a-z\u3400-\u9fff]+", " ", normalized).strip()
    return hashlib.sha256(f"{normalized}|{category}".encode("utf-8")).hexdigest()[:20] if normalized else "unresolved"


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def prepare(manifest_path: Path, out_dir: Path) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError("batch manifest must contain a jobs array")
    batch_id = str(manifest.get("batch_id", "")).strip()
    if not batch_id:
        raise ValueError("batch_id must be non-empty")

    state_path = out_dir / "batch_state.json"
    previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {"jobs": {}}
    previous_jobs = previous.get("jobs", {}) if isinstance(previous.get("jobs", {}), dict) else {}
    state_jobs: dict[str, dict] = {}

    for row in jobs:
        if not isinstance(row, dict):
            raise ValueError("every batch job must be an object")
        task_id = str(row.get("task_id", "")).strip()
        source_status = str(row.get("status", "pending"))
        if source_status not in STATUSES:
            raise ValueError(f"invalid status for {task_id or '<missing>'}: {source_status}")
        if not task_id:
            task_id = f"blocked-row-{row.get('row_number', 'unknown')}"
            source_status = "blocked"
            row = {**row, "error": row.get("error") or "missing task_id"}
        safe = bool(SAFE_TASK_ID.fullmatch(task_id))
        if not safe:
            source_status = "blocked"
            row = {**row, "error": row.get("error") or "task_id contains unsafe path characters"}

        payload = {
            "row_number": row.get("row_number"),
            "task_id": task_id,
            "raw_input": str(row.get("raw_input", "")),
            "overrides": row.get("overrides", {}),
        }
        input_hash = stable_hash(payload)
        old = previous_jobs.get(task_id, {}) if isinstance(previous_jobs.get(task_id, {}), dict) else {}
        unchanged = old.get("input_hash") == input_hash

        if source_status in {"blocked", "skipped"}:
            status, stage = source_status, "input"
        elif unchanged:
            status = old.get("status", "pending") if old.get("status") in STATUSES else "pending"
            stage = old.get("stage", "input")
        else:
            status, stage = "pending", "input"

        task_dir = out_dir / task_id
        if safe and status != "skipped":
            task_dir.mkdir(parents=True, exist_ok=True)
            atomic_json(task_dir / "row_input.json", payload)

        state_jobs[task_id] = {
            "row_number": row.get("row_number"),
            "status": status,
            "stage": stage,
            "input_hash": input_hash,
            "input_changed": bool(old) and not unchanged,
            "retries": old.get("retries", {}) if unchanged else {},
            "output_dir": str(task_dir.resolve()) if safe else "",
            "error": row.get("error", "") if status == "blocked" else old.get("error", "") if unchanged else "",
            "images": old.get("images", []) if unchanged else [],
            "research_key": research_key(payload["raw_input"]),
            "reference_mode": old.get("reference_mode", "") if unchanged else "",
            "normalized_product_title": old.get("normalized_product_title", "") if unchanged else "",
            "detail_page_keywords": old.get("detail_page_keywords", []) if unchanged else [],
            "physical_qa": old.get("physical_qa", "") if unchanged else "",
        }

    state = {
        "schema_version": "1.1",
        "batch_id": batch_id,
        "source_workbook": manifest.get("source_workbook", ""),
        "jobs": state_jobs,
    }
    atomic_json(state_path, state)
    return state_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    print(prepare(args.manifest, args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
