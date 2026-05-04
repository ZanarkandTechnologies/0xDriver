# Progress

Live orchestration log for 0xDriver.

## Current Goal

Build the CARLA/Fail2Drive-first minimal-shot VLA harness:

- keep the Waymo/open-loop support track archived and available
- use Fail2Drive seeds as OOD scenario sources
- generate regional behavior and object novelty
- log CARLA entity tracks and policy outputs
- compare frozen policy behavior with and without retrieved safety memory

## Completed

- [x] TASK-001 fixture-backed pipeline
- [x] TASK-002 optional real Waymo integration
- [x] TASK-003 Waymo Linux Docker runtime
- [x] TASK-004 real Waymo batch baseline
- [x] TASK-005 experiment harness and deterministic baselines
- [x] TASK-006 motion-prior hybrid planner
- [x] TASK-007 local scenario forge, memory bank, CARLA smoke, Fail2Drive dry-run planning
- [x] TASK-008 live CARLA Python API probe through Docker
- [x] TASK-009 ego spawn, camera capture, and entity tracks
- [x] TASK-010 regional driving behavior library
- [x] TASK-011 scenario-to-CARLA script compiler
- [x] TASK-012 generated asset pipeline
- [x] TASK-013 policy adapter interface
- [x] TASK-014 retrieval-augmented VLA comparison harness
- [x] TASK-015 SimLingo backend readiness and run planner
- [x] TASK-016 local CARLA 0.9.16 Docker client proof
- [x] TASK-017 remote GPU SimLingo one-route proof with precise runtime blocker

## Active Roadmap

- [ ] TASK-019 SimLingo result ingestion
- [ ] TASK-018 generated route/scenario injection into Bench2Drive/SimLingo

## Latest Evidence

- TASK-008 TCP smoke reached CARLA at `127.0.0.1:2000`.
- TASK-008 Docker probe reached CARLA through `host.docker.internal:2000`.
- Probe reported map `Carla/Maps/Town10HD_Opt`, actor count `23`, server
  version `0.9.16`, and client version `0.9.16`.
- TASK-009 live ego smoke spawned ego actor `24`, camera actor `25`, captured
  `ego_camera.png`, wrote `entity_tracks.json`, and destroyed actors `[25, 24]`.
- TASK-010 generated six OOD behavior traces covering no-signal cut-ins,
  sudden brakes, motorcycle filtering, wrong-way shoulder creep, informal
  right-of-way pushes, and fast low-profile two-wheeler proxies.
- TASK-011 compiled a generated recipe plus `motorcycle_filtering` into a
  CARLA script plan with ego actor, OOD actor, RGB sensor, ticks, expected
  outputs, and cleanup order.
- TASK-012 planned three generated OOD assets in dry-run mode, validated scale,
  collision, placement, license metadata, and emitted Meshy setup blockers when
  no API key is present.
- TASK-013 added mock, memory-aware mock, local hybrid fallback, and
  setup-checked VLM/API, SimLingo/CarLLaVA, and Alpamayo policy adapters.
- TASK-014 compared mock policy and mock+memory on the same
  `motorcycle_filtering` pressure case, improving the proxy driving score from
  `58.0` to `95.0` while keeping `live_model_claim=false`.
- TASK-015 cloned external SimLingo, inspected commit
  `743b243afd6cf5ff51b9fa1f8cac86f22d569684`, confirmed CARLA `0.9.15`,
  Python `3.8`, CUDA-required live inference, and generated a Bench2Drive
  dry-run command plan.
- TASK-016 built the Linux amd64 CARLA 0.9.16 Docker client bridge and local
  proof script for the Apple Silicon CARLA wrapper.
- TASK-017 synced the repo to a Prime Intellect RTX PRO 6000 host, installed
  CARLA 0.9.15 plus AdditionalMaps, installed SimLingo, downloaded the pinned
  checkpoint, reached CARLA route execution, and recorded the first-tick
  Blackwell `sm_120` / torch `sm_90` kernel blocker.
- TASK-019 parses the TASK-017 Bench2Drive result JSON and produces a compact
  SimLingo result report with CUDA compatibility and route-log signals.
- Full local gate during TASK-019: `bash scripts/pre_push_check.sh` passed with
  118 tests.
- Full local gate during TASK-017: `bash scripts/pre_push_check.sh` passed with
  114 tests.

## Operator Inputs

Useful soon:

- keep CARLA open for live TASK-009 proof
- Meshy or equivalent API key for real TASK-012 asset generation
- SimLingo checkpoint path or Hugging Face access
- H100/H200-class Linux NVIDIA GPU instance with CARLA 0.9.15 for the next
  stock SimLingo run; Blackwell needs a separate PyTorch/CARLA rebuild lane

Missing inputs should be logged as blockers on the relevant ticket while local
mock/dry-run work continues.
