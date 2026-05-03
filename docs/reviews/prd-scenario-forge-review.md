# PRD Review: Minimal-Shot VLA Scenario Forge

Reviewed: 2026-05-03 18:37 +0800

## Scope

- Changed files: `docs/prd.md`, `docs/MEMORY.md`, `docs/HISTORY.md`
- Rubrics: `spec-contract`, `implementation-plan`
- Context checked: current SoTA pivot, CARLA platform requirements, Apple
  Silicon CARLA wrapper discussion, Fail2Drive benchmark shape,
  SimLingo/CarLLaVA adapter path, Alpamayo model requirements.

## Verdict

Overall score: **4.2 / 5.0**

Verdict: **pass for PRD/planning handoff**

The PRD is coherent, execution-oriented, and appropriately scoped around the new
challenge objective. It avoids over-centering FlashDrive-style runtime work,
keeps Waymo as supporting evidence, and names the next concrete SLC:
dependency-light scenario generation plus retrieval memory before remote CARLA
runtime.

## Rubric Scores

### Spec Contract

Score: **4.3 / 5.0**

- Story coherence: strong. The project now solves one clear problem: evaluating
  minimal-shot closed-loop generalization with generated OOD scenarios and
  memory-guided VLA behavior.
- Scope clarity: strong. CARLA/Fail2Drive are the main path; Waymo, Alpamayo,
  and serving acceleration are explicitly staged rather than blended into the
  first slice.
- Acceptance testability: strong enough for ticketing. User stories have
  concrete fixture, parsing, report, and dry-run proof requirements.
- Remaining caveat: the PRD still needs decomposition into tickets before code
  changes resume.

### Implementation Plan

Score: **4.1 / 5.0**

- Execution order: strong. The plan starts with local fixture-compatible
  scenario/memory code, then external Fail2Drive parsing, then remote CARLA,
  then real VLA policies.
- Modularity: strong. Proposed namespaces keep scenarios, memory, simulator
  adapters, and policies independently ownable.
- Proof clarity: good. The plan defines unit tests, fixture-only QA, remote
  runtime proof, latency tables, and demo evidence.
- Risk clarity: good. It calls out CARLA install cost, dependency pinning,
  Alpamayo camera/coordinate adaptation, XML export uncertainty, and RAG
  fairness boundaries. It now also distinguishes official Linux NVIDIA runtime
  from the experimental Apple Silicon wrapper path.
- Remaining caveat: GPU/cloud specifics should be captured in the first runtime
  ticket once the provider is known.

## Findings

No blocking findings.

## Next Action

Create the first implementation ticket for **Local Scenario Forge and Memory
Harness**, keeping CARLA/Fail2Drive execution in dry-run mode until a Linux
NVIDIA GPU host is available.
