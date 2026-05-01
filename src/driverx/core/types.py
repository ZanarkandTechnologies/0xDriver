"""Canonical typed data crossing 0xDriver module boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Point = tuple[float, float]
RgbColor = tuple[int, int, int]
TrajectoryPoints = list[Point]


@dataclass(frozen=True)
class CameraImage:
    """A lightweight RGB image used by fixture and visualization paths."""

    name: str
    width: int
    height: int
    pixels: list[list[RgbColor]]

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("CameraImage width and height must be positive.")
        if len(self.pixels) != self.height:
            raise ValueError("CameraImage pixel rows must match height.")
        for row in self.pixels:
            if len(row) != self.width:
                raise ValueError("CameraImage pixel columns must match width.")


@dataclass(frozen=True)
class FrameBundle:
    frame_name: str
    front_images: list[CameraImage]
    ego_history_xy: TrajectoryPoints
    future_xy: TrajectoryPoints | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.frame_name:
            raise ValueError("FrameBundle frame_name is required.")
        if not self.front_images:
            raise ValueError("FrameBundle must include at least one front image.")
        if len(self.ego_history_xy) < 2:
            raise ValueError("FrameBundle requires at least two ego history points.")
        if self.future_xy is not None and len(self.future_xy) != 20:
            raise ValueError("Waymo E2E future_xy must contain exactly 20 points.")


@dataclass(frozen=True)
class DrivingIntent:
    scene_type: str
    hazards: list[str]
    ego_intent: str
    target_behavior: str
    speed_profile: str
    lateral_bias: Literal["left", "center", "right"]
    uncertainty: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("DrivingIntent uncertainty must be between 0 and 1.")
        required = [
            self.scene_type,
            self.ego_intent,
            self.target_behavior,
            self.speed_profile,
            self.lateral_bias,
        ]
        if any(not value for value in required):
            raise ValueError("DrivingIntent fields must be non-empty.")


@dataclass(frozen=True)
class TrajectoryCandidate:
    points_xy: TrajectoryPoints
    source: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.points_xy) != 20:
            raise ValueError("TrajectoryCandidate must contain exactly 20 points.")


@dataclass(frozen=True)
class ArtifactRef:
    name: str
    path: Path
    kind: str

    def to_jsonable(self) -> dict[str, str]:
        return {
            "name": self.name,
            "path": str(self.path),
            "kind": self.kind,
        }


@dataclass(frozen=True)
class SceneRunResult:
    frame_name: str
    run_dir: Path
    intent: DrivingIntent | None
    selected_trajectory: TrajectoryCandidate | None
    metrics: dict[str, Any]
    timings_ms: dict[str, float]
    artifacts: list[ArtifactRef]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "frame_name": self.frame_name,
            "run_dir": str(self.run_dir),
            "intent": self.intent.__dict__ if self.intent is not None else None,
            "selected_trajectory": (
                {
                    "points_xy": self.selected_trajectory.points_xy,
                    "source": self.selected_trajectory.source,
                    "score": self.selected_trajectory.score,
                    "metadata": self.selected_trajectory.metadata,
                }
                if self.selected_trajectory is not None
                else None
            ),
            "metrics": self.metrics,
            "timings_ms": self.timings_ms,
            "artifacts": [artifact.to_jsonable() for artifact in self.artifacts],
        }
