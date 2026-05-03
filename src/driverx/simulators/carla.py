"""CARLA runtime config and server smoke checks."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.core.config import read_config_mapping


@dataclass(frozen=True)
class CarlaRunConfig:
    host: str
    port: int
    timeout_s: float
    carla_root: Path | None
    fail2drive_root: Path
    route_path: Path
    agent_path: Path
    output_dir: Path
    track: str = "MAP"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "timeout_s": self.timeout_s,
            "carla_root": str(self.carla_root) if self.carla_root else None,
            "fail2drive_root": str(self.fail2drive_root),
            "route_path": str(self.route_path),
            "agent_path": str(self.agent_path),
            "output_dir": str(self.output_dir),
            "track": self.track,
        }


@dataclass(frozen=True)
class CarlaSmokeResult:
    host: str
    port: int
    reachable: bool
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "reachable": self.reachable,
            "error": self.error,
        }


def _path(value: Any, default: str | None = None) -> Path | None:
    raw = value if value not in (None, "") else default
    return Path(str(raw)).expanduser() if raw is not None else None


def load_carla_run_config(path: Path) -> CarlaRunConfig:
    raw = read_config_mapping(path)
    carla = raw.get("carla", {})
    fail2drive = raw.get("fail2drive", {})
    if not isinstance(carla, dict):
        raise ValueError("Config field 'carla' must be a mapping.")
    if not isinstance(fail2drive, dict):
        raise ValueError("Config field 'fail2drive' must be a mapping.")
    fail2drive_root = _path(fail2drive.get("root"), "../external/fail2drive")
    if fail2drive_root is None:
        raise ValueError("fail2drive.root is required.")
    route_path = _path(fail2drive.get("route_path"), "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml")
    agent_path = _path(fail2drive.get("agent_path"), "team_code/visu_agent.py")
    output_dir = _path(fail2drive.get("output_dir"), "artifacts/carla")
    if route_path is None or agent_path is None or output_dir is None:
        raise ValueError("fail2drive.route_path, agent_path, and output_dir are required.")
    return CarlaRunConfig(
        host=str(carla.get("host", "127.0.0.1")),
        port=int(carla.get("port", 2000)),
        timeout_s=float(carla.get("timeout_s", 1.0)),
        carla_root=_path(carla.get("root")),
        fail2drive_root=fail2drive_root,
        route_path=route_path,
        agent_path=agent_path,
        output_dir=output_dir,
        track=str(fail2drive.get("track", "MAP")),
    )


def smoke_carla_server(host: str, port: int, timeout_s: float) -> CarlaSmokeResult:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return CarlaSmokeResult(host=host, port=port, reachable=True)
    except OSError as exc:
        return CarlaSmokeResult(
            host=host,
            port=port,
            reachable=False,
            error=str(exc),
        )
