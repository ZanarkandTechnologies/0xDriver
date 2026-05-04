"""Compile DriverX route-pack overlays into companion CARLA injection plans."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from driverx.behaviors import default_behavior_plans, simulate_behavior
from driverx.scenarios import ScenarioRecipe
from driverx.simulators.bench2drive_routes import OVERLAY_CONTRACT
from driverx.simulators.carla_script import (
    CarlaActorScript,
    CarlaScriptPlan,
    compile_carla_script_plan,
    validate_carla_script_plan,
)

RUNTIME_MODE = "dry_run_companion_plan"
RUNTIME_NOTE = (
    "This plan compiles DriverX sidecar overlays into CARLA actor/sensor/tick "
    "plans. It does not launch CARLA or modify stock SimLingo behavior until a "
    "live companion injector runs beside the benchmark route."
)


@dataclass(frozen=True)
class OverlayInjectionRoute:
    recipe_id: str
    route_path: Path
    overlay_path: Path
    mutation: str
    overlay_actors: list[dict[str, Any]]
    environment: dict[str, Any]
    driverx_runtime_contract: list[str]
    behavior_id: str
    memory_query: list[str]
    expected_failure_mode: str
    script_plan: CarlaScriptPlan
    validation_errors: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "route_path": str(self.route_path),
            "overlay_path": str(self.overlay_path),
            "mutation": self.mutation,
            "overlay_actors": self.overlay_actors,
            "environment": self.environment,
            "driverx_runtime_contract": self.driverx_runtime_contract,
            "behavior_id": self.behavior_id,
            "memory_query": self.memory_query,
            "expected_failure_mode": self.expected_failure_mode,
            "script_plan": self.script_plan.to_jsonable(),
            "validation_errors": self.validation_errors,
        }


@dataclass(frozen=True)
class OverlayInjectionPlan:
    route_pack_path: Path
    route_suite_path: Path
    runtime_mode: str
    runtime_note: str
    routes: list[OverlayInjectionRoute]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "route_pack_path": str(self.route_pack_path),
            "route_suite_path": str(self.route_suite_path),
            "runtime_mode": self.runtime_mode,
            "runtime_note": self.runtime_note,
            "num_routes": len(self.routes),
            "routes": [route.to_jsonable() for route in self.routes],
            "validation_errors": [
                error
                for route in self.routes
                for error in route.validation_errors
            ],
        }


def compile_overlay_injection_plan(
    route_pack_path: Path,
    output_dir: Path,
    *,
    behavior_id: str | None = None,
) -> OverlayInjectionPlan:
    manifest_path = route_pack_path.expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    exports = list(manifest.get("exports", []))
    if not exports:
        raise ValueError(f"Route pack contains no exports: {manifest_path}")
    behavior_plans = {plan.behavior_id: plan for plan in default_behavior_plans()}
    route_suite_path = _resolve_path(str(manifest["route_suite_path"]), manifest_path)
    routes: list[OverlayInjectionRoute] = []
    for index, export in enumerate(exports):
        export_mapping = dict(export)
        route_path = _resolve_path(str(export_mapping["route_path"]), manifest_path)
        overlay_path = _resolve_path(str(export_mapping["overlay_path"]), manifest_path)
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        recipe = ScenarioRecipe.from_jsonable(dict(overlay["recipe"]))
        selected_behavior_id = str(
            behavior_id
            or overlay.get("behavior_id")
            or manifest.get("behavior_id")
            or ""
        )
        if selected_behavior_id not in behavior_plans:
            raise ValueError(f"Unsupported behavior_id: {selected_behavior_id}")
        route_output_dir = output_dir / "routes" / f"{index:03d}_{_slug(recipe.recipe_id)}"
        route_recipe = replace(recipe, route_path=route_path)
        script_plan = compile_carla_script_plan(
            route_recipe,
            simulate_behavior(behavior_plans[selected_behavior_id]),
            route_output_dir,
        )
        overlay_actors = [dict(actor) for actor in recipe.actors]
        environment = dict(recipe.environment)
        driverx_runtime_contract = [
            str(item) for item in overlay.get("driverx_runtime_contract", [])
        ]
        script_plan = _augment_script_plan_with_overlay(script_plan, overlay_actors)
        routes.append(
            OverlayInjectionRoute(
                recipe_id=recipe.recipe_id,
                route_path=route_path,
                overlay_path=overlay_path,
                mutation=recipe.mutation,
                overlay_actors=overlay_actors,
                environment=environment,
                driverx_runtime_contract=driverx_runtime_contract,
                behavior_id=selected_behavior_id,
                memory_query=list(recipe.memory_query),
                expected_failure_mode=recipe.expected_failure_mode,
                script_plan=script_plan,
                validation_errors=[
                    *validate_carla_script_plan(script_plan),
                    *_validate_overlay_contract(
                        recipe_id=recipe.recipe_id,
                        overlay_actors=overlay_actors,
                        driverx_runtime_contract=driverx_runtime_contract,
                    ),
                ],
            )
        )
    return OverlayInjectionPlan(
        route_pack_path=manifest_path,
        route_suite_path=route_suite_path,
        runtime_mode=RUNTIME_MODE,
        runtime_note=RUNTIME_NOTE,
        routes=routes,
    )


def write_overlay_injection_plan(run_dir: Path, plan: OverlayInjectionPlan) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "overlay_injection_plan.json"
    report_path = run_dir / "overlay_injection_plan.md"
    payload = plan.to_jsonable()
    payload["json_path"] = str(json_path)
    payload["report_path"] = str(report_path)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_plan_markdown(payload), encoding="utf-8")
    return payload


def compact_overlay_injection_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_mode": summary.get("runtime_mode"),
        "num_routes": summary.get("num_routes"),
        "route_suite_path": summary.get("route_suite_path"),
        "validation_errors": summary.get("validation_errors", []),
        "routes": [
            {
                "recipe_id": route.get("recipe_id"),
                "mutation": route.get("mutation"),
                "behavior_id": route.get("behavior_id"),
                "overlay_actor_count": len(route.get("overlay_actors", [])),
                "overlay_roles": [
                    actor.get("role")
                    for actor in route.get("overlay_actors", [])
                ],
                "companion_blueprints": [
                    actor.get("blueprint_filter")
                    for actor in route.get("script_plan", {}).get("actors", [])
                    if str(actor.get("actor_ref", "")).startswith("companion_actor_")
                ],
                "tick_count": len(route.get("script_plan", {}).get("ticks", [])),
                "validation_errors": route.get("validation_errors", []),
            }
            for route in summary.get("routes", [])
        ],
        "json_path": summary.get("json_path"),
        "report_path": summary.get("report_path"),
    }


def _resolve_path(raw: str, manifest_path: Path) -> Path:
    path = Path(raw).expanduser()
    candidates = [
        path,
        manifest_path.parent / path,
        Path.cwd() / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    candidate_list = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Route-pack referenced path not found; checked {candidate_list}")


def _validate_overlay_contract(
    *,
    recipe_id: str,
    overlay_actors: list[dict[str, Any]],
    driverx_runtime_contract: list[str],
) -> list[str]:
    errors: list[str] = []
    if not overlay_actors:
        errors.append(f"{recipe_id} overlay declares no route-specific actors")
    if not driverx_runtime_contract:
        errors.append(f"{recipe_id} overlay dropped driverx_runtime_contract")
    elif driverx_runtime_contract != OVERLAY_CONTRACT:
        errors.append(f"{recipe_id} overlay driverx_runtime_contract drifted")
    return errors


def _augment_script_plan_with_overlay(
    script_plan: CarlaScriptPlan,
    overlay_actors: list[dict[str, Any]],
) -> CarlaScriptPlan:
    companion_actors = [
        _companion_actor_script(index, actor)
        for index, actor in enumerate(overlay_actors)
    ]
    companion_ticks = [
        _companion_tick(actor_script, overlay_actors[index])
        for index, actor_script in enumerate(companion_actors)
    ]
    cleanup_order = [
        *script_plan.cleanup_order[:-1],
        *(actor.actor_ref for actor in companion_actors),
        script_plan.cleanup_order[-1],
    ]
    return replace(
        script_plan,
        actors=[*script_plan.actors, *companion_actors],
        ticks=[*companion_ticks, *script_plan.ticks],
        cleanup_order=cleanup_order,
    )


def _companion_actor_script(index: int, actor: dict[str, Any]) -> CarlaActorScript:
    role = str(actor.get("role", "overlay_actor"))
    asset = str(actor.get("asset", "generic_overlay_asset"))
    placement = str(actor.get("placement", "near route"))
    return CarlaActorScript(
        actor_ref=f"companion_actor_{index}",
        role=role,
        blueprint_filter=_blueprint_for_overlay(role, asset),
        spawn_transform=_spawn_transform_for_overlay(role, asset, placement, index),
        behavior_id=None,
        sample_count=1,
    )


def _companion_tick(actor_script: CarlaActorScript, actor: dict[str, Any]) -> dict[str, Any]:
    return {
        "t_s": 0.0,
        "actor_ref": actor_script.actor_ref,
        "target_transform": actor_script.spawn_transform,
        "target_speed_mps": 0.0,
        "overlay_role": str(actor.get("role", "")),
        "overlay_asset": str(actor.get("asset", "")),
        "overlay_placement": str(actor.get("placement", "")),
    }


def _blueprint_for_overlay(role: str, asset: str) -> str:
    key = f"{role} {asset}".lower()
    if "two_wheeler" in key or "motorcycle" in key or "scooter" in key:
        return "vehicle.kawasaki.ninja"
    if "pedestrian" in key or "walker" in key:
        return "walker.pedestrian.*"
    if "barrier" in key or "construction" in key or "occluder" in key:
        return "static.prop.streetbarrier"
    if "sign" in key or "visual" in key or "distractor" in key:
        return "static.prop.trafficwarning"
    if "vehicle" in key or "stalled" in key:
        return "vehicle.*"
    return "static.prop.trafficcone"


def _spawn_transform_for_overlay(
    role: str,
    asset: str,
    placement: str,
    index: int,
) -> dict[str, dict[str, float]]:
    key = f"{role} {asset} {placement}".lower()
    offset = float(index) * 1.5
    if "occluder" in key or "before crossing" in key:
        return _transform(8.0 + offset, -1.75, 0.2, 90.0)
    if "distractor" in key or "outside" in key or "sign" in key:
        return _transform(12.0 + offset, 4.5, 0.2, 0.0)
    if "two_wheeler" in key or "adjacent lane" in key:
        return _transform(2.0 + offset, 1.75, 0.2, 0.0)
    if "block" in key or "lane" in key:
        return _transform(10.0 + offset, 0.0, 0.2, 0.0)
    return _transform(6.0 + offset, 0.0, 0.2, 0.0)


def _transform(x: float, y: float, z: float = 0.2, yaw: float = 0.0) -> dict[str, dict[str, float]]:
    return {
        "location": {"x": x, "y": y, "z": z},
        "rotation": {"pitch": 0.0, "yaw": yaw, "roll": 0.0},
    }


def _plan_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Overlay Injection Plan",
        "",
        f"- runtime_mode: `{payload['runtime_mode']}`",
        f"- routes: `{payload['num_routes']}`",
        f"- route_pack_path: `{payload['route_pack_path']}`",
        f"- route_suite_path: `{payload['route_suite_path']}`",
        f"- validation_errors: `{len(payload['validation_errors'])}`",
        "",
        payload["runtime_note"],
        "",
        "## Routes",
        "",
        "| recipe | mutation | overlay roles | companion blueprints | behavior | ticks | validation |",
        "|---|---|---|---|---|---|---|",
    ]
    for route in payload["routes"]:
        companion_blueprints = [
            actor["blueprint_filter"]
            for actor in route["script_plan"]["actors"]
            if str(actor["actor_ref"]).startswith("companion_actor_")
        ]
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(route["recipe_id"]),
                    _cell(route["mutation"]),
                    _cell(", ".join(str(actor["role"]) for actor in route["overlay_actors"])),
                    _cell(", ".join(companion_blueprints)),
                    _cell(route["behavior_id"]),
                    _cell(len(route["script_plan"]["ticks"])),
                    _cell(", ".join(route["validation_errors"]) or "ok"),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


__all__ = [
    "OverlayInjectionPlan",
    "OverlayInjectionRoute",
    "compact_overlay_injection_summary",
    "compile_overlay_injection_plan",
    "write_overlay_injection_plan",
]
