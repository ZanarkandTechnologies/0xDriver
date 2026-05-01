"""Candidate ranking."""

from __future__ import annotations

from driverx.core.types import FrameBundle, TrajectoryCandidate
from driverx.planning.safety import obstacle_cost, smoothness_cost


def rank_candidates(
    frame: FrameBundle,
    candidates: list[TrajectoryCandidate],
) -> TrajectoryCandidate:
    if not candidates:
        raise ValueError("At least one candidate is required for ranking.")

    objects = list(frame.metadata.get("objects", []))
    ranked: list[TrajectoryCandidate] = []
    for candidate in candidates:
        cost = candidate.score
        cost += obstacle_cost(candidate, objects)
        cost += smoothness_cost(candidate) * 0.15
        if "fallback" in candidate.source:
            cost += 0.35
        ranked.append(
            TrajectoryCandidate(
                points_xy=candidate.points_xy,
                source=candidate.source,
                score=round(cost, 6),
                metadata={**candidate.metadata, "rank_cost": round(cost, 6)},
            )
        )
    return min(ranked, key=lambda item: item.score)
