"""Typed scenario records for CARLA/Fail2Drive generalization work."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ScenarioSplit = Literal["Base", "Generalization", "Generated"]
ScenarioSource = Literal["fixture", "fail2drive", "generated"]


def _string_list(values: list[Any]) -> list[str]:
    return [str(value) for value in values if str(value)]


@dataclass(frozen=True)
class ScenarioSeed:
    seed_id: str
    source: ScenarioSource
    split: ScenarioSplit
    scenario_class: str
    route_id: str
    route_path: Path | None = None
    ood_tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.seed_id:
            raise ValueError("ScenarioSeed seed_id is required.")
        if not self.scenario_class:
            raise ValueError("ScenarioSeed scenario_class is required.")
        if not self.route_id:
            raise ValueError("ScenarioSeed route_id is required.")

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "seed_id": self.seed_id,
            "source": self.source,
            "split": self.split,
            "scenario_class": self.scenario_class,
            "route_id": self.route_id,
            "route_path": str(self.route_path) if self.route_path else None,
            "ood_tags": self.ood_tags,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "ScenarioSeed":
        route_path = payload.get("route_path")
        return cls(
            seed_id=str(payload["seed_id"]),
            source=str(payload.get("source", "fixture")),  # type: ignore[arg-type]
            split=str(payload["split"]),  # type: ignore[arg-type]
            scenario_class=str(payload["scenario_class"]),
            route_id=str(payload["route_id"]),
            route_path=Path(route_path) if route_path else None,
            ood_tags=_string_list(list(payload.get("ood_tags", []))),
        )


@dataclass(frozen=True)
class MutationPolicy:
    mutations: tuple[str, ...] = (
        "obstacle_substitution",
        "occlusion",
        "visual_noise",
        "lane_blockage",
        "regional_driving_behavior",
    )

    def __post_init__(self) -> None:
        if not self.mutations:
            raise ValueError("MutationPolicy requires at least one mutation.")


@dataclass(frozen=True)
class ScenarioRecipe:
    recipe_id: str
    parent_seed_id: str
    mutation: str
    actors: list[dict[str, Any]]
    environment: dict[str, Any]
    expected_failure_mode: str
    memory_query: list[str]
    solvability_assumption: str = "Privileged expert can complete route by slowing, yielding, or rerouting locally."
    route_path: Path | None = None

    def __post_init__(self) -> None:
        if not self.recipe_id:
            raise ValueError("ScenarioRecipe recipe_id is required.")
        if not self.parent_seed_id:
            raise ValueError("ScenarioRecipe parent_seed_id is required.")
        if not self.mutation:
            raise ValueError("ScenarioRecipe mutation is required.")
        if not self.expected_failure_mode:
            raise ValueError("ScenarioRecipe expected_failure_mode is required.")

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "parent_seed_id": self.parent_seed_id,
            "mutation": self.mutation,
            "actors": self.actors,
            "environment": self.environment,
            "expected_failure_mode": self.expected_failure_mode,
            "memory_query": self.memory_query,
            "solvability_assumption": self.solvability_assumption,
            "route_path": str(self.route_path) if self.route_path else None,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "ScenarioRecipe":
        route_path = payload.get("route_path")
        return cls(
            recipe_id=str(payload["recipe_id"]),
            parent_seed_id=str(payload["parent_seed_id"]),
            mutation=str(payload["mutation"]),
            actors=list(payload.get("actors", [])),
            environment=dict(payload.get("environment", {})),
            expected_failure_mode=str(payload["expected_failure_mode"]),
            memory_query=_string_list(list(payload.get("memory_query", []))),
            solvability_assumption=str(
                payload.get(
                    "solvability_assumption",
                    "Privileged expert can complete route by slowing, yielding, or rerouting locally.",
                )
            ),
            route_path=Path(route_path) if route_path else None,
        )


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    policy: str
    success: bool
    driving_score: float | None = None
    route_completion: float | None = None
    infractions: dict[str, list[str]] = field(default_factory=dict)
    failure_summary: str | None = None
    latency_ms: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("ScenarioResult scenario_id is required.")
        if not self.policy:
            raise ValueError("ScenarioResult policy is required.")

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "policy": self.policy,
            "success": self.success,
            "driving_score": self.driving_score,
            "route_completion": self.route_completion,
            "infractions": self.infractions,
            "failure_summary": self.failure_summary,
            "latency_ms": self.latency_ms,
            "tags": self.tags,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "ScenarioResult":
        return cls(
            scenario_id=str(payload["scenario_id"]),
            policy=str(payload.get("policy", "unknown_policy")),
            success=bool(payload.get("success", False)),
            driving_score=(
                float(payload["driving_score"])
                if payload.get("driving_score") is not None
                else None
            ),
            route_completion=(
                float(payload["route_completion"])
                if payload.get("route_completion") is not None
                else None
            ),
            infractions={
                str(key): _string_list(list(value))
                for key, value in dict(payload.get("infractions", {})).items()
            },
            failure_summary=(
                str(payload["failure_summary"])
                if payload.get("failure_summary") is not None
                else None
            ),
            latency_ms={
                str(key): float(value)
                for key, value in dict(payload.get("latency_ms", {})).items()
            },
            tags=_string_list(list(payload.get("tags", []))),
        )
