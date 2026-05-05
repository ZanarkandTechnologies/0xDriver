# TASK-025 QA Report

## Ticket

- `TASK-025`
- Scope: verify the OOD suite evidence report artifact set and focused regression surface without modifying implementation files.

## Verification basis

- Ticket: `tickets/TASK-025/ticket.md`
- Requested artifact root:
  `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/ood-suite-report`
- Upstream evidence inputs inspected:
  - `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/scenario-forge/scenario_suite_summary.json`
  - `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_route_pack.json`
  - `tickets/TASK-021/artifacts/qa/2026-05-04T220000Z/overlay-injection/overlay_injection_plan.json`
  - `tickets/TASK-023/artifacts/qa/2026-05-05T053000Z/sidecar-plan/simlingo_sidecar_plan.json`
  - `tickets/TASK-024/artifacts/2026-05-05T153000+0800/sample-sidecar-run/simlingo_sidecar_run.json`
  - `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/rag-comparison/rag_comparison.json`
  - `tickets/TASK-019/artifacts/qa/2026-05-04T200000Z/result-ingestion/simlingo_result_record.json`
  - `blockers.md`

### Exact commands run

```bash
PYTHONPATH=src python3 -m unittest tests.test_ood_suite_report tests.test_cli_ood_suite_report
PYTHONPATH=src python3 -m driverx build-ood-suite-report --scenario-summary tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/scenario-forge/scenario_suite_summary.json --route-pack tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_route_pack.json --overlay-plan tickets/TASK-021/artifacts/qa/2026-05-04T220000Z/overlay-injection/overlay_injection_plan.json --sidecar-plan tickets/TASK-023/artifacts/qa/2026-05-05T053000Z/sidecar-plan/simlingo_sidecar_plan.json --sidecar-run tickets/TASK-024/artifacts/2026-05-05T153000+0800/sample-sidecar-run/simlingo_sidecar_run.json --rag-comparison tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/rag-comparison/rag_comparison.json --simlingo-result tickets/TASK-019/artifacts/qa/2026-05-04T200000Z/result-ingestion/simlingo_result_record.json --blockers blockers.md --output-root tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/qa/2026-05-05_155859_ood-suite-verification/cli-rebuild --run-id ood-suite-report
bash scripts/pre_push_check.sh
```

## Ticket reconciliation

- Ticket Evidence claims `2` companion actors in the report proof highlights.
- The requested canonical artifact
  `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/ood-suite-report/ood_suite_manifest.json`
  reports `companion_actor_count: 0`.
- The upstream overlay plan contains `2` companion actors total, and both:
  - `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/ood-suite-report-001/ood_suite_manifest.json`
  - `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/qa/2026-05-05_155859_ood-suite-verification/cli-rebuild/ood-suite-report/ood_suite_manifest.json`
  report `companion_actor_count: 2`.
- Conclusion: implementation currently behaves correctly, but the ticket’s primary checked artifact path is stale.

## Screens covered

- Summary frame: [01-qa-summary.png](screens/01-qa-summary.png)
- Drift frame: [02-manifest-drift.png](screens/02-manifest-drift.png)

## Design intent

- Provide one compact evidence surface that reconciles scenario generation, route export, overlay planning, sidecar readiness, RAG comparison, prior SimLingo result ingestion, and live blockers.

## Verdict

- `FAIL`
- Reason: focused regression checks passed and a fresh CLI rebuild is correct, but the requested checked artifact under `ood-suite-report/` is stale on companion-actor normalization and does not cleanly satisfy the report-evidence surface the ticket points to.

## Acceptance criteria status

- `AC-1: PASS` Fresh CLI rebuild loaded all optional evidence inputs, produced `8` present components, and reported no missing components. Evidence: `logs/cli-rebuild.json`, `cli-rebuild/ood-suite-report/ood_suite_manifest.json`
- `AC-2: FAIL` The requested manifest at `ood-suite-report/ood_suite_manifest.json` exists but normalizes `companion_actor_count` incorrectly as `0` instead of `2`. Evidence: `logs/manifest-diff-old-vs-rebuild.txt`, `logs/errors.txt`
- `AC-3: FAIL` The requested markdown report at `ood-suite-report/ood_suite_report.md` repeats the stale `companion_actor_count: 0` highlight, so the checked evidence surface is inconsistent with its upstream overlay plan. Evidence: `logs/manifest-diff-old-vs-rebuild.txt`, `screens/02-manifest-drift.png`
- `AC-4: PASS` `build-ood-suite-report` CLI is present and completed successfully against the real ticket artifact inputs. Evidence: `logs/cli-rebuild.json`
- `AC-5: PASS` Focused unit and CLI tests passed: `4` tests. Evidence: `logs/focused-unittest.txt`
- `AC-6: PASS` `bash scripts/pre_push_check.sh` passed: `149` tests, lint/compile gate clean. Evidence: `logs/pre-push-check.txt`

## Top visual diffs

- No UI surface is in scope. The attached PNGs are text-summary evidence frames only.

## Top behavior diffs

- Requested artifact drift: `ood-suite-report/ood_suite_manifest.json` reports `overlay_plan.metrics.companion_actor_count = 0`.
- Fresh rebuild and `ood-suite-report-001` report `overlay_plan.metrics.companion_actor_count = 2`.
- Upstream `overlay_injection_plan.json` contains `2` `companion_actor_*` entries across two routes, so the stale artifact is the outlier.

## Missing instrumentation

- No immutable pointer marks which sibling artifact directory is canonical after reruns (`ood-suite-report` vs `ood-suite-report-001`).
- The checked evidence surface lacks a generated-at/version/hash field that would make stale report detection cheap.

## What to automate next

- Add a regression that compares generated OOD suite metrics against the upstream overlay-plan companion-actor count using the real ticket-style fixture bundle.
- Add a lightweight QA check that rejects ticket evidence when a sibling rerun differs from the advertised canonical artifact path.

## Artifacts

- Focused tests log: [focused-unittest.txt](logs/focused-unittest.txt)
- Pre-push gate log: [pre-push-check.txt](logs/pre-push-check.txt)
- CLI rebuild stdout JSON: [cli-rebuild.json](logs/cli-rebuild.json)
- Drift log, stale artifact vs rebuild: [manifest-diff-old-vs-rebuild.txt](logs/manifest-diff-old-vs-rebuild.txt)
- Drift log, `ood-suite-report-001` vs rebuild: [manifest-diff-001-vs-rebuild.txt](logs/manifest-diff-001-vs-rebuild.txt)
- QA snapshot: [snapshot.json](snapshot.json)
- Fresh rebuilt manifest: [ood_suite_manifest.json](cli-rebuild/ood-suite-report/ood_suite_manifest.json)
- Fresh rebuilt report: [ood_suite_report.md](cli-rebuild/ood-suite-report/ood_suite_report.md)

## Storyboard frames

- Frame 1: [01-qa-summary.png](screens/01-qa-summary.png)
- Frame 2: [02-manifest-drift.png](screens/02-manifest-drift.png)
