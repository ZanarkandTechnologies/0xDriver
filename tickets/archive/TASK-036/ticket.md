# TASK-036: Generated OOD Suite Runner

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-033, TASK-034, TASK-035
- location: `src/driverx/pipeline`, CLI, tests, docs
- enter when: one route-video smoke and one overlay evidence surface exist
- leave when: generated OOD recipes can be run or planned as a suite with
  per-scenario evidence bundles and aggregate readiness
- blockers: live route execution needs graphics-capable CARLA runtime
- spawned follow-ups: TASK-037 policy runtime matrix
- complexity: L

## Summary

Run the generated scenarios as a suite instead of one hand-picked route. In
blocked environments, emit a dry-run suite plan with precise missing runtime
requirements.

## Acceptance Criteria

- [x] Build per-recipe route/video smoke plans.
- [x] Attach overlay/evidence bundle paths per recipe.
- [x] Aggregate blockers and readiness.
- [x] Support `--limit` for 1 -> 10 ramp.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_generated_ood_suite_runner`
- `bash scripts/pre_push_check.sh`

## Blockers

- Live execution needs a working CARLA host.

## Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_generated_ood_suite_runner`
  passed with 2 tests.
- `PYTHONPATH=src python3 -m driverx run-generated-ood-suite --scenario-config configs/scenario_forge.sample.yaml --carla-config configs/carla_local.sample.yaml --route-root ../external/fail2drive --limit 1 --run-id task36-suite-1b`
  wrote `artifacts/runs/task36-suite-1b/generated_ood_suite.json` and
  `artifacts/runs/task36-suite-1b/generated_ood_suite.md`, including one
  per-recipe Fail2Drive video-smoke plan, one route evidence bundle, the route
  pack, overlay plan, overlay evidence, and aggregate live blockers.
- `bash scripts/pre_push_check.sh` passed with 181 tests.
- Review pass:
  `tickets/TASK-036/artifacts/review/20260505T191339-review.json` scored
  `4.0` overall with no blocking findings.
