"""Deterministic trajectory baselines for experiment comparisons."""

from __future__ import annotations

from driverx.core.types import FrameBundle, Point, TrajectoryCandidate


def _delta(previous: Point, current: Point) -> Point:
    return current[0] - previous[0], current[1] - previous[1]


def _last_velocity(frame: FrameBundle) -> Point:
    return _delta(frame.ego_history_xy[-2], frame.ego_history_xy[-1])


def _last_acceleration(frame: FrameBundle) -> Point:
    if len(frame.ego_history_xy) < 3:
        return 0.0, 0.0
    vx0, vy0 = _delta(frame.ego_history_xy[-3], frame.ego_history_xy[-2])
    vx1, vy1 = _delta(frame.ego_history_xy[-2], frame.ego_history_xy[-1])
    return vx1 - vx0, vy1 - vy0


def _candidate(
    frame: FrameBundle,
    *,
    strategy: str,
    score: float,
    velocity_scale: float,
    acceleration_scale: float = 0.0,
    decay: float | None = None,
) -> TrajectoryCandidate:
    vx, vy = _last_velocity(frame)
    ax, ay = _last_acceleration(frame)
    x, y = frame.ego_history_xy[-1]
    points: list[Point] = []
    for step in range(20):
        progress = step / 19.0
        if decay is None:
            step_scale = velocity_scale
        else:
            step_scale = velocity_scale * max(0.0, 1.0 - progress * decay)
        vx_step = vx * step_scale + ax * acceleration_scale * progress
        vy_step = vy * step_scale + ay * acceleration_scale * progress
        x += vx_step
        y += vy_step
        points.append((round(x, 4), round(y, 4)))
    return TrajectoryCandidate(
        points_xy=points,
        source=strategy,
        score=score,
        metadata={
            "strategy": strategy,
            "velocity_scale": velocity_scale,
            "acceleration_scale": acceleration_scale,
            "decay": decay,
            "baseline": True,
        },
    )


def generate_rule_baselines(frame: FrameBundle) -> list[TrajectoryCandidate]:
    """Generate simple non-VLA candidate trajectories from ego history."""

    return [
        _candidate(
            frame,
            strategy="constant_velocity",
            score=0.25,
            velocity_scale=1.0,
        ),
        _candidate(
            frame,
            strategy="constant_acceleration",
            score=0.30,
            velocity_scale=1.0,
            acceleration_scale=1.0,
        ),
        _candidate(
            frame,
            strategy="cautious_stop",
            score=0.55,
            velocity_scale=0.85,
            decay=1.0,
        ),
    ]
