"""Synthetic fixture scenes for local, dependency-free runs."""

from __future__ import annotations

from driverx.core.types import CameraImage, FrameBundle, RgbColor


def _gradient_image(name: str, width: int, height: int, tint: RgbColor) -> CameraImage:
    pixels: list[list[RgbColor]] = []
    for y in range(height):
        row: list[RgbColor] = []
        for x in range(width):
            horizon = int(80 + 40 * (y / max(height - 1, 1)))
            lane = int(30 * (x / max(width - 1, 1)))
            row.append(
                (
                    min(255, tint[0] + lane),
                    min(255, tint[1] + horizon),
                    min(255, tint[2] + lane // 2),
                )
            )
        pixels.append(row)
    return CameraImage(name=name, width=width, height=height, pixels=pixels)


def _construction_merge() -> FrameBundle:
    ego_history = [
        (-4.0, 0.00),
        (-3.0, 0.00),
        (-2.0, 0.00),
        (-1.0, 0.00),
        (0.0, 0.00),
    ]
    future = [
        (0.85, -0.01),
        (1.65, -0.02),
        (2.38, -0.04),
        (3.05, -0.07),
        (3.67, -0.11),
        (4.25, -0.17),
        (4.80, -0.24),
        (5.34, -0.32),
        (5.88, -0.40),
        (6.43, -0.48),
        (7.00, -0.55),
        (7.60, -0.61),
        (8.24, -0.65),
        (8.92, -0.68),
        (9.64, -0.70),
        (10.40, -0.70),
        (11.20, -0.69),
        (12.04, -0.67),
        (12.92, -0.64),
        (13.84, -0.60),
    ]
    return FrameBundle(
        frame_name="fixture_construction_merge_001",
        front_images=[
            _gradient_image("front_left", 96, 54, (70, 80, 92)),
            _gradient_image("front", 96, 54, (82, 78, 86)),
            _gradient_image("front_right", 96, 54, (88, 76, 74)),
        ],
        ego_history_xy=ego_history,
        future_xy=future,
        metadata={
            "scenario": "construction_merge",
            "route": "continue_through_work_zone",
            "objects": [
                {"kind": "cone", "x": 5.3, "y": 0.65},
                {"kind": "cone", "x": 7.1, "y": 0.62},
                {"kind": "stopped_vehicle", "x": 9.0, "y": 0.35},
                {"kind": "occlusion", "x": 4.6, "y": -1.35},
            ],
            "hazards": [
                "construction cones narrowing the lane",
                "stopped service vehicle near lane center",
                "pedestrian occlusion near the right shoulder",
            ],
            "expected_behavior": "slow left-biased pass through work zone",
        },
    )


def _straight_clear() -> FrameBundle:
    ego_history = [(-4.0, 0.0), (-3.0, 0.0), (-2.0, 0.0), (-1.0, 0.0), (0.0, 0.0)]
    future = [(float(i + 1), 0.0) for i in range(20)]
    return FrameBundle(
        frame_name="fixture_straight_clear_001",
        front_images=[
            _gradient_image("front_left", 96, 54, (72, 92, 102)),
            _gradient_image("front", 96, 54, (76, 90, 98)),
            _gradient_image("front_right", 96, 54, (72, 86, 94)),
        ],
        ego_history_xy=ego_history,
        future_xy=future,
        metadata={
            "scenario": "straight_clear",
            "route": "continue_in_lane",
            "objects": [],
            "hazards": [],
            "expected_behavior": "continue steadily",
        },
    )


def load_fixture_frame(name: str) -> FrameBundle:
    fixtures = {
        "construction_merge": _construction_merge,
        "straight_clear": _straight_clear,
    }
    if name not in fixtures:
        valid = ", ".join(sorted(fixtures))
        raise ValueError(f"Unknown fixture '{name}'. Valid fixtures: {valid}")
    return fixtures[name]()
