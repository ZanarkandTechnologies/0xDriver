"""SimLingo/CarLLaVA checkout inspection and dry-run command planning."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.core.config import read_config_mapping


@dataclass(frozen=True)
class SimLingoRunConfig:
    simlingo_root: Path
    carla_root: Path
    checkpoint_path: Path
    route_path: Path
    output_dir: Path
    seed: int = 1
    world_port: int = 20000
    traffic_manager_port: int = 10000
    timeout_s: int = 600

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "simlingo_root": str(self.simlingo_root),
            "carla_root": str(self.carla_root),
            "checkpoint_path": str(self.checkpoint_path),
            "route_path": str(self.route_path),
            "output_dir": str(self.output_dir),
            "seed": self.seed,
            "world_port": self.world_port,
            "traffic_manager_port": self.traffic_manager_port,
            "timeout_s": self.timeout_s,
        }


@dataclass(frozen=True)
class SimLingoReadiness:
    root: Path
    exists: bool
    commit: str | None
    required_files: dict[str, bool]
    carla_version: str
    python_version: str
    requires_cuda: bool
    apple_silicon_live_supported: bool
    blockers: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "exists": self.exists,
            "commit": self.commit,
            "required_files": self.required_files,
            "carla_version": self.carla_version,
            "python_version": self.python_version,
            "requires_cuda": self.requires_cuda,
            "apple_silicon_live_supported": self.apple_silicon_live_supported,
            "blockers": self.blockers,
        }


@dataclass(frozen=True)
class SimLingoCommandPlan:
    command: list[str]
    cwd: Path
    env: dict[str, str]
    dry_run: bool
    expected_outputs: list[Path]
    readiness: SimLingoReadiness
    live_blockers: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "cwd": str(self.cwd),
            "env": self.env,
            "dry_run": self.dry_run,
            "expected_outputs": [str(path) for path in self.expected_outputs],
            "readiness": self.readiness.to_jsonable(),
            "live_blockers": self.live_blockers,
        }


REQUIRED_FILES = {
    "readme": "README.md",
    "environment": "environment.yaml",
    "agent": "team_code/agent_simlingo.py",
    "team_config": "team_code/config_simlingo.py",
    "bench2drive_evaluator": "Bench2Drive/leaderboard/leaderboard/leaderboard_evaluator.py",
    "bench2drive_scenario_runner": "Bench2Drive/scenario_runner",
    "training_package": "simlingo_training",
}


def load_simlingo_run_config(path: Path) -> SimLingoRunConfig:
    raw = read_config_mapping(path)
    simlingo = raw.get("simlingo", {})
    carla = raw.get("carla", {})
    if not isinstance(simlingo, dict):
        raise ValueError("Config field 'simlingo' must be a mapping.")
    if not isinstance(carla, dict):
        raise ValueError("Config field 'carla' must be a mapping.")
    root = _path(simlingo.get("root"), "../external/simlingo")
    carla_root = _path(carla.get("root"), "~/software/carla0915")
    checkpoint_path = _path(
        simlingo.get("checkpoint_path"),
        "outputs/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt",
    )
    route_path = _path(
        simlingo.get("route_path"),
        "leaderboard/data/bench2drive_split/bench2drive_00.xml",
    )
    output_dir = _path(simlingo.get("output_dir"), "artifacts/simlingo")
    return SimLingoRunConfig(
        simlingo_root=root,
        carla_root=carla_root,
        checkpoint_path=checkpoint_path,
        route_path=route_path,
        output_dir=output_dir,
        seed=int(simlingo.get("seed", 1)),
        world_port=int(simlingo.get("world_port", 20000)),
        traffic_manager_port=int(simlingo.get("traffic_manager_port", 10000)),
        timeout_s=int(simlingo.get("timeout_s", 600)),
    )


def inspect_simlingo_checkout(root: Path) -> SimLingoReadiness:
    resolved = root.expanduser().resolve()
    exists = resolved.exists() and resolved.is_dir()
    required = {
        label: (resolved / relative).exists()
        for label, relative in REQUIRED_FILES.items()
    }
    blockers: list[str] = []
    if not exists:
        blockers.append(f"SimLingo checkout not found: {resolved}")
    for label, present in required.items():
        if not present:
            blockers.append(f"Missing SimLingo required file: {REQUIRED_FILES[label]}")
    commit = _git_commit(resolved) if exists else None
    return SimLingoReadiness(
        root=resolved,
        exists=exists,
        commit=commit,
        required_files=required,
        carla_version="0.9.15",
        python_version="3.8",
        requires_cuda=True,
        apple_silicon_live_supported=False,
        blockers=blockers,
    )


def plan_simlingo_run(config: SimLingoRunConfig) -> SimLingoCommandPlan:
    root = config.simlingo_root.expanduser().resolve()
    readiness = inspect_simlingo_checkout(root)
    route_path = _resolve_under(root, config.route_path)
    checkpoint_path = _resolve_under(root, config.checkpoint_path)
    output_dir = config.output_dir.expanduser().resolve()
    result_file = output_dir / "res" / f"seed_{config.seed}_res.json"
    viz_path = output_dir / "viz"
    env = {
        "CARLA_ROOT": str(config.carla_root.expanduser().resolve()),
        "WORK_DIR": str(root),
        "PYTHONPATH": _pythonpath(root, config.carla_root.expanduser().resolve()),
        "SCENARIO_RUNNER_ROOT": str(root / "Bench2Drive" / "scenario_runner"),
        "LEADERBOARD_ROOT": str(root / "Bench2Drive" / "leaderboard"),
        "SAVE_PATH": str(viz_path),
    }
    command = [
        "python",
        str(root / "Bench2Drive" / "leaderboard" / "leaderboard" / "leaderboard_evaluator.py"),
        f"--routes={route_path}",
        "--repetitions=1",
        "--track=SENSORS",
        f"--checkpoint={result_file}",
        f"--timeout={config.timeout_s}",
        f"--agent={root / 'team_code' / 'agent_simlingo.py'}",
        f"--agent-config={checkpoint_path}",
        f"--traffic-manager-seed={config.seed}",
        f"--port={config.world_port}",
        f"--traffic-manager-port={config.traffic_manager_port}",
    ]
    return SimLingoCommandPlan(
        command=command,
        cwd=root,
        env=env,
        dry_run=True,
        expected_outputs=[result_file, viz_path],
        readiness=readiness,
        live_blockers=_live_blockers(
            readiness=readiness,
            carla_root=config.carla_root.expanduser().resolve(),
            checkpoint_path=checkpoint_path,
            route_path=route_path,
        ),
    )


def write_simlingo_readiness(run_dir: Path, readiness: SimLingoReadiness) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "simlingo_readiness.json"
    report_path = run_dir / "simlingo_readiness.md"
    payload = readiness.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_readiness_markdown(readiness), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def write_simlingo_plan(run_dir: Path, plan: SimLingoCommandPlan) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "simlingo_command_plan.json"
    report_path = run_dir / "simlingo_command_plan.md"
    payload = plan.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_plan_markdown(plan), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _path(value: Any, default: str) -> Path:
    raw = value if value not in (None, "") else default
    return Path(str(raw)).expanduser()


def _resolve_under(root: Path, path: Path) -> Path:
    return path.expanduser().resolve() if path.is_absolute() else (root / path).resolve()


def _pythonpath(root: Path, carla_root: Path) -> str:
    return ":".join(
        [
            str(root),
            str(carla_root / "PythonAPI"),
            str(carla_root / "PythonAPI" / "carla"),
            str(carla_root / "PythonAPI" / "carla" / "dist" / "carla-0.9.15-py3.8-linux-x86_64.egg"),
            str(root / "Bench2Drive" / "scenario_runner"),
            str(root / "Bench2Drive" / "leaderboard"),
        ]
    )


def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _live_blockers(
    *,
    readiness: SimLingoReadiness,
    carla_root: Path,
    checkpoint_path: Path,
    route_path: Path,
) -> list[str]:
    blockers = list(readiness.blockers)
    if not carla_root.exists():
        blockers.append(f"CARLA 0.9.15 root not found: {carla_root}")
    if not checkpoint_path.exists():
        blockers.append(f"SimLingo checkpoint not found: {checkpoint_path}")
    if not route_path.exists():
        blockers.append(f"Bench2Drive route not found: {route_path}")
    blockers.append("Live SimLingo inference requires Linux NVIDIA CUDA; Apple Silicon is planning/smoke only.")
    return blockers


def _readiness_markdown(readiness: SimLingoReadiness) -> str:
    lines = [
        "# SimLingo Readiness",
        "",
        f"- root: `{readiness.root}`",
        f"- exists: `{readiness.exists}`",
        f"- commit: `{readiness.commit}`",
        f"- CARLA version: `{readiness.carla_version}`",
        f"- Python version: `{readiness.python_version}`",
        f"- requires CUDA: `{readiness.requires_cuda}`",
        f"- Apple Silicon live supported: `{readiness.apple_silicon_live_supported}`",
        "",
        "## Required Files",
        "",
    ]
    for label, present in readiness.required_files.items():
        lines.append(f"- `{label}`: `{present}`")
    lines.extend(["", "## Blockers", ""])
    if readiness.blockers:
        lines.extend(f"- {blocker}" for blocker in readiness.blockers)
    else:
        lines.append("- None for dry-run planning. Live execution still needs Linux NVIDIA, CARLA 0.9.15, and a checkpoint.")
    lines.append("")
    return "\n".join(lines)


def _plan_markdown(plan: SimLingoCommandPlan) -> str:
    lines = [
        "# SimLingo Command Plan",
        "",
        f"- cwd: `{plan.cwd}`",
        f"- dry_run: `{plan.dry_run}`",
        f"- readiness_blockers: `{len(plan.readiness.blockers)}`",
        f"- live_blockers: `{len(plan.live_blockers)}`",
        "",
        "## Command",
        "",
        "```bash",
        " ".join(plan.command),
        "```",
        "",
        "## Environment",
        "",
    ]
    for key, value in plan.env.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Expected Outputs", ""])
    lines.extend(f"- `{path}`" for path in plan.expected_outputs)
    lines.extend(["", "## Live Blockers", ""])
    lines.extend(f"- {blocker}" for blocker in plan.live_blockers)
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "SimLingoCommandPlan",
    "SimLingoReadiness",
    "SimLingoRunConfig",
    "inspect_simlingo_checkout",
    "load_simlingo_run_config",
    "plan_simlingo_run",
    "write_simlingo_plan",
    "write_simlingo_readiness",
]
