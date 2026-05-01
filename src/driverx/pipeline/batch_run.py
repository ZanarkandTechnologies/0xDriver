"""Tiny validation batch orchestration."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir, write_json_artifact
from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig
from driverx.pipeline.scene_run import run_scene


def run_batch(config: DriverConfig, fixture_names: list[str]) -> dict[str, Any]:
    if not fixture_names:
        raise ValueError("At least one fixture is required for run-batch.")

    batch_dir = prepare_run_dir(config.output.root, config.output.run_id)
    batch_id = batch_dir.name

    scenes: list[dict[str, Any]] = []
    ade_values: list[float] = []
    for fixture_name in fixture_names:
        scene_config = replace(
            config,
            dataset=DatasetConfig(kind="fixture", name=fixture_name),
            output=OutputConfig(root=batch_dir, run_id=fixture_name),
        )
        result = run_scene(scene_config)
        ade = result.metrics.get("ade")
        if isinstance(ade, int | float):
            ade_values.append(float(ade))
        scenes.append(
            {
                "fixture": fixture_name,
                "frame_name": result.frame_name,
                "run_dir": str(result.run_dir),
                "ade": ade,
                "selected_source": result.metrics.get("selected_source"),
            }
        )

    summary = {
        "batch_id": batch_id,
        "batch_dir": str(batch_dir),
        "num_scenes": len(scenes),
        "mean_ade": round(sum(ade_values) / len(ade_values), 6) if ade_values else None,
        "scenes": scenes,
    }
    summary_path = Path(batch_dir) / "batch_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["summary_path"] = str(summary_path)
    write_json_artifact(batch_dir, "run_metadata", {"author": config.author, "method_name": config.method_name})
    return summary
