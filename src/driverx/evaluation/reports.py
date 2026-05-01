"""Evaluate saved run artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.evaluation.ade import average_displacement_error


def evaluate_run_dir(run_dir: Path) -> dict[str, Any]:
    trajectory_path = run_dir / "selected_trajectory.json"
    frame_path = run_dir / "frame.json"
    if not trajectory_path.exists():
        raise FileNotFoundError(f"Missing selected trajectory: {trajectory_path}")
    if not frame_path.exists():
        raise FileNotFoundError(f"Missing frame artifact: {frame_path}")

    trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    future = frame.get("future_xy")
    if future is None:
        return {
            "frame_name": frame.get("frame_name"),
            "ade": None,
            "reason": "No ground-truth future_xy is available.",
        }
    ade = average_displacement_error(
        [tuple(point) for point in trajectory["points_xy"]],
        [tuple(point) for point in future],
    )
    return {
        "frame_name": frame.get("frame_name"),
        "ade": round(ade, 6),
        "num_points": len(trajectory["points_xy"]),
    }
