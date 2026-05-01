"""Configuration loading for CLI and pipeline runs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DatasetConfig:
    kind: str = "fixture"
    name: str = "construction_merge"
    path: Path | None = None


@dataclass(frozen=True)
class ReasonerConfig:
    backend: str = "mock"
    uncertainty: float = 0.34


@dataclass(frozen=True)
class OutputConfig:
    root: Path = Path("artifacts/runs")
    run_id: str | None = None


@dataclass(frozen=True)
class DriverConfig:
    dataset: DatasetConfig
    reasoner: ReasonerConfig
    output: OutputConfig
    author: str = "0xDriver"
    method_name: str = "fixture_vla_intent_planner"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "dataset": {
                "kind": self.dataset.kind,
                "name": self.dataset.name,
                "path": str(self.dataset.path) if self.dataset.path else None,
            },
            "reasoner": {
                "backend": self.reasoner.backend,
                "uncertainty": self.reasoner.uncertainty,
            },
            "output": {
                "root": str(self.output.root),
                "run_id": self.output.run_id,
            },
            "author": self.author,
            "method_name": self.method_name,
        }


def _expand_path(value: str | None) -> Path | None:
    if value is None:
        return None
    return Path(os.path.expandvars(os.path.expanduser(value)))


def _read_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        raw = json.loads(text)
    else:
        raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return raw


def load_config(path: Path) -> DriverConfig:
    raw = _read_mapping(path)
    dataset_raw = raw.get("dataset", {})
    reasoner_raw = raw.get("reasoner", {})
    output_raw = raw.get("output", {})

    if not isinstance(dataset_raw, dict):
        raise ValueError("Config field 'dataset' must be a mapping.")
    if not isinstance(reasoner_raw, dict):
        raise ValueError("Config field 'reasoner' must be a mapping.")
    if not isinstance(output_raw, dict):
        raise ValueError("Config field 'output' must be a mapping.")

    dataset = DatasetConfig(
        kind=str(dataset_raw.get("kind", "fixture")),
        name=str(dataset_raw.get("name", "construction_merge")),
        path=_expand_path(dataset_raw.get("path")),
    )
    reasoner = ReasonerConfig(
        backend=str(reasoner_raw.get("backend", "mock")),
        uncertainty=float(reasoner_raw.get("uncertainty", 0.34)),
    )
    output = OutputConfig(
        root=_expand_path(output_raw.get("root")) or Path("artifacts/runs"),
        run_id=(
            str(output_raw["run_id"])
            if output_raw.get("run_id") not in (None, "")
            else None
        ),
    )
    return DriverConfig(
        dataset=dataset,
        reasoner=reasoner,
        output=output,
        author=str(raw.get("author", "0xDriver")),
        method_name=str(raw.get("method_name", "fixture_vla_intent_planner")),
    )
