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
- [x] TASK-019 SimLingo result ingestion
- [x] TASK-018 generated Bench2Drive route pack export
- [x] TASK-021 overlay injection dry-run plan
- [x] TASK-022 live companion actor injector interface
- [x] TASK-023 SimLingo sidecar orchestration plan
- [x] TASK-024 local timed sidecar process runner
- [x] TASK-025 OOD suite evidence report
- [x] TASK-026 remote SimLingo evidence classifier
- [x] TASK-027 OOD suite remote evidence ingestion
- [x] TASK-028 GPU host suitability report

## Active Roadmap

- [x] TASK-020 H100/H200 stock SimLingo rerun reached artifact-backed CARLA
  graphics/Vulkan blocker
- [ ] TASK-024 live timed sidecar execution on H100/H200 after TASK-020
- [ ] live H100-generated suite execution after TASK-020

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
- TASK-018 exports generated OOD recipes to stock-compatible Bench2Drive route
  XML, DriverX sidecar overlays, and a SimLingo command plan with an absolute
  `--routes` path.
- TASK-021 compiles TASK-018 sidecar overlays into dry-run companion CARLA
  actor/sensor/tick plans with `2` routes, distinct overlay actors
  (`occluder`, `distractor`), route-specific companion blueprints
  (`static.prop.streetbarrier`, `static.prop.trafficwarning`), preserved
  runtime contracts, `25` behavior samples plus `1` companion spawn tick per
  route (`26` ticks total), and zero validation errors.
- TASK-022 consumes a TASK-021 plan, spawns only `companion_actor_*` overlays,
  applies their planned ticks, writes entity tracks, and cleans up the spawned
  actors. Local native evidence records the expected missing-`carla` package
  setup blocker; fake-CARLA tests prove spawn/tick/track/cleanup behavior.
- TASK-023 pairs the TASK-018 SimLingo command plan with the TASK-021 overlay
  injection plan into a manual two-process sidecar launch plan, preserving
  SimLingo blockers, DriverX overlay validation state, expected outputs, and a
  Docker CARLA-client command for local overlay injection.
- TASK-020 RunPod H100 direct TCP SSH is reachable with x86_64 Linux, H100
  80GB HBM3, driver `580.126.09`, and persistent `/workspace`; root disk is
  only `20G`, so conda, cache, models, CARLA, and artifacts must stay under
  `/workspace`.
- TASK-020 now has `scripts/pull_remote_simlingo_artifacts.sh` so compact H100
  evidence can be pulled back without copying model weights, CARLA files,
  archives, media, caches, or generated videos into the repo.
- TASK-020 now has `scripts/run_remote_simlingo_route.sh` so the generated
  remote stock-route script can be launched, logged, and followed by compact
  artifact pullback whether it succeeds or hits a precise runtime blocker.
- TASK-026 adds `summarize-simlingo-evidence`, a local classifier for pulled
  H100 SimLingo artifacts. It detects missing roots, incomplete/completed
  bootstraps, route logs, CUDA compatibility JSON, `*_res.json` route results,
  and writes a compact JSON/Markdown verdict without requiring CARLA,
  SimLingo, TensorFlow, or a GPU.
- TASK-020 H100 route wrapper pulled compact live evidence. CUDA compatibility
  is good for SimLingo on H100 (`sm_90`), but CARLA 0.9.15 exits before
  opening port `20000`; diagnostics show default Vulkan only exposes
  `llvmpipe` and the NVIDIA Vulkan ICD fails with
  `ERROR_INCOMPATIBLE_DRIVER`. This blocks closed-loop route proof on the
  current H100 container before model inference begins.
- TASK-027 lets the OOD suite report consume both old TASK-019
  `simlingo_result_record.json` artifacts and new TASK-026
  `remote_simlingo_evidence.json` artifacts. Current report evidence now
  surfaces `simlingo_state=route_infrastructure_blocked`, the H100 route log,
  the CARLA runtime diagnostics path, and the TASK-020 CARLA/Vulkan blocker in
  one top-level manifest.
- TASK-028 adds `assess-gpu-host`, a local host suitability report over
  torch/CUDA compatibility, CARLA graphics diagnostics, pulled SimLingo
  evidence, and optional GPU snapshots. Current H100 evidence is classified as
  `blocked`: SimLingo CUDA support is ready for `sm_90`, but CARLA graphics are
  blocked by the Vulkan/port failure; the report recommends a graphics-capable
  NVIDIA host instead of another compute-only H100/H200 container.
- TASK-024 adds `run-simlingo-sidecar`, a timed process runner for existing
  TASK-023 plans. Local evidence executed harmless SimLingo/overlay sample
  commands, wrote process logs, timings, exit codes, JSON, and Markdown.
- TASK-025 adds `build-ood-suite-report`, a single manifest/report over the
  generated scenario summary, Bench2Drive route pack, overlay plan, sidecar
  plan/run evidence, RAG comparison, SimLingo result, and blocker ledger.
  Current evidence reports `2` generated recipes, `2` route-pack routes, `2`
  companion actors, sidecar runner success, mock RAG score delta `37.0`, and
  the prior RTX PRO 6000 SimLingo CUDA blocker while TASK-020 reruns on H100.
- Focused local tests during TASK-024:
  `PYTHONPATH=src python3 -m unittest tests.test_simlingo_sidecar_runner tests.test_cli_simlingo_sidecar_runner`
  passed with 4 tests.
- Full local gate during TASK-024: `bash scripts/pre_push_check.sh` passed with
  143 tests.
- Focused local tests during TASK-020 pullback helper:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_docker_scripts` passed
  with 13 tests, including a local execution fixture for the compact pullback
  allowlist, heavy-directory exclusions, and non-zero remote route wrapper
  pullback/exit-code behavior.
- Full local gate during TASK-020 pullback helper:
  `bash scripts/pre_push_check.sh` passed with 154 tests after the route
  wrapper was added.
- Focused local tests during TASK-023:
  `PYTHONPATH=src python3 -m unittest tests.test_simlingo_sidecar tests.test_cli_simlingo_sidecar`
  passed with 4 tests.
- Full local gate during TASK-023: `bash scripts/pre_push_check.sh` passed with
  139 tests.
- Focused local tests during TASK-022:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_injection tests.test_cli_carla_injection`
  passed with 5 tests.
- Full local gate during TASK-022: `bash scripts/pre_push_check.sh` passed with
  135 tests.
- Full local gate during TASK-021: `bash scripts/pre_push_check.sh` passed with
  130 tests.
- Full local gate during TASK-018: `bash scripts/pre_push_check.sh` passed with
  125 tests.
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
