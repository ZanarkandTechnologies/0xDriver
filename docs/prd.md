# PRD: Minimal-Shot VLA Scenario Forge

## Problem / Context

SoTA Commission I rewards autonomy systems that generalize to unfamiliar
environments with little or no task-specific data. The previous 0xDriver slice
proved useful Waymo E2E infrastructure, but an offline trajectory benchmark alone
does not fully satisfy the challenge prompt to create a simulation environment
with randomized scenario generation.

The project should now center on a closed-loop CARLA/Fail2Drive-style testbed:
use CARLA as the simulation engine, Fail2Drive as the seed OOD benchmark, and
0xDriver as the agentic layer that generates new long-tail scenarios, records
VLA/VLM policy behavior, extracts failures into a retrieval memory, and reruns
policies with that memory as compact minimal-shot guidance.

The thesis is:

> Minimal-shot autonomy should improve by reasoning from abstract prior
> experience, not by fine-tuning on every edge case. We turn closed-loop OOD
> failures into reusable safety memory, generate harder variants, and measure
> whether VLA policies transfer the lesson.

## Audience

- Primary: SoTA Commission I judges evaluating novelty, feasibility, technical
  excellence, and adherence to the minimal-shot autonomy brief.
- Secondary: autonomy researchers comparing VLA/VLM policies under closed-loop
  distribution shift.
- Internal: the project owner using a local Mac for orchestration and a rented
  Linux GPU box for CARLA/VLA runtime proof.

## JTBD

When I want to test whether a minimal-shot driving policy can handle unfamiliar
long-tail cases, I want a reproducible CARLA scenario forge that generates
paired in-distribution/OOD cases, runs a VLA/VLM policy, stores the failures as
retrieval memory, and reruns generated variants, so I can demonstrate
generalization without training a new AV model from scratch.

## SLC Slice (Next Release)

Build the first dependency-light **Scenario Forge + Memory Harness** that can run
locally without CARLA, then has explicit adapters for a remote CARLA/Fail2Drive
runtime.

The smallest complete valuable slice:

1. Ingest Fail2Drive route and result metadata from a configured external
   checkout or fixture.
2. Represent paired base/generalization scenarios as typed scenario records.
3. Generate new OOD scenario recipes from seed cases using deterministic
   mutation policies.
4. Build a retrieval memory bank from Fail2Drive failure summaries and future
   run results.
5. Produce a report that shows scenario coverage, generated variants, memory
   entries, expected policy probes, and readiness for CARLA execution.
6. Preserve Waymo E2E as supporting real-world open-loop evidence, not the main
   simulation environment.

This slice is useful before running CARLA because it locks the core data model,
scenario-generation algorithm, and evidence surfaces while the Mac cannot run the
official CARLA server locally.

## Goals

- Reframe 0xDriver as a minimal-shot closed-loop evaluation environment rather
  than only a Waymo offline predictor.
- Use CARLA/Fail2Drive as the first simulation target because CARLA has mature
  route/scenario tooling and Fail2Drive already defines paired OOD evaluation.
- Generate OOD scenario recipes that can later be exported into Fail2Drive route
  XML or a companion scenario hub.
- Build a retrieval memory format that injects abstract safety lessons into VLA
  prompts or policy adapters without fine-tuning.
- Support SimLingo/CarLLaVA as the first CARLA-native VLA baseline, with
  Alpamayo as a later higher-prestige trajectory-VLA adapter.
- Keep realistic compute and latency visible: local scenario/report work on Mac,
  CARLA/VLA runtime on a Linux NVIDIA GPU host, and model-serving timings logged
  separately from simulator timings.

## Non-Goals

- Do not build a new physics/rendering engine; CARLA is the simulation engine.
- Do not make Apple Silicon CARLA the critical runtime path. A community
  Wine/Kegworks wrapper may be explored as an optional local smoke-test path,
  but official/reproducible benchmark execution should still target Linux
  NVIDIA hardware unless the wrapper proves stable with Fail2Drive.
- Do not fine-tune Alpamayo, SimLingo, Qwen, LLaVA, or any AV model.
- Do not adapt Alpamayo weights into LLaVA/CarLLaVA architecture.
- Do not claim official Fail2Drive leaderboard fairness for RAG-assisted runs
  that use Fail2Drive failures as memory.
- Do not convert Waymo E2E scenes into CARLA or AlpaSim scenes in the first
  slice.
- Do not optimize CUDA kernels, quantization, speculative decoding, or
  FlashDrive-style runtime acceleration until the closed-loop evaluation loop
  exists.

## User Stories

