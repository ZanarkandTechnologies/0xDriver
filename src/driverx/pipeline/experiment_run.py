"""Cross-strategy batch experiment orchestration."""

from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir, write_json_artifact
from driverx.core.config import DriverConfig, OutputConfig
from driverx.core.types import FrameBundle, TrajectoryCandidate
from driverx.datasets import iter_waymo_frames, load_frame
from driverx.evaluation.ade import average_displacement_error
from driverx.pipeline.batch_run import DEFAULT_WAYMO_BATCH_COUNT
from driverx.pipeline.scene_run import run_loaded_scene
from driverx.planning.baselines import generate_rule_baselines
from driverx.planning.ranking import rank_candidates
from driverx.planning.smoothing import smooth_candidate

RULE_STRATEGIES = (
    "constant_velocity",
    "constant_acceleration",
    "cautious_stop",
)
ANALYSIS_ONLY_STRATEGIES = {"oracle_best_rule"}


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _trajectory_payload(candidate: TrajectoryCandidate) -> dict[str, Any]:
    return {
        "source": candidate.source,
        "score": candidate.score,
        "metadata": candidate.metadata,
        "points_xy": candidate.points_xy,
    }


def _ade(frame: FrameBundle, candidate: TrajectoryCandidate) -> float | None:
    if frame.future_xy is None:
        return None
    return round(average_displacement_error(candidate.points_xy, frame.future_xy), 6)


def _strategy_result(
    *,
    strategy: str,
    frame: FrameBundle,
    candidate: TrajectoryCandidate,
    trajectory_path: Path,
    run_dir: Path,
    analysis_only: bool = False,
) -> dict[str, Any]:
    return {
        "strategy": strategy,
        "frame_name": frame.frame_name,
        "source": candidate.source,
        "ade": _ade(frame, candidate),
        "score": candidate.score,
        "trajectory_path": str(trajectory_path),
        "run_dir": str(run_dir),
        "analysis_only": analysis_only,
    }


def _write_strategy_trajectory(
    frame_dir: Path,
    strategy: str,
    candidate: TrajectoryCandidate,
) -> Path:
    path = frame_dir / f"{strategy}_trajectory.json"
    path.write_text(json.dumps(_trajectory_payload(candidate), indent=2), encoding="utf-8")
    return path


def _best_by_ade(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [result for result in results if _number(result.get("ade")) is not None]
    if not scored:
        return None
    return min(scored, key=lambda result: float(result["ade"]))


def _worst_by_ade(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [result for result in results if _number(result.get("ade")) is not None]
    if not scored:
        return None
    return max(scored, key=lambda result: float(result["ade"]))


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _strategy_summaries(frames: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for frame in frames:
        strategies = frame.get("strategies", {})
        if not isinstance(strategies, dict):
            continue
        for strategy, result in strategies.items():
            if isinstance(result, dict):
                by_strategy.setdefault(strategy, []).append(result)

    summaries: dict[str, dict[str, Any]] = {}
    for strategy, results in sorted(by_strategy.items()):
        ade_values = [
            float(result["ade"])
            for result in results
            if _number(result.get("ade")) is not None
        ]
        summaries[strategy] = {
            "strategy": strategy,
            "analysis_only": strategy in ANALYSIS_ONLY_STRATEGIES,
            "num_scenes": len(results),
            "mean_ade": _mean(ade_values),
            "best_scene": _best_by_ade(results),
            "worst_scene": _worst_by_ade(results),
        }
    return summaries


def _best_strategy_by_mean(
    summaries: dict[str, dict[str, Any]],
    *,
    analysis_mode: str,
) -> str | None:
    if analysis_mode not in {"deployable", "analysis_only", "all"}:
        raise ValueError(f"Unsupported analysis_mode: {analysis_mode}")
    scored = [
        summary
        for summary in summaries.values()
        if _number(summary.get("mean_ade")) is not None
        and (
            analysis_mode == "all"
            or (analysis_mode == "analysis_only" and summary.get("analysis_only"))
            or (analysis_mode == "deployable" and not summary.get("analysis_only"))
        )
    ]
    if not scored:
        return None
    best = min(scored, key=lambda summary: float(summary["mean_ade"]))
    return str(best["strategy"])


def _markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


def _strategy_table(summaries: dict[str, dict[str, Any]]) -> list[str]:
    lines = [
        "| strategy | mean ADE | best ADE | worst ADE | analysis only |",
        "|---|---:|---:|---:|---|",
    ]
    for strategy, summary in summaries.items():
        best = summary.get("best_scene")
        worst = summary.get("worst_scene")
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(strategy),
                    _markdown_cell(summary.get("mean_ade")),
                    _markdown_cell(best.get("ade") if isinstance(best, dict) else None),
                    _markdown_cell(worst.get("ade") if isinstance(worst, dict) else None),
                    "yes" if summary.get("analysis_only") else "no",
                ]
            )
            + " |"
        )
    return lines


