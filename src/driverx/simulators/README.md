# driverx.simulators

## Purpose

Owns adapter surfaces for external simulators. The local path covers CARLA
server smoke checks, CARLA Python API probing through Docker, and Fail2Drive
dry-run command planning.

## Public API

- `load_carla_run_config(path)`
- `smoke_carla_server(host, port, timeout_s)`
- `probe_carla_client(config)`
- `write_carla_probe(run_dir, result)`
- `plan_fail2drive_run(config, recipe)`

## Example

```bash
PYTHONPATH=src python3 -m driverx smoke-carla --config configs/carla_local.sample.yaml
bash scripts/run_carla_client_docker.sh python -m driverx probe-carla \
  --host host.docker.internal \
  --port 2000 \
  --run-id task8-carla-probe
bash scripts/run_carla_client_docker.sh python -m driverx spawn-ego-smoke \
  --host host.docker.internal \
  --port 2000 \
  --run-id task9-ego-smoke
PYTHONPATH=src python3 -m driverx plan-carla-run \
  --config configs/carla_local.sample.yaml \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --recipe-id generated-base-animals-0076-visual-noise-000
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_simulator_adapters
```
