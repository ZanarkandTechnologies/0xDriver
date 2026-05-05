# TASK-039: Alpamayo CARLA Adapter

## Status

- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-038
- location: `src/driverx/policies`, `src/driverx/simulators`, tests
- enter when: Alpamayo offline probe establishes load and trajectory shape
- leave when: CARLA camera/ego/nav observations can be transformed into
  Alpamayo inputs and its trajectory can be converted into CARLA control intent
- blockers: waits on TASK-038 data-shape evidence
- spawned follow-ups: TASK-040 submission demo pack
- complexity: L

## Summary

Build the closed-loop Alpamayo adapter only after the offline probe proves the
model shape. This ticket should not guess at undocumented tensors.

## Acceptance Criteria

- [ ] Observation transform uses documented/probed camera, egomotion, and route
  fields.
- [ ] Trajectory output converts to control intent with validation.
- [ ] Adapter has offline replay tests before live CARLA.

## Verification

- pending TASK-038.

## Blockers

- TASK-038 must provide real Alpamayo shape evidence.
