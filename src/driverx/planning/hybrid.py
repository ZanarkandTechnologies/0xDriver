"""Hybrid semantic and motion-prior candidate generation."""

from __future__ import annotations

from driverx.core.types import DrivingIntent, FrameBundle, TrajectoryCandidate
from driverx.planning.baselines import generate_rule_baselines
from driverx.planning.candidates import generate_candidates


def _with_family(candidate: TrajectoryCandidate, family: str) -> TrajectoryCandidate:
    return TrajectoryCandidate(
        points_xy=candidate.points_xy,
        source=candidate.source,
        score=candidate.score,
        metadata={**candidate.metadata, "candidate_family": family},
    )


def generate_hybrid_candidates(
    frame: FrameBundle,
    intent: DrivingIntent,
) -> list[TrajectoryCandidate]:
    """Combine VLA-style intent candidates with fast ego-history priors."""

    semantic_candidates = [
        _with_family(candidate, "semantic_intent")
        for candidate in generate_candidates(frame, intent)
    ]
    motion_prior_candidates = [
        _with_family(candidate, "motion_prior")
        for candidate in generate_rule_baselines(frame)
    ]
    return [*semantic_candidates, *motion_prior_candidates]
