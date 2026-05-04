"""Typed policy adapter contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from driverx.core.types import DrivingIntent, FrameBundle, TrajectoryCandidate
from driverx.memory import MemoryEntry
from driverx.scenarios import ScenarioRecipe


@dataclass(frozen=True)
class PolicyContext:
    frame: FrameBundle
    recipe: ScenarioRecipe | None = None
    memories: list[MemoryEntry] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def memory_ids(self) -> list[str]:
        return [memory.entry_id for memory in self.memories]


@dataclass(frozen=True)
class PolicyAction:
    mode: str
    trajectory: TrajectoryCandidate | None
    control: dict[str, float | str | bool]
    safety_notes: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "trajectory": (
                {
                    "points_xy": self.trajectory.points_xy,
                    "source": self.trajectory.source,
                    "score": self.trajectory.score,
                    "metadata": self.trajectory.metadata,
                }
                if self.trajectory is not None
                else None
            ),
            "control": self.control,
            "safety_notes": self.safety_notes,
        }


@dataclass(frozen=True)
class PolicyDecision:
    policy_id: str
    adapter_kind: str
    intent: DrivingIntent
    action: PolicyAction
    latency_ms: float
    reason_summary: str
    retrieved_memory_ids: list[str] = field(default_factory=list)
    setup_blocker: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "adapter_kind": self.adapter_kind,
            "intent": {
                "scene_type": self.intent.scene_type,
                "hazards": self.intent.hazards,
                "ego_intent": self.intent.ego_intent,
                "target_behavior": self.intent.target_behavior,
                "speed_profile": self.intent.speed_profile,
                "lateral_bias": self.intent.lateral_bias,
                "uncertainty": self.intent.uncertainty,
            },
            "action": self.action.to_jsonable(),
            "latency_ms": self.latency_ms,
            "reason_summary": self.reason_summary,
            "retrieved_memory_ids": self.retrieved_memory_ids,
            "setup_blocker": self.setup_blocker,
        }


class PolicyAdapter(Protocol):
    policy_id: str

    def decide(self, context: PolicyContext) -> PolicyDecision:
        """Produce a structured policy decision from frame and optional memory."""


class PolicySetupError(RuntimeError):
    """Raised when a real policy adapter is selected without required setup."""

