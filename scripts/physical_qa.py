#!/usr/bin/env python3
"""Create or validate the manual physical-consistency QA record for six generated roles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


GATES = ("dimensions_proportions", "scale_cues", "camera_perspective", "faces_edges_openings", "state_transition", "panel_seam_tab_topology", "material_thickness", "cross_role_identity")


def create(identity: dict) -> dict:
    visual = identity.get("visual_identity", {})
    return {"schema_version": "1.0", "identity": {"physical_dimensions": visual.get("physical_dimensions", "unknown"), "structure_states": visual.get("structure_states", [])}, "gates": {gate: {"status": "pending", "notes": ""} for gate in GATES}, "passed": False}


def validate(record: dict) -> dict:
    gates = record.get("gates", {})
    missing = [gate for gate in GATES if gate not in gates]
    invalid = [gate for gate in GATES if gates.get(gate, {}).get("status") not in {"pass", "not_applicable"}]
    result = {"valid": not missing and not invalid and record.get("passed") is True, "missing_gates": missing, "failed_or_pending_gates": invalid, "top_level_passed": record.get("passed") is True}
    if not result["valid"]:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity", type=Path); parser.add_argument("--record", required=True, type=Path); parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate(json.loads(args.record.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2)); return 0
    if not args.identity:
        parser.error("--identity is required when creating a record")
    record = create(json.loads(args.identity.read_text(encoding="utf-8")))
    args.record.parent.mkdir(parents=True, exist_ok=True); args.record.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.record); return 0


if __name__ == "__main__":
    raise SystemExit(main())
