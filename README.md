# 0xDriver

0xDriver is a research engineering project for the SoTA Commission I
minimal-shot autonomy challenge. The current thesis is:

> Use CARLA/Fail2Drive to generate closed-loop long-tail scenarios, turn policy
> failures into compact safety memory, and test whether VLA/VLM policies improve
> with minimal retrieved context instead of fine-tuning.

The earlier Waymo E2E work remains in the repo as an open-loop real-data support
track. The main submission direction is now CARLA/Fail2Drive scenario
generation and evaluation.

## Project Goal

Build a minimal-shot scenario forge that can:

- load Fail2Drive route seeds or tiny local fixtures
- generate deterministic weird-but-plausible OOD scenario recipes
- build retrieval memory from closed-loop failures
- prepare CARLA/Fail2Drive dry-run command plans
- smoke-check a local CARLA server when available
- preserve Waymo ADE/batch evidence as supporting real-world context

## Core Architecture Direction

```mermaid
flowchart TD
    A["Fail2Drive routes / fixture seeds"] --> B["Scenario seed loader"]
    B --> C["OOD recipe generator"]
    C --> D["Scenario suite artifacts"]
    E["Policy result records"] --> F["Failure memory bank"]
    F --> G["Retrieved safety context"]
    C --> G
    G --> H["VLA/VLM policy prompt or adapter"]
    C --> I["CARLA/Fail2Drive dry-run command plan"]
    I --> J["Mac smoke path or Linux NVIDIA runtime"]
    K["Waymo E2E support track"] --> L["Open-loop ADE evidence"]
```

## Shared Inspiration Resources

- SoTA Commission I: Minimal-Shot Autonomy. The challenge asks for a simulation
  environment or autonomy demo, plus repo, analysis, video/deck, and motivation.
