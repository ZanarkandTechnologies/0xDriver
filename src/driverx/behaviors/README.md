# driverx.behaviors

## Purpose

Owns deterministic OOD actor behavior traces for scenario generation. These
traces let tests verify the intended pressure before live CARLA scripts exist.

## Public API

- `default_behavior_plans()`
- `simulate_behavior(plan)`
- `summarize_behavior_suite(traces)`
- `write_behavior_suite(run_dir, traces)`

## Example

```bash
PYTHONPATH=src python3 -m driverx generate-behaviors --run-id task10-behaviors
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_behaviors
```
