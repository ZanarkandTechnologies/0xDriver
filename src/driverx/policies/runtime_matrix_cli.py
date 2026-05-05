"""CLI glue for policy runtime readiness matrices."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.policies.runtime_matrix import build_policy_runtime_matrix


def command_build_policy_runtime_matrix(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = build_policy_runtime_matrix(
        run_dir,
        carla_config_path=args.carla_config,
        simlingo_config_path=args.simlingo_config,
        suite_path=args.suite,
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_policy_runtime_matrix_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "build-policy-runtime-matrix",
        help="Report which policy adapters are locally ready, planned, or blocked.",
    )
    parser.add_argument("--carla-config", type=Path)
    parser.add_argument("--simlingo-config", type=Path)
    parser.add_argument("--suite", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="policy-runtime-matrix")
    parser.set_defaults(func=command_build_policy_runtime_matrix)


__all__ = [
    "command_build_policy_runtime_matrix",
    "register_policy_runtime_matrix_parser",
]
