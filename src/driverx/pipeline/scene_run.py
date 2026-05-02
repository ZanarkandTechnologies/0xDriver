"""One-scene orchestration for fixture-backed 0xDriver runs."""

from __future__ import annotations

from typing import Any

from driverx.core.artifacts import prepare_run_dir, write_json_artifact
from driverx.core.config import DriverConfig
from driverx.core.timing import StageTimer
from driverx.core.types import ArtifactRef, FrameBundle, SceneRunResult, TrajectoryCandidate
from driverx.datasets import load_frame
from driverx.evaluation.ade import average_displacement_error
from driverx.planning.candidates import generate_candidates
from driverx.planning.ranking import rank_candidates
from driverx.planning.smoothing import smooth_candidate
from driverx.reasoning import build_reasoner
from driverx.submission.waymo_packager import package_run_dir
from driverx.vision.render import render_scene_svg


def _frame_payload(frame: FrameBundle) -> dict[str, Any]:
    return {
        "frame_name": frame.frame_name,
        "ego_history_xy": frame.ego_history_xy,
        "future_xy": frame.future_xy,
        "metadata": frame.metadata,
        "front_images": [
            {"name": image.name, "width": image.width, "height": image.height}
            for image in frame.front_images
        ],
    }


def _trajectory_payload(candidate: TrajectoryCandidate) -> dict[str, Any]:
    return {
        "source": candidate.source,
        "score": candidate.score,
        "metadata": candidate.metadata,
        "points_xy": candidate.points_xy,
    }


def _metadata_payload(config: DriverConfig) -> dict[str, Any]:
    return {
        "author": config.author,
        "affiliation": config.affiliation,
        "account_name": config.account_name,
        "method_name": config.method_name,
        "method_link": config.method_link,
        "description": config.description,
        "num_model_parameters": config.num_model_parameters,
        "dataset": {
            "kind": config.dataset.kind,
            "name": config.dataset.name,
            "path": str(config.dataset.path) if config.dataset.path else None,
            "frame_index": config.dataset.frame_index,
            "limit": config.dataset.limit,
        },
        "reasoner": {
            "backend": config.reasoner.backend,
            "uncertainty": config.reasoner.uncertainty,
        },
    }


def _fallback_intent(frame: FrameBundle, error: Exception) -> dict[str, Any]:
    return {
        "scene_type": "reasoner_validation_fallback",
        "hazards": [str(item) for item in frame.metadata.get("hazards", [])],
        "ego_intent": "fallback to safe stop after invalid reasoner output",
        "target_behavior": "stop",
        "speed_profile": "brake",
        "lateral_bias": "center",
        "uncertainty": 1.0,
        "validation_error": str(error),
    }


def inspect_scene(config: DriverConfig) -> SceneRunResult:
    timer = StageTimer()
    artifacts: list[ArtifactRef] = []
    run_dir = prepare_run_dir(config.output.root, config.output.run_id)
    with timer.track("load_frame"):
        frame = load_frame(config.dataset)
    artifacts.append(write_json_artifact(run_dir, "run_metadata", _metadata_payload(config)))
    artifacts.append(write_json_artifact(run_dir, "frame", _frame_payload(frame)))
    with timer.track("render_scene"):
        artifacts.append(render_scene_svg(frame, run_dir / "scene_inspection.svg"))
    metrics = {"mode": "inspect", "num_front_images": len(frame.front_images)}
    artifacts.append(write_json_artifact(run_dir, "metrics", metrics))
    artifacts.append(write_json_artifact(run_dir, "timings", timer.timings_ms))
    return SceneRunResult(
        frame_name=frame.frame_name,
        run_dir=run_dir,
        intent=None,
        selected_trajectory=None,
        metrics=metrics,
        timings_ms=timer.timings_ms,
        artifacts=artifacts,
    )


def run_scene(config: DriverConfig) -> SceneRunResult:
    timer = StageTimer()
    artifacts: list[ArtifactRef] = []
    run_dir = prepare_run_dir(config.output.root, config.output.run_id)

    with timer.track("load_frame"):
        frame = load_frame(config.dataset)
    artifacts.append(write_json_artifact(run_dir, "run_metadata", _metadata_payload(config)))
    artifacts.append(write_json_artifact(run_dir, "frame", _frame_payload(frame)))

    with timer.track("reason"):
        reasoner = build_reasoner(config.reasoner)
        try:
            intent = reasoner.infer_intent(frame)
        except ValueError as exc:
            error_payload = {
                "error_type": exc.__class__.__name__,
                "message": str(exc),
                "fallback": "safe_stop",
            }
            artifacts.append(write_json_artifact(run_dir, "reasoner_error", error_payload))
            from driverx.reasoning.schema import intent_from_mapping

            intent = intent_from_mapping(_fallback_intent(frame, exc))
    artifacts.append(write_json_artifact(run_dir, "intent", intent.__dict__))

    with timer.track("generate_candidates"):
        raw_candidates = generate_candidates(frame, intent)
    artifacts.append(
        write_json_artifact(
            run_dir,
            "raw_candidates",
            [_trajectory_payload(candidate) for candidate in raw_candidates],
        )
    )

    with timer.track("smooth_candidates"):
        candidates = [smooth_candidate(candidate) for candidate in raw_candidates]

    with timer.track("rank_candidates"):
        selected = rank_candidates(frame, candidates)
    artifacts.append(
        write_json_artifact(
            run_dir,
            "smoothed_candidates",
            [_trajectory_payload(candidate) for candidate in candidates],
        )
    )
    artifacts.append(write_json_artifact(run_dir, "selected_trajectory", _trajectory_payload(selected)))

    with timer.track("evaluate"):
        metrics: dict[str, Any] = {
            "mode": "run",
            "num_candidates": len(candidates),
            "selected_source": selected.source,
            "selected_score": selected.score,
        }
        if frame.future_xy is not None:
            metrics["ade"] = round(
                average_displacement_error(selected.points_xy, frame.future_xy),
                6,
            )
    artifacts.append(write_json_artifact(run_dir, "metrics", metrics))

    with timer.track("render_scene"):
        artifacts.append(
            render_scene_svg(
                frame,
                run_dir / "scene_prediction.svg",
                selected=selected,
                candidates=candidates,
            )
        )

    with timer.track("package_submission"):
        package = package_run_dir(run_dir)
    artifacts.append(ArtifactRef(name="submission_dry_run", path=run_dir / "submission_dry_run.json", kind="json"))
    artifacts.append(write_json_artifact(run_dir, "submission_summary", package))
    artifacts.append(write_json_artifact(run_dir, "timings", timer.timings_ms))

    return SceneRunResult(
        frame_name=frame.frame_name,
        run_dir=run_dir,
        intent=intent,
        selected_trajectory=selected,
        metrics=metrics,
        timings_ms=timer.timings_ms,
        artifacts=artifacts,
    )
