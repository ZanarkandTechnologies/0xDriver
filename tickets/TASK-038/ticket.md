# TASK-038: Alpamayo Offline Probe

## Status

- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-037, RTX 6000 Ada or equivalent GPU, Hugging Face access
- location: `src/driverx/policies`, `scripts`, remote artifacts, tests
- enter when: policy runtime matrix identifies Alpamayo as a high-value adapter
- leave when: Alpamayo can be loaded or produces a precise model/runtime
  blocker, with memory and latency evidence
- blockers: live proof needs GPU SSH plus HF access on the remote
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: L

## Summary

Probe Alpamayo offline before trying closed-loop CARLA. The target is model
load, input/output shape discovery, one prepared observation, trajectory output,
latency, and blocker classification.

## Acceptance Criteria

- [ ] Remote probe script records GPU, package versions, model load state,
  memory usage, and latency.
- [ ] Adapter stub records expected Alpamayo input/output schema.
- [ ] Failure modes are classified without leaking credentials.

## Verification

- local tests for parser/classifier
- remote optional: one Alpamayo load/probe run

## Blockers

- Needs remote GPU and HF access for live proof.
