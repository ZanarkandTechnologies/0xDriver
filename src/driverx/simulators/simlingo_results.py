"""Parse and report SimLingo/Bench2Drive result artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SimLingoRouteRecord:
    route_id: str | None
    scenario_name: str | None
    town_name: str | None
    status: str | None
    success: bool
    driving_score: float | None
    route_completion: float | None
    infraction_penalty: float | None
    duration_game_s: float | None
    duration_system_s: float | None
    infractions: dict[str, Any]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "scenario_name": self.scenario_name,
            "town_name": self.town_name,
            "status": self.status,
            "success": self.success,
            "driving_score": self.driving_score,
            "route_completion": self.route_completion,
            "infraction_penalty": self.infraction_penalty,
            "duration_game_s": self.duration_game_s,
            "duration_system_s": self.duration_system_s,
            "infractions": self.infractions,
        }


@dataclass(frozen=True)
class SimLingoRunRecord:
    source_path: Path
    entry_status: str | None
    eligible: bool | None
    status: str | None
    success: bool
    driving_score: float | None
    route_completion: float | None
    infraction_penalty: float | None
    duration_game_s: float | None
    duration_system_s: float | None
    infractions: dict[str, Any]
    sensors: list[str]
    exception_summary: str | None
    progress_completed: int | None
    progress_total: int | None
    route_count: int
    routes: list[SimLingoRouteRecord]

    @property
    def primary_route(self) -> SimLingoRouteRecord | None:
        return self.routes[0] if self.routes else None

    @property
    def route_id(self) -> str | None:
        return self.primary_route.route_id if self.primary_route else None

    @property
    def scenario_name(self) -> str | None:
        return self.primary_route.scenario_name if self.primary_route else None

    @property
    def town_name(self) -> str | None:
        return self.primary_route.town_name if self.primary_route else None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "entry_status": self.entry_status,
            "eligible": self.eligible,
            "status": self.status,
            "success": self.success,
            "driving_score": self.driving_score,
            "route_completion": self.route_completion,
            "infraction_penalty": self.infraction_penalty,
            "duration_game_s": self.duration_game_s,
            "duration_system_s": self.duration_system_s,
            "infractions": self.infractions,
            "sensors": self.sensors,
            "exception_summary": self.exception_summary,
            "progress_completed": self.progress_completed,
            "progress_total": self.progress_total,
            "route_count": self.route_count,
            "routes": [route.to_jsonable() for route in self.routes],
            "primary_route": self.primary_route.to_jsonable() if self.primary_route else None,
        }


def parse_simlingo_result(path: Path) -> SimLingoRunRecord:
    payload = json.loads(path.read_text(encoding="utf-8"))
    checkpoint = _mapping(payload.get("_checkpoint"))
    global_record = _mapping(checkpoint.get("global_record"))
    raw_records = checkpoint.get("records", [])
    routes = [
        _route_record(_mapping(record))
        for record in raw_records
        if isinstance(record, dict)
    ]
    global_scores = _mapping(global_record.get("scores_mean"))
    global_meta = _mapping(global_record.get("meta"))
    status = _str_or_none(global_record.get("status") or (routes[0].status if routes else None))
    progress = _progress(checkpoint.get("progress"))
    return SimLingoRunRecord(
        source_path=path,
        entry_status=_str_or_none(payload.get("entry_status")),
        eligible=_bool_or_none(payload.get("eligible")),
        status=status,
        success=_is_success_status(status) and all(route.success for route in routes),
        driving_score=_prefer(_float_or_none(global_scores.get("score_composed")), _first_score(routes, "driving_score")),
        route_completion=_prefer(_float_or_none(global_scores.get("score_route")), _first_score(routes, "route_completion")),
        infraction_penalty=_prefer(_float_or_none(global_scores.get("score_penalty")), _first_score(routes, "infraction_penalty")),
        duration_game_s=_prefer(_float_or_none(global_meta.get("duration_game")), _first_score(routes, "duration_game_s")),
        duration_system_s=_prefer(_float_or_none(global_meta.get("duration_system")), _first_score(routes, "duration_system_s")),
        infractions=dict(_mapping(global_record.get("infractions")) or (routes[0].infractions if routes else {})),
        sensors=[str(sensor) for sensor in payload.get("sensors", []) if sensor is not None],
        exception_summary=_exception_summary(global_meta.get("exceptions")),
        progress_completed=progress[0],
        progress_total=progress[1],
        route_count=len(routes),
        routes=routes,
    )


def write_simlingo_result_report(
    run_dir: Path,
    record: SimLingoRunRecord,
    *,
    compatibility_path: Path | None = None,
    route_log_path: Path | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    compatibility = _load_optional_json(compatibility_path)
    route_log_summary = _route_log_summary(route_log_path)
    payload = {
        "record": record.to_jsonable(),
        "compatibility": compatibility,
        "route_log": route_log_summary,
        "blocker": _blocker(record, compatibility, route_log_summary),
    }
    json_path = run_dir / "simlingo_result_record.json"
    report_path = run_dir / "simlingo_result_report.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_result_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def compact_simlingo_result_summary(summary: dict[str, Any]) -> dict[str, Any]:
    record = _mapping(summary.get("record"))
    route_log = _mapping(summary.get("route_log"))
    primary_route = _mapping(record.get("primary_route"))
    return {
        "record": {
            key: record.get(key)
            for key in [
                "status",
                "success",
                "driving_score",
                "route_completion",
                "infraction_penalty",
                "progress_completed",
                "progress_total",
                "route_count",
                "exception_summary",
            ]
        },
        "primary_route": _compact_route(primary_route),
        "compatibility": summary.get("compatibility"),
        "route_log_signals": route_log.get("signals"),
        "blocker": summary.get("blocker"),
        "json_path": summary.get("json_path"),
        "report_path": summary.get("report_path"),
    }


def _compact_route(route: dict[str, Any]) -> dict[str, Any] | None:
    if not route:
        return None
    return {
        key: route.get(key)
        for key in [
            "route_id",
            "scenario_name",
            "town_name",
            "status",
            "success",
            "driving_score",
            "route_completion",
            "infraction_penalty",
        ]
    }


def _route_record(record: dict[str, Any]) -> SimLingoRouteRecord:
    scores = _mapping(record.get("scores"))
    meta = _mapping(record.get("meta"))
    status = _str_or_none(record.get("status"))
    return SimLingoRouteRecord(
        route_id=_str_or_none(record.get("route_id")),
        scenario_name=_str_or_none(record.get("scenario_name")),
        town_name=_str_or_none(record.get("town_name")),
        status=status,
        success=_is_success_status(status),
        driving_score=_float_or_none(scores.get("score_composed")),
        route_completion=_float_or_none(scores.get("score_route")),
        infraction_penalty=_float_or_none(scores.get("score_penalty")),
        duration_game_s=_float_or_none(meta.get("duration_game")),
        duration_system_s=_float_or_none(meta.get("duration_system")),
        infractions=dict(_mapping(record.get("infractions"))),
    )


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _str_or_none(value: Any) -> str | None:
    return None if value is None else str(value)


def _bool_or_none(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_success_status(status: str | None) -> bool:
    return bool(status and status.lower() in {"completed", "success", "succeeded", "finished"})


def _first_score(routes: list[SimLingoRouteRecord], attr: str) -> float | None:
    return getattr(routes[0], attr) if routes else None


def _prefer(primary: float | None, fallback: float | None) -> float | None:
    return primary if primary is not None else fallback


def _progress(value: Any) -> tuple[int | None, int | None]:
    if isinstance(value, list) and len(value) >= 2:
        return _int_or_none(value[0]), _int_or_none(value[1])
    return None, None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _exception_summary(exceptions: Any) -> str | None:
    if not isinstance(exceptions, list) or not exceptions:
        return None
    first = exceptions[0]
    if isinstance(first, list) and len(first) >= 3:
        return f"{first[0]}: {first[2]}"
    return str(first)


def _load_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _route_log_summary(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    signals = [
        "load_world success",
        "traffic_manager init success",
        "> Running the route",
        "CUDA error: no kernel image is available for execution on the device",
    ]
    return {
        "path": str(path),
        "signals": {signal: signal in text for signal in signals},
        "tail": "\n".join(text.splitlines()[-40:]),
    }


def _blocker(
    record: SimLingoRunRecord,
    compatibility: dict[str, Any] | None,
    route_log_summary: dict[str, Any] | None,
) -> str | None:
    if record.success:
        return None
    signals = _mapping(route_log_summary.get("signals")) if route_log_summary else {}
    if signals.get("CUDA error: no kernel image is available for execution on the device"):
        required = compatibility.get("required_arch") if compatibility else None
        compiled = compatibility.get("compiled_arches") if compatibility else None
        return (
            "CUDA no-kernel-image at first model tick"
            + (f"; required `{required}`, compiled arches `{compiled}`" if required else "")
        )
    return record.exception_summary or record.status


def _result_markdown(payload: dict[str, Any]) -> str:
    record = payload["record"]
    primary = record.get("primary_route") or {}
    compatibility = payload.get("compatibility")
    route_log = payload.get("route_log")
    lines = [
        "# SimLingo Result Report",
        "",
        f"- status: `{record['status']}`",
        f"- success: `{record['success']}`",
        f"- route_count: `{record['route_count']}`",
        f"- progress: `{record['progress_completed']}` / `{record['progress_total']}`",
        f"- route_completion: `{record['route_completion']}`",
        f"- driving_score: `{record['driving_score']}`",
        f"- infraction_penalty: `{record['infraction_penalty']}`",
        f"- primary_route: `{primary.get('route_id')}`",
        f"- primary_scenario: `{primary.get('scenario_name')}`",
        f"- primary_town: `{primary.get('town_name')}`",
        f"- exception: `{record['exception_summary']}`",
        "",
        "## Blocker",
        "",
        payload.get("blocker") or "None.",
        "",
    ]
    if compatibility:
        lines.extend(
            [
                "## CUDA Compatibility",
                "",
                f"- device: `{compatibility.get('device_name')}`",
                f"- torch: `{compatibility.get('torch_version')}`",
                f"- required_arch: `{compatibility.get('required_arch')}`",
                f"- compiled_arches: `{compatibility.get('compiled_arches')}`",
                f"- compatible: `{compatibility.get('compatible')}`",
                "",
            ]
        )
    if route_log:
        lines.extend(
            [
                "## Route Log Signals",
                "",
                *(f"- `{key}`: `{value}`" for key, value in route_log["signals"].items()),
                "",
            ]
        )
    return "\n".join(lines)


__all__ = [
    "SimLingoRouteRecord",
    "SimLingoRunRecord",
    "compact_simlingo_result_summary",
    "parse_simlingo_result",
    "write_simlingo_result_report",
]
