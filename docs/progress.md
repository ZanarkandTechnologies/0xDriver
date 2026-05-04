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

## Active Roadmap

- [ ] TASK-011 scenario-to-CARLA script compiler
- [ ] TASK-012 generated asset pipeline
- [ ] TASK-013 policy adapter interface
- [ ] TASK-014 retrieval-augmented VLA comparison harness

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
- Full local gate after TASK-008: `bash scripts/pre_push_check.sh` passed with
  61 tests.

## Operator Inputs

Useful soon:

- keep CARLA open for live TASK-009 proof
- Meshy or equivalent API key for real TASK-012 asset generation
- real VLA target/checkpoint/API for TASK-013/TASK-014
- cloud GPU budget/provider for reproducible Fail2Drive + VLA runs

Missing inputs should be logged as blockers on the relevant ticket while local
mock/dry-run work continues.
