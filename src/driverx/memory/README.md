# driverx.memory

## Purpose

Turns closed-loop scenario results into compact safety memory and retrieves
relevant entries for generated OOD recipes.

## Public API

- `build_memory_bank(results)`
- `retrieve_memory(recipe, bank, limit)`
- `write_memory_bank(run_dir, bank)`

## Example

```bash
PYTHONPATH=src python3 -m driverx build-memory \
  --results tests/fixtures/fail2drive_like/results.json
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_scenario_forge
```
