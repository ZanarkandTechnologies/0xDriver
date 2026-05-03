# TASK-007 QA Report

QA time: 2026-05-03 19:50 +0800

## Verdict

PASS

## Commands

```bash
bash scripts/pre_push_check.sh
PYTHONPATH=src python3 -m driverx forge-scenarios --config configs/scenario_forge.sample.yaml --count 8 --seed 7 --run-id task7-scenario-forge
PYTHONPATH=src python3 -m driverx build-memory --results tests/fixtures/fail2drive_like/results.json --run-id task7-memory-bank
PYTHONPATH=src python3 -m driverx plan-carla-run --config configs/carla_local.sample.yaml --recipe artifacts/runs/task7-scenario-forge/scenario_recipes.json --recipe-id generated-base-animals-0076-visual-noise-000 --run-id task7-carla-plan
PYTHONPATH=src python3 -m driverx smoke-carla --config configs/carla_local.sample.yaml
```

## Evidence

- Local gate: PASS, 57 tests.
- Scenario suite: `artifacts/runs/task7-scenario-forge/scenario_suite_report.md`.
- Scenario recipes: `artifacts/runs/task7-scenario-forge/scenario_recipes.json`.
- Memory bank: `artifacts/runs/task7-memory-bank/memory_bank.md`.
- Memory JSON: `artifacts/runs/task7-memory-bank/memory_bank.json`.
- CARLA dry-run plan: `artifacts/runs/task7-carla-plan/carla_command_plan.json`.
- CARLA dry-run route: selected recipe `generated-base-animals-0076-visual-noise-000` maps to `/Users/kenjipcx/SOTA/external/fail2drive/fail2drive_split/Base_Animals_0076.xml`.
- CARLA smoke: current local server unreachable, reported cleanly as JSON with `reachable: false` and no traceback.

## Acceptance Criteria Reconciliation

- AC-1 external Fail2Drive checkout exists and is not committed: PASS (`../external/fail2drive`, commit `69c982b`).
- AC-2 completed ticket folders archived: PASS (`tickets/archive/TASK-001` through `TASK-006`).
- AC-3 `forge-scenarios` artifacts written: PASS.
- AC-4 `build-memory` artifacts written: PASS.
- AC-5 `plan-carla-run` dry-run command plan written: PASS; multi-recipe suites now require explicit `--recipe-id`.
- AC-6 `smoke-carla` clean reachable/unreachable result: PASS.
- AC-7 tests cover fixture parsing, deterministic generation, memory retrieval, command planning, smoke failure, and CLI compatibility: PASS.
- AC-8 existing Waymo commands remain covered by regression suite: PASS.
- AC-9 README and architecture present CARLA/Fail2Drive main path and Waymo support track: PASS.

## Residual Risk

- The Apple Silicon CARLA wrapper was not launched during QA.
- Generated recipes are not yet exported into executable Fail2Drive XML.
- Real SimLingo/Alpamayo policies are follow-up runtime tickets.
