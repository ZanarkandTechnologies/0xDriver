"""Command-line entrypoints for 0xDriver."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from driverx.core.config import DriverConfig, OutputConfig, load_config


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/mock.yaml"),
        help="Path to a driverx YAML or JSON config.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Override output.root from config.",
    )
    parser.add_argument(
        "--run-id",
        help="Override output.run_id from config.",
    )


def _load_config_from_args(args: argparse.Namespace) -> DriverConfig:
    config = load_config(args.config)
    if args.output_root is None and args.run_id is None:
        return config
    return replace(
        config,
        output=OutputConfig(
            root=args.output_root or config.output.root,
            run_id=args.run_id if args.run_id is not None else config.output.run_id,
        ),
    )


def _command_inspect_scene(args: argparse.Namespace) -> int:
    from driverx.pipeline.scene_run import inspect_scene

    config = _load_config_from_args(args)
    result = inspect_scene(config)
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_run_scene(args: argparse.Namespace) -> int:
    from driverx.pipeline.scene_run import run_scene

    config = _load_config_from_args(args)
    result = run_scene(config)
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_run_batch(args: argparse.Namespace) -> int:
    from driverx.pipeline.batch_run import run_batch

    config = _load_config_from_args(args)
    result = run_batch(
        config,
        fixture_names=args.fixtures,
        frame_start=args.frame_start,
        frame_count=args.frame_count,
    )
    print(json.dumps(result, indent=2))
    return 0


def _command_run_experiment(args: argparse.Namespace) -> int:
    from driverx.pipeline.experiment_run import run_experiment

    config = _load_config_from_args(args)
    result = run_experiment(
        config,
        frame_start=args.frame_start,
        frame_count=args.frame_count,
    )
    print(json.dumps(result, indent=2))
    return 0


def _command_evaluate(args: argparse.Namespace) -> int:
    from driverx.evaluation.reports import evaluate_run_dir

    report = evaluate_run_dir(args.run_dir)
    print(json.dumps(report, indent=2))
    return 0


def _command_package_submission(args: argparse.Namespace) -> int:
    from driverx.submission.waymo_packager import package_run_dir

    package = package_run_dir(args.run_dir, output_path=args.output, official=args.official)
    print(json.dumps(package, indent=2))
    return 0


def _mapping_output(raw: dict, default_run_id: str) -> OutputConfig:
    from driverx.core.config import OutputConfig

    output = raw.get("output", {})
    if not isinstance(output, dict):
        raise ValueError("Config field 'output' must be a mapping.")
    return OutputConfig(
        root=Path(str(output.get("root", "artifacts/runs"))),
        run_id=str(output.get("run_id", default_run_id)),
    )


def _command_forge_scenarios(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.core.config import read_config_mapping
    from driverx.scenarios import (
        MutationPolicy,
        generate_scenario_recipes,
        load_scenario_seeds,
        write_scenario_suite,
    )

    raw = read_config_mapping(args.config)
    scenario = raw.get("scenario", {})
    if not isinstance(scenario, dict):
        raise ValueError("Config field 'scenario' must be a mapping.")
    output = _mapping_output(raw, "scenario-forge")
    if args.output_root is not None or args.run_id is not None:
        output = OutputConfig(
            root=args.output_root or output.root,
            run_id=args.run_id if args.run_id is not None else output.run_id,
        )
    seed_path = Path(str(scenario.get("seeds_path", "tests/fixtures/fail2drive_like/seeds.json")))
    count = args.count if args.count is not None else int(scenario.get("count", 8))
    random_seed = args.seed if args.seed is not None else int(scenario.get("random_seed", 7))
    mutations_raw = str(
        scenario.get(
            "mutations",
            "obstacle_substitution,occlusion,visual_noise,lane_blockage,regional_driving_behavior",
        )
    )
    mutations = tuple(item.strip() for item in mutations_raw.split(",") if item.strip())
    seeds = load_scenario_seeds(seed_path)
    recipes = generate_scenario_recipes(
        seeds,
        MutationPolicy(mutations=mutations),
        count=count,
        random_seed=random_seed,
    )
    run_dir = prepare_run_dir(output.root, output.run_id)
    summary = write_scenario_suite(run_dir, seeds, recipes)
    print(json.dumps(summary, indent=2))
    return 0


def _command_build_memory(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.memory import build_memory_bank, write_memory_bank
    from driverx.scenarios import load_scenario_results

    results = load_scenario_results(args.results)
    bank = build_memory_bank(results)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_memory_bank(run_dir, bank)
    print(json.dumps(summary, indent=2))
    return 0


def _select_recipe_payload(
    recipes: list[dict[str, object]],
    recipe_id: str | None,
    path: Path,
) -> dict[str, object]:
    if not recipes:
        raise ValueError(f"No recipes found in {path}")
    if recipe_id is not None:
        for recipe in recipes:
            if str(recipe.get("recipe_id")) == recipe_id:
                return recipe
        raise ValueError(f"Recipe id not found in {path}: {recipe_id}")
    if len(recipes) == 1:
        return recipes[0]
    raise ValueError(
        f"{path} contains {len(recipes)} recipes; pass --recipe-id to plan one explicit route."
    )


def _load_recipe(path: Path, recipe_id: str | None):
    from driverx.scenarios import ScenarioRecipe

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return ScenarioRecipe.from_jsonable(
            _select_recipe_payload([dict(recipe) for recipe in raw], recipe_id, path)
        )
    if isinstance(raw, dict) and "recipes" in raw:
        recipes = raw.get("recipes", [])
        return ScenarioRecipe.from_jsonable(
            _select_recipe_payload([dict(recipe) for recipe in recipes], recipe_id, path)
        )
    if isinstance(raw, dict):
        if recipe_id is not None and str(raw.get("recipe_id")) != recipe_id:
            raise ValueError(f"Recipe id not found in {path}: {recipe_id}")
        return ScenarioRecipe.from_jsonable(raw)
    raise ValueError(f"Unsupported recipe JSON: {path}")


def _command_plan_carla_run(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import load_carla_run_config, plan_fail2drive_run

    config = load_carla_run_config(args.config)
    recipe = _load_recipe(args.recipe, args.recipe_id)
    plan = plan_fail2drive_run(config, recipe)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    path = run_dir / "carla_command_plan.json"
    payload = plan.to_jsonable()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["plan_path"] = str(path)
    print(json.dumps(payload, indent=2))
    return 0


def _command_smoke_carla(args: argparse.Namespace) -> int:
    from driverx.simulators import load_carla_run_config, smoke_carla_server

    config = load_carla_run_config(args.config)
    result = smoke_carla_server(config.host, config.port, config.timeout_s)
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_probe_carla(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import CarlaProbeConfig, load_carla_run_config
    from driverx.simulators import probe_carla_client, write_carla_probe

    config = load_carla_run_config(args.config)
    probe_config = CarlaProbeConfig(
        host=args.host if args.host is not None else config.host,
        port=args.port if args.port is not None else config.port,
        timeout_s=args.timeout_s if args.timeout_s is not None else config.timeout_s,
    )
    result = probe_carla_client(probe_config)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_carla_probe(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


def _command_spawn_ego_smoke(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import CarlaEgoSmokeConfig, load_carla_run_config
    from driverx.simulators import run_ego_spawn_smoke, write_ego_smoke

    config = load_carla_run_config(args.config)
    smoke_config = CarlaEgoSmokeConfig(
        host=args.host if args.host is not None else config.host,
        port=args.port if args.port is not None else config.port,
        timeout_s=args.timeout_s if args.timeout_s is not None else config.timeout_s,
        tick_count=args.tick_count,
        camera_width=args.camera_width,
        camera_height=args.camera_height,
    )
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = run_ego_spawn_smoke(smoke_config, run_dir)
    summary = write_ego_smoke(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


def _command_generate_behaviors(args: argparse.Namespace) -> int:
    from driverx.behaviors import default_behavior_plans, simulate_behavior
    from driverx.behaviors import write_behavior_suite
    from driverx.core.artifacts import prepare_run_dir

    traces = [simulate_behavior(plan) for plan in default_behavior_plans()]
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_behavior_suite(run_dir, traces)
    print(json.dumps(summary, indent=2))
    return 0


def _command_show_config(args: argparse.Namespace) -> int:
    config = _load_config_from_args(args)
    print(json.dumps(config.to_jsonable(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="driverx",
        description="Run the 0xDriver fixture-backed autonomy pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect-scene",
        help="Render one configured scene without running the planner.",
    )
    _add_config_arg(inspect_parser)
    inspect_parser.set_defaults(func=_command_inspect_scene)

    run_parser = subparsers.add_parser(
        "run-scene",
        help="Run one scene through reasoning, planning, evaluation, and artifacts.",
    )
    _add_config_arg(run_parser)
    run_parser.set_defaults(func=_command_run_scene)

    batch_parser = subparsers.add_parser(
        "run-batch",
        help="Run a tiny validation batch over fixture scenes or Waymo frames.",
    )
    _add_config_arg(batch_parser)
    batch_parser.add_argument(
        "--fixtures",
        nargs="+",
        default=None,
        help="Fixture names to run. Defaults to two fixtures for fixture configs.",
    )
    batch_parser.add_argument(
        "--frame-start",
        type=int,
        help="First global Waymo frame index to stream for dataset.kind=waymo.",
    )
    batch_parser.add_argument(
        "--frame-count",
        type=int,
        help="Number of Waymo frames to stream for dataset.kind=waymo.",
    )
    batch_parser.set_defaults(func=_command_run_batch)

    experiment_parser = subparsers.add_parser(
        "run-experiment",
        help="Compare trajectory strategies over fixture or Waymo frames.",
    )
    _add_config_arg(experiment_parser)
    experiment_parser.add_argument(
        "--frame-start",
        type=int,
        help="First global Waymo frame index to stream for dataset.kind=waymo.",
    )
    experiment_parser.add_argument(
        "--frame-count",
        type=int,
        help="Number of Waymo frames to stream. Defaults to 10 for dataset.kind=waymo.",
    )
    experiment_parser.set_defaults(func=_command_run_experiment)

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate an existing run directory.",
    )
    evaluate_parser.add_argument("--run-dir", type=Path, required=True)
    evaluate_parser.set_defaults(func=_command_evaluate)

    package_parser = subparsers.add_parser(
        "package-submission",
        help="Create a dry-run Waymo-style submission package from a run directory.",
    )
    package_parser.add_argument("--run-dir", type=Path, required=True)
    package_parser.add_argument("--output", type=Path)
    package_parser.add_argument(
        "--official",
        action="store_true",
        help="Use official Waymo protobuf serialization when optional deps are installed.",
    )
    package_parser.set_defaults(func=_command_package_submission)

    forge_parser = subparsers.add_parser(
        "forge-scenarios",
        help="Generate deterministic OOD scenario recipes from Fail2Drive-style seeds.",
    )
    forge_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/scenario_forge.sample.yaml"),
    )
    forge_parser.add_argument("--count", type=int)
    forge_parser.add_argument("--seed", type=int)
    forge_parser.add_argument("--output-root", type=Path)
    forge_parser.add_argument("--run-id")
    forge_parser.set_defaults(func=_command_forge_scenarios)

    memory_parser = subparsers.add_parser(
        "build-memory",
        help="Build compact safety memory from scenario result records.",
    )
    memory_parser.add_argument("--results", type=Path, required=True)
    memory_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    memory_parser.add_argument("--run-id", default="memory-bank")
    memory_parser.set_defaults(func=_command_build_memory)

    plan_parser = subparsers.add_parser(
        "plan-carla-run",
        help="Write a dry-run CARLA/Fail2Drive command plan for one recipe.",
    )
    plan_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    plan_parser.add_argument("--recipe", type=Path, required=True)
    plan_parser.add_argument(
        "--recipe-id",
        help="Recipe id to select when --recipe points at a multi-recipe suite.",
    )
    plan_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    plan_parser.add_argument("--run-id", default="carla-plan")
    plan_parser.set_defaults(func=_command_plan_carla_run)

    smoke_parser = subparsers.add_parser(
        "smoke-carla",
        help="Check whether a CARLA server TCP port is reachable.",
    )
    smoke_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    smoke_parser.set_defaults(func=_command_smoke_carla)

    probe_parser = subparsers.add_parser(
        "probe-carla",
        help="Collect CARLA Python API state into JSON/Markdown artifacts.",
    )
    probe_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    probe_parser.add_argument("--host")
    probe_parser.add_argument("--port", type=int)
    probe_parser.add_argument("--timeout-s", type=float)
    probe_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    probe_parser.add_argument("--run-id", default="carla-probe")
    probe_parser.set_defaults(func=_command_probe_carla)

    ego_parser = subparsers.add_parser(
        "spawn-ego-smoke",
        help="Spawn one CARLA ego vehicle and camera, capture tracks, then clean up.",
    )
    ego_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    ego_parser.add_argument("--host")
    ego_parser.add_argument("--port", type=int)
    ego_parser.add_argument("--timeout-s", type=float)
    ego_parser.add_argument("--tick-count", type=int, default=5)
    ego_parser.add_argument("--camera-width", type=int, default=320)
    ego_parser.add_argument("--camera-height", type=int, default=180)
    ego_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    ego_parser.add_argument("--run-id", default="ego-smoke")
    ego_parser.set_defaults(func=_command_spawn_ego_smoke)

    behavior_parser = subparsers.add_parser(
        "generate-behaviors",
        help="Generate deterministic OOD behavior traces and metrics.",
    )
    behavior_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    behavior_parser.add_argument("--run-id", default="behavior-suite")
    behavior_parser.set_defaults(func=_command_generate_behaviors)

    config_parser = subparsers.add_parser(
        "show-config",
        help="Print the resolved config.",
    )
    _add_config_arg(config_parser)
    config_parser.set_defaults(func=_command_show_config)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (FileNotFoundError, ImportError, IndexError, OSError, ValueError) as exc:
        print(f"driverx error: {exc}", file=sys.stderr)
        return 2


__all__ = ["DriverConfig", "build_parser", "main"]
