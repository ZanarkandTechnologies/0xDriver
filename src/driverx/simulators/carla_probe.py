"""CARLA Python API probe and artifact writing."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CarlaProbeConfig:
    host: str
    port: int
    timeout_s: float


@dataclass(frozen=True)
class CarlaProbeResult:
    connected: bool
    host: str
    port: int
    map_name: str | None = None
    actor_count: int | None = None
    weather: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None
    server_version: str | None = None
    client_version: str | None = None
    elapsed_seconds: float | None = None
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "map_name": self.map_name,
            "actor_count": self.actor_count,
            "weather": self.weather,
            "settings": self.settings,
            "server_version": self.server_version,
            "client_version": self.client_version,
            "elapsed_seconds": self.elapsed_seconds,
            "error": self.error,
        }


def _public_attrs(obj: object, names: tuple[str, ...]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if isinstance(value, (str, int, float, bool)) or value is None:
                payload[name] = value
    return payload


def _maybe_call(obj: object, name: str) -> str | None:
    method = getattr(obj, name, None)
    if method is None:
        return None
    try:
        return str(method())
    except Exception:
        return None


def probe_carla_client(config: CarlaProbeConfig) -> CarlaProbeResult:
    try:
        carla = importlib.import_module("carla")
    except ImportError as exc:
        return CarlaProbeResult(
            connected=False,
            host=config.host,
            port=config.port,
            error=(
                f"CARLA Python package is unavailable: {exc}. "
                "Run through scripts/run_carla_client_docker.sh or install carla==0.9.16."
            ),
        )

    try:
        client = carla.Client(config.host, config.port)
        client.set_timeout(config.timeout_s)
        world = client.get_world()
        world_map = world.get_map()
        actors = world.get_actors()
        weather = world.get_weather()
        settings = world.get_settings()
        snapshot = world.get_snapshot()
        timestamp = getattr(snapshot, "timestamp", None)
        elapsed_seconds = (
            float(timestamp.elapsed_seconds)
            if timestamp is not None and hasattr(timestamp, "elapsed_seconds")
            else None
        )
        return CarlaProbeResult(
            connected=True,
            host=config.host,
            port=config.port,
            map_name=str(getattr(world_map, "name", "")) or None,
            actor_count=len(actors),
            weather=_public_attrs(
                weather,
                (
                    "cloudiness",
                    "precipitation",
                    "precipitation_deposits",
                    "wind_intensity",
                    "sun_azimuth_angle",
                    "sun_altitude_angle",
                    "fog_density",
                    "wetness",
                ),
            ),
            settings=_public_attrs(
                settings,
                (
                    "synchronous_mode",
                    "fixed_delta_seconds",
                    "no_rendering_mode",
                    "substepping",
                    "max_substep_delta_time",
                    "max_substeps",
                ),
            ),
            server_version=_maybe_call(client, "get_server_version"),
            client_version=_maybe_call(client, "get_client_version")
            or str(getattr(carla, "__version__", "")) or None,
            elapsed_seconds=elapsed_seconds,
        )
    except Exception as exc:
        return CarlaProbeResult(
            connected=False,
            host=config.host,
            port=config.port,
            error=f"CARLA probe failed: {exc}",
        )


def _probe_markdown(result: CarlaProbeResult) -> str:
    status = "connected" if result.connected else "failed"
    lines = [
        "# CARLA Probe",
        "",
        f"- status: {status}",
        f"- endpoint: `{result.host}:{result.port}`",
        f"- map: `{result.map_name}`",
        f"- actors: `{result.actor_count}`",
        f"- server_version: `{result.server_version}`",
        f"- client_version: `{result.client_version}`",
        f"- elapsed_seconds: `{result.elapsed_seconds}`",
    ]
    if result.error:
        lines.append(f"- error: `{result.error}`")
    if result.settings:
        lines.extend(["", "## Settings", ""])
        for key, value in result.settings.items():
            lines.append(f"- `{key}`: `{value}`")
    if result.weather:
        lines.extend(["", "## Weather", ""])
        for key, value in result.weather.items():
            lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_carla_probe(run_dir: Path, result: CarlaProbeResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "carla_probe.json"
    report_path = run_dir / "carla_probe.md"
    json_path.write_text(json.dumps(result.to_jsonable(), indent=2), encoding="utf-8")
    report_path.write_text(_probe_markdown(result), encoding="utf-8")
    return {
        **result.to_jsonable(),
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


__all__ = [
    "CarlaProbeConfig",
    "CarlaProbeResult",
    "probe_carla_client",
    "write_carla_probe",
]
