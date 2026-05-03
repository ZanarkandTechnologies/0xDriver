"""Load Fail2Drive-style route seeds and scenario results."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from driverx.scenarios.types import ScenarioResult, ScenarioSeed

ROUTE_FILE_RE = re.compile(r"^(Base|Generalization)_(.+)_(\d{4})\.xml$")
RESULT_FILE_RE = re.compile(r"^(\d{4})_res\.json$")


def _camel_tags(value: str) -> list[str]:
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|\d+", value)
    tags = [part.lower() for part in parts if part]
    tags.append(value.lower())
    return sorted(set(tags))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _seed_from_xml(path: Path) -> ScenarioSeed | None:
    match = ROUTE_FILE_RE.match(path.name)
    if not match:
        return None
    split, scenario_class, route_id = match.groups()
    try:
        tree = ElementTree.parse(path)
        route = tree.getroot().find("route")
        parsed_route_id = route.attrib.get("id", route_id) if route is not None else route_id
    except ElementTree.ParseError:
        parsed_route_id = route_id
    return ScenarioSeed(
        seed_id=path.stem,
        source="fail2drive",
        split=split,  # type: ignore[arg-type]
        scenario_class=scenario_class,
        route_id=str(parsed_route_id).zfill(4),
        route_path=path,
        ood_tags=_camel_tags(scenario_class),
    )


def _seeds_from_json(path: Path) -> list[ScenarioSeed]:
    raw = _load_json(path)
    rows = raw.get("seeds", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError(f"Scenario seed JSON must be a list or contain 'seeds': {path}")
    return [ScenarioSeed.from_jsonable(dict(row)) for row in rows]


def load_scenario_seeds(path: Path) -> list[ScenarioSeed]:
    """Load tiny fixture seeds or real Fail2Drive route XML seeds."""

    if not path.exists():
        raise FileNotFoundError(f"Scenario seed path not found: {path}")
    if path.is_file() and path.suffix.lower() == ".json":
        seeds = _seeds_from_json(path)
    elif path.is_file() and path.suffix.lower() == ".xml":
        seed = _seed_from_xml(path)
        seeds = [seed] if seed is not None else []
    elif path.is_dir():
        seed_json = path / "seeds.json"
        if seed_json.exists():
            seeds = _seeds_from_json(seed_json)
        else:
            seeds = [
                seed
                for seed in (_seed_from_xml(xml_path) for xml_path in sorted(path.glob("*.xml")))
                if seed is not None
            ]
    else:
        raise ValueError(f"Unsupported scenario seed path: {path}")
    if not seeds:
        raise ValueError(f"No scenario seeds found in {path}")
    return seeds


def _success_from_infractions(infractions: dict[str, Any]) -> bool:
    ignored = {"min_speed_infractions", "outside_route_lanes"}
    for name, entries in infractions.items():
        if name in ignored:
            continue
        if entries:
            return False
    return True


def _result_from_fail2drive_checkpoint(path: Path, policy: str = "unknown_policy") -> ScenarioResult | None:
    raw = _load_json(path)
    records = raw.get("_checkpoint", {}).get("records") if isinstance(raw, dict) else None
    if not records:
        return None
    record = records[0]
    scores = record.get("scores", {}) or {}
    infractions = record.get("infractions", {}) or {}
    route_match = RESULT_FILE_RE.match(path.name)
    route_id = route_match.group(1) if route_match else path.stem
    success = _success_from_infractions(infractions)
    return ScenarioResult(
        scenario_id=route_id,
        policy=policy,
        success=success,
        driving_score=(
            float(scores["score_composed"])
            if scores.get("score_composed") is not None
            else None
        ),
        route_completion=(
            float(scores["score_route"])
            if scores.get("score_route") is not None
            else None
        ),
        infractions={
            str(key): [str(entry) for entry in value]
            for key, value in dict(infractions).items()
        },
        failure_summary=None if success else "Fail2Drive record contains non-ignored infractions.",
        tags=[],
    )


def _results_from_json(path: Path) -> list[ScenarioResult]:
    raw = _load_json(path)
    if isinstance(raw, dict) and "_checkpoint" in raw:
        result = _result_from_fail2drive_checkpoint(path)
        return [result] if result is not None else []
    rows = raw.get("results", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError(f"Scenario result JSON must be a list or contain 'results': {path}")
    return [ScenarioResult.from_jsonable(dict(row)) for row in rows]


def load_scenario_results(path: Path) -> list[ScenarioResult]:
    """Load direct fixture results or Fail2Drive result JSON records."""

    if not path.exists():
        raise FileNotFoundError(f"Scenario result path not found: {path}")
    if path.is_file() and path.suffix.lower() == ".json":
        results = _results_from_json(path)
    elif path.is_dir():
        result_json = path / "results.json"
        if result_json.exists():
            results = _results_from_json(result_json)
        else:
            results = []
            for json_path in sorted(path.glob("**/*.json")):
                result = _result_from_fail2drive_checkpoint(json_path)
                if result is not None:
                    results.append(result)
    else:
        raise ValueError(f"Unsupported scenario result path: {path}")
    if not results:
        raise ValueError(f"No scenario results found in {path}")
    return results
