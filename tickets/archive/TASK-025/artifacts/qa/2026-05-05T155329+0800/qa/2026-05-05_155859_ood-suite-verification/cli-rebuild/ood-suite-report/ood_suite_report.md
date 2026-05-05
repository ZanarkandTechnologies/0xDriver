# OOD Suite Evidence Report

- component_count: `8`
- present_components: `scenario_summary, route_pack, overlay_plan, sidecar_plan, sidecar_run, rag_comparison, simlingo_result, blockers`
- missing_components: `none`
- has_open_blockers: `True`

## Readiness

- `scenario_generation_ready`: `True`
- `bench2drive_route_pack_ready`: `True`
- `overlay_injection_ready`: `True`
- `sidecar_launch_ready`: `False`
- `sidecar_run_passed`: `True`
- `live_policy_result_passed`: `False`
- `has_open_blockers`: `True`

## Metric Highlights

- `generated_recipe_count`: `2`
- `mutation_count`: `2`
- `bench2drive_route_count`: `2`
- `companion_actor_count`: `2`
- `sidecar_run_success`: `True`
- `sidecar_duration_s`: `0.112236`
- `rag_driving_score_delta`: `37.0`
- `simlingo_success`: `False`
- `simlingo_driving_score`: `0.0`

## Components

| Component | Status | Key metrics | Path |
| --- | --- | --- | --- |
| `scenario_summary` | `ready` | seed_count=3, recipe_count=2, mutations=['occlusion', 'visual_noise'] | `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/scenario-forge/scenario_suite_summary.json` |
| `route_pack` | `ready` | route_count=2, route_suite_path=tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_routes/generated_routes.xml, simlingo_plan_path=tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_command_plan.json | `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_route_pack.json` |
| `overlay_plan` | `ready` | route_count=2, companion_actor_count=2, validation_error_count=0 | `tickets/TASK-021/artifacts/qa/2026-05-04T220000Z/overlay-injection/overlay_injection_plan.json` |
| `sidecar_plan` | `blocked` | command_count=2, expected_output_count=4 | `tickets/TASK-023/artifacts/qa/2026-05-05T053000Z/sidecar-plan/simlingo_sidecar_plan.json` |
| `sidecar_run` | `passed` | success=True, duration_s=0.112236, process_count=2 | `tickets/TASK-024/artifacts/2026-05-05T153000+0800/sample-sidecar-run/simlingo_sidecar_run.json` |
| `rag_comparison` | `ready` | policy=mock, scenario_id=construction_merge::motorcycle_filtering, driving_score_delta=37.0, infraction_delta=-2, live_model_claim=False | `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/rag-comparison/rag_comparison.json` |
| `simlingo_result` | `blocked` | success=False, status=Failed, driving_score=0.0, route_completion=0.0, primary_route=RouteScenario_1711_rep0 | `tickets/TASK-019/artifacts/qa/2026-05-04T200000Z/result-ingestion/simlingo_result_record.json` |
| `blockers` | `ready` | open_blocker_count=0 | `blockers.md` |

## Open Blockers

- sidecar_plan: SimLingo live execution requires Linux NVIDIA; current platform is Darwin.
- sidecar_plan: CARLA 0.9.15 root not found: /Users/kenjipcx/software/carla0915
- sidecar_plan: SimLingo checkpoint not found: /workspace/models/simlingo/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt
- simlingo_result: CUDA no-kernel-image at first model tick; required `sm_120`, compiled arches `['sm_50', 'sm_60', 'sm_70', 'sm_75', 'sm_80', 'sm_86', 'sm_90']`
