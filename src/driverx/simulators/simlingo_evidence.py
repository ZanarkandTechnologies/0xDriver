"""Classify compact remote SimLingo evidence artifacts."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.simulators.simlingo_results import (
    compact_simlingo_result_summary,
    parse_simlingo_result,
    write_simlingo_result_report,
)


@dataclass(frozen=True)
class SimLingoEvidenceScan:
    artifact_root: Path
    state: str
    blockers: list[str]
    bootstrap_log_path: Path | None
    bootstrap_complete: bool
    bootstrap_markers: dict[str, bool]
    bootstrap_tail: str | None
    route_result_paths: list[Path]
    selected_result_path: Path | None
    route_log_path: Path | None
    compatibility_path: Path | None
    diagnostics_path: Path | None
    result_summary: dict[str, Any] | None

    @property
    def has_route_result(self) -> bool:
        return self.selected_result_path is not None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "artifact_root": str(self.artifact_root),
            "state": self.state,
            "blockers": self.blockers,
            "bootstrap_log_path": _path_str(self.bootstrap_log_path),
            "bootstrap_complete": self.bootstrap_complete,
            "bootstrap_markers": self.bootstrap_markers,
            "bootstrap_tail": self.bootstrap_tail,
            "route_result_paths": [str(path) for path in self.route_result_paths],
            "selected_result_path": _path_str(self.selected_result_path),
            "route_log_path": _path_str(self.route_log_path),
            "compatibility_path": _path_str(self.compatibility_path),
            "diagnostics_path": _path_str(self.diagnostics_path),
            "result_summary": self.result_summary,
        }


def scan_simlingo_evidence(artifact_root: Path) -> SimLingoEvidenceScan:
    artifact_root = artifact_root.expanduser()
    if not artifact_root.exists():
        return SimLingoEvidenceScan(
            artifact_root=artifact_root,
            state="artifact_root_missing",
            blockers=[f"Artifact root does not exist: {artifact_root}"],
            bootstrap_log_path=None,
            bootstrap_complete=False,
            bootstrap_markers={},
            bootstrap_tail=None,
            route_result_paths=[],
            selected_result_path=None,
            route_log_path=None,
            compatibility_path=None,
            diagnostics_path=None,
            result_summary=None,
        )

    bootstrap_log = _first_existing(
        [
            artifact_root / "bootstrap.log",
            *sorted(artifact_root.glob("**/bootstrap.log")),
        ]
    )
    bootstrap_summary = _bootstrap_summary(bootstrap_log)
    route_results = _route_result_paths(artifact_root)
    selected_result = route_results[0] if route_results else None
    route_log = _first_existing(
        [
            artifact_root / "run_one_route_with_carla.log",
            artifact_root / "run_one_route.log",
            *sorted(artifact_root.glob("**/run_one_route_with_carla.log")),
            *sorted(artifact_root.glob("**/run_one_route.log")),
        ]
    )
    compatibility = _first_existing(
        [
            artifact_root / "torch_cuda_compatibility.json",
            *sorted(artifact_root.glob("**/torch_cuda_compatibility.json")),
        ]
    )
    diagnostics = _first_existing(
        [
            artifact_root / "carla_runtime_diagnostics.md",
            *sorted(artifact_root.glob("**/carla_runtime_diagnostics.md")),
        ]
    )
    result_summary = _result_summary(selected_result, compatibility, route_log)
    route_log_summary = _route_log_signals(route_log)
    blockers = _blockers(
        artifact_root=artifact_root,
        bootstrap_complete=bootstrap_summary["complete"],
        route_results=route_results,
        result_summary=result_summary,
        bootstrap_markers=bootstrap_summary["markers"],
        route_log_path=route_log,
        route_log_summary=route_log_summary,
    )
    return SimLingoEvidenceScan(
        artifact_root=artifact_root,
        state=_state(
            bootstrap_complete=bootstrap_summary["complete"],
            route_results=route_results,
            result_summary=result_summary,
            blockers=blockers,
        ),
        blockers=blockers,
        bootstrap_log_path=bootstrap_log,
        bootstrap_complete=bootstrap_summary["complete"],
        bootstrap_markers=bootstrap_summary["markers"],
        bootstrap_tail=bootstrap_summary["tail"],
        route_result_paths=route_results,
        selected_result_path=selected_result,
        route_log_path=route_log,
        compatibility_path=compatibility,
        diagnostics_path=diagnostics,
        result_summary=result_summary,
    )


def write_simlingo_evidence_report(run_dir: Path, scan: SimLingoEvidenceScan) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    result_report_summary = None
    if scan.selected_result_path is not None:
        result_report_summary = write_simlingo_result_report(
            run_dir / "simlingo-result",
            parse_simlingo_result(scan.selected_result_path),
            compatibility_path=scan.compatibility_path,
            route_log_path=scan.route_log_path,
        )
    payload = {
        **scan.to_jsonable(),
        "result_report": compact_simlingo_result_summary(result_report_summary)
        if result_report_summary
        else None,
    }
    json_path = run_dir / "remote_simlingo_evidence.json"
    report_path = run_dir / "remote_simlingo_evidence.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_evidence_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def compact_simlingo_evidence_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": summary.get("state"),
        "blockers": summary.get("blockers", []),
        "selected_result_path": summary.get("selected_result_path"),
        "route_log_path": summary.get("route_log_path"),
        "compatibility_path": summary.get("compatibility_path"),
        "diagnostics_path": summary.get("diagnostics_path"),
        "result_report": summary.get("result_report"),
        "json_path": summary.get("json_path"),
        "report_path": summary.get("report_path"),
    }


def _route_result_paths(root: Path) -> list[Path]:
    candidates = sorted(root.glob("**/*_res.json"))
    result_paths: list[Path] = []
    for candidate in candidates:
        if candidate.name == "simlingo_result_record.json":
            continue
        if _looks_like_simlingo_result(candidate):
            result_paths.append(candidate)
    return sorted(result_paths, key=lambda path: (len(path.parts), str(path)))


def _looks_like_simlingo_result(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and isinstance(payload.get("_checkpoint"), dict)


def _result_summary(
    selected_result: Path | None,
    compatibility_path: Path | None,
    route_log_path: Path | None,
) -> dict[str, Any] | None:
    if selected_result is None:
        return None
    record = parse_simlingo_result(selected_result)
    route_log = _route_log_signals(route_log_path)
    compatibility = _load_optional_json(compatibility_path)
    summary = {
        "record": record.to_jsonable(),
        "compatibility": compatibility,
        "route_log": route_log,
        "blocker": _result_blocker(record, compatibility, route_log),
    }
    return compact_simlingo_result_summary(summary)


def _bootstrap_summary(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "complete": False,
            "markers": {},
            "tail": None,
        }
    markers = {
        "runtime_python_packages": False,
        "torch_cuda_compatibility": False,
        "huggingface_checkpoint": False,
        "driverx_remote_checks": False,
        "next_manual_live_command": False,
        "bootstrap_complete": False,
        "traceback": False,
        "error": False,
        "failed": False,
    }
    tail: deque[str] = deque(maxlen=40)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            lowered = line.lower()
            tail.append(line)
            markers["runtime_python_packages"] |= "== runtime python packages ==" in line
            markers["torch_cuda_compatibility"] |= "== torch cuda compatibility ==" in line
            markers["huggingface_checkpoint"] |= "== huggingface checkpoint ==" in line
            markers["driverx_remote_checks"] |= "== driverx remote checks ==" in line
            markers["next_manual_live_command"] |= "== next manual/live command ==" in line
            markers["bootstrap_complete"] |= "bootstrap complete:" in line
            markers["traceback"] |= "Traceback" in line
            markers["error"] |= "ERROR" in line or "Error" in line
            markers["failed"] |= "failed" in lowered
    return {
        "complete": markers["bootstrap_complete"],
        "markers": markers,
        "tail": "\n".join(tail),
    }


def _route_log_signals(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    signals = [
        "load_world success",
        "traffic_manager init success",
        "> Running the route",
        "CARLA did not open port",
        "CUDA error: no kernel image is available for execution on the device",
        "Finished route",
        "Agent crashed",
    ]
    return {
        "path": str(path),
        "signals": {signal: signal in text for signal in signals},
    }


def _result_blocker(record: Any, compatibility: dict[str, Any] | None, route_log: dict[str, Any] | None) -> str | None:
    if record.success:
        return None
    signals = dict(route_log.get("signals") or {}) if route_log else {}
    if signals.get("CUDA error: no kernel image is available for execution on the device"):
        required = compatibility.get("required_arch") if compatibility else None
        compiled = compatibility.get("compiled_arches") if compatibility else None
        return (
            "CUDA no-kernel-image at first model tick"
            + (f"; required `{required}`, compiled arches `{compiled}`" if required else "")
        )
    return record.exception_summary or record.status


def _blockers(
    *,
    artifact_root: Path,
    bootstrap_complete: bool,
    route_results: list[Path],
    result_summary: dict[str, Any] | None,
    bootstrap_markers: dict[str, bool],
    route_log_path: Path | None,
    route_log_summary: dict[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    if not any(artifact_root.iterdir()):
        return [f"Artifact root is empty: {artifact_root}"]
    if result_summary and result_summary.get("blocker"):
        blockers.append(str(result_summary["blocker"]))
    if route_results:
        return blockers
    if route_log_path is not None:
        route_signals = dict(route_log_summary.get("signals") or {}) if route_log_summary else {}
        if route_signals.get("CARLA did not open port"):
            blockers.append(
                "CARLA server did not open port before route execution; "
                f"route log: {route_log_path}"
            )
            return blockers
        blockers.append(f"Route log exists but no SimLingo `*_res.json` result was found: {route_log_path}")
    elif bootstrap_complete:
        blockers.append("Bootstrap completed but no route result has been pulled yet.")
    elif bootstrap_markers.get("traceback") or bootstrap_markers.get("error"):
        blockers.append("Bootstrap log contains error markers before completion.")
    else:
        blockers.append("Bootstrap appears incomplete or still running; no route result has been pulled yet.")
    return blockers


def _state(
    *,
    bootstrap_complete: bool,
    route_results: list[Path],
    result_summary: dict[str, Any] | None,
    blockers: list[str],
) -> str:
    if route_results and result_summary and not result_summary.get("blocker"):
        return "route_result_success"
    if route_results:
        return "route_result_blocked"
    if blockers and any("CARLA server did not open port" in blocker for blocker in blockers):
        return "route_infrastructure_blocked"
    if bootstrap_complete:
        return "bootstrap_complete_no_route_result"
    if blockers:
        return "bootstrap_incomplete"
    return "unknown"


def _evidence_markdown(payload: dict[str, Any]) -> str:
    result_report = payload.get("result_report") or {}
    record = result_report.get("record") if isinstance(result_report, dict) else {}
    primary_route = result_report.get("primary_route") if isinstance(result_report, dict) else {}
    lines = [
        "# Remote SimLingo Evidence",
        "",
        f"- state: `{payload['state']}`",
        f"- artifact_root: `{payload['artifact_root']}`",
        f"- bootstrap_complete: `{payload['bootstrap_complete']}`",
        f"- selected_result_path: `{payload.get('selected_result_path')}`",
        f"- route_log_path: `{payload.get('route_log_path')}`",
        f"- compatibility_path: `{payload.get('compatibility_path')}`",
        f"- diagnostics_path: `{payload.get('diagnostics_path')}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = payload.get("blockers") or []
    lines.extend([*(f"- {blocker}" for blocker in blockers)] or ["None."])
    if record:
        lines.extend(
            [
                "",
                "## Route Result",
                "",
                f"- success: `{record.get('success')}`",
                f"- status: `{record.get('status')}`",
                f"- driving_score: `{record.get('driving_score')}`",
                f"- route_completion: `{record.get('route_completion')}`",
                f"- primary_route: `{primary_route.get('route_id')}`",
                f"- primary_scenario: `{primary_route.get('scenario_name')}`",
                f"- blocker: `{result_report.get('blocker')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Bootstrap Markers",
            "",
            *(
                f"- `{key}`: `{value}`"
                for key, value in dict(payload.get("bootstrap_markers") or {}).items()
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _load_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _path_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None


__all__ = [
    "SimLingoEvidenceScan",
    "compact_simlingo_evidence_summary",
    "scan_simlingo_evidence",
    "write_simlingo_evidence_report",
]
