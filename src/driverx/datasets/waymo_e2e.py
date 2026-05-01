"""Optional Waymo E2E loader placeholder.

The fixture pipeline is the default v1 path. This module preserves the seam for
real Waymo TFRecords without forcing TensorFlow/Waymo dependencies on local QA.
"""

from __future__ import annotations

from driverx.core.config import DatasetConfig
from driverx.core.types import FrameBundle


def load_waymo_frame(config: DatasetConfig) -> FrameBundle:
    if config.path is None:
        raise FileNotFoundError(
            "Waymo dataset path is required for dataset.kind=waymo. "
            "Set dataset.path in config or use ${WAYMO_E2E_DATASET}."
        )
    raise NotImplementedError(
        "Real Waymo TFRecord parsing is not implemented in v1. "
        "Use dataset.kind=fixture for local runs, then add TensorFlow and "
        "waymo-open-dataset support behind this function."
    )
