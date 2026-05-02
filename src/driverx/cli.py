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
        help="Number of Waymo frames to stream for dataset.kind=waymo.",
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
    except (FileNotFoundError, ImportError, IndexError, ValueError) as exc:
        print(f"driverx error: {exc}", file=sys.stderr)
        return 2


__all__ = ["DriverConfig", "build_parser", "main"]
