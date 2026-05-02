"""Configuration loading for CLI and pipeline runs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetConfig:
    kind: str = "fixture"
    name: str = "construction_merge"
    path: Path | None = None
    frame_index: int = 0
    limit: int | None = None


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
    affiliation: str = "Independent"
    account_name: str = ""
    method_name: str = "fixture_vla_intent_planner"
    method_link: str = ""
    description: str = ""
    num_model_parameters: str = "0K"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "dataset": {
                "kind": self.dataset.kind,
                "name": self.dataset.name,
                "path": str(self.dataset.path) if self.dataset.path else None,
                "frame_index": self.dataset.frame_index,
                "limit": self.dataset.limit,
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
            "affiliation": self.affiliation,
            "account_name": self.account_name,
            "method_name": self.method_name,
            "method_link": self.method_link,
            "description": self.description,
            "num_model_parameters": self.num_model_parameters,
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
        raw = _parse_simple_yaml(text)
    if not isinstance(raw, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return raw


def _parse_scalar(value: str) -> Any:
    stripped = value.strip()
    if stripped in {"", "null", "None", "~"}:
        return None
    if stripped in {"true", "false"}:
        return stripped == "true"
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        pass
    if (stripped.startswith('"') and stripped.endswith('"')) or (
        stripped.startswith("'") and stripped.endswith("'")
    ):
        return stripped[1:-1]
    return stripped


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small mapping subset used by repo configs.

    This intentionally supports only root mappings and one nested mapping level.
    It keeps the local fixture path dependency-free while still allowing users to
    replace these sample configs with JSON for more complex cases.
    """

    parsed_lines: list[tuple[str, int, str, str]] = []
    for raw_line in text.splitlines():
        line_without_comment = raw_line.split("#", 1)[0].rstrip()
        if not line_without_comment.strip():
            continue
        indent = len(line_without_comment) - len(line_without_comment.lstrip(" "))
        if ":" not in line_without_comment:
            raise ValueError(f"Unsupported config line: {raw_line}")
        key, value = line_without_comment.strip().split(":", 1)
        parsed_lines.append((raw_line, indent, key, value))

    root: dict[str, Any] = {}
    current_section: str | None = None
    for index, (raw_line, indent, key, value) in enumerate(parsed_lines):
        if indent == 0:
            if value.strip() == "":
                next_indent = (
                    parsed_lines[index + 1][1]
                    if index + 1 < len(parsed_lines)
                    else 0
                )
                if next_indent > indent:
                    root[key] = {}
                    current_section = key
                else:
                    root[key] = None
                    current_section = None
            else:
                root[key] = _parse_scalar(value)
                current_section = None
        elif indent == 2 and current_section is not None:
            section = root.get(current_section)
            if not isinstance(section, dict):
                raise ValueError(f"Config section is not a mapping: {current_section}")
            section[key] = _parse_scalar(value)
        else:
            raise ValueError(f"Unsupported config indentation: {raw_line}")
    return root


def _string_field(raw: dict[str, Any], key: str, default: str = "") -> str:
    value = raw.get(key, default)
    if value is None:
        return default
    return str(value)


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
        frame_index=int(dataset_raw.get("frame_index", 0) or 0),
        limit=(
            int(dataset_raw["limit"])
            if dataset_raw.get("limit") not in (None, "")
            else None
        ),
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
        author=_string_field(raw, "author", "0xDriver"),
        affiliation=_string_field(raw, "affiliation", "Independent"),
        account_name=_string_field(raw, "account_name", ""),
        method_name=_string_field(raw, "method_name", "fixture_vla_intent_planner"),
        method_link=_string_field(raw, "method_link", ""),
        description=_string_field(raw, "description", ""),
        num_model_parameters=_string_field(raw, "num_model_parameters", "0K"),
    )
