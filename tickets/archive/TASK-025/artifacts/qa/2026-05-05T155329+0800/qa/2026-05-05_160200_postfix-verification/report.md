# TASK-025 Post-Fix QA

Verdict: PASS

## Evidence

- Focused tests: `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/qa/2026-05-05_160200_postfix-verification/logs/focused-unittest.txt`
- Local gate: `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/qa/2026-05-05_160200_postfix-verification/logs/pre-push-check.txt`
- Canonical manifest: `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/ood-suite-report/ood_suite_manifest.json`
- Canonical report: `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/ood-suite-report/ood_suite_report.md`

## Checks

- companion_actor_count: `2`
- generated_recipe_count: `2`
- bench2drive_route_count: `2`
- sidecar_run_success: `True`
- rag_driving_score_delta: `37.0`
- has_open_blockers: `True`
- open_blocker_count: `4`

The open blockers are intentionally preserved downstream runtime blockers from
sidecar and SimLingo inputs. TASK-025's own implementation and evidence surface
are no longer blocked.
