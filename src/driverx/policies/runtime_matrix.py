"""Policy runtime readiness matrix for local, CARLA, and VLA adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any

from driverx.simulators import load_carla_run_config, load_simlingo_run_config, plan_simlingo_run


@dataclass(frozen=True)
class PolicyRuntimeRow:
    policy: str
    runtime_kind: str
    required_hardware: str
    ready_state: str
    command: list[str]
    config_path: Path | None = None
    blocker: str | None = None

    @property
    def ready(self) -> bool:
        return self.ready_state in {"ready", "dry_run_ready"}

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "policy": self.policy,
            "runtime_kind": self.runtime_kind,
            "required_hardware": self.required_hardware,
            "ready_state": self.ready_state,
            "ready": self.ready,
            "command": self.command,
            "config_path": str(self.config_path) if self.config_path else None,
            "blocker": self.blocker,
        }


def build_policy_runtime_matrix(
    run_dir: Path,
    *,
    carla_config_path: Path | None = None,
    simlingo_config_path: Path | None = None,
    suite_path: Path | None = None,
) -> dict[str, Any]:
    rows = [
        _local_policy("mock", "python -m driverx run-policy-fixture --policy mock"),
        _local_policy("mock-memory", "python -m driverx run-policy-fixture --policy mock-memory --with-memory"),
        _local_policy("hybrid", "python -m driverx run-policy-fixture --policy hybrid"),
        *_fail2drive_rows(carla_config_path, suite_path),
        _simlingo_row(simlingo_config_path, suite_path),
        _alpamayo_row(suite_path),
    ]
    payload = {
        "row_count": len(rows),
        "ready_count": sum(1 for row in rows if row.ready),
        "blocked_count": sum(1 for row in rows if row.blocker),
        "rows": [row.to_jsonable() for row in rows],
        "blockers": [
            f"{row.policy}: {row.blocker}"
            for row in rows
            if row.blocker
        ],
    }
    return write_policy_runtime_matrix(run_dir, payload)


def write_policy_runtime_matrix(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "policy_runtime_matrix.json"
    report_path = run_dir / "policy_runtime_matrix.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _local_policy(policy: str, command: str) -> PolicyRuntimeRow:
    return PolicyRuntimeRow(
        policy=policy,
        runtime_kind="local_python_policy",
        required_hardware="CPU only; no model downloads",
        ready_state="ready",
        command=command.split(),
    )


def _fail2drive_rows(
    carla_config_path: Path | None,
    suite_path: Path | None,
) -> list[PolicyRuntimeRow]:
    if carla_config_path is None:
        blocker = "Pass --carla-config to validate Fail2Drive checkout paths."
        return [
            _fail2drive_row("fail2drive-basic", None, suite_path, blocker),
            _fail2drive_row("fail2drive-expert", None, suite_path, blocker),
        ]
    try:
        config = load_carla_run_config(carla_config_path)
        root = config.fail2drive_root.expanduser().resolve()
        evaluator = root / "leaderboard" / "leaderboard" / "leaderboard_evaluator_local.py"
        agent = (root / config.agent_path).resolve() if not config.agent_path.is_absolute() else config.agent_path
        route = _suite_or_route(suite_path, root / config.route_path)
        missing = [
            label
            for label, path in [
                ("Fail2Drive evaluator", evaluator),
                ("Fail2Drive agent", agent),
                ("route or suite", route),
            ]
            if not path.exists()
        ]
        blocker = f"Missing {', '.join(missing)} for Fail2Drive dry-run planning." if missing else None
    except Exception as exc:
        blocker = str(exc)
        route = suite_path or Path("unknown-route")
    return [
        _fail2drive_row("fail2drive-basic", carla_config_path, route, blocker),
        _fail2drive_row("fail2drive-expert", carla_config_path, route, blocker),
    ]


def _fail2drive_row(
    policy: str,
    config_path: Path | None,
    route_path: Path | None,
    blocker: str | None,
) -> PolicyRuntimeRow:
    command = [
        "python",
        "-m",
        "driverx",
        "plan-fail2drive-video-smoke",
    ]
    if config_path is not None:
        command.extend(["--config", str(config_path)])
    return PolicyRuntimeRow(
        policy=policy,
        runtime_kind="carla_rule_or_expert_agent",
        required_hardware="CARLA server with graphics; no model GPU or checkpoint",
        ready_state="dry_run_ready" if blocker is None else "blocked",
        command=command,
        config_path=config_path,
        blocker=blocker,
    )


def _suite_or_route(suite_path: Path | None, fallback: Path) -> Path:
    return suite_path.expanduser() if suite_path is not None else fallback.expanduser()


def _simlingo_row(
    simlingo_config_path: Path | None,
    suite_path: Path | None,
) -> PolicyRuntimeRow:
    resolved_suite_path = suite_path.expanduser().resolve() if suite_path is not None else None
    command = ["python", "-m", "driverx", "plan-simlingo-run"]
    if simlingo_config_path is not None:
        command.extend(["--config", str(simlingo_config_path)])
    if resolved_suite_path is not None:
        command.extend(["--route-path", str(resolved_suite_path)])
    blocker = None
    ready_state = "blocked"
    if simlingo_config_path is None:
        blocker = "Pass --simlingo-config with root, checkpoint, CARLA 0.9.15, and route path."
    else:
        try:
            config = load_simlingo_run_config(simlingo_config_path)
            if resolved_suite_path is not None:
                config = replace(config, route_path=resolved_suite_path)
            plan = plan_simlingo_run(config)
            if plan.live_blockers:
                blocker = "; ".join(plan.live_blockers)
            else:
                ready_state = "dry_run_ready"
        except Exception as exc:
            blocker = str(exc)
    return PolicyRuntimeRow(
        policy="simlingo",
        runtime_kind="closed_loop_vla_bench2drive",
        required_hardware="Linux NVIDIA CUDA host plus CARLA 0.9.15 and SimLingo checkpoint",
        ready_state=ready_state,
        command=command,
        config_path=simlingo_config_path,
        blocker=blocker,
    )


def _alpamayo_row(suite_path: Path | None) -> PolicyRuntimeRow:
    command = [
        "python",
        "-m",
        "driverx",
        "probe-alpamayo",
    ]
    if suite_path is not None:
        command.extend(["--route-suite", str(suite_path)])
    return PolicyRuntimeRow(
        policy="alpamayo",
        runtime_kind="reasoning_vla_adapter",
        required_hardware="Linux NVIDIA host with Alpamayo checkpoint/runtime access; exact VRAM TBD in TASK-038",
        ready_state="blocked",
        command=command,
        blocker="Alpamayo runtime is intentionally deferred to TASK-038 offline probe.",
    )


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Policy Runtime Matrix",
        "",
        f"- rows: `{payload.get('row_count')}`",
        f"- ready_count: `{payload.get('ready_count')}`",
        f"- blocked_count: `{payload.get('blocked_count')}`",
        "",
        "| policy | runtime | ready | hardware | blocker |",
        "|---|---|---|---|---|",
    ]
    for row in list(payload.get("rows", [])):
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("policy")),
                    _cell(row.get("runtime_kind")),
                    _cell(row.get("ready_state")),
                    _cell(row.get("required_hardware")),
                    _cell(row.get("blocker")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


__all__ = [
    "PolicyRuntimeRow",
    "build_policy_runtime_matrix",
    "write_policy_runtime_matrix",
]
