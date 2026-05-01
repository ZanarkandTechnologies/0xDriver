# Progress

Live orchestration log for the first 0xDriver implementation pass.

## Current Goal

Implement the first fixture-backed offline Waymo E2E-style pipeline:

- package/config skeleton
- synthetic frame fixtures
- scene visualization
- structured mock VLA intent
- candidate trajectory generation
- smoothing/ranking/safety checks
- ADE and latency reports
- submission dry-run packaging
- CLI entrypoints
- tests and final QA evidence

## Checklist

- [x] Bootstrap docs, PRD, and directory plan exist.
- [ ] Create parent implementation ticket.
- [x] Add Python package and CLI skeleton.
- [ ] Add fixture data path and mock scene loader.
- [ ] Add visualization artifact generation.
- [ ] Add structured intent schema and mock reasoner.
- [ ] Add candidate planning, smoothing, ranking, and fallback.
- [ ] Add ADE, latency, and evidence reports.
- [ ] Add submission dry-run packager.
- [ ] Add tests and local validation commands.
- [ ] Run code review.
- [ ] Run final QA against PRD user stories.
- [ ] Update docs and close implementation pass.

## Commit Plan

1. Planning/control baseline.
2. Package and CLI skeleton.
3. Fixture pipeline plus artifacts.
4. Planning/evaluation/submission behavior.
5. Tests, docs, review, and QA evidence.

## Notes

- Real Waymo TFRecord parsing is optional for v1 and must fail with clear setup
  guidance when dependencies or data are missing.
- Mock/fixture runs are the default proof path so the repo works without cloud
  GPU or Waymo downloads.
- Cloud VLA backends remain adapter-only until the core offline loop is solid.
