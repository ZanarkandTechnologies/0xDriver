# Evaluation

## Purpose

Compute local proxy metrics and reports over saved run artifacts.

## Public API

- `average_displacement_error(prediction, ground_truth)`
- `evaluate_run_dir(run_dir)`

## Minimal Example

```python
ade = average_displacement_error(prediction, future)
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_evaluation
```
