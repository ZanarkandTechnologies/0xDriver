# PRD: Latency-Aware Minimal-Shot Driving Pipeline

## Problem / Context

Minimal-shot autonomy asks whether a vehicle can handle rare, unfamiliar
scenarios without memorizing a heavily collected map or dataset. Recent VLA work
suggests large visual reasoning models can help with long-tail scene
understanding, but running them naively as an end-to-end driver is too slow and
too brittle for a credible near-term submission.

0xDriver should demonstrate an engineering thesis instead: use a slow general
VLA/VLM reasoner to produce compact driving intent, then compile that intent
into fast, constrained trajectory proposals that can be evaluated on Waymo E2E
frames.

## Audience

- Primary: SoTA Commission I judges evaluating novelty, feasibility, technical
  excellence, and adherence to the minimal-shot autonomy brief.
- Secondary: autonomy engineers reviewing whether the architecture is credible
  and reproducible.
- Internal: the project owner using the repo to test how far an agent can take
  the concept from inspiration to submission package.

## JTBD

When I have a rare Waymo E2E driving scene and limited time before submission, I
want a VLA-inspired pipeline that produces explainable 5-second ego trajectory
predictions, so I can demonstrate minimal-shot driving behavior without training
a new model from scratch.

## SLC Slice (Next Release)

Build the first complete offline Waymo E2E research loop:

1. Load a small validation subset from Waymo E2E TFRecords.
2. Render front-camera panels with ego future trajectory overlays.
3. Produce structured scene intent using a mockable VLA/VLM reasoner interface.
4. Generate candidate 20-point trajectories for 5 seconds at 4 Hz.
5. Smooth/rank the trajectories with deterministic constraints.
6. Compute local ADE against validation labels.
7. Package dry-run submission protobuf shards.
8. Produce analysis/demo evidence showing successes, failure cases, and latency
   accounting.

This slice is useful before full model acceleration because it proves the data,
evaluation, artifact, and architecture loop end to end.

## Goals

- Produce a repo structure that can support a SoTA submission package.
- Demonstrate an offline Waymo E2E pipeline on at least one real or fixture-backed
  frame before scaling.
- Keep VLA/VLM integration swappable across mock, API, and cloud GPU backends.
- Record raw intent, pre-smooth trajectory, post-smooth trajectory, metrics, and
  latency for every evaluated scene.
- Make the final story honest: deployment-aware VLA planning, not a claim of
  production-grade self-driving.

## Non-Goals

- Train a VLA model from scratch.
- Fine-tune Alpamayo, OpenPI, or other large models in the first slice.
- Build a real-time closed-loop autonomous vehicle stack in v1.
- Optimize CUDA kernels, quantization kernels, or speculative decoding in v1.
- Check in Waymo dataset shards, generated videos, model weights, or cloud
  credentials.
- Build a web UI before the notebook/demo evidence path exists.

## User Stories

### US-001: Load And Inspect Waymo E2E Scenes

**Description:** As a researcher, I want to load Waymo E2E frames and inspect
camera views plus ego trajectories so that I can understand the input and label
shape before model work.

**Acceptance Criteria:**

- [ ] A documented command or notebook cell loads at least one E2E frame.
- [ ] The front-left, front, and front-right camera strip renders successfully.
- [ ] Ground-truth future ego waypoints are projected or overlaid for inspection.
- [ ] Missing dataset path errors explain how to configure the local data root.

### US-002: Produce Structured VLA Driving Intent

**Description:** As an autonomy engineer, I want the model output to be compact
validated JSON so that trajectory code can use it safely without parsing prose.

**Acceptance Criteria:**

- [ ] The reasoner contract includes scene type, hazards, ego intent, target
  behavior, speed profile, lateral bias, and uncertainty.
- [ ] A mock reasoner can run without cloud GPU access.
- [ ] Invalid reasoner output fails closed and records a validation error.
- [ ] The raw intent is saved as evidence for each evaluated frame.

### US-003: Generate And Smooth Trajectory Candidates

**Description:** As a builder, I want deterministic trajectory candidates around
the VLA intent so that the system can produce valid 20-point predictions even
when the model is uncertain or slow.

**Acceptance Criteria:**

- [ ] Candidate generation outputs one or more `(20, 2)` trajectories.
- [ ] Smoothing enforces basic continuity and avoids obvious waypoint jumps.
- [ ] Fallback behavior exists for unavailable or low-confidence model output.
- [ ] Pre-smooth and post-smooth trajectories are saved for comparison.

### US-004: Evaluate And Package Submission Artifacts

**Description:** As a challenge participant, I want local metrics and dry-run
submission packaging so that the repo can become a real submission instead of a
demo-only script.

**Acceptance Criteria:**

- [ ] ADE is computed over a small validation sample.
- [ ] Submission protobuf shards can be generated from predictions.
- [ ] A latency table separates loading/rendering, reasoning, planning,
  smoothing, scoring, and packaging.
- [ ] The analysis notebook or report includes at least one understood failure
  case.

## Functional Requirements

- FR-1: The system must treat Waymo dataset paths as configuration, not hardcoded
  repo paths.
- FR-2: The reasoner must support at least mock and future real-model backends.
- FR-3: Reasoner output must be validated before planner use.
- FR-4: Trajectory generation must output exactly 20 future `(x, y)` points for
  the Waymo E2E submission path.
- FR-5: Evaluation must include ADE as a local proxy metric.
- FR-6: Evidence artifacts must connect scene input, structured intent, raw
  trajectory, smoothed trajectory, metrics, and latency.
- FR-7: The pipeline must allow cloud GPU inference without making cloud network
  latency part of the offline Waymo evaluation claim.

## Constraints

- Security/privacy: do not commit credentials, dataset shards, generated
  submission archives, or model weights.
- Performance: v1 must measure latency honestly but does not need to hit
  real-time control rates.
- Platform: local development happens on a MacBook with 48GB unified memory;
  CUDA/Triton acceleration requires rented NVIDIA GPU hardware.
- Budget/time: optimize for a May 10, 2026 challenge deadline and a demo-worthy
  first release rather than model research depth.
- Reproducibility: every evidence artifact should be traceable to frame name,
  config, reasoner backend, and timestamp.

## Risks / Unknowns

- Waymo E2E data access and download size may slow implementation.
- Current Waymo Python package constraints may force Python/TensorFlow version
  choices.
- Real VLA/VLM backends may produce weak driving intent without prompt and
  schema iteration.
- Cloud GPU setup may take longer than the core offline pipeline.
- Rater feedback metric is not fully available locally, so ADE and qualitative
  evidence remain proxy checks.

## Backpressure / Evidence to Ship

- Tests: unit tests for schema validation, trajectory shape, smoothing bounds,
  ADE calculation, and submission packing once code exists.
- QA: tiny-run smoke test that executes loader or fixture, mock reasoner,
  planner, evaluator, and artifact writer.
- Perf checks: latency report per stage; cloud VLA timing recorded separately
  from local planning/smoothing.
- Demo proof: rendered input panel, intent JSON, predicted trajectory overlay,
  ADE table, one failure case, and final architecture diagram.