def _frame_table(frames: list[dict[str, Any]], summaries: dict[str, dict[str, Any]]) -> list[str]:
    strategies = list(summaries)
    lines = [
        "| frame index | frame name | " + " | ".join(strategies) + " |",
        "|---:|---|" + "|".join("---:" for _ in strategies) + "|",
    ]
    for frame in frames:
        cells = [
            _markdown_cell(frame.get("frame_index")),
            _markdown_cell(frame.get("frame_name")),
        ]
        frame_strategies = frame.get("strategies", {})
        for strategy in strategies:
            result = frame_strategies.get(strategy, {}) if isinstance(frame_strategies, dict) else {}
            cells.append(_markdown_cell(result.get("ade") if isinstance(result, dict) else None))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _write_report(experiment_dir: Path, summary: dict[str, Any]) -> Path:
    lines = [
        f"# Experiment Report: {summary['experiment_id']}",
        "",
        "## Summary",
        "",
        f"- Dataset kind: `{summary['dataset_kind']}`",
        f"- Frame start: `{summary.get('frame_start')}`",
        f"- Frame count: `{summary['frame_count']}`",
        f"- Scenes: `{summary['num_scenes']}`",
        f"- Best deployable strategy: `{summary.get('best_strategy_by_mean_ade')}`",
        f"- Best analysis-only strategy: `{summary.get('best_analysis_strategy_by_mean_ade')}`",
        "",
        "## Strategy Mean ADE",
        "",
        *_strategy_table(summary["strategy_summaries"]),
        "",
        "## Per-Frame ADE",
        "",
        *_frame_table(summary["frames"], summary["strategy_summaries"]),
        "",
        "## Notes",
        "",
        "- `oracle_best_rule` is analysis-only because it uses ground-truth ADE to select among rule baselines.",
        "- ADE is a local proxy metric, not the hidden Waymo rater-feedback metric.",
        "",
    ]
    report_path = experiment_dir / "experiment_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _rule_strategy_results(frame: FrameBundle, frame_dir: Path) -> dict[str, dict[str, Any]]:
    raw = generate_rule_baselines(frame)
    smoothed = [smooth_candidate(candidate) for candidate in raw]
    results: dict[str, dict[str, Any]] = {}
    for candidate in smoothed:
        strategy = str(candidate.metadata.get("strategy", candidate.source.replace("_smooth", "")))
        trajectory_path = _write_strategy_trajectory(frame_dir, strategy, candidate)
        results[strategy] = _strategy_result(
            strategy=strategy,
            frame=frame,
            candidate=candidate,
            trajectory_path=trajectory_path,
            run_dir=frame_dir,
        )

    ranked = rank_candidates(frame, smoothed)
    ranked_path = _write_strategy_trajectory(frame_dir, "rule_ranked", ranked)
    results["rule_ranked"] = _strategy_result(
        strategy="rule_ranked",
        frame=frame,
        candidate=ranked,
        trajectory_path=ranked_path,
        run_dir=frame_dir,
    )

    oracle = _best_by_ade(list(results.values()))
    if oracle is not None:
        oracle_strategy = str(oracle["strategy"])
        oracle_candidate = next(
            candidate
            for candidate in smoothed
            if str(candidate.metadata.get("strategy")) == oracle_strategy
        )
        oracle_path = _write_strategy_trajectory(frame_dir, "oracle_best_rule", oracle_candidate)
        results["oracle_best_rule"] = _strategy_result(
            strategy="oracle_best_rule",
            frame=frame,
            candidate=oracle_candidate,
            trajectory_path=oracle_path,
            run_dir=frame_dir,
            analysis_only=True,
        )

    write_json_artifact(frame_dir, "rule_baselines", results)
    return results


