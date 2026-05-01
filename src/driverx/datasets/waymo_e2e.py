"""Optional Waymo E2E loader placeholder.

The fixture pipeline is the default v1 path. This module preserves the seam for
real Waymo TFRecords without forcing TensorFlow/Waymo dependencies on local QA.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from driverx.core.config import DatasetConfig
from driverx.core.types import CameraImage, FrameBundle, RgbColor


def load_waymo_frame(config: DatasetConfig) -> FrameBundle:
    if config.path is None:
        raise FileNotFoundError(
            "Waymo dataset path is required for dataset.kind=waymo. "
            "Set dataset.path in config or use ${WAYMO_E2E_DATASET}."
        )
    if not config.path.exists():
        raise FileNotFoundError(f"Waymo dataset path does not exist: {config.path}")
    if config.path.suffix.lower() == ".json":
        return _load_waymo_json_fixture(config.path)
    raise NotImplementedError(
        "Real Waymo TFRecord parsing requires TensorFlow and waymo-open-dataset. "
        "For local v1 QA, use a Waymo E2E-shaped JSON fixture or dataset.kind=fixture."
    )


def _gradient_image(name: str, width: int, height: int, tint: RgbColor) -> CameraImage:
    pixels: list[list[RgbColor]] = []
    for y in range(height):
        row: list[RgbColor] = []
        for x in range(width):
            row.append(
                (
                    min(255, tint[0] + int(24 * x / max(width - 1, 1))),
                    min(255, tint[1] + int(36 * y / max(height - 1, 1))),
                    min(255, tint[2] + int(18 * x / max(width - 1, 1))),
                )
            )
        pixels.append(row)
    return CameraImage(name=name, width=width, height=height, pixels=pixels)


def _points(raw: list[list[float]]) -> list[tuple[float, float]]:
    return [(float(point[0]), float(point[1])) for point in raw]


def _load_waymo_json_fixture(path: Path) -> FrameBundle:
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    image_specs = raw.get("front_images", [])
    if not isinstance(image_specs, list) or not image_specs:
        raise ValueError("Waymo JSON fixture requires front_images.")
    images: list[CameraImage] = []
    for spec in image_specs:
        tint = cast(
            RgbColor,
            tuple(int(value) for value in spec.get("tint", [80, 80, 80])),
        )
        images.append(
            _gradient_image(
                name=str(spec["name"]),
                width=int(spec.get("width", 96)),
                height=int(spec.get("height", 54)),
                tint=tint,
            )
        )
    return FrameBundle(
        frame_name=str(raw["frame_name"]),
        front_images=images,
        ego_history_xy=_points(raw["ego_history_xy"]),
        future_xy=_points(raw["future_xy"]) if raw.get("future_xy") is not None else None,
        metadata=dict(raw.get("metadata", {})),
    )
