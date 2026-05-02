"""Optional Waymo E2E loaders.

The fixture pipeline remains the default path. Real TFRecord support lives here
behind lazy imports so local QA does not need TensorFlow or Waymo packages.
"""

from __future__ import annotations

import glob
import importlib
import json
from pathlib import Path
from typing import Any, Iterator, cast

from driverx.core.config import DatasetConfig
from driverx.core.types import CameraImage, FrameBundle, RgbColor
from driverx.waymo_runtime import WAYMO_RUNTIME_HINT

FRONT_CAMERA_ORDER = [2, 1, 3]
FRONT_CAMERA_NAMES = {
    1: "front",
    2: "front_left",
    3: "front_right",
}


class WaymoDependencyError(ImportError):
    """Raised when official Waymo parsing is requested without optional deps."""


def load_waymo_frame(config: DatasetConfig) -> FrameBundle:
    if config.path is None:
        raise FileNotFoundError(
            "Waymo dataset path is required for dataset.kind=waymo. "
            "Set dataset.path in config or use ${WAYMO_E2E_TFRECORD}."
        )
    path_text = str(config.path)
    has_glob = any(char in path_text for char in "*?[]")
    if not has_glob and not config.path.exists():
        raise FileNotFoundError(f"Waymo dataset path does not exist: {config.path}")
    if not has_glob and config.path.suffix.lower() == ".json":
        return _load_waymo_json_fixture(config.path)
    return load_waymo_tfrecord_frame(config)


def load_waymo_tfrecord_frame(config: DatasetConfig) -> FrameBundle:
    """Load one Waymo E2E frame from a TFRecord file, directory, or glob."""

    return next(iter_waymo_frames(config, start_index=config.frame_index, count=1))


def iter_waymo_frames(
    config: DatasetConfig,
    start_index: int,
    count: int,
) -> Iterator[FrameBundle]:
    """Stream a contiguous Waymo E2E frame range once."""

    if config.path is None:
        raise FileNotFoundError("Waymo TFRecord path is required.")
    if start_index < 0:
        raise ValueError("start_index must be non-negative.")
    if count < 0:
        raise ValueError("count must be non-negative.")
    if count == 0:
        return
    if config.limit is not None and start_index >= config.limit:
        raise ValueError("start_index must be smaller than dataset.limit.")

    has_glob = any(char in str(config.path) for char in "*?[]")
    if not has_glob and config.path.suffix.lower() == ".json":
        if start_index > 0:
            raise IndexError(f"No Waymo JSON fixture frame found at index {start_index}.")
        yield _load_waymo_json_fixture(config.path)
        if count > 1:
            raise IndexError(
                f"Requested {count} Waymo frames from JSON fixture, but only 1 is available."
            )
        return

    paths = _expand_tfrecord_paths(config.path)
    tf, e2e_pb2 = _load_waymo_dependencies()
    global_index = 0
    yielded = 0
    stop_index = start_index + count
    for path in paths:
        dataset = tf.data.TFRecordDataset([str(path)], compression_type="")
        for raw_data in dataset.as_numpy_iterator():
            if config.limit is not None and global_index >= config.limit:
                break
            if global_index >= stop_index:
                return
            if global_index >= start_index:
                frame = e2e_pb2.E2EDFrame()
                frame.ParseFromString(raw_data)
                yield _frame_from_waymo_proto(
                    frame,
                    source_path=path,
                    frame_index=global_index,
                    tf=tf,
                )
                yielded += 1
                if yielded >= count:
                    return
            global_index += 1
    raise IndexError(
        f"Requested {count} Waymo E2E frames starting at {start_index}, "
        f"but only {yielded} frame(s) were available in {config.path}."
    )


def _load_waymo_dependencies() -> tuple[Any, Any]:
    try:
        tf = importlib.import_module("tensorflow")
        e2e_pb2 = importlib.import_module(
            "waymo_open_dataset.protos.end_to_end_driving_data_pb2"
        )
    except (ImportError, ModuleNotFoundError) as exc:
        raise WaymoDependencyError(
            "Real Waymo TFRecord parsing requires TensorFlow and "
            f"waymo-open-dataset. {WAYMO_RUNTIME_HINT}"
        ) from exc
    return tf, e2e_pb2