### US-001: Ingest Fail2Drive Seeds

**Description:** As a researcher, I want to load Fail2Drive route/result metadata
so that existing paired OOD cases become the seed set for generation and memory.

**Acceptance Criteria:**

- [ ] A documented command reads a configured Fail2Drive checkout path or local
  fixture without committing external benchmark assets.
- [ ] Scenario records preserve split (`Base` or `Generalization`), scenario
  class, route id, source file, and known metrics when result JSON exists.
- [ ] Missing external paths fail with actionable setup guidance.
- [ ] The fixture path passes without CARLA, TensorFlow, or GPU dependencies.

### US-002: Generate OOD Scenario Recipes

**Description:** As a challenge participant, I want an agentic generator to
produce weird-but-plausible scenario variants so that the simulation environment
goes beyond static benchmark replay.

**Acceptance Criteria:**

- [ ] Generator outputs deterministic recipes from a seed id and random seed.
- [ ] Recipes include scenario family, mutation type, actors/assets, placement
  intent, expected failure mode, and solvability assumption.
- [ ] Supported first mutations include obstacle substitution, occlusion,
  misleading visual texture, irrelevant hazard outside ego path, lane blockage,
  and regional driving behavior such as motorcycle filtering.
- [ ] Generated recipes are written as JSON/Markdown evidence and can later be
  exported to Fail2Drive XML.

### US-003: Build Retrieval Safety Memory

**Description:** As a minimal-shot policy designer, I want prior OOD failures
compressed into abstract driving lessons so that a frozen VLA can reason with
few-shot context instead of being fine-tuned.

**Acceptance Criteria:**

- [ ] Memory entries include situation, observed failure, abstract principle,
  recommended behavior, source scenario, and confidence.
- [ ] Retrieval can select the top relevant entries from current scenario tags
  or policy-observed uncertainty.
- [ ] Prompt snippets are short enough to fit into a VLA/VLM context without
  turning into verbose chain-of-thought.
- [ ] Reports compare intended policy behavior with and without memory context.

### US-004: Prepare CARLA/Fail2Drive Execution Adapter

**Description:** As an engineer, I want a clean adapter boundary between
0xDriver and a remote CARLA runtime so that the Mac can author scenarios while a
Linux GPU host runs the simulator and policies.

**Acceptance Criteria:**

- [ ] Adapter config names CARLA host, Fail2Drive root, route path, agent path,
  policy kind, output directory, and expected result parser.
- [ ] Local dry-run mode emits the exact command plan without launching CARLA.
- [ ] Result ingestion understands Fail2Drive/CARLA JSON records for driving
  score, route completion, infractions, and success.
- [ ] Runtime notes distinguish simulator GPU requirements from VLA inference
  GPU requirements.

### US-005: Keep Waymo E2E As Supporting Evidence

**Description:** As a reviewer, I want the existing Waymo E2E pipeline preserved
so that the submission can show both real logged long-tail evidence and
closed-loop generated simulation evidence.

**Acceptance Criteria:**

- [ ] Existing Waymo fixture and real batch commands remain documented.
- [ ] Future VLA/Alpamayo comparisons can still use the current hybrid planner
  baseline and ADE reports.
- [ ] The README/PRD does not imply Waymo E2E is a closed-loop simulator.

## Functional Requirements

- FR-1: The system must treat CARLA, Fail2Drive, SimLingo, Alpamayo, and Waymo
  paths as configuration, not checked-in repo assets.
- FR-2: Scenario seed ingestion must support fixture mode and external checkout
  mode.
- FR-3: Generated scenario recipes must be deterministic under an explicit seed.
- FR-4: Memory entries must be serializable JSON and human-readable Markdown.
- FR-5: Reports must show base vs OOD scenario coverage, generated variants,
  retrieved memory, expected behavior, and open runtime blockers.
- FR-6: The first CARLA adapter must be policy-agnostic: SimLingo first,
  Alpamayo later, generic VLM/API mode optional.
- FR-7: Alpamayo integration must be represented as a trajectory policy adapter,
  not as a LLaVA/CarLLaVA model-weight conversion.
- FR-8: Latency accounting must separate scenario generation, retrieval,
  simulator step time, model inference time, trajectory/control conversion, and
  result parsing.
- FR-9: No dataset shards, simulator binaries, generated videos, model weights,
  secrets, or submission archives may be committed.

## Technical Planning Notes

### Recommended Build Path

