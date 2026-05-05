"""CLI glue for generated OOD suite orchestration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.pipeline.generated_ood_suite import GeneratedOodSuiteConfig, run_generated_ood_suite


def command_run_generated_ood_suite(args: argparse.Namespace) -> int:
    summary = run_generated_ood_suite(
        GeneratedOodSuiteConfig(
            scenario_config_path=args.scenario_config,
            carla_config_path=args.carla_config,
            output_root=args.output_root,
            run_id=args.run_id,
            route_root=args.route_root,
            behavior_id=args.behavior_id,
            count=args.count,
            limit=args.limit,
            random_seed=args.seed,
        )
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_generated_ood_suite_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "run-generated-ood-suite",
        help="Generate OOD recipes, route plans, and evidence bundles as a suite.",
    )
    parser.add_argument("--scenario-config", type=Path, default=Path("configs/scenario_forge.sample.yaml"))
    parser.add_argument("--carla-config", type=Path, default=Path("configs/carla_local.sample.yaml"))
    parser.add_argument("--route-root", type=Path)
    parser.add_argument("--behavior-id", default="no_signal_cut_in")
    parser.add_argument("--count", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="generated-ood-suite")
    parser.set_defaults(func=command_run_generated_ood_suite)


__all__ = ["command_run_generated_ood_suite", "register_generated_ood_suite_parser"]
