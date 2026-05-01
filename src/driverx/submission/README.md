# Submission

## Purpose

Package predictions into a dry-run Waymo E2E-like submission artifact.

## Public API

- `package_run_dir(run_dir, output_path=None)`

## Minimal Example

```python
package = package_run_dir(run_dir)
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock
```
