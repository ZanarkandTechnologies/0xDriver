# Datasets

## Purpose

Load frames into the canonical `FrameBundle` shape.

## Public API

- `load_frame(config)`
- `load_fixture_frame(name)`
- `load_waymo_frame(config)` for JSON fixtures or optional real TFRecord support
- `load_waymo_tfrecord_frame(config)` for official Waymo E2E TFRecords when
  optional dependencies are installed

## Minimal Example

```python
from driverx.datasets.fixtures import load_fixture_frame

frame = load_fixture_frame("construction_merge")
```

```python
from pathlib import Path
from driverx.core.config import DatasetConfig
from driverx.datasets.waymo_e2e import load_waymo_frame

frame = load_waymo_frame(
    DatasetConfig(kind="waymo", path=Path("/data/validation.tfrecord-00000"))
)
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock
PYTHONPATH=src python3 -m unittest tests.test_waymo_loader
```
