# TASK-013: Policy Adapter Interface

## Status

- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-011
- location: `src/driverx/policies`, `src/driverx/memory`, tests
- enter when: compiled scenarios need policy execution surfaces
- leave when: mock/rule/VLM-ready policy adapters share one contract
- blockers: real SimLingo/Alpamayo credentials needed only for live adapters
- spawned follow-ups: TASK-014 RAG comparison
- complexity: L

## Summary

Define the policy adapter boundary for frozen reasoning VLA/VLM policies. The
first implementation includes deterministic mock and local hybrid adapters so
the harness can be tested before real model access.

## Acceptance Criteria

- [ ] `PolicyAdapter` interface returns structured intent/action, latency, and
  reason summary.
- [ ] Mock adapter supports no-memory and memory-aware behavior.
- [ ] Local hybrid planner adapter can act as fallback.
- [ ] VLM/API, SimLingo, and Alpamayo adapters exist as setup-checked stubs with
  clear blockers.
- [ ] Tests cover adapter selection, memory injection, and missing dependency
  guidance.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx run-policy-fixture --policy mock --run-id task13-policy`

## Blockers

- Real model checkpoints/API keys are not required for the adapter contract.
