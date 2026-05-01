"""Helpers for stable run directories and JSON artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from driverx.core.types import ArtifactRef


def timestamp_run_id(prefix: str = "run") -> str:
    return f"{prefix}-{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%S%fZ')}"


def prepare_run_dir(root: Path, run_id: str | None = None) -> Path:
    base = root / (run_id or timestamp_run_id())
    run_dir = base
    suffix = 1
    while run_dir.exists():
        run_dir = root / f"{base.name}-{suffix:03d}"
        suffix += 1
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def write_json_artifact(run_dir: Path, name: str, payload: Any) -> ArtifactRef:
    path = run_dir / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return ArtifactRef(name=name, path=path, kind="json")


def read_json_artifact(run_dir: Path, name: str) -> Any:
    path = run_dir / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))