1. **TASK-007:** Local Scenario Forge and Memory Harness.
2. **TASK-008:** Fail2Drive external checkout adapter and route/result parser.
3. **TASK-009:** Remote CARLA command runner with dry-run and result ingestion.
4. **TASK-010:** SimLingo/CarLLaVA baseline execution on a small Fail2Drive
   route subset.
5. **TASK-011:** Alpamayo adapter spike: CARLA observations to Alpamayo tensors,
   Alpamayo trajectory to SimLingo-style PID control.
6. **TASK-012:** Retrieval-augmented VLA comparison and generated OOD demo.
7. **TASK-013:** Optional runtime acceleration: async inference, caching,
   smaller model/API mode, quantization, or FlashDrive-inspired serving.

### Adapter Targets

- `driverx.scenarios`: owns seed records, generated recipes, and mutation
  policies.
- `driverx.memory`: owns failure memory entries, retrieval, and prompt snippets.
- `driverx.simulators.fail2drive`: owns Fail2Drive route/result parsing and
  command-plan generation.
- `driverx.simulators.carla`: owns CARLA runtime config, remote host command
  templates, and result collection.
- `driverx.policies`: future adapter namespace for `simlingo`, `alpamayo`,
  `bench2drive_vl_api`, and existing local hybrid planner.

### Signature Delta Sketch

```python
load_fail2drive_routes(root: Path) -> list[ScenarioSeed]
load_fail2drive_results(results_root: Path) -> list[ScenarioResult]
generate_scenario_recipes(
    seeds: list[ScenarioSeed],
    policy: MutationPolicy,
    count: int,
    random_seed: int,
) -> list[ScenarioRecipe]
build_memory_bank(results: list[ScenarioResult]) -> MemoryBank
retrieve_memory(recipe: ScenarioRecipe, bank: MemoryBank, limit: int) -> list[MemoryEntry]
plan_carla_run(config: CarlaRunConfig, recipe: ScenarioRecipe) -> CarlaCommandPlan
summarize_scenario_suite(records: list[ScenarioRecord]) -> ScenarioSuiteSummary
```

### Type Sketch

```python
ScenarioSeed = {
  "seed_id": str,
  "source": "fail2drive" | "fixture" | "generated",
  "split": "Base" | "Generalization",
  "scenario_class": str,
  "route_id": str,
  "route_path": str,
  "ood_tags": list[str],
}

ScenarioRecipe = {
  "recipe_id": str,
  "parent_seed_id": str,
  "mutation": str,
  "actors": list[dict],
  "environment": dict,
  "expected_failure_mode": str,
  "memory_query": list[str],
  "export_targets": ["fail2drive_xml"],
}

MemoryEntry = {
  "entry_id": str,
  "situation": str,
  "observed_failure": str,
  "principle": str,
  "recommended_behavior": str,
  "source_scenario": str,
  "confidence": float,
}

ScenarioResult = {
  "scenario_id": str,
  "policy": str,
  "driving_score": float | None,
  "route_completion": float | None,
  "infractions": dict[str, list[str]],
  "success": bool,
  "latency_ms": dict[str, float],
}
```

### Typed Flow Example

`Base_Animals_0075.xml` and `Generalization_Animals_0075.xml`
-> `ScenarioSeed(split="Base")` + `ScenarioSeed(split="Generalization")`
-> result parser records that a policy fails the OOD animal crossing
-> `MemoryEntry(principle="unknown animate object on route is occupied space")`
-> generator creates `Generated_Animals_0075_haze_motorcycle_01`
-> retrieval injects the memory principle into the VLA prompt
-> remote CARLA run compares policy vs policy+memory
-> report shows whether route completion, infractions, and success improved.

## Operator Inputs Needed Upfront

To let the agent work autonomously, the project needs these decisions or assets
as soon as they become relevant:

1. A Linux NVIDIA GPU runtime for reproducible CARLA/Fail2Drive execution. A
   community Apple Silicon wrapper exists and can be tried for local smoke
   tests, but it should not block or replace the official runtime path until it
   proves stable with the Python client and Fail2Drive stack.
2. Whether to use Fail2Drive full install, plugin branch, or a separate external
   checkout mounted outside this repo.
3. Whether first real policy should be SimLingo/CarLLaVA, Bench2Drive-VL API
   mode, or Alpamayo. Default recommendation: SimLingo first, Alpamayo second.
4. Hugging Face access for any model checkpoints or simulator assets that
   require gated downloads.
5. A small initial route subset for first live proof, such as `Animals`,
   `PedestriansOnRoad`, `CustomObstacles`, and `ObscuredStop`.
6. Budget ceiling for cloud GPU experiments and whether long-running CARLA jobs
   can use a rented instance overnight.
