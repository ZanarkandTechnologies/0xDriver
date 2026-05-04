"""Export generated DriverX recipes as Bench2Drive route packs."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from driverx.scenarios import ScenarioRecipe

INJECTION_STRATEGY = "stock_bench2drive_xml_plus_driverx_sidecar_overlay"
RUNTIME_NOTE = (
    "The route XML stays stock-compatible for SimLingo/Bench2Drive. "
    "Generated actors, assets, and regional behaviors are recorded in DriverX "
    "sidecar overlays for companion injection or later scenario-runner adapters."
)
OVERLAY_CONTRACT = [
    "Use route_path for single-recipe replay or debugging.",
    "Use route_suite_path from the route-pack manifest, or the generated SimLingo command plan, for suite execution.",
    "Use this overlay to choose companion CARLA actor scripts, generated assets, and retrieved memory.",
    "Do not claim the sidecar overlay changes stock SimLingo behavior until a companion injector is running.",
]


@dataclass(frozen=True)
class Bench2DriveRouteExport:
    recipe_id: str
    source_route_path: Path
    route_path: Path
    overlay_path: Path
    route_id: str | None
    town_name: str | None
    scenario_types: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "source_route_path": str(self.source_route_path),
            "route_path": str(self.route_path),
            "overlay_path": str(self.overlay_path),
            "route_id": self.route_id,
            "town_name": self.town_name,
            "scenario_types": self.scenario_types,
        }


@dataclass(frozen=True)
class Bench2DriveRouteSuite:
    suite_id: str
    behavior_id: str
    route_suite_path: Path
    exports: list[Bench2DriveRouteExport]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "behavior_id": self.behavior_id,
            "route_suite_path": str(self.route_suite_path),
            "injection_strategy": INJECTION_STRATEGY,
            "runtime_note": RUNTIME_NOTE,
            "num_routes": len(self.exports),
            "exports": [export.to_jsonable() for export in self.exports],
        }


def build_bench2drive_route_suite(
    run_dir: Path,
    recipes: list[ScenarioRecipe],
    *,
    route_root: Path,
    behavior_id: str,
) -> Bench2DriveRouteSuite:
    """Write stock-compatible route XML plus DriverX overlays for recipes."""

    if not recipes:
        raise ValueError("At least one ScenarioRecipe is required.")
    routes_dir = run_dir / "bench2drive_routes"
    overlays_dir = run_dir / "driverx_overlays"
    routes_dir.mkdir(parents=True, exist_ok=True)
    overlays_dir.mkdir(parents=True, exist_ok=True)
    suite_root = ElementTree.Element("routes")
    exports: list[Bench2DriveRouteExport] = []
    for index, recipe in enumerate(recipes):
        source_route_path = resolve_recipe_route_path(recipe, route_root)
        route = _single_route(source_route_path)
        route_metadata = _route_metadata(route)
        route_filename = f"{index:03d}_{_slug(recipe.recipe_id)}.xml"
        route_path = routes_dir / route_filename
        overlay_path = overlays_dir / f"{index:03d}_{_slug(recipe.recipe_id)}.json"
        _write_single_route(route_path, route, recipe)
        overlay_path.write_text(
            json.dumps(
                _overlay_payload(
                    recipe=recipe,
                    behavior_id=behavior_id,
                    source_route_path=source_route_path,
                    route_path=route_path,
                    route_metadata=route_metadata,
                ),
                indent=2,
            ),
            encoding="utf-8",
        )
        suite_root.append(
            ElementTree.Comment(
                f" driverx_recipe_id={recipe.recipe_id} overlay={overlay_path.name} "
            )
        )
        suite_root.append(copy.deepcopy(route))
        exports.append(
            Bench2DriveRouteExport(
                recipe_id=recipe.recipe_id,
                source_route_path=source_route_path,
                route_path=route_path,
                overlay_path=overlay_path,
                route_id=route_metadata["route_id"],
                town_name=route_metadata["town_name"],
                scenario_types=list(route_metadata["scenario_types"]),
            )
        )
    route_suite_path = routes_dir / "generated_routes.xml"
    _write_xml(route_suite_path, suite_root)
    return Bench2DriveRouteSuite(
        suite_id=run_dir.name,
        behavior_id=behavior_id,
        route_suite_path=route_suite_path,
        exports=exports,
    )


def resolve_recipe_route_path(recipe: ScenarioRecipe, route_root: Path) -> Path:
    if recipe.route_path is None:
        raise ValueError(f"Recipe {recipe.recipe_id} does not declare route_path.")
    route_path = recipe.route_path.expanduser()
    candidates = [
        route_path,
        route_root.expanduser() / route_path,
        route_root.expanduser() / route_path.name,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    candidate_list = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Route XML not found for {recipe.recipe_id}; checked {candidate_list}")


def write_bench2drive_route_suite(
    run_dir: Path,
    suite: Bench2DriveRouteSuite,
    *,
    simlingo_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = suite.to_jsonable()
    if simlingo_plan is not None:
        payload["simlingo_command_plan_path"] = simlingo_plan.get("json_path")
        payload["simlingo_expected_outputs"] = simlingo_plan.get("expected_outputs", [])
        payload["simlingo_live_blockers"] = simlingo_plan.get("live_blockers", [])
    manifest_path = run_dir / "bench2drive_route_pack.json"
    report_path = run_dir / "bench2drive_route_pack.md"
    payload["manifest_path"] = str(manifest_path)
    payload["report_path"] = str(report_path)
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_route_suite_markdown(payload), encoding="utf-8")
    return payload


def _single_route(path: Path) -> ElementTree.Element:
    tree = ElementTree.parse(path)
    root = tree.getroot()
    if root.tag != "routes":
        raise ValueError(f"Bench2Drive route XML root must be <routes>: {path}")
    routes = root.findall("route")
    if len(routes) != 1:
        raise ValueError(f"Expected exactly one <route> in {path}; found {len(routes)}")
    return copy.deepcopy(routes[0])


def _write_single_route(path: Path, route: ElementTree.Element, recipe: ScenarioRecipe) -> None:
    root = ElementTree.Element("routes")
    root.append(ElementTree.Comment(f" driverx_recipe_id={recipe.recipe_id} "))
    root.append(copy.deepcopy(route))
    _write_xml(path, root)


def _write_xml(path: Path, root: ElementTree.Element) -> None:
    ElementTree.indent(root, space="  ")
    path.write_text(ElementTree.tostring(root, encoding="unicode"), encoding="utf-8")


def _route_metadata(route: ElementTree.Element) -> dict[str, Any]:
    scenarios = route.find("scenarios")
    scenario_types = []
    if scenarios is not None:
        scenario_types = [
            str(scenario.attrib.get("type", scenario.attrib.get("name", "")))
            for scenario in scenarios.findall("scenario")
            if scenario.attrib.get("type") or scenario.attrib.get("name")
        ]
    return {
        "route_id": route.attrib.get("id"),
        "town_name": route.attrib.get("town"),
        "scenario_types": sorted(set(scenario_types)),
    }


def _overlay_payload(
    *,
    recipe: ScenarioRecipe,
    behavior_id: str,
    source_route_path: Path,
    route_path: Path,
    route_metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "recipe": recipe.to_jsonable(),
        "behavior_id": behavior_id,
        "source_route_path": str(source_route_path),
        "route_path": str(route_path),
        "route_metadata": route_metadata,
        "injection_strategy": INJECTION_STRATEGY,
        "runtime_note": RUNTIME_NOTE,
        "driverx_runtime_contract": OVERLAY_CONTRACT,
    }


def _route_suite_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bench2Drive Route Pack",
        "",
        f"- suite_id: `{payload['suite_id']}`",
        f"- behavior_id: `{payload['behavior_id']}`",
        f"- routes: `{payload['num_routes']}`",
        f"- route_suite_path: `{payload['route_suite_path']}`",
        f"- injection_strategy: `{payload['injection_strategy']}`",
        "",
        payload["runtime_note"],
        "",
        "## Routes",
        "",
        "| recipe | route id | town | scenarios | overlay |",
        "|---|---|---|---|---|",
    ]
    for export in payload["exports"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(export["recipe_id"]),
                    _cell(export["route_id"]),
                    _cell(export["town_name"]),
                    _cell(", ".join(export["scenario_types"])),
                    _cell(export["overlay_path"]),
                ]
            )
            + " |"
        )
    if payload.get("simlingo_command_plan_path"):
        lines.extend(
            [
                "",
                "## SimLingo Plan",
                "",
                f"- command_plan: `{payload['simlingo_command_plan_path']}`",
                f"- live_blockers: `{len(payload.get('simlingo_live_blockers', []))}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


__all__ = [
    "Bench2DriveRouteExport",
    "Bench2DriveRouteSuite",
    "build_bench2drive_route_suite",
    "resolve_recipe_route_path",
    "write_bench2drive_route_suite",
]
