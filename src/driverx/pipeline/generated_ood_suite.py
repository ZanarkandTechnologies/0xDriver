"""Orchestrate generated OOD scenarios into dry-run route and evidence bundles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.core.config import read_config_mapping
from driverx.pipeline.route_evidence import RouteEvidenceInputs, build_route_evidence
from driverx.scenarios import (
    MutationPolicy,
    ScenarioRecipe,
    generate_scenario_recipes,
    load_scenario_seeds,
    write_scenario_suite,
)
from driverx.simulators import (
    Fail2DriveVideoSmokeConfig,
    OverlayEvidenceInputs,
    build_bench2drive_route_suite,
    build_overlay_evidence,
    compile_overlay_injection_plan,
    load_carla_run_config,
    plan_fail2drive_video_smoke,
    write_bench2drive_route_suite,
    write_fail2drive_video_smoke_plan,
    write_overlay_injection_plan,
)


@dataclass(frozen=True)
class GeneratedOodSuiteConfig:
    scenario_config_path: Path
    carla_config_path: Path
    output_root: Path
    run_id: str
    route_root: Path | None = None
    behavior_id: str = "no_signal_cut_in"
    count: int | None = None
    limit: int | None = None
    random_seed: int | None = None


def run_generated_ood_suite(config: GeneratedOodSuiteConfig) -> dict[str, Any]:
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    scenario_raw = read_config_mapping(config.scenario_config_path)
    scenario = _mapping(scenario_raw.get("scenario"))
    count = config.count if config.count is not None else int(scenario.get("count", 8))
    random_seed = config.random_seed if config.random_seed is not None else int(scenario.get("random_seed", 7))
    seeds_path = Path(str(scenario.get("seeds_path", "tests/fixtures/fail2drive_like/seeds.json")))
    mutations = _mutations(str(scenario.get("mutations", "")))
    seeds = load_scenario_seeds(seeds_path)
    recipes = generate_scenario_recipes(
        seeds,
        MutationPolicy(mutations=mutations),
        count=count,
        random_seed=random_seed,
    )
    if config.limit is not None:
        recipes = recipes[: config.limit]
    if not recipes:
        raise ValueError("Generated OOD suite needs at least one recipe.")
    scenario_summary = write_scenario_suite(run_dir / "scenario-forge", seeds, recipes)
    carla_config = load_carla_run_config(config.carla_config_path)
    route_root = (config.route_root or carla_config.fail2drive_root).expanduser()
    route_pack_dir = run_dir / "route-pack"
    route_suite = build_bench2drive_route_suite(
        route_pack_dir,
        recipes,
        route_root=route_root,
        behavior_id=config.behavior_id,
    )
    route_pack = write_bench2drive_route_suite(route_pack_dir, route_suite)
    overlay_dir = run_dir / "overlay-plan"
    overlay_plan = compile_overlay_injection_plan(
        Path(str(route_pack["manifest_path"])),
        overlay_dir,
        behavior_id=config.behavior_id,
    )
    overlay_plan_summary = write_overlay_injection_plan(overlay_dir, overlay_plan)
    recipe_records = [
        _recipe_record(run_dir, carla_config, recipe, index)
        for index, recipe in enumerate(recipes)
    ]
    overlay_evidence = build_overlay_evidence(
        run_dir / "overlay-evidence",
        OverlayEvidenceInputs(
            overlay_plan_path=Path(str(overlay_plan_summary["json_path"])),
        ),
    )
    blockers = _aggregate_blockers(recipe_records, overlay_evidence)
    payload = {
        "suite_id": run_dir.name,
        "status": "ready" if not blockers else "blocked",
        "num_recipes": len(recipes),
        "limit": config.limit,
        "behavior_id": config.behavior_id,
        "scenario_summary_path": scenario_summary["summary_path"],
        "route_pack_path": route_pack["manifest_path"],
        "overlay_plan_path": overlay_plan_summary["json_path"],
        "overlay_evidence_path": overlay_evidence["json_path"],
        "recipe_records": recipe_records,
        "readiness": _readiness(recipe_records, overlay_evidence, blockers),
        "blockers": blockers,
    }
    return write_generated_ood_suite(run_dir, payload)


def write_generated_ood_suite(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    json_path = run_dir / "generated_ood_suite.json"
    report_path = run_dir / "generated_ood_suite.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _recipe_record(
    run_dir: Path,
    carla_config: Any,
    recipe: ScenarioRecipe,
    index: int,
) -> dict[str, Any]:
    recipe_dir = run_dir / "recipes" / f"{index:03d}_{_slug(recipe.recipe_id)}"
    route_config = replace(carla_config, route_path=recipe.route_path or carla_config.route_path)
    smoke_config = Fail2DriveVideoSmokeConfig.from_carla_config(
        route_config,
        output_dir=recipe_dir / "fail2drive_outputs",
    )
    smoke_summary = write_fail2drive_video_smoke_plan(
        recipe_dir,
        plan_fail2drive_video_smoke(smoke_config),
    )
    evidence = build_route_evidence(
        recipe_dir / "route-evidence",
        RouteEvidenceInputs(plan_path=Path(str(smoke_summary["json_path"]))),
    )
    return {
        "recipe_id": recipe.recipe_id,
        "parent_seed_id": recipe.parent_seed_id,
        "mutation": recipe.mutation,
        "route_path": str(recipe.route_path) if recipe.route_path else None,
        "video_smoke_plan_path": smoke_summary["json_path"],
        "route_evidence_path": evidence["json_path"],
        "route_evidence_status": evidence["status"],
        "blockers": list(evidence.get("blockers", [])),
    }


def _aggregate_blockers(
    recipe_records: list[dict[str, Any]],
    overlay_evidence: dict[str, Any],
) -> list[str]:
    seen: set[str] = set()
    blockers: list[str] = []
    for record in recipe_records:
        for blocker in list(record.get("blockers", [])):
            text = f"{record['recipe_id']}: {blocker}"
            if text not in seen:
                blockers.append(text)
                seen.add(text)
    for blocker in list(overlay_evidence.get("blockers", [])):
        text = f"overlay: {blocker}"
        if text not in seen:
            blockers.append(text)
            seen.add(text)
    return blockers


def _readiness(
    recipe_records: list[dict[str, Any]],
    overlay_evidence: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    return {
        "recipe_count": len(recipe_records),
        "route_evidence_ready_count": sum(
            1 for record in recipe_records if record.get("route_evidence_status") == "ready"
        ),
        "overlay_evidence_status": overlay_evidence.get("status"),
        "blocker_count": len(blockers),
        "can_run_live": False if blockers else True,
    }


def _mutations(raw: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    return values or (
        "obstacle_substitution",
        "occlusion",
        "visual_noise",
        "lane_blockage",
        "regional_driving_behavior",
    )


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value.lower()).strip("-")


def _markdown(payload: dict[str, Any]) -> str:
    readiness = _mapping(payload.get("readiness"))
    lines = [
        "# Generated OOD Suite",
        "",
        f"- suite_id: `{payload.get('suite_id')}`",
        f"- status: `{payload.get('status')}`",
        f"- recipes: `{payload.get('num_recipes')}`",
        f"- behavior_id: `{payload.get('behavior_id')}`",
        f"- blocker_count: `{readiness.get('blocker_count')}`",
        f"- overlay_evidence_status: `{readiness.get('overlay_evidence_status')}`",
        "",
        "## Recipe Records",
        "",
    ]
    for record in list(payload.get("recipe_records", [])):
        lines.append(
            f"- `{record.get('recipe_id')}`: route_evidence=`{record.get('route_evidence_status')}`, "
            f"blockers=`{len(list(record.get('blockers', [])))}`"
        )
    lines.extend(["", "## Blockers", ""])
    blockers = [str(blocker) for blocker in list(payload.get("blockers", []))]
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers[:20])
        if len(blockers) > 20:
            lines.append(f"- ... {len(blockers) - 20} more")
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "GeneratedOodSuiteConfig",
    "run_generated_ood_suite",
    "write_generated_ood_suite",
]
