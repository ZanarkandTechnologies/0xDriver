# TASK-016 QA Report

## Verdict

PASS for local Docker runtime setup. Live CARLA connectivity is not currently
proved because the host simulator did not answer on `host.docker.internal:2000`
during this pass.

## Evidence

- Unit test: `PYTHONPATH=src python3 -m unittest tests.test_carla_docker_scripts`
  passed with 5 tests, including a fake-Docker subprocess contract test for
  proof-script run ids and timeout defaults.
- Syntax/lint gate: `python3 -m compileall -q src tests` passed.
- Full gate: `bash scripts/pre_push_check.sh` passed with 107 tests.
- Docker build: `bash scripts/build_carla_client_docker.sh` built
  `driverx-carla-client:0.9.16`.
- Docker import proof:
  `scripts/run_carla_client_docker.sh python -c 'import carla; from importlib.metadata import version; print(version("carla"))'`
  printed `0.9.16`.
- One-command proof:
  `bash scripts/prove_carla_0916_docker.sh` printed `CARLA Python API: 0.9.16`
  and wrote timeout artifacts from default run id `task16-proof`.
- Proof artifacts:
  - `artifacts/runs/task16-proof-probe/carla_probe.json`
  - `artifacts/runs/task16-proof-probe/carla_probe.md`
  - `artifacts/runs/task16-proof-ego/ego_smoke.json`
  - `artifacts/runs/task16-proof-ego/ego_smoke.md`
  - `artifacts/runs/task16-proof-probe-001/carla_probe.json`
  - `artifacts/runs/task16-proof-probe-001/carla_probe.md`
  - `artifacts/runs/task16-proof-ego-001/ego_smoke.json`
  - `artifacts/runs/task16-proof-ego-001/ego_smoke.md`
- Machine-readable QA summary:
  `tickets/TASK-016/artifacts/qa/result.json`

## Residual Risk

- The host CARLA server was not reachable from Docker during this QA pass, so
  the live map/actor/camera path should be rerun once CARLA.app is open and
  fully loaded.
