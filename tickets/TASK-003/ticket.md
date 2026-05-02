# TASK-003: Establish Waymo Linux Runtime And Real-Shard Smoke Test

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-002, local validation shard in `data/`
- location: docker, requirements, scripts, docs, configs
- enter when: user provides a validation TFRecord and asks to install runnable dependencies
- leave when: Waymo dependencies are installed in a compatible isolated runtime and the real validation shard is smoke-tested
- blockers: none for Docker runtime; local macOS ARM native Waymo wheel is unavailable
- spawned follow-ups: GPU/VLA serving ticket after real-data smoke passes
- complexity: M

## Description

The official Waymo package does not provide macOS ARM wheels. This ticket adds a
repeatable Linux amd64 Docker runtime that can install the official Waymo stack
without polluting system Python, then uses it to run the real validation shard
through the existing `driverx` loader.

## Goal

Make real Waymo E2E validation possible from the MacBook by using Docker as the
compatibility boundary, while preserving fixture-backed local development.

## Plan

### Change

Add a Linux Waymo requirements file, Dockerfile, and helper scripts for building
and running the real-data smoke path.

### Why

Waymo’s official `waymo-open-dataset-tf-2-12-0==1.6.7` wheel exists for Linux
x86_64, not macOS ARM. Docker provides the cleanest local bridge before renting
a GPU box.

### Before -> After

- Before: local Python 3.14/3.11 cannot install Waymo/TensorFlow packages.
- After: `docker build --platform linux/amd64` creates a `driverx-waymo:local`
  image that can import TensorFlow and Waymo packages and execute the repo CLI
  against mounted data.

### Touch

- `.gitignore`
- `pyproject.toml`
- `requirements/waymo-linux.txt`
- `docker/waymo.Dockerfile`
- `scripts/build_waymo_docker.sh`
- `scripts/run_waymo_docker.sh`
- `README.md`
- `docs/HISTORY.md`
- `docs/progress.md`

### Acceptance Criteria

- [x] Local macOS native install failure is documented as a platform limitation.
- [x] Docker dependency resolution succeeds on `linux/amd64`.
- [x] `driverx` imports TensorFlow and Waymo inside the Docker runtime.
- [x] The provided validation TFRecord runs through `inspect-scene` or fails with
  an implementation-level parser error that can be addressed next.
- [x] README documents the local-Docker path and the cloud GPU path.

### Evidence Checklist

- [x] Docker build output.
- [x] Import smoke output.
- [x] Real validation-shard CLI output.
- [x] Updated docs.
- [x] Final review/QA note.

### Build Notes

Initial preflight:

- Native `.venv-waymo` on macOS ARM failed because Waymo only ships Linux x86_64
  wheels.
- `python:3.11-slim` amd64 failed dependency resolution because `jaxlib==0.4.13`
  is unavailable for that combo from the default index.
- `python:3.10-slim` amd64 dry-run succeeds when pip uses
  `https://storage.googleapis.com/jax-releases/jax_releases.html`, but building
  from that base stalled on the 524 MB TensorFlow wheel download.
- `tensorflow/tensorflow:2.13.0` resolves and installs Waymo dependencies but
  uses Python 3.8, which cannot run the current Python 3.10+ `driverx` source.
- Final runtime target is `python:3.10-slim` Linux amd64 with cached pip
  downloads, long timeouts, and the Waymo-only requirement.
- `pyproject.toml` now declares Python 3.10+ because the source only needs 3.10
  features and the Waymo Linux runtime resolves there.
- `datetime.UTC` was replaced with `timezone.utc` so the CLI works under Python
  3.10 in Docker.
- Official Waymo dependency guidance is centralized in `driverx.waymo_runtime`
  so TFRecord parsing and official submission packaging point Apple Silicon
  users to the same Docker runtime.
- The previous `.[waymo]` optional extra was removed because it could not carry
  the required JAX wheel index. Linux native installs must use
  `requirements/waymo-linux.txt`.
- `docker/waymo.Dockerfile` now pins the Python base image digest and pip
  version. The Waymo package still controls its transitive dependency set, so
  this is a practical repeatability boundary, not a full hash-locked ML image.
- `.dockerignore` excludes `data/`, generated artifacts, local virtualenvs, and
  caches from the Docker build context.

### Runtime Evidence

- Docker build: `scripts/build_waymo_docker.sh` completed and exported
  `driverx-waymo:local` after pinning the Python base image digest and pip
  version.
- Import smoke:
  - `tensorflow=2.13.0`
  - `waymo_e2e_proto=ok`
  - `driverx=ok`
- Inspect smoke: `scripts/run_waymo_docker.sh` loaded frame
  `11d68b183960928432c0ab7af24ac86d-058`, wrote
  `artifacts/runs/waymo-docker-smoke-003/scene_inspection.svg`, and reported
  three front camera images.
- Baseline run: `scripts/run_waymo_docker.sh python -m driverx run-scene
  --config configs/waymo_local.sample.yaml --run-id waymo-docker-baseline-003`
  completed with mock intent, a smoothed 20-point trajectory, ADE `11.482393`,
  and dry-run submission artifacts.
- Official dependency guidance:
  - Native macOS command fails with the Docker runtime hint.
  - Docker command imports official Waymo submission deps and then fails on the
    expected missing `account_name` metadata.
  - Linux native dry-run dependency resolution with
    `python -m pip install --dry-run -r requirements/waymo-linux.txt` succeeds
    and finds `jaxlib==0.4.13`.

### QA Reconciliation

- Local package checks: PASS. `bash scripts/pre_push_check.sh` ran compileall
  plus 28 unittest cases successfully.
- Docker dependency resolution: PASS.
- Docker import smoke: PASS.
- Real validation-shard inspect path: PASS.
- Real validation-shard baseline planner path: PASS.
- Official submission dependency path: PASS.
- Linux native requirements dry-run: PASS.

### Artifact Links

- `artifacts/runs/waymo-docker-smoke-003/scene_inspection.svg`
- `artifacts/runs/waymo-docker-baseline-003/scene_prediction.svg`
- `artifacts/runs/waymo-docker-baseline-003/metrics.json`
- `docs/reviews/TASK-003-runtime-review.md`

### User Evidence

- Final verdict: dependency runtime and real-shard baseline proof passed. Final
  review passed at 4.5 / 5.0 with no blocking findings.

### Required Evidence

- [x] Unit/integration/e2e tests pass as applicable.
- [x] Docker smoke path proof captured.
