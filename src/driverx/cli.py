"""Command-line entrypoints for 0xDriver."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from driverx.core.config import DriverConfig, load_config


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/mock.yaml"),
        help="Path to a driverx YAML or JSON config.",
    )


def _command_inspect_scene(args: argparse.Namespace) -> int:
    from driverx.pipeline.scene_run import inspect_scene

    config = load_config(args.config)
    result = inspect_scene(config)
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_run_scene(args: argparse.Namespace) -> int:
    from driverx.pipeline.scene_run import run_scene

    config = load_config(args.config)
    result = run_scene(config)
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_evaluate(args: argparse.Namespace) -> int:
    from driverx.evaluation.reports import evaluate_run_dir

    report = evaluate_run_dir(args.run_dir)
    print(json.dumps(report, indent=2))
    return 0


def _command_package_submission(args: argparse.Namespace) -> int:
    from driverx.submission.waymo_packager import package_run_dir

    package = package_run_dir(args.run_dir, output_path=args.output)
    print(json.dumps(package, indent=2))
    return 0


def _command_show_config(args: argparse.Namespace) -> int:
    config = load_config(args.config)
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
    return int(args.func(args))


__all__ = ["DriverConfig", "build_parser", "main"]
