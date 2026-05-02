"""Small validation batch orchestration."""

from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir, write_json_artifact
from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig
from driverx.core.types import ArtifactRef, SceneRunResult
from driverx.datasets import iter_waymo_frames
from driverx.pipeline.scene_run import run_loaded_scene, run_scene

DEFAULT_WAYMO_BATCH_COUNT = 10
DEFAULT_FIXTURE_BATCH_NAMES = ("construction_merge", "straight_clear")


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _artifact_path(artifacts: list[ArtifactRef], name: str) -> str:
    for artifact in artifacts:
        if artifact.name == name:
            return str(artifact.path)
    return ""


def _scene_record(
    result: SceneRunResult,
    *,
    frame_index: int | None,
    fixture_name: str | None = None,
    timings_ms: dict[str, float] | None = None,
) -> dict[str, Any]:
    selected = result.selected_trajectory
    record: dict[str, Any] = {
        "fixture": fixture_name,
        "frame_index": frame_index,
        "frame_name": result.frame_name,
        "run_dir": str(result.run_dir),
        "ade": _number(result.metrics.get("ade")),
        "selected_source": result.metrics.get("selected_source"),
        "selected_score": selected.score if selected is not None else None,
        "timings_ms": timings_ms if timings_ms is not None else result.timings_ms,
        "scene_prediction": _artifact_path(result.artifacts, "scene_prediction"),
    }
    return record


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _mean_timings(scenes: list[dict[str, Any]]) -> dict[str, float]:
    timing_values: dict[str, list[float]] = {}
    for scene in scenes:
        timings = scene.get("timings_ms", {})
        if not isinstance(timings, dict):
            continue
        for stage, value in timings.items():
            number = _number(value)
            if number is None:
                continue
            timing_values.setdefault(str(stage), []).append(number)
    return {
        stage: round(sum(values) / len(values), 3)
        for stage, values in sorted(timing_values.items())
        if values
    }


def _best_scene(scenes: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [scene for scene in scenes if _number(scene.get("ade")) is not None]
    if not scored:
        return None
    return min(scored, key=lambda scene: float(scene["ade"]))


def _worst_scene(scenes: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [scene for scene in scenes if _number(scene.get("ade")) is not None]
    if not scored:
        return None
    return max(scored, key=lambda scene: float(scene["ade"]))


def _markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


def _render_ade_table(scenes: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| # | frame index | frame name | ADE | selected source | scene prediction |",
        "|---:|---:|---|---:|---|---|",
    ]
    for idx, scene in enumerate(scenes, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(idx),
                    _markdown_cell(scene.get("frame_index")),
                    _markdown_cell(scene.get("frame_name")),
                    _markdown_cell(scene.get("ade")),
                    _markdown_cell(scene.get("selected_source")),
                    _markdown_cell(scene.get("scene_prediction")),
                ]
            )
            + " |"
        )
    return lines


def _render_latency_table(mean_timings_ms: dict[str, float]) -> list[str]:
    lines = ["| stage | mean ms |", "|---|---:|"]
    for stage, mean_ms in mean_timings_ms.items():
        lines.append(f"| {_markdown_cell(stage)} | {mean_ms:.3f} |")
    if len(lines) == 2:
        lines.append("| no timing data | |")
    return lines


def _write_batch_report(batch_dir: Path, summary: dict[str, Any]) -> Path:
    best = summary.get("best_scene")
    worst = summary.get("worst_scene")
    lines = [
        f"# Batch Report: {summary['batch_id']}",
        "",
        "## Summary",
        "",
        f"- Dataset kind: `{summary['dataset_kind']}`",
        f"- Frame start: `{summary.get('frame_start')}`",
        f"- Frame count: `{summary['frame_count']}`",
        f"- Scenes: `{summary['num_scenes']}`",
        f"- Mean ADE: `{summary.get('mean_ade')}`",
        f"- Best scene: `{best.get('frame_name') if isinstance(best, dict) else None}`",
        f"- Worst scene: `{worst.get('frame_name') if isinstance(worst, dict) else None}`",
        f"- Worst-scene SVG: `{worst.get('scene_prediction') if isinstance(worst, dict) else None}`",
        "",
        "## ADE Table",
        "",
        *_render_ade_table(summary["scenes"]),
        "",
        "## Latency Table",
        "",
        *_render_latency_table(summary["mean_timings_ms"]),
        "",
    ]
    report_path = batch_dir / "batch_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _finalize_summary(
    *,
    config: DriverConfig,
    batch_dir: Path,
    batch_id: str,
    dataset_kind: str,
    frame_start: int | None,
    frame_count: int,
    scenes: list[dict[str, Any]],
) -> dict[str, Any]:
    ade_values = [
        float(scene["ade"])
        for scene in scenes
        if _number(scene.get("ade")) is not None
    ]
    summary_path = batch_dir / "batch_summary.json"
    report_path = batch_dir / "batch_report.md"
    summary = {
        "batch_id": batch_id,
        "batch_dir": str(batch_dir),
        "dataset_kind": dataset_kind,
        "frame_start": frame_start,
        "frame_count": frame_count,
        "num_scenes": len(scenes),
        "mean_ade": _mean(ade_values),
        "best_scene": _best_scene(scenes),
        "worst_scene": _worst_scene(scenes),
        "mean_timings_ms": _mean_timings(scenes),
        "scenes": scenes,
        "summary_path": str(summary_path),
        "report_path": str(report_path),
    }
    report_path = _write_batch_report(batch_dir, summary)
    summary["report_path"] = str(report_path)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_json_artifact(
        batch_dir,
        "run_metadata",
        {
            "author": config.author,
            "method_name": config.method_name,
            "dataset_kind": dataset_kind,
            "frame_start": frame_start,
            "frame_count": frame_count,
        },
    )
    return summary


