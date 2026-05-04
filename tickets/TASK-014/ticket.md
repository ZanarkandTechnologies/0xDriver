# TASK-014: Retrieval-Augmented VLA Comparison Harness

## Status

- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-010, TASK-013
- location: `src/driverx/pipeline`, `src/driverx/policies`, `src/driverx/memory`, tests, reports
- enter when: behavior traces and policy adapters exist
- leave when: no-memory vs memory-guided policy comparison reports are generated
- blockers: real VLA needed only for final live claim; mock comparison can prove harness
- spawned follow-ups: final demo and runtime acceleration
- complexity: L

## Summary

Run matched scenarios with and without retrieved safety memory, then compare
success proxies, infractions, entity tracks, reason summaries, and latency.
Until a real VLA is attached, the mock policy proves harness behavior only.

## Acceptance Criteria

- [ ] Comparison runner executes `policy` and `policy+memory` modes on the same
  scenario seed.
- [ ] Report includes scenario id, retrieved memory ids, behavior metrics,
  policy outputs, latency, and improvement/regression notes.
- [ ] Mock policy demonstrates a controlled memory-sensitive outcome without
  claiming real model performance.
- [ ] Tests cover deterministic A/B pairing and report aggregation.
- [ ] Live-model blockers are logged without blocking local harness tests.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx run-rag-comparison --policy mock --run-id task14-rag`

## Blockers

- Real VLA comparison requires a selected policy backend and credentials.
