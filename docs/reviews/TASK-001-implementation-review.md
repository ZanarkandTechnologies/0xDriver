# TASK-001 Implementation Review

- Review date: 2026-05-02
- Scope: fixture-backed 0xDriver runtime, CLI, tests, evidence, docs
- Latest verdict: PASS after reviewer/QA blocking findings were resolved

## Review Passes

### Pass 1

Verdict: revise.

Blocking findings:

- Raw/pre-smooth/post-smooth trajectory evidence was not separated.
- Stage-separated timings were too coarse.
- Run directory creation could clobber evidence.
- Renderer showed construction objects on clear-scene fixtures.
- Submission metadata ignored config.

Resolution:

- Added `raw_candidates.json`, `smoothed_candidates.json`, and
  `selected_trajectory.json`.
- Split timings into load, reason, generate, smooth, rank, evaluate, render, and
  package stages.
- Made run directories collision-safe.
- Made renderer consult fixture metadata before drawing objects.
- Wrote `run_metadata.json` and consumed it in the submission packager.

### Pass 2

Verdict: revise.

Blocking findings:

- Durable review artifact was missing.
- `docs/progress.md` was stale.
- `docs/bootstrap-brief.md` still referenced Python 3.10.

Resolution:

- Added this review artifact and linked it from the ticket.
- Reconciled `docs/progress.md`.
- Updated bootstrap runtime language to Python 3.11 or newer.

### QA Pass

Verdict: revise, then fixed.

Blocking findings:

- Invalid reasoner output raised errors in tests but did not record a runtime
  validation-error artifact.
- Submission packaging was JSON-only.
- No understood failure case was documented.

Resolution:

- Added `invalid_mock` reasoner backend and fail-closed fallback behavior.
- Runtime now writes `reasoner_error.json` for malformed reasoner output.
- Submission packager writes `submission_shard_00000.pb` plus
  `submission_schema.proto`.
- QA report documents the invalid-reasoner fallback as the first understood
  failure case.

## Final Validation

```bash
bash scripts/pre_push_check.sh
```

Result: PASS, `16` unittest cases.

## Residual Caveats

- The protobuf shard uses the repo's dry-run schema, not the official Waymo
  challenge protobuf schema.
- Real Waymo TFRecord loading remains a follow-up; v1 includes a
  `dataset.kind=waymo` JSON fixture loader for local E2E-shaped frame proof.
- Real VLA/VLM integration remains a follow-up.
