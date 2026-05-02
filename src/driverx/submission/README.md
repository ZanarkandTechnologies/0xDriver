# Submission

## Purpose

Package predictions into dry-run Waymo E2E-like artifacts, with an optional
official Waymo protobuf serialization path when the Waymo package is installed.

## Public API

- `package_run_dir(run_dir, output_path=None, official=False)`

## Minimal Example

```python
package = package_run_dir(run_dir)
official_package = package_run_dir(run_dir, official=True)
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock
PYTHONPATH=src python3 -m unittest tests.test_submission_packager
```
