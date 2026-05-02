# Progress

Live orchestration log for the first 0xDriver implementation pass.

## Current Goal

Implement optional real Waymo E2E integration without breaking the dependency-free
fixture path:

- real TFRecord loader seam
- official Waymo dependency detection
- official submission protobuf packaging path
- sample local Waymo config
- fallback tests and docs for missing optional deps
- preserve mock pipeline gate

## Checklist

- [x] TASK-001 fixture-backed loop complete.
- [x] Create TASK-002 for real Waymo/protobuf optional integration.
- [ ] Add optional dependency metadata and config fields.
- [ ] Implement real TFRecord loader path.
- [ ] Implement official protobuf packaging path.
- [ ] Add tests for optional-dependency and fixture continuity.
- [ ] Update README and durable docs.
- [ ] Run tests, review, and commit.

## Commit Plan

1. Ticket and config/dependency metadata.
2. Waymo loader implementation.
3. Official submission packager implementation.
4. Tests and docs.
5. Review, QA evidence, and commit.

## Notes

- Real Waymo data is not needed to implement the optional parser, but it is
  needed to validate against an actual downloaded shard.
- Mock/fixture runs remain the default proof path so the repo works without
  cloud GPU, TensorFlow, Waymo downloads, or model credentials.
- Cloud VLA backends remain out of scope until official data/package surfaces
  are credible.