def _run_frame_experiment(
    config: DriverConfig,
    experiment_dir: Path,
    frame: FrameBundle,
    frame_index: int | None,
) -> dict[str, Any]:
    run_id = "fixture" if frame_index is None else f"frame-{frame_index:06d}"
    frame_dir = experiment_dir / run_id
    frame_dir.mkdir(parents=True, exist_ok=False)

    strategy_results: dict[str, dict[str, Any]] = {}
    intent_config = replace(
        config,
        output=OutputConfig(root=frame_dir, run_id="intent_planner"),
    )
    intent_result = run_loaded_scene(intent_config, frame)
    if intent_result.selected_trajectory is not None:
        trajectory_path = intent_result.run_dir / "selected_trajectory.json"
        strategy_results["intent_planner"] = _strategy_result(
            strategy="intent_planner",
            frame=frame,
            candidate=intent_result.selected_trajectory,
            trajectory_path=trajectory_path,
            run_dir=intent_result.run_dir,
        )

    strategy_results.update(_rule_strategy_results(frame, frame_dir))
    return {
        "frame_index": frame_index,
        "frame_name": frame.frame_name,
        "run_dir": str(frame_dir),
        "intent_planner_run_dir": str(intent_result.run_dir),
        "strategies": strategy_results,
    }


def _frames_for_experiment(
    config: DriverConfig,
    frame_start: int | None,
    frame_count: int | None,
) -> tuple[int | None, int, list[tuple[int | None, FrameBundle]], dict[str, float]]:
    timings: dict[str, float] = {}
    started = time.perf_counter()
    if config.dataset.kind == "fixture":
        frame = load_frame(config.dataset)
        timings["load_frames"] = round((time.perf_counter() - started) * 1000.0, 3)
        return None, 1, [(None, frame)], timings
    if config.dataset.kind == "waymo":
        effective_start = config.dataset.frame_index if frame_start is None else frame_start
        if frame_count is not None:
            effective_count = frame_count
        elif config.dataset.limit is not None:
            effective_count = config.dataset.limit - effective_start
        else:
            effective_count = DEFAULT_WAYMO_BATCH_COUNT
        if effective_count <= 0:
            raise ValueError("Waymo frame_count must be positive.")
        frames = [
            (effective_start + offset, frame)
            for offset, frame in enumerate(
                iter_waymo_frames(config.dataset, effective_start, effective_count)
            )
        ]
        timings["load_frames"] = round((time.perf_counter() - started) * 1000.0, 3)
        return effective_start, effective_count, frames, timings
    raise ValueError(f"Unsupported dataset kind for run-experiment: {config.dataset.kind}")


def run_experiment(
    config: DriverConfig,
    frame_start: int | None = None,
    frame_count: int | None = None,
) -> dict[str, Any]:
    experiment_dir = prepare_run_dir(config.output.root, config.output.run_id)
    experiment_id = experiment_dir.name
    effective_start, effective_count, frames, timings = _frames_for_experiment(
        config,
        frame_start,
        frame_count,
    )

    records: list[dict[str, Any]] = []
    for frame_index, frame in frames:
        records.append(_run_frame_experiment(config, experiment_dir, frame, frame_index))

    summaries = _strategy_summaries(records)
    summary_path = experiment_dir / "experiment_summary.json"
    report_path = experiment_dir / "experiment_report.md"
    summary = {
        "experiment_id": experiment_id,
        "experiment_dir": str(experiment_dir),
        "dataset_kind": config.dataset.kind,
        "frame_start": effective_start,
        "frame_count": effective_count,
        "num_scenes": len(records),
        "strategy_summaries": summaries,
        "best_strategy_by_mean_ade": _best_strategy_by_mean(
            summaries,
            analysis_mode="deployable",
        ),
        "best_analysis_strategy_by_mean_ade": _best_strategy_by_mean(
            summaries,
            analysis_mode="analysis_only",
        ),
        "timings_ms": timings,
        "frames": records,
        "summary_path": str(summary_path),
        "report_path": str(report_path),
    }
    report_path = _write_report(experiment_dir, summary)
    summary["report_path"] = str(report_path)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_json_artifact(
        experiment_dir,
        "run_metadata",
        {
            "author": config.author,
            "method_name": config.method_name,
            "dataset_kind": config.dataset.kind,
            "frame_start": effective_start,
            "frame_count": effective_count,
            "strategies": list(summaries),
        },
    )
    return summary
