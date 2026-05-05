"""Evidence reports for DriverX companion overlay injection runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.behaviors import default_behavior_plans, simulate_behavior


@dataclass(frozen=True)
class OverlayEvidenceInputs:
    overlay_plan_path: Path
    overlay_run_path: Path | None = None
    route_evidence_path: Path | None = None


def build_overlay_evidence(run_dir: Path, inputs: OverlayEvidenceInputs) -> dict[str, Any]:
    plan_path = inputs.overlay_plan_path.expanduser()
    plan = _load_json(plan_path)
    run = _load_optional_json(inputs.overlay_run_path)
    route_evidence = _load_optional_json(inputs.route_evidence_path)
    routes = [dict(route) for route in list(plan.get("routes", [])) if isinstance(route, dict)]
    tracks = _load_tracks(run, inputs.overlay_run_path)
    route_links = _route_links(routes, run)
    cleanup = _cleanup_summary(run)
    behavior_assertions = _behavior_assertions(routes)
    blockers = _blockers(
        overlay_run_path=inputs.overlay_run_path,
        run=run,
        routes=routes,
        tracks=tracks,
        cleanup=cleanup,
        behavior_assertions=behavior_assertions,
    )
    payload = {
        "status": _status(blockers, run),
        "overlay_plan_path": str(plan_path),
        "overlay_run_path": str(inputs.overlay_run_path.expanduser()) if inputs.overlay_run_path else None,
        "route_evidence_path": str(inputs.route_evidence_path.expanduser()) if inputs.route_evidence_path else None,
        "route_pack_path": plan.get("route_pack_path"),
        "route_suite_path": plan.get("route_suite_path"),
        "recipe_ids": [route["recipe_id"] for route in route_links],
        "route_links": route_links,
        "behavior_assertions": behavior_assertions,
        "track_summary": tracks,
        "cleanup": cleanup,
        "route_evidence_summary": _route_evidence_summary(route_evidence),
        "blockers": blockers,
    }
    return write_overlay_evidence(run_dir, payload)


def write_overlay_evidence(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "overlay_evidence.json"
    report_path = run_dir / "overlay_evidence.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Overlay plan not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _load_optional_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    expanded = path.expanduser()
    if not expanded.exists():
        return {"__missing_path__": str(expanded)}
    payload = json.loads(expanded.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {expanded}")
    return payload


def _load_tracks(run: dict[str, Any], run_path: Path | None) -> dict[str, Any]:
    raw_path = run.get("tracks_path")
    tracks_path = _resolve_embedded_path(raw_path, run_path)
    if tracks_path is None:
        return {"path": None, "exists": False, "track_count": 0, "actor_refs": []}
    if not tracks_path.exists():
        return {"path": str(tracks_path), "exists": False, "track_count": 0, "actor_refs": []}
    payload = json.loads(tracks_path.read_text(encoding="utf-8"))
    tracks = [dict(track) for track in payload if isinstance(track, dict)] if isinstance(payload, list) else []
    actor_refs = sorted(
        {
            str(track.get("actor_ref"))
            for track in tracks
            if track.get("actor_ref") is not None
        }
    )
    recipe_ids = sorted(
        {
            str(track.get("recipe_id"))
            for track in tracks
            if track.get("recipe_id") is not None
        }
    )
    return {
        "path": str(tracks_path),
        "exists": True,
        "track_count": len(tracks),
        "actor_refs": actor_refs,
        "recipe_ids": recipe_ids,
        "tracks": tracks,
    }


def _resolve_embedded_path(raw_path: Any, owner_path: Path | None) -> Path | None:
    if raw_path in (None, ""):
        return None
    path = Path(str(raw_path)).expanduser()
    if path.is_absolute() or owner_path is None:
        return path
    return owner_path.expanduser().parent / path


def _route_links(routes: list[dict[str, Any]], run: dict[str, Any]) -> list[dict[str, Any]]:
    result_by_recipe = {
        str(result.get("recipe_id")): dict(result)
        for result in list(run.get("route_results", []))
        if isinstance(result, dict) and result.get("recipe_id") is not None
    }
    links: list[dict[str, Any]] = []
    for route in routes:
        recipe_id = str(route.get("recipe_id", "unknown-route"))
        result = result_by_recipe.get(recipe_id, {})
        links.append(
            {
                "recipe_id": recipe_id,
                "behavior_id": route.get("behavior_id"),
                "mutation": route.get("mutation"),
                "expected_failure_mode": route.get("expected_failure_mode"),
                "route_path": route.get("route_path"),
                "overlay_path": route.get("overlay_path"),
                "run_connected": run.get("connected"),
                "spawned_actor_ids": result.get("spawned_actor_ids", []),
                "destroyed_actor_ids": result.get("destroyed_actor_ids", []),
                "applied_tick_count": result.get("applied_tick_count"),
                "track_count": result.get("track_count"),
                "error": result.get("error"),
            }
        )
    return links


def _cleanup_summary(run: dict[str, Any]) -> dict[str, Any]:
    spawned = [int(actor_id) for actor_id in list(run.get("spawned_actor_ids", []))]
    destroyed = [int(actor_id) for actor_id in list(run.get("destroyed_actor_ids", []))]
    spawned_set = set(spawned)
    destroyed_set = set(destroyed)
    return {
        "spawned_actor_ids": spawned,
        "destroyed_actor_ids": destroyed,
        "all_destroyed": bool(spawned) and spawned_set.issubset(destroyed_set),
        "undestroyed_actor_ids": sorted(spawned_set - destroyed_set),
    }


def _behavior_assertions(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    behavior_plans = {plan.behavior_id: plan for plan in default_behavior_plans()}
    assertions: list[dict[str, Any]] = []
    for route in routes:
        behavior_id = str(route.get("behavior_id", ""))
        plan = behavior_plans.get(behavior_id)
        if plan is None:
            assertions.append(
                {
                    "recipe_id": route.get("recipe_id"),
                    "behavior_id": behavior_id,
                    "passed": False,
                    "reason": f"Unknown behavior_id: {behavior_id}",
                    "metrics": {},
                }
            )
            continue
        trace = simulate_behavior(plan)
        passed, reason = _check_behavior_metrics(behavior_id, trace.metrics)
        assertions.append(
            {
                "recipe_id": route.get("recipe_id"),
                "behavior_id": behavior_id,
                "passed": passed,
                "reason": reason,
                "metrics": trace.metrics,
            }
        )
    return assertions


def _check_behavior_metrics(behavior_id: str, metrics: dict[str, float]) -> tuple[bool, str]:
    if behavior_id == "no_signal_cut_in":
        passed = metrics.get("lateral_displacement_m", 0.0) >= 2.0
        return passed, "lateral displacement creates a lane-change pressure"
    if behavior_id == "sudden_brake":
        passed = metrics.get("max_deceleration_mps2", 0.0) >= 5.0
        return passed, "deceleration creates rear-end pressure"
    if behavior_id == "motorcycle_filtering":
        passed = (
            metrics.get("lateral_displacement_m", 0.0) >= 1.5
            and metrics.get("max_heading_abs_deg", 0.0) >= 4.0
        )
        return passed, "lateral weave creates filtering pressure"
    return True, "behavior trace has a generated metric contract"


def _route_evidence_summary(route_evidence: dict[str, Any]) -> dict[str, Any] | None:
    if not route_evidence:
        return None
    return {
        "status": route_evidence.get("status"),
        "video": route_evidence.get("video"),
        "metrics": route_evidence.get("metrics"),
        "blocker_count": len(list(route_evidence.get("blockers", []))),
    }


def _blockers(
    *,
    overlay_run_path: Path | None,
    run: dict[str, Any],
    routes: list[dict[str, Any]],
    tracks: dict[str, Any],
    cleanup: dict[str, Any],
    behavior_assertions: list[dict[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    if overlay_run_path is None:
        blockers.append("Missing live overlay run path; run `run-overlay-injection` against CARLA first.")
    elif run.get("__missing_path__"):
        blockers.append(f"Missing live overlay run: {run['__missing_path__']}")
    if run and run.get("connected") is False:
        error = run.get("error") or "unknown CARLA connection failure"
        blockers.append(f"Live CARLA overlay run failed cleanly: {error}")
    if not routes:
        blockers.append("Overlay plan contains no routes.")
    if run and run.get("connected") is True and not cleanup.get("all_destroyed"):
        blockers.append(f"Overlay cleanup incomplete; undestroyed actors: {cleanup.get('undestroyed_actor_ids')}")
    if run and run.get("connected") is True and not tracks.get("exists"):
        blockers.append(f"Overlay tracks missing: {tracks.get('path')}")
    for assertion in behavior_assertions:
        if assertion.get("passed") is not True:
            blockers.append(
                f"Behavior assertion failed for {assertion.get('recipe_id')} "
                f"({assertion.get('behavior_id')}): {assertion.get('reason')}"
            )
    return blockers


def _status(blockers: list[str], run: dict[str, Any]) -> str:
    if not blockers and run.get("connected") is True:
        return "ready"
    if run.get("connected") is True:
        return "partial"
    return "blocked"


def _markdown(payload: dict[str, Any]) -> str:
    cleanup = dict(payload.get("cleanup", {}))
    tracks = dict(payload.get("track_summary", {}))
    lines = [
        "# Overlay Evidence",
        "",
        f"- status: `{payload.get('status')}`",
        f"- route_count: `{len(list(payload.get('route_links', [])))}`",
        f"- recipes: `{', '.join(payload.get('recipe_ids', []))}`",
        f"- track_count: `{tracks.get('track_count')}`",
        f"- all_destroyed: `{cleanup.get('all_destroyed')}`",
        f"- blockers: `{len(list(payload.get('blockers', [])))}`",
        "",
        "## Behavior Assertions",
        "",
    ]
    for assertion in list(payload.get("behavior_assertions", [])):
        lines.append(
            f"- `{assertion.get('recipe_id')}` / `{assertion.get('behavior_id')}`: "
            f"passed=`{assertion.get('passed')}` reason=`{assertion.get('reason')}`"
        )
    lines.extend(["", "## Route Links", ""])
    for route in list(payload.get("route_links", [])):
        lines.append(
            f"- `{route.get('recipe_id')}`: spawned `{route.get('spawned_actor_ids')}`, "
            f"destroyed `{route.get('destroyed_actor_ids')}`, tracks `{route.get('track_count')}`"
        )
    lines.extend(["", "## Blockers", ""])
    blockers = [str(blocker) for blocker in list(payload.get("blockers", []))]
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "OverlayEvidenceInputs",
    "build_overlay_evidence",
    "write_overlay_evidence",
]
