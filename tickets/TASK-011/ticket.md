# TASK-011: Scenario-To-CARLA Script Compiler

## Status

- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-009, TASK-010
- location: `src/driverx/simulators`, `src/driverx/behaviors`, CLI, tests
- enter when: entity tracks and behavior traces exist
- leave when: scenario recipes compile into CARLA actor script plans
- blockers: live CARLA execution optional; compiler can be tested offline
- spawned follow-ups: Fail2Drive XML export
- complexity: L

## Summary

Compile `ScenarioRecipe` plus `BehaviorPlan` into a CARLA script plan: spawn
blueprints, transforms, per-tick controls, sensors, expected outputs, and
cleanup. This is the executable layer before full Fail2Drive XML export.

## Acceptance Criteria

- [ ] Compiler emits deterministic CARLA script plan JSON.
- [ ] Actor plans include blueprint filters, spawn transforms, behavior binding,
  and cleanup policy.
- [ ] Sensor plans include camera pose, resolution, and output path.
- [ ] Plan validator rejects missing route path, unsupported behavior, and
  invalid spawn constraints.
- [ ] Tests cover valid compile and invalid configs.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx compile-carla-script --recipe <recipe> --behavior <behavior> --run-id task11-script`

## Blockers

- TASK-009/TASK-010 supply the spawn and behavior contracts.