7. Whether the final submission should be a 1-5 minute video or a slide deck.
   Default recommendation: video with a short backup deck.

## Constraints

- Security/privacy: do not commit credentials, model weights, dataset shards,
  simulator binaries, generated videos, or private cloud instance details.
- Performance: local planner/report steps should run on Mac; CARLA and heavy
  VLA inference should run on Linux NVIDIA hardware with explicit timing logs.
- Platform: CARLA packaged server is officially built for Windows/Linux and
  expects a dedicated GPU. A community Apple Silicon path runs the Windows
  CARLA package through Wine/Kegworks/D3DMetal and has reported M4 results, so
  the MacBook M5 Pro may be viable for exploratory local smoke tests. Treat that
  path as experimental until CARLA server, Python client, Fail2Drive routes, and
  policy execution all work together.
- Budget/time: prioritize a credible SLC before May 10, 2026: local scenario
  generation + memory + at least one real/simulated route proof.
- Reproducibility: every generated scenario, memory entry, command plan, and
  result report must include source ids, config, random seed, and timestamp.
- Fairness: using Fail2Drive failures as RAG memory is an experimental
  minimal-shot method, not a leaderboard-clean Fail2Drive score.

## Risks / Unknowns

- CARLA/Fail2Drive installation can consume hours on a fresh GPU machine.
- The Apple Silicon CARLA wrapper may run the simulator but still fail on client
  control, Python package compatibility, offscreen rendering, or Fail2Drive
  integration.
- SimLingo and Bench2Drive-VL have dependency stacks tied to specific CARLA,
  Python, PyTorch, CUDA, and leaderboard versions.
- Alpamayo-to-CARLA adaptation may need nontrivial camera-rig and coordinate
  conversions before control is stable.
- Fail2Drive route XML export may need direct compatibility checks before
  generated recipes can become executable scenarios.
- RAG memory can cause over-specific behavior if prompts quote benchmark cases
  instead of abstract safety principles.
- A short deadline may require the Alpamayo adapter and serving acceleration to
  remain explicit extensions rather than the first demo path.

## Backpressure / Evidence to Ship

- Tests: unit tests for seed parsing, result parsing, deterministic generation,
  memory retrieval, report writing, and dry-run command planning.
- QA: fixture-only scenario-suite run that produces JSON/Markdown artifacts
  without CARLA.
- Runtime proof: at least one remote CARLA/Fail2Drive route pair once GPU
  access exists.
- Perf checks: latency table separating scenario generation, retrieval,
  simulator runtime, policy inference, control conversion, and result parsing.
- Demo proof: generated scenario table, memory entry, policy run result,
  failure explanation, and a visual/video artifact from CARLA or Fail2Drive.
- Review proof: code review and QA evidence attached to each implementation
  ticket after this PRD is decomposed.

## References

- [CARLA packaged install docs](https://carla.readthedocs.io/en/0.9.16/start_quickstart/):
  CARLA is built for Windows/Linux, recommends a dedicated GPU, and launches an
  Unreal spectator/server process.
- [CARLA introduction](https://carla.readthedocs.io/en/latest/start_introduction/):
  CARLA is an Unreal-based client/server simulator with Python/C++ control APIs.
- [Apple Silicon CARLA community discussion](https://github.com/carla-simulator/carla/discussions/9037)
  and linked guide: reports Windows CARLA packages running on M-series Macs via
  Wine/Kegworks/D3DMetal, with Python client support still handled through
  workarounds.
- [Fail2Drive paper](https://arxiv.org/abs/2604.08535) and
  [Fail2Drive repo](https://github.com/autonomousvision/fail2drive): paired
  in-distribution/generalization routes, 17 unseen scenario classes, 30 novel
  assets, result parser, and custom scenario toolbox.
- [SimLingo paper](https://arxiv.org/abs/2503.09594) and
  [SimLingo repo](https://github.com/RenzKa/simlingo): CARLA-native VLA-style
  policy surface and closed-loop evaluation stack.
- [CarLLaVA paper](https://arxiv.org/abs/2406.10165): camera-only
  closed-loop VLM driving precedent for CARLA.
- [Alpamayo 1.5 repo](https://github.com/NVlabs/alpamayo1.5) and
  [Hugging Face model card](https://huggingface.co/nvidia/Alpamayo-1.5-10B):
  reasoning VLA that outputs 6.4-second trajectories and should be adapted
  through a policy wrapper, not model-weight conversion.
- Waymo E2E: real long-tail logged camera evidence; useful support track, not a
  closed-loop simulator.
