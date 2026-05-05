"""CLI glue for GPU host suitability assessment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.gpu_host_suitability import (
    assess_gpu_host_suitability,
    write_gpu_host_suitability_report,
)


def command_assess_gpu_host(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    assessment = assess_gpu_host_suitability(
        gpu_snapshot_path=args.gpu_snapshot,
        torch_compatibility_path=args.torch_compatibility,
        carla_diagnostics_path=args.carla_diagnostics,
        simlingo_evidence_path=args.simlingo_evidence,
    )
    summary = write_gpu_host_suitability_report(run_dir, assessment)
    print(json.dumps(summary, indent=2))
    return 0


def register_gpu_host_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "assess-gpu-host",
        help="Assess whether a remote GPU host is suitable for SimLingo plus CARLA.",
    )
    parser.add_argument("--gpu-snapshot", type=Path)
    parser.add_argument("--torch-compatibility", type=Path)
    parser.add_argument("--carla-diagnostics", type=Path)
    parser.add_argument("--simlingo-evidence", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="gpu-host-suitability")
    parser.set_defaults(func=command_assess_gpu_host)


__all__ = ["command_assess_gpu_host", "register_gpu_host_parser"]
