# Vision

## Purpose

Render evidence artifacts for scene inspection and trajectory prediction.

## Public API

- `render_scene_svg(frame, output_path, selected=None, candidates=None)`

## Minimal Example

```python
from driverx.vision import render_scene_svg
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock
```
