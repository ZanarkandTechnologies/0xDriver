# driverx.scenarios

## Purpose

Owns Fail2Drive-style scenario seeds, generated OOD recipes, and scenario suite
reports for the 0xDriver closed-loop generalization track.

## Public API

- `load_scenario_seeds(path)`
- `generate_scenario_recipes(seeds, mutation_policy, count, random_seed)`
- `write_scenario_suite(run_dir, seeds, recipes)`

## Example

```bash
PYTHONPATH=src python3 -m driverx forge-scenarios \
  --config configs/scenario_forge.sample.yaml
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_scenario_forge
```
