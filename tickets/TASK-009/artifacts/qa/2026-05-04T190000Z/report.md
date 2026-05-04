# TASK-009 QA Report

QA time: 2026-05-04 19:00 +0800

## Verdict

PASS

## Commands

```bash
PYTHONPATH=src python3 -m unittest tests.test_carla_ego tests.test_carla_probe tests.test_cli
bash scripts/pre_push_check.sh
bash scripts/run_carla_client_docker.sh python -m driverx spawn-ego-smoke --host host.docker.internal --port 2000 --timeout-s 10 --tick-count 5 --run-id task9-ego-smoke
```

## Evidence

- Local targeted tests: PASS, 18 tests.
- Full local gate: PASS, 65 tests.
- Live map: `Carla/Maps/Town10HD_Opt`.
- Spawned actor ids: `[24, 25]`.
- Destroyed actor ids: `[25, 24]`.
- Track count: `10`.
- Camera artifact: `artifacts/runs/task9-ego-smoke/ego_camera.png`.
- Track artifact: `artifacts/runs/task9-ego-smoke/entity_tracks.json`.

## Acceptance Criteria Reconciliation

- AC-1 fake/local command path works without CARLA: PASS.
- AC-2 live spawn/destroy works through Docker bridge: PASS.
- AC-3 entity tracks include actor id, type, tick, transform, and velocity:
  PASS.
- AC-4 sensor capture writes a frame artifact: PASS.
- AC-5 cleanup logs destroyed actor ids: PASS.
- AC-6 tests prove cleanup and missing package guidance: PASS.

## Residual Risk

- Actor spawning is still a smoke test, not a route-following scenario.
- Live actor ids vary by CARLA session.
