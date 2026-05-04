"""Typed OOD behavior traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BehaviorPlan:
    behavior_id: str
    actor_kind: str
    duration_s: float = 6.0
    dt_s: float = 0.25
    parameters: dict[str, float | str | bool] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    expected_pressure: str = ""

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "behavior_id": self.behavior_id,
            "actor_kind": self.actor_kind,
            "duration_s": self.duration_s,
            "dt_s": self.dt_s,
            "parameters": self.parameters,
            "tags": self.tags,
            "expected_pressure": self.expected_pressure,
        }


@dataclass(frozen=True)
class BehaviorSample:
    t_s: float
    x_m: float
    y_m: float
    speed_mps: float
    heading_deg: float

    def to_jsonable(self) -> dict[str, float]:
        return {
            "t_s": self.t_s,
            "x_m": self.x_m,
            "y_m": self.y_m,
            "speed_mps": self.speed_mps,
            "heading_deg": self.heading_deg,
        }


@dataclass(frozen=True)
class BehaviorTrace:
    plan: BehaviorPlan
    samples: list[BehaviorSample]
    metrics: dict[str, float]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_jsonable(),
            "samples": [sample.to_jsonable() for sample in self.samples],
            "metrics": self.metrics,
        }
