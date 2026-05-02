# Progress

Live orchestration log for the first 0xDriver implementation pass.

## Current Goal

Establish the first real-data Waymo batch baseline before adding VLA/GPU serving:

- stream a configurable validation frame range once
- preserve fixture `run-batch` compatibility
- write per-frame artifacts under the batch root
- write `batch_summary.json` and `batch_report.md`
- identify the best/worst ADE scenes and worst-scene SVG failure case

## Checklist

- [x] TASK-001 fixture-backed loop complete.
- [x] Create TASK-002 for real Waymo/protobuf optional integration.
- [x] Add optional dependency metadata and config fields.
- [x] Implement real TFRecord loader path.
- [x] Implement official protobuf packaging path.
- [x] Add tests for optional-dependency and fixture continuity.
- [x] Update README and durable docs.
- [x] Run tests and commit implementation.
- [x] Run review and final QA.
- [x] Create TASK-003 for real Waymo runtime setup.
- [x] Build Docker Waymo runtime.
- [x] Smoke-test imports inside Docker.
- [x] Run validation shard through the loader.
- [x] Document the local-vs-cloud GPU workflow.
- [x] Create TASK-004 for real Waymo batch baseline.
- [x] Add loaded-frame execution seam.
- [x] Add streaming Waymo frame iterator.
- [x] Extend `run-batch` with Waymo frame ranges and report aggregation.
- [x] Add fake-Waymo unit tests for batch aggregation.
- [x] Run real 10-frame Waymo Docker baseline.
- [x] Attach TASK-004 review and QA evidence.

## Commit Plan

1. Ticket start.
2. Streaming batch implementation and unit tests.
3. Docs and durable baseline rule.
4. Review, QA evidence, and closeout.

## Notes

- Real Waymo data is not needed to implement the optional parser, but it is
  needed to validate against an actual downloaded shard.
- Current clean proof without real data is: optional dependency paths fail with
  actionable setup guidance and no traceback.
- TASK-002 final review passed at `4.2 / 5.0`; final QA passed all stated
  acceptance criteria.
- Mock/fixture runs remain the default proof path so the repo works without
  cloud GPU, TensorFlow, Waymo downloads, or model credentials.
- Cloud VLA backends remain out of scope until official data/package surfaces
  are credible.
- TASK-003 Docker proof: `driverx-waymo:local` imports TensorFlow 2.13.0,
  Waymo E2E protos, and `driverx`; the downloaded validation shard loads frame
  `11d68b183960928432c0ab7af24ac86d-058` with three front cameras.
- Baseline real-frame proof: `waymo-docker-baseline-003` completed with mock intent,
  a smoothed 20-point trajectory, ADE `11.482393`, and load-frame timing near
  `4.15s` under local amd64 Docker emulation.
- Official submission dependency guidance is shared across loader and packager:
  native macOS failure points to Docker; Docker reaches official dependency
  loading and then validates missing `account_name` as expected.
- Linux native dependency guidance now points to `requirements/waymo-linux.txt`;
  `pip install --dry-run -r requirements/waymo-linux.txt` resolves the Waymo
  tree and finds `jaxlib==0.4.13` through the configured JAX wheel index.
- TASK-004 local proof: `bash scripts/pre_push_check.sh` passes with 34 unittest
  cases after adding Waymo batch aggregation tests.
- TASK-004 Docker proof: `waymo-batch-10` streamed 10 validation frames, wrote
  `artifacts/runs/waymo-batch-10/batch_summary.json` and
  `artifacts/runs/waymo-batch-10/batch_report.md`, produced mean ADE
  `6.204769`, best ADE `0.517203` at frame index `4`, and worst ADE
  `13.953167` at frame index `6`.
- TASK-004 review repair: fixture batch defaults moved into `run_batch`, the CLI
  now passes fixture names through unchanged, tests prove CLI/API fixture-default
  agreement, and `waymo-batch-default-10` proves real-data default count without
  passing `--frame-count`.
