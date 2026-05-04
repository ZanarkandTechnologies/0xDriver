# TASK-010: Regional Driving Behavior Library

## Status

- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-007
- location: `src/driverx/behaviors`, `tests`, reports
- enter when: scenario recipes exist and need executable actor behavior intent
- leave when: deterministic OOD behavior traces can be generated and validated offline
- blockers: none for offline behavior simulation
- spawned follow-ups: TASK-011 CARLA script compiler
- complexity: M

## Summary

Create a behavior library for regional/OOD traffic, including Malaysian-style
traffic patterns: no-signal cut-ins, sudden braking, motorcycle filtering,
wrong-way shoulder creep, informal right-of-way pushes, and low-profile fast
two-wheeler stunt proxies.

## Scope

In scope:

- typed behavior plans.
- deterministic trace simulation.
- metrics for lateral aggression, braking jerk, gap acceptance, wrong-way time,
  and route conflict.
- JSON/Markdown reports.

Out of scope:

- real CARLA actor control; that is TASK-011.
- real traffic prediction models.

## Acceptance Criteria

- [ ] At least six behavior templates exist.
- [ ] Each template generates deterministic actor coordinates over time.
- [ ] Tests assert the intended erratic property for each behavior.
- [ ] Reports summarize behavior metrics and expected failure pressure.
- [ ] Scenario recipes can reference behavior ids.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx generate-behaviors --run-id task10-behaviors`

## Blockers

- None.
