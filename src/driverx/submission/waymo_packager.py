"""Dry-run Waymo E2E submission packaging.

This writes a JSON artifact with the same essential frame/trajectory structure
as the official protobuf submission. Real protobuf serialization can be added
once the Waymo dependency is enabled.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def package_run_dir(run_dir: Path, output_path: Path | None = None) -> dict[str, Any]:
    trajectory_path = run_dir / "selected_trajectory.json"
    frame_path = run_dir / "frame.json"
    if not trajectory_path.exists():
        raise FileNotFoundError(f"Missing selected trajectory: {trajectory_path}")
    if not frame_path.exists():
        raise FileNotFoundError(f"Missing frame artifact: {frame_path}")

    trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    metadata_path = run_dir / "run_metadata.json"
    metadata = (
        json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata_path.exists()
        else {}
    )
    package = {
        "submission_type": "E2ED_SUBMISSION_DRY_RUN",
        "authors": [str(metadata.get("author", "0xDriver"))],
        "affiliation": "Independent",
        "unique_method_name": str(
            metadata.get("method_name", "fixture_vla_intent_planner")
        ),
        "uses_public_model_pretraining": True,
        "public_model_names": ["mock-vla-intent-reasoner"],
        "num_model_parameters": "0",
        "predictions": [
            {
                "frame_name": frame["frame_name"],
                "trajectory": {
                    "pos_x": [point[0] for point in trajectory["points_xy"]],
                    "pos_y": [point[1] for point in trajectory["points_xy"]],
                },
            }
        ],
    }
    output = output_path or (run_dir / "submission_dry_run.json")
    output.write_text(json.dumps(package, indent=2), encoding="utf-8")
    return {"path": str(output), "predictions": len(package["predictions"])}
