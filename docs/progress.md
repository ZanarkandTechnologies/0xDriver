# Progress

Live orchestration log for the first 0xDriver implementation pass.

## Current Goal

Establish a compatible real Waymo runtime and smoke-test the downloaded
validation shard:

- document macOS ARM native package limitation
- build Linux amd64 Docker image with official Waymo dependencies
- run import smoke inside Docker
- run the validation TFRecord through `driverx inspect-scene`
- capture the next parser/runtime issue if the real shard exposes one

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

## Commit Plan

1. Ticket and config/dependency metadata.
2. Waymo loader implementation.
3. Official submission packager implementation.
4. Tests and docs.
5. Review, QA evidence, and commit.

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
