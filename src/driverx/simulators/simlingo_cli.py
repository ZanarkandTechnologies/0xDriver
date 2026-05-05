"""CLI glue for SimLingo and sidecar commands."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators import (
    build_simlingo_sidecar_plan,
    compact_simlingo_evidence_summary,
    compact_simlingo_result_summary,
    inspect_simlingo_checkout,
    load_simlingo_run_config,
    parse_simlingo_result,
    plan_simlingo_run,
    run_simlingo_sidecar_processes,
    scan_simlingo_evidence,
    write_simlingo_evidence_report,
    write_simlingo_plan,
    write_simlingo_readiness,
    write_simlingo_result_report,
    write_simlingo_sidecar_plan,
    write_simlingo_sidecar_run,
)


def command_inspect_simlingo(args: argparse.Namespace) -> int:
    readiness = inspect_simlingo_checkout(args.root)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_simlingo_readiness(run_dir, readiness)
    print(json.dumps(summary, indent=2))
    return 0


def command_plan_simlingo_run(args: argparse.Namespace) -> int:
    config = load_simlingo_run_config(args.config)
    if args.checkpoint_path is not None:
        config = replace(config, checkpoint_path=args.checkpoint_path)
    if args.route_path is not None:
        config = replace(config, route_path=args.route_path)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_simlingo_plan(run_dir, plan_simlingo_run(config))
    print(json.dumps(summary, indent=2))
    return 0


def command_ingest_simlingo_result(args: argparse.Namespace) -> int:
    record = parse_simlingo_result(args.result)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_simlingo_result_report(
        run_dir,
        record,
        compatibility_path=args.compatibility,
        route_log_path=args.route_log,
    )
    print(json.dumps(compact_simlingo_result_summary(summary), indent=2))
    return 0


def command_summarize_simlingo_evidence(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    scan = scan_simlingo_evidence(args.artifact_root)
    summary = write_simlingo_evidence_report(run_dir, scan)
    print(json.dumps(compact_simlingo_evidence_summary(summary), indent=2))
    return 0


def command_plan_simlingo_sidecar(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    plan = build_simlingo_sidecar_plan(
        simlingo_plan_path=args.simlingo_plan,
        overlay_plan_path=args.overlay_plan,
        output_dir=run_dir,
        carla_config_path=args.carla_config,
        tick_limit=args.tick_limit,
        overlay_start_delay_s=args.overlay_start_delay_s,
        use_docker_carla_client=args.docker_carla_client,
    )
    summary = write_simlingo_sidecar_plan(run_dir, plan)
    print(json.dumps(summary, indent=2))
    return 0


def command_run_simlingo_sidecar(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = run_simlingo_sidecar_processes(
        args.plan,
        run_dir,
        timeout_s=args.timeout_s,
        dry_run=args.dry_run,
    )
    summary = write_simlingo_sidecar_run(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0 if result.success else 1


def register_simlingo_parsers(subparsers: Any) -> None:
    simlingo_inspect_parser = subparsers.add_parser(
        "inspect-simlingo",
        help="Inspect an external SimLingo/CarLLaVA checkout and write readiness artifacts.",
    )
    simlingo_inspect_parser.add_argument("--root", type=Path, default=Path("../external/simlingo"))
    _add_output_args(simlingo_inspect_parser, "simlingo-readiness")
    simlingo_inspect_parser.set_defaults(func=command_inspect_simlingo)

    simlingo_plan_parser = subparsers.add_parser(
        "plan-simlingo-run",
        help="Write a dry-run SimLingo Bench2Drive evaluation command plan.",
    )
    simlingo_plan_parser.add_argument("--config", type=Path, default=Path("configs/simlingo.sample.yaml"))
    simlingo_plan_parser.add_argument("--checkpoint-path", type=Path)
    simlingo_plan_parser.add_argument("--route-path", type=Path)
    _add_output_args(simlingo_plan_parser, "simlingo-plan")
    simlingo_plan_parser.set_defaults(func=command_plan_simlingo_run)

    simlingo_ingest_parser = subparsers.add_parser(
        "ingest-simlingo-result",
        help="Parse a SimLingo/Bench2Drive result JSON and write a report.",
    )
    simlingo_ingest_parser.add_argument("--result", type=Path, required=True)
    simlingo_ingest_parser.add_argument("--compatibility", type=Path)
    simlingo_ingest_parser.add_argument("--route-log", type=Path)
    _add_output_args(simlingo_ingest_parser, "simlingo-result")
    simlingo_ingest_parser.set_defaults(func=command_ingest_simlingo_result)

    simlingo_evidence_parser = subparsers.add_parser(
        "summarize-simlingo-evidence",
        help="Classify compact pulled remote SimLingo artifacts.",
    )
    simlingo_evidence_parser.add_argument("--artifact-root", type=Path, required=True)
    _add_output_args(simlingo_evidence_parser, "remote-simlingo-evidence")
    simlingo_evidence_parser.set_defaults(func=command_summarize_simlingo_evidence)

    sidecar_parser = subparsers.add_parser(
        "plan-simlingo-sidecar",
        help="Plan a two-process SimLingo plus DriverX overlay-injector run.",
    )
    sidecar_parser.add_argument("--simlingo-plan", type=Path, required=True)
    sidecar_parser.add_argument("--overlay-plan", type=Path, required=True)
    sidecar_parser.add_argument("--carla-config", type=Path, default=Path("configs/carla_local.sample.yaml"))
    sidecar_parser.add_argument("--tick-limit", type=int)
    sidecar_parser.add_argument("--overlay-start-delay-s", type=float, default=5.0)
    sidecar_parser.add_argument("--docker-carla-client", action="store_true")
    _add_output_args(sidecar_parser, "simlingo-sidecar")
    sidecar_parser.set_defaults(func=command_plan_simlingo_sidecar)

    sidecar_run_parser = subparsers.add_parser(
        "run-simlingo-sidecar",
        help="Run commands from a SimLingo sidecar plan with timed process supervision.",
    )
    sidecar_run_parser.add_argument("--plan", type=Path, required=True)
    sidecar_run_parser.add_argument("--timeout-s", type=float)
    sidecar_run_parser.add_argument("--dry-run", action="store_true")
    _add_output_args(sidecar_run_parser, "simlingo-sidecar-run")
    sidecar_run_parser.set_defaults(func=command_run_simlingo_sidecar)


def _add_output_args(parser: argparse.ArgumentParser, run_id: str) -> None:
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default=run_id)


__all__ = [
    "command_ingest_simlingo_result",
    "command_inspect_simlingo",
    "command_plan_simlingo_run",
    "command_plan_simlingo_sidecar",
    "command_run_simlingo_sidecar",
    "command_summarize_simlingo_evidence",
    "register_simlingo_parsers",
]
