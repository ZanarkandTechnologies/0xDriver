"""Submission-facing report for generated OOD suite evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OodSuiteInput:
    label: str
    path: Path | None


def build_ood_suite_report(
    run_dir: Path,
    *,
    scenario_summary_path: Path | None = None,
    route_pack_path: Path | None = None,
    overlay_plan_path: Path | None = None,
    sidecar_plan_path: Path | None = None,
    sidecar_run_path: Path | None = None,
    rag_comparison_path: Path | None = None,
    simlingo_result_path: Path | None = None,
    blockers_path: Path | None = None,
) -> dict[str, Any]:
    """Normalize current OOD evidence artifacts into one manifest/report."""

    inputs = [
        OodSuiteInput("scenario_summary", scenario_summary_path),
        OodSuiteInput("route_pack", route_pack_path),
        OodSuiteInput("overlay_plan", overlay_plan_path),
        OodSuiteInput("sidecar_plan", sidecar_plan_path),
        OodSuiteInput("sidecar_run", sidecar_run_path),
        OodSuiteInput("rag_comparison", rag_comparison_path),
        OodSuiteInput("simlingo_result", simlingo_result_path),
        OodSuiteInput("blockers", blockers_path),
    ]
    components = [_component_summary(item) for item in inputs if item.path is not None]
    if not components:
        raise ValueError("At least one OOD suite evidence input path is required.")
    summary = {
        "component_count": len(components),
        "present_components": [component["label"] for component in components if component["status"] != "missing"],
        "missing_components": [component["label"] for component in components if component["status"] == "missing"],
        "readiness": _readiness(components),
        "metric_highlights": _metric_highlights(components),
        "open_blockers": _open_blockers(components),
        "components": components,
    }
    return write_ood_suite_report(run_dir, summary)


def write_ood_suite_report(run_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "ood_suite_manifest.json"
    report_path = run_dir / "ood_suite_report.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(summary), encoding="utf-8")
    return {
        **summary,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _component_summary(input_item: OodSuiteInput) -> dict[str, Any]:
    assert input_item.path is not None
    path = input_item.path.expanduser()
    if not path.exists():
        return {
            "label": input_item.label,
            "status": "missing",
            "path": str(path),
            "metrics": {},
            "blockers": [f"Missing artifact: {path}"],
        }
    if input_item.label == "blockers":
        return _blocker_component(input_item.label, path)
    payload = _load_json(path)
    metrics, blockers, status = _extract_component_signals(input_item.label, payload)
    return {
        "label": input_item.label,
        "status": status,
        "path": str(path),
        "metrics": metrics,
        "blockers": blockers,
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _extract_component_signals(label: str, payload: dict[str, Any]) -> tuple[dict[str, Any], list[str], str]:
    if label == "scenario_summary":
        recipes = list(payload.get("recipes", []))
        seeds = list(payload.get("seeds", []))
        mutation_counts = _mapping(payload.get("mutation_counts"))
        mutations = sorted(str(key) for key in mutation_counts if str(key))
        if not mutations:
            mutations = sorted(
                {
                    str(recipe.get("mutation", {}).get("kind"))
                    for recipe in recipes
                    if isinstance(recipe, dict) and isinstance(recipe.get("mutation"), dict)
                }
                - {""}
            )
        return {
            "seed_count": _prefer_count(payload, "seed_count", seeds),
            "recipe_count": _prefer_count(payload, "recipe_count", recipes),
            "mutations": mutations,
        }, [], "ready"
    if label == "route_pack":
        routes = list(payload.get("routes", payload.get("exports", [])))
        return {
            "route_count": _prefer_count(payload, "route_count", routes),
            "route_suite_path": payload.get("route_suite_path"),
            "simlingo_plan_path": payload.get("simlingo_plan_path")
            or payload.get("simlingo_command_plan_path"),
        }, [], "ready"
    if label == "overlay_plan":
        routes = list(payload.get("routes", []))
        validation_errors = list(payload.get("validation_errors", []))
        companion_count = sum(
            1
            for route in routes
            for actor in list(_mapping(_mapping(route).get("script_plan")).get("actors", []))
            if str(_mapping(actor).get("actor_ref", "")).startswith("companion_actor")
        )
        return {
            "route_count": _prefer_count(payload, "route_count", routes),
            "companion_actor_count": companion_count,
            "validation_error_count": len(validation_errors),
        }, [str(error) for error in validation_errors], "blocked" if validation_errors else "ready"
    if label == "sidecar_plan":
        commands = list(payload.get("commands", []))
        blockers = [str(blocker) for blocker in list(payload.get("blockers", []))]
        return {
            "command_count": len(commands),
            "expected_output_count": len(list(payload.get("expected_outputs", []))),
        }, blockers, "blocked" if blockers else "ready"
    if label == "sidecar_run":
        blockers = [str(blocker) for blocker in list(payload.get("plan_blockers", []))]
        error = payload.get("error")
        if error:
            blockers.append(str(error))
        return {
            "success": payload.get("success"),
            "duration_s": payload.get("duration_s"),
            "process_count": len(list(payload.get("process_records", []))),
        }, blockers, "passed" if payload.get("success") is True else "blocked"
    if label == "rag_comparison":
        improvement = _mapping(payload.get("improvement"))
        return {
            "policy": payload.get("policy"),
            "scenario_id": payload.get("scenario_id"),
            "driving_score_delta": improvement.get("driving_score_delta"),
            "infraction_delta": improvement.get("infraction_delta"),
            "live_model_claim": payload.get("live_model_claim"),
        }, [], "ready"
    if label == "simlingo_result":
        record = _mapping(payload.get("record"))
        primary = _mapping(record.get("primary_route"))
        blocker = payload.get("blocker")
        return {
            "success": record.get("success"),
            "status": record.get("status"),
            "driving_score": record.get("driving_score"),
            "route_completion": record.get("route_completion"),
            "primary_route": primary.get("route_id"),
        }, [str(blocker)] if blocker else [], "passed" if record.get("success") is True else "blocked"
    return {}, [], "ready"


def _blocker_component(label: str, path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    open_blockers = _parse_open_blockers(text)
    return {
        "label": label,
        "status": "blocked" if open_blockers else "ready",
        "path": str(path),
        "metrics": {"open_blocker_count": len(open_blockers)},
        "blockers": open_blockers,
    }


def _parse_open_blockers(text: str) -> list[str]:
    lines = text.splitlines()
    in_open = False
    blockers: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if _is_open_blocker_heading(stripped):
            in_open = True
            continue
        if in_open and stripped.startswith("#"):
            break
        if not in_open:
            continue
        if stripped.startswith(("- ", "* ")):
            if current:
                blockers.append(" ".join(current).strip())
            current = [stripped[2:].strip()]
        elif current and (line.startswith("  ") or line.startswith("\t")):
            current.append(stripped)
    if current:
        blockers.append(" ".join(current).strip())
    return [blocker for blocker in blockers if blocker and blocker.lower() != "none currently."]


def _is_open_blocker_heading(stripped: str) -> bool:
    if not stripped.startswith("#"):
        return False
    heading = stripped.lstrip("#").strip().lower()
    return heading in {"open", "open blockers", "current blockers"}


def _readiness(components: list[dict[str, Any]]) -> dict[str, Any]:
    by_label = {component["label"]: component for component in components}
    return {
        "scenario_generation_ready": _is_present_ready(by_label, "scenario_summary"),
        "bench2drive_route_pack_ready": _is_present_ready(by_label, "route_pack"),
        "overlay_injection_ready": _is_present_ready(by_label, "overlay_plan"),
        "sidecar_launch_ready": _is_present_ready(by_label, "sidecar_plan"),
        "sidecar_run_passed": by_label.get("sidecar_run", {}).get("status") == "passed",
        "live_policy_result_passed": by_label.get("simlingo_result", {}).get("status") == "passed",
        "has_open_blockers": bool(_open_blockers(components)),
    }


def _is_present_ready(by_label: dict[str, dict[str, Any]], label: str) -> bool:
    return by_label.get(label, {}).get("status") in {"ready", "passed"}


def _metric_highlights(components: list[dict[str, Any]]) -> dict[str, Any]:
    highlights: dict[str, Any] = {}
    for component in components:
        label = str(component["label"])
        metrics = _mapping(component.get("metrics"))
        if label == "scenario_summary":
            highlights["generated_recipe_count"] = metrics.get("recipe_count")
            highlights["mutation_count"] = len(list(metrics.get("mutations", [])))
        elif label == "route_pack":
            highlights["bench2drive_route_count"] = metrics.get("route_count")
        elif label == "overlay_plan":
            highlights["companion_actor_count"] = metrics.get("companion_actor_count")
        elif label == "sidecar_run":
            highlights["sidecar_run_success"] = metrics.get("success")
            highlights["sidecar_duration_s"] = metrics.get("duration_s")
        elif label == "rag_comparison":
            highlights["rag_driving_score_delta"] = metrics.get("driving_score_delta")
        elif label == "simlingo_result":
            highlights["simlingo_success"] = metrics.get("success")
            highlights["simlingo_driving_score"] = metrics.get("driving_score")
    return highlights


def _open_blockers(components: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for component in components:
        for blocker in list(component.get("blockers", [])):
            blockers.append(f"{component['label']}: {blocker}")
    return blockers


def _prefer_count(payload: dict[str, Any], key: str, values: list[Any]) -> int:
    value = payload.get(key, payload.get("num_" + key.removesuffix("_count") + "s"))
    return int(value) if isinstance(value, int) else len(values)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _markdown(summary: dict[str, Any]) -> str:
    readiness = _mapping(summary.get("readiness"))
    lines = [
        "# OOD Suite Evidence Report",
        "",
        f"- component_count: `{summary['component_count']}`",
        f"- present_components: `{', '.join(summary['present_components'])}`",
        f"- missing_components: `{', '.join(summary['missing_components']) or 'none'}`",
        f"- has_open_blockers: `{readiness.get('has_open_blockers')}`",
        "",
        "## Readiness",
        "",
    ]
    for key, value in readiness.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Metric Highlights", ""])
    for key, value in _mapping(summary.get("metric_highlights")).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Components", "", "| Component | Status | Key metrics | Path |", "| --- | --- | --- | --- |"])
    for component in list(summary.get("components", [])):
        metrics = ", ".join(f"{key}={value}" for key, value in _mapping(component.get("metrics")).items())
        lines.append(
            f"| `{component['label']}` | `{component['status']}` | {metrics or 'none'} | `{component['path']}` |"
        )
    lines.extend(["", "## Open Blockers", ""])
    blockers = list(summary.get("open_blockers", []))
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


__all__ = [
    "build_ood_suite_report",
    "write_ood_suite_report",
]
