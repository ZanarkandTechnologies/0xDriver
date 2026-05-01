# Datasets

## Purpose

Load frames into the canonical `FrameBundle` shape.

## Public API

- `load_frame(config)`
- `load_fixture_frame(name)`
- `load_waymo_frame(config)` placeholder for future real TFRecord support

## Minimal Example

```python
from driverx.datasets.fixtures import load_fixture_frame

frame = load_fixture_frame("construction_merge")
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock
```
