# TASK-015 QA Report

## Result

Pass.

## Acceptance Criteria

- SimLingo checkout discovery reports root, commit, required files, CARLA
  version, Python version, CUDA requirement, and Apple Silicon limitations:
  passed.
- Dry-run command planner emits a single-route Bench2Drive evaluation command
  with env vars, ports, checkpoint, route, agent file, and expected outputs:
  passed.
- CLI exposes readiness and command planning artifacts: passed.
- Policy stub guidance points to readiness/planning command: passed.
- Tests cover fake checkout readiness, missing file blockers, and command
  planning without importing SimLingo or CARLA: passed.

## Evidence

- Unit/CLI tests: `PYTHONPATH=src python3 -m unittest tests.test_simlingo_adapter tests.test_cli tests.test_policies`
- Readiness proof: `PYTHONPATH=src python3 -m driverx inspect-simlingo --run-id task15-simlingo-readiness`
- Plan proof: `PYTHONPATH=src python3 -m driverx plan-simlingo-run --run-id task15-simlingo-plan`
- Artifacts:
  - `artifacts/runs/task15-simlingo-readiness/simlingo_readiness.json`
  - `artifacts/runs/task15-simlingo-readiness/simlingo_readiness.md`
  - `artifacts/runs/task15-simlingo-plan-001/simlingo_command_plan.json`
  - `artifacts/runs/task15-simlingo-plan-001/simlingo_command_plan.md`

## Result Snapshot

- Checkout: `/Users/kenjipcx/SOTA/external/simlingo`
- Commit: `743b243afd6cf5ff51b9fa1f8cac86f22d569684`
- Required files: all present
- CARLA version: `0.9.15`
- Python version: `3.8`
- Requires CUDA: `true`
- Apple Silicon live supported: `false`

## Residual Risk

Live execution is not possible on the local Apple Silicon setup. The generated
command plan must be run on Linux NVIDIA after CARLA 0.9.15 and checkpoint
assets are installed.