def _expand_tfrecord_paths(path: Path) -> list[Path]:
    raw = str(path)
    if any(char in raw for char in "*?[]"):
        matches = [Path(match) for match in glob.glob(raw)]
    elif path.is_dir():
        matches = list(path.glob("*.tfrecord*"))
    else:
        matches = [path]
    existing = sorted(match for match in matches if match.exists())
    if not existing:
        raise FileNotFoundError(f"No Waymo TFRecord files matched: {path}")
    return existing


def _sample_decoded_image(name: str, decoded: Any, width: int = 160, height: int = 90) -> CameraImage:
    source_height = int(decoded.shape[0])
    source_width = int(decoded.shape[1])
    target_width = min(width, source_width)
    target_height = min(height, source_height)
    pixels: list[list[RgbColor]] = []
    for y in range(target_height):
        source_y = int(round(y * (source_height - 1) / max(target_height - 1, 1)))
        row: list[RgbColor] = []
        for x in range(target_width):
            source_x = int(round(x * (source_width - 1) / max(target_width - 1, 1)))
            pixel = decoded[source_y, source_x]
            if hasattr(pixel, "tolist"):
                pixel_values = pixel.tolist()
            else:
                pixel_values = pixel
            if isinstance(pixel_values, list):
                channels = pixel_values[:3]
            else:
                channels = [pixel_values, pixel_values, pixel_values]
            row.append(cast(RgbColor, tuple(int(value) for value in channels)))
        pixels.append(row)
    return CameraImage(name=name, width=target_width, height=target_height, pixels=pixels)


def _front_camera_images(data: Any, tf: Any) -> list[CameraImage]:
    images: list[CameraImage] = []
    images_by_name = {int(image.name): image for image in data.frame.images}
    for camera_name in FRONT_CAMERA_ORDER:
        image_content = images_by_name.get(camera_name)
        if image_content is None:
            continue
        decoded = tf.io.decode_image(image_content.image, channels=3).numpy()
        images.append(
            _sample_decoded_image(
                name=FRONT_CAMERA_NAMES.get(camera_name, f"camera_{camera_name}"),
                decoded=decoded,
            )
        )
    if not images:
        raise ValueError("Waymo E2E frame did not include front camera images.")
    return images


def _xy_points(x_values: Any, y_values: Any, limit: int | None = None) -> list[tuple[float, float]]:
    points = [(float(x), float(y)) for x, y in zip(x_values, y_values, strict=False)]
    if limit is not None:
        return points[:limit]
    return points


def _initial_speed(data: Any) -> float | None:
    vel_x = getattr(data.past_states, "vel_x", [])
    vel_y = getattr(data.past_states, "vel_y", [])
    if len(vel_x) == 0 or len(vel_y) == 0:
        return None
    return float((float(vel_x[-1]) ** 2 + float(vel_y[-1]) ** 2) ** 0.5)


def _frame_from_waymo_proto(data: Any, source_path: Path, frame_index: int, tf: Any) -> FrameBundle:
    history = _xy_points(data.past_states.pos_x, data.past_states.pos_y)
    if len(history) < 2:
        raise ValueError("Waymo E2E frame requires at least two past ego states.")
    future = _xy_points(data.future_states.pos_x, data.future_states.pos_y, limit=20)
    future_xy = future if len(future) == 20 else None
    metadata: dict[str, Any] = {
        "dataset": "waymo_e2e",
        "scenario": "waymo_e2e",
        "source_path": str(source_path),
        "frame_index": frame_index,
        "initial_speed_mps": _initial_speed(data),
        "hazards": [],
    }
    return FrameBundle(
        frame_name=str(data.frame.context.name),
        front_images=_front_camera_images(data, tf),
        ego_history_xy=history,
        future_xy=future_xy,
        metadata=metadata,
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
