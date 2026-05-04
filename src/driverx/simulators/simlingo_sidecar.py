"""Dry-run orchestration for stock SimLingo plus DriverX overlay injection."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SidecarCommandEntry:
    label: str
    command: list[str]
    cwd: Path
    env: dict[str, str]
    start_after_s: float
    expected_outputs: list[Path] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "command": self.command,
            "cwd": str(self.cwd),
            "env": self.env,
            "start_after_s": self.start_after_s,
            "expected_outputs": [str(path) for path in self.expected_outputs],
            "notes": self.notes,
        }


@dataclass(frozen=True)
class SimLingoSidecarPlan:
    simlingo_plan_path: Path
    overlay_plan_path: Path
    dry_run: bool
    launch_mode: str
    route_count: int
    commands: list[SidecarCommandEntry]
    blockers: list[str]
    expected_outputs: list[Path]
    notes: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "simlingo_plan_path": str(self.simlingo_plan_path),
            "overlay_plan_path": str(self.overlay_plan_path),
            "dry_run": self.dry_run,
            "launch_mode": self.launch_mode,
            "route_count": self.route_count,
            "commands": [command.to_jsonable() for command in self.commands],
            "blockers": self.blockers,
            "expected_outputs": [str(path) for path in self.expected_outputs],
            "notes": self.notes,
        }


def build_simlingo_sidecar_plan(
    *,
    simlingo_plan_path: Path,
    overlay_plan_path: Path,
    output_dir: Path,
    carla_config_path: Path,
    tick_limit: int | None = None,
    overlay_start_delay_s: float = 5.0,
    use_docker_carla_client: bool = False,
) -> SimLingoSidecarPlan:
    simlingo_file = simlingo_plan_path.expanduser().resolve()
    overlay_file = overlay_plan_path.expanduser().resolve()
    simlingo = json.loads(simlingo_file.read_text(encoding="utf-8"))
    overlay = json.loads(overlay_file.read_text(encoding="utf-8"))
    output_dir = output_dir.expanduser().resolve()
    route_count = int(overlay.get("num_routes", len(list(overlay.get("routes", [])))))
    overlay_run_dir = output_dir / "overlay-injection-run"
    commands = [
        SidecarCommandEntry(
            label="simlingo_bench2drive",
            command=[str(item) for item in list(simlingo.get("command", []))],
            cwd=Path(str(simlingo.get("cwd", "."))).expanduser(),
            env={str(key): str(value) for key, value in dict(simlingo.get("env", {})).items()},
            start_after_s=0.0,
            expected_outputs=[
                Path(str(path)).expanduser()
                for path in list(simlingo.get("expected_outputs", []))
            ],
            notes=[
                "Launches stock SimLingo/Bench2Drive. It owns ego control and benchmark route lifecycle.",
            ],
        ),
        SidecarCommandEntry(
            label="driverx_overlay_injector",
            command=_overlay_command(
                overlay_plan_path=overlay_file,
                carla_config_path=carla_config_path,
                output_root=overlay_run_dir,
                tick_limit=tick_limit,
                use_docker_carla_client=use_docker_carla_client,
            ),
            cwd=Path.cwd(),
            env={"PYTHONPATH": "src"},
            start_after_s=overlay_start_delay_s,
            expected_outputs=[
                overlay_run_dir / "overlay-injection-run" / "overlay_injection_run.json",
                overlay_run_dir / "overlay-injection-run" / "entity_tracks.json",
            ],
            notes=[
                "Runs DriverX companion actors only; it must not spawn ego or stock route actors.",
                "Start delay is a coarse launch offset until live route lifecycle hooks exist.",
            ],
        ),
    ]
    return SimLingoSidecarPlan(
        simlingo_plan_path=simlingo_file,
        overlay_plan_path=overlay_file,
        dry_run=True,
        launch_mode="manual_two_process_sidecar",
        route_count=route_count,
        commands=commands,
        blockers=_sidecar_blockers(simlingo, overlay, route_count),
        expected_outputs=[
            path
            for command in commands
            for path in command.expected_outputs
        ],
        notes=[
            "This artifact is a launch plan, not a live process supervisor.",
            "Use it on the same machine/CARLA server that runs SimLingo.",
            "For stock SimLingo today, prefer an H100/H200 host; RTX PRO 6000 Blackwell needs a rebuild lane.",
        ],
    )


def write_simlingo_sidecar_plan(run_dir: Path, plan: SimLingoSidecarPlan) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "simlingo_sidecar_plan.json"
    report_path = run_dir / "simlingo_sidecar_plan.md"
    payload = plan.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_sidecar_markdown(plan), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _overlay_command(
    *,
    overlay_plan_path: Path,
    carla_config_path: Path,
    output_root: Path,
    tick_limit: int | None,
    use_docker_carla_client: bool,
) -> list[str]:
    base = [
        "python",
        "-m",
        "driverx",
        "run-overlay-injection",
        "--config",
        str(carla_config_path),
        "--plan",
        str(overlay_plan_path),
        "--output-root",
        str(output_root),
        "--run-id",
        "overlay-injection-run",
    ]
    if tick_limit is not None:
        base.extend(["--tick-limit", str(tick_limit)])
    if not use_docker_carla_client:
        return base
    return ["bash", "scripts/run_carla_client_docker.sh", *base]


def _sidecar_blockers(
    simlingo: dict[str, Any],
    overlay: dict[str, Any],
    route_count: int,
) -> list[str]:
    blockers = [str(blocker) for blocker in list(simlingo.get("live_blockers", []))]
    overlay_errors = [str(error) for error in list(overlay.get("validation_errors", []))]
    blockers.extend(f"Overlay plan validation error: {error}" for error in overlay_errors)
    if route_count <= 0:
        blockers.append("Overlay plan contains no routes.")
    if not simlingo.get("command"):
        blockers.append("SimLingo plan contains no command.")
    return blockers


def _sidecar_markdown(plan: SimLingoSidecarPlan) -> str:
    lines = [
        "# SimLingo Sidecar Plan",
        "",
        f"- dry_run: `{plan.dry_run}`",
        f"- launch_mode: `{plan.launch_mode}`",
        f"- route_count: `{plan.route_count}`",
        f"- blockers: `{len(plan.blockers)}`",
        f"- simlingo_plan_path: `{plan.simlingo_plan_path}`",
        f"- overlay_plan_path: `{plan.overlay_plan_path}`",
        "",
        "## Commands",
        "",
    ]
    for command in plan.commands:
        lines.extend(
            [
                f"### {command.label}",
                "",
                f"- cwd: `{command.cwd}`",
                f"- start_after_s: `{command.start_after_s}`",
                "",
                "```bash",
                " ".join(command.command),
                "```",
                "",
            ]
        )
    lines.extend(["## Blockers", ""])
    if plan.blockers:
        lines.extend(f"- {blocker}" for blocker in plan.blockers)
    else:
        lines.append("- None recorded in the input plans.")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in plan.notes)
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "SidecarCommandEntry",
    "SimLingoSidecarPlan",
    "build_simlingo_sidecar_plan",
    "write_simlingo_sidecar_plan",
]
