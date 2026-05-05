# TASK-008 QA Report

QA time: 2026-05-04 18:58 +0800

## Verdict

PASS

## Commands

```bash
PYTHONPATH=src python3 -m unittest tests.test_carla_probe tests.test_cli tests.test_simulator_adapters
bash scripts/pre_push_check.sh
PYTHONPATH=src python3 -m driverx smoke-carla --config configs/carla_local.sample.yaml
bash scripts/run_carla_client_docker.sh python -m driverx probe-carla --host host.docker.internal --port 2000 --timeout-s 10 --run-id task8-carla-probe
```

## Evidence

- Local targeted tests: PASS, 19 tests.
- Full local gate: PASS, 61 tests.
- TCP smoke: `reachable: true` for `127.0.0.1:2000`.
- Live Docker probe: `artifacts/runs/task8-carla-probe/carla_probe.json`.
- Probe map: `Carla/Maps/Town10HD_Opt`.
- Probe actor count: `23`.
- Probe server/client version: `0.9.16` / `0.9.16`.

## Acceptance Criteria Reconciliation

- AC-1 live TCP smoke reaches CARLA: PASS.
- AC-2 Docker helper runs repo commands in Python 3.10 amd64: PASS.
- AC-3 `probe-carla` writes JSON and Markdown artifacts: PASS.
- AC-4 probe records map name and actor count: PASS.
- AC-5 missing package/server failures are actionable JSON: PASS via tests and native no-package probe.
- AC-6 tests pass without live CARLA: PASS.
- AC-7 live QA records real probe result: PASS.

## Residual Risk

- The live probe is read-only; actor spawning and cleanup are TASK-009.
- Docker installs the CARLA wheel on each disposable run unless a cached image
  is introduced later.