- [Fail2Drive](https://github.com/autonomousvision/fail2drive): paired
  CARLA routes for closed-loop generalization, 17 unseen scenario classes, novel
  assets, result parser, and route toolbox.
- [CARLA](https://carla.readthedocs.io/en/latest/start_introduction/): Unreal
  client/server simulator for autonomous-driving research.
- [SimLingo](https://github.com/RenzKa/simlingo): CARLA-native VLA-style policy
  target for the first real closed-loop policy proof.
- [Alpamayo 1.5](https://github.com/NVlabs/alpamayo1.5): later higher-prestige
  reasoning VLA adapter target.
- [Waymo Open Dataset](https://waymo.com/open/): retained as real logged
  open-loop evidence and trajectory baseline support.

## Repository Shape

- `docs/prd.md`: current scenario-forge PRD.
- `ARCHITECTURE.md`: top-level system map.
- `tickets/TASK-007/ticket.md`: active scenario-forge implementation ticket.
- `tickets/archive/`: completed Waymo/fixture support-track tickets.
- `src/driverx/scenarios/`: scenario seeds, recipes, and reports.
- `src/driverx/memory/`: failure memory and retrieval.
- `src/driverx/simulators/`: CARLA smoke checks and Fail2Drive command plans.
- `src/driverx/datasets/`, `planning/`, `pipeline/`, `submission/`: Waymo and
  open-loop support-track code.

## Current Status

TASK-001 through TASK-006 established a working Waymo/open-loop measuring stick:
fixture runs, optional real Waymo TFRecords through Docker, streaming batch
reports, deterministic baselines, and a hybrid semantic-intent plus motion-prior
planner.

TASK-007 starts the closed-loop pivot: scenario generation, failure memory, and
CARLA/Fail2Drive dry-run planning without requiring CARLA to be installed.
TASK-008 adds the first live CARLA Python API proof through Docker when the
local CARLA app is running.

## Quickstart: Scenario Forge

```bash
# Generate deterministic OOD scenario recipes from fixture seeds
PYTHONPATH=src python3 -m driverx forge-scenarios \
  --config configs/scenario_forge.sample.yaml \
  --count 8 \
  --seed 7

# Build compact safety memory from fixture policy failures
PYTHONPATH=src python3 -m driverx build-memory \
  --results tests/fixtures/fail2drive_like/results.json \
  --run-id memory-bank

# Plan a dry-run Fail2Drive/CARLA command from one generated recipe file
PYTHONPATH=src python3 -m driverx plan-carla-run \
  --config configs/carla_local.sample.yaml \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --recipe-id generated-base-animals-0076-visual-noise-000

# Check whether a local CARLA server is reachable
PYTHONPATH=src python3 -m driverx smoke-carla \
  --config configs/carla_local.sample.yaml

# Probe the live CARLA Python API through Docker
bash scripts/build_carla_client_docker.sh
bash scripts/run_carla_client_docker.sh python -m driverx probe-carla \
  --host host.docker.internal \
  --port 2000 \
  --run-id task8-carla-probe

# Spawn one ego vehicle/camera, capture a frame, log tracks, and clean up
bash scripts/run_carla_client_docker.sh python -m driverx spawn-ego-smoke \
  --host host.docker.internal \
  --port 2000 \
  --run-id task9-ego-smoke

# Build the local CARLA 0.9.16 client image and run both live proofs
bash scripts/prove_carla_0916_docker.sh

# If Docker times out on host.docker.internal:2000, the client image is still
# valid; keep CARLA.app open, wait for the town to finish loading, and rerun.
# Use DRIVERX_DOCKER_ENV_FILE=.env only when a container needs local env vars.

# Generate regional/OOD behavior traces and metrics
PYTHONPATH=src python3 -m driverx generate-behaviors \
  --run-id task10-behaviors

# Compile one generated recipe and behavior into a CARLA script plan
PYTHONPATH=src python3 -m driverx compile-carla-script \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --recipe-id generated-base-animals-0076-visual-noise-000 \
  --behavior-id motorcycle_filtering \
  --run-id task11-carla-script

# Plan generated OOD assets and attach asset ids to scenario recipes
PYTHONPATH=src python3 -m driverx plan-assets \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --run-id task12-assets

# Run a fixture through the policy adapter surface
PYTHONPATH=src python3 -m driverx run-policy-fixture \
  --policy mock \
  --with-memory \
  --run-id task13-policy-memory

# Compare a policy with and without retrieved safety memory
PYTHONPATH=src python3 -m driverx run-rag-comparison \
  --policy mock \
  --run-id task14-rag

# Inspect and plan the external SimLingo/CarLLaVA backend
PYTHONPATH=src python3 -m driverx inspect-simlingo \
  --run-id task15-simlingo-readiness
PYTHONPATH=src python3 -m driverx plan-simlingo-run \
  --config configs/simlingo.sample.yaml \
  --run-id task15-simlingo-plan
PYTHONPATH=src python3 -m driverx ingest-simlingo-result \
  --result tickets/TASK-017/artifacts/qa/2026-05-04T194700Z/seed_1_res.json \
  --compatibility tickets/TASK-017/artifacts/qa/2026-05-04T194700Z/torch_cuda_compatibility.json \
  --route-log tickets/TASK-017/artifacts/qa/2026-05-04T194700Z/run_one_route.log \
  --run-id task19-simlingo-result

# On a Linux NVIDIA GPU host, sync this repo and launch the SimLingo bootstrap
# in tmux. `HF_TOKEN` is read from the local environment or ignored `.env`,
# copied through a temporary remote file, then that temporary file is removed
# after the tmux job starts. Existing host Hugging Face login state is preserved.
bash scripts/sync_remote_gpu.sh root@31.22.104.74 /workspace/0xDriver
bash scripts/run_remote_simlingo_bootstrap.sh root@31.22.104.74 /workspace/0xDriver
```

Stock SimLingo currently targets Python 3.8 and `torch==2.2.0+cu121`. That
works best on CUDA architectures already compiled into that wheel, especially
H100/H200-class `sm_90` hosts. RTX PRO 6000 Blackwell requires `sm_120`, so it
needs a separate PyTorch/CARLA rebuild lane before it can run the stock route.

Generated run artifacts are written under `artifacts/runs/` and remain ignored
by git.

## External Fail2Drive Checkout

Fail2Drive and SimLingo are used as read-only external references, not vendored
into this repo:

```bash
mkdir -p ../external
git clone https://github.com/autonomousvision/fail2drive.git ../external/fail2drive
git clone https://github.com/RenzKa/simlingo.git ../external/simlingo
```

`configs/carla_local.sample.yaml` defaults to `../external/fail2drive`. The
SimLingo planner defaults to `../external/simlingo`. Local tests use tiny
fixtures, so they do not require CARLA, Conda, model checkpoints, or CUDA.

## Optional CARLA On Apple Silicon

CARLA can reportedly run on Apple Silicon through a community
Wine/Kegworks/D3DMetal wrapper for the Windows CARLA package. Treat that as a
local smoke-test path until CARLA server, Python client, Fail2Drive routes, and
policy execution all work together.

For reproducible Fail2Drive + VLA experiments, use Linux NVIDIA hardware.

## Waymo Support Track

The existing Waymo commands remain available:

```bash
PYTHONPATH=src python3 -m driverx inspect-scene --config configs/mock.yaml
PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml --run-id demo
PYTHONPATH=src python3 -m driverx run-batch --config configs/mock.yaml --run-id demo-batch
PYTHONPATH=src python3 -m driverx run-experiment --config configs/mock.yaml --run-id demo-experiment
bash scripts/pre_push_check.sh
```

Real Waymo TFRecords still use the Docker compatibility bridge documented by
the archived TASK-003 through TASK-006 evidence.
