# TASK-036: Generated OOD Suite Runner

## Status

- state: building
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

- [ ] Build per-recipe route/video smoke plans.
- [ ] Attach overlay/evidence bundle paths per recipe.
- [ ] Aggregate blockers and readiness.
- [ ] Support `--limit` for 1 -> 10 ramp.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_generated_ood_suite_runner`
- `bash scripts/pre_push_check.sh`

## Blockers

- Live execution needs a working CARLA host.
