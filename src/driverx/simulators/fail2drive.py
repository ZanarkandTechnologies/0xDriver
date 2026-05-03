"""Fail2Drive command planning without launching CARLA."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.scenarios.types import ScenarioRecipe
from driverx.simulators.carla import CarlaRunConfig


@dataclass(frozen=True)
class CarlaCommandPlan:
    command: list[str]
    cwd: Path
    env: dict[str, str]
    dry_run: bool
    expected_outputs: list[Path]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "cwd": str(self.cwd),
            "env": self.env,
            "dry_run": self.dry_run,
            "expected_outputs": [str(path) for path in self.expected_outputs],
        }


def _resolve_under(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _require_existing_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    if not path.is_file():
        raise ValueError(f"{label} must be a file: {path}")


def plan_fail2drive_run(
    config: CarlaRunConfig,
    recipe: ScenarioRecipe,
) -> CarlaCommandPlan:
    root = config.fail2drive_root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Fail2Drive checkout not found: {root}")
    if not root.is_dir():
        raise ValueError(f"Fail2Drive root must be a directory: {root}")
    if recipe.route_path is None:
        raise ValueError(
            "ScenarioRecipe.route_path is required for Fail2Drive planning; "
            "generate recipes from seeds with route_path or pass a single explicit route-backed recipe."
        )
    route_path = _resolve_under(root, recipe.route_path).resolve()
    agent_path = _resolve_under(root, config.agent_path)
    output_dir = config.output_dir.resolve() / recipe.recipe_id
    evaluator = root / "leaderboard" / "leaderboard" / "leaderboard_evaluator_local.py"
    _require_existing_file(evaluator, "Fail2Drive evaluator")
    _require_existing_file(agent_path, "Fail2Drive agent")
    _require_existing_file(route_path, "Fail2Drive route")
    command = [
        "python",
        str(evaluator),
        "--agent",
        str(agent_path),
        "--track",
        config.track,
        "--routes",
        str(route_path),
        "--checkpoint",
        str(output_dir),
    ]
    env = {
        "CARLA_HOST": config.host,
        "CARLA_PORT": str(config.port),
        "FAIL2DRIVE_ROOT": str(root),
    }
    if config.carla_root is not None:
        env["CARLA_ROOT"] = str(config.carla_root.resolve())
    return CarlaCommandPlan(
        command=command,
        cwd=root,
        env=env,
        dry_run=True,
        expected_outputs=[output_dir, output_dir / "res"],
    )
