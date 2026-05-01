"""Dataset loading entrypoints."""

from driverx.core.config import DatasetConfig
from driverx.core.types import FrameBundle
from driverx.datasets.fixtures import load_fixture_frame
from driverx.datasets.waymo_e2e import load_waymo_frame


def load_frame(config: DatasetConfig) -> FrameBundle:
    if config.kind == "fixture":
        return load_fixture_frame(config.name)
    if config.kind == "waymo":
        return load_waymo_frame(config)
    raise ValueError(f"Unsupported dataset kind: {config.kind}")


__all__ = ["load_frame", "load_fixture_frame", "load_waymo_frame"]