def _run_fixture_batch(
    config: DriverConfig,
    batch_dir: Path,
    fixture_names: list[str],
) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    for fixture_name in fixture_names:
        scene_config = replace(
            config,
            dataset=DatasetConfig(kind="fixture", name=fixture_name),
            output=OutputConfig(root=batch_dir, run_id=fixture_name),
        )
        result = run_scene(scene_config)
        scenes.append(_scene_record(result, frame_index=None, fixture_name=fixture_name))
    return scenes


def _run_waymo_batch(
    config: DriverConfig,
    batch_dir: Path,
    frame_start: int,
    frame_count: int,
) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    iterator = iter_waymo_frames(
        config.dataset,
        start_index=frame_start,
        count=frame_count,
    )
    for offset in range(frame_count):
        frame_index = frame_start + offset
        started = time.perf_counter()
        frame = next(iterator)
        load_ms = (time.perf_counter() - started) * 1000.0
        scene_config = replace(
            config,
            dataset=replace(config.dataset, frame_index=frame_index),
            output=OutputConfig(root=batch_dir, run_id=f"frame-{frame_index:06d}"),
        )
        result = run_loaded_scene(scene_config, frame)
        timings = {"load_frame": round(load_ms, 3), **result.timings_ms}
        write_json_artifact(result.run_dir, "timings", timings)
        scenes.append(_scene_record(result, frame_index=frame_index, timings_ms=timings))
    return scenes


def run_batch(
    config: DriverConfig,
    fixture_names: list[str] | None = None,
    frame_start: int | None = None,
    frame_count: int | None = None,
) -> dict[str, Any]:
    batch_dir = prepare_run_dir(config.output.root, config.output.run_id)
    batch_id = batch_dir.name

    if fixture_names is not None:
        if not fixture_names:
            raise ValueError("At least one fixture is required for run-batch.")
        scenes = _run_fixture_batch(config, batch_dir, fixture_names)
        dataset_kind = "fixture"
        effective_frame_start = None
        effective_frame_count = len(scenes)
    elif config.dataset.kind == "fixture":
        scenes = _run_fixture_batch(config, batch_dir, list(DEFAULT_FIXTURE_BATCH_NAMES))
        dataset_kind = "fixture"
        effective_frame_start = None
        effective_frame_count = len(scenes)
    elif config.dataset.kind == "waymo":
        effective_frame_start = (
            config.dataset.frame_index if frame_start is None else frame_start
        )
        if frame_count is not None:
            effective_frame_count = frame_count
        elif config.dataset.limit is not None:
            effective_frame_count = config.dataset.limit - effective_frame_start
        else:
            effective_frame_count = DEFAULT_WAYMO_BATCH_COUNT
        if effective_frame_count <= 0:
            raise ValueError("Waymo frame_count must be positive.")
        scenes = _run_waymo_batch(
            config,
            batch_dir,
            effective_frame_start,
            effective_frame_count,
        )
        dataset_kind = "waymo"
    else:
        raise ValueError(f"Unsupported dataset kind for run-batch: {config.dataset.kind}")

    summary = _finalize_summary(
        config=config,
        batch_dir=batch_dir,
        batch_id=batch_id,
        dataset_kind=dataset_kind,
        frame_start=effective_frame_start,
        frame_count=effective_frame_count,
        scenes=scenes,
    )
    return summary
