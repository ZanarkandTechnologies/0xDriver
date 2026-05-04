# TASK-014 QA Report

## Result

Pass.

## Acceptance Criteria

- Runner executes `policy` and `policy+memory` on the same scenario seed:
  passed.
- Report includes scenario id, retrieved memory ids, behavior metrics, policy
  outputs, latency, and improvement/regression notes: passed.
- Mock policy demonstrates controlled memory-sensitive outcome without claiming
  real model performance: passed with `live_model_claim=false`.
- Tests cover deterministic A/B pairing and report aggregation: passed.
- Live-model blockers are logged without blocking local harness tests: passed.

## Evidence

- Unit/CLI tests: `PYTHONPATH=src python3 -m unittest tests.test_rag_comparison tests.test_policies tests.test_cli`
- Mock proof: `PYTHONPATH=src python3 -m driverx run-rag-comparison --policy mock --run-id task14-rag`
- Alpamayo blocker proof: `PYTHONPATH=src python3 -m driverx run-rag-comparison --policy alpamayo --run-id task14-rag-alpamayo-blocked`
- Mock artifacts:
  - `artifacts/runs/task14-rag/rag_comparison.json`
  - `artifacts/runs/task14-rag/rag_comparison.md`
- Blocker artifacts:
  - `artifacts/runs/task14-rag-alpamayo-blocked/rag_comparison.json`
  - `artifacts/runs/task14-rag-alpamayo-blocked/rag_comparison.md`

## Result Snapshot

- Scenario: `construction_merge::motorcycle_filtering`
- No-memory score: `58.0`
- Memory-guided score: `95.0`
- Infraction delta: `-2`
- Live model claim: `false`

## Residual Risk

The current score proves harness behavior only. A real VLA backend is still
needed for submission claims about model capability.

