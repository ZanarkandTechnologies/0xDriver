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
- `simlingo_state`: `route_infrastructure_blocked`
- `simlingo_driving_score`: `None`

## Components

| Component | Status | Key metrics | Path |
| --- | --- | --- | --- |
| `scenario_summary` | `ready` | seed_count=3, recipe_count=2, mutations=['occlusion', 'visual_noise'] | `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/scenario-forge/scenario_suite_summary.json` |
| `route_pack` | `ready` | route_count=2, route_suite_path=tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_routes/generated_routes.xml, simlingo_plan_path=tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_command_plan.json | `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_route_pack.json` |
| `overlay_plan` | `ready` | route_count=2, companion_actor_count=2, validation_error_count=0 | `tickets/TASK-021/artifacts/qa/2026-05-04T220000Z/overlay-injection/overlay_injection_plan.json` |
| `sidecar_plan` | `blocked` | command_count=2, expected_output_count=4 | `tickets/TASK-023/artifacts/qa/2026-05-05T053000Z/sidecar-plan/simlingo_sidecar_plan.json` |
| `sidecar_run` | `passed` | success=True, duration_s=0.112236, process_count=2 | `tickets/TASK-024/artifacts/2026-05-05T153000+0800/sample-sidecar-run/simlingo_sidecar_run.json` |
| `rag_comparison` | `ready` | policy=mock, scenario_id=construction_merge::motorcycle_filtering, driving_score_delta=37.0, infraction_delta=-2, live_model_claim=False | `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/rag-comparison/rag_comparison.json` |
| `simlingo_result` | `blocked` | success=False, state=route_infrastructure_blocked, selected_result_path=None, route_log_path=tickets/TASK-020/artifacts/task20-remote/run_one_route_with_carla.log, compatibility_path=tickets/TASK-020/artifacts/task20-remote/torch_cuda_compatibility.json, diagnostics_path=tickets/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md, status=None, driving_score=None, route_completion=None, primary_route=None | `tickets/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.json` |
| `blockers` | `blocked` | open_blocker_count=1 | `blockers.md` |

## Open Blockers

- sidecar_plan: SimLingo live execution requires Linux NVIDIA; current platform is Darwin.
- sidecar_plan: CARLA 0.9.15 root not found: /Users/kenjipcx/software/carla0915
- sidecar_plan: SimLingo checkpoint not found: /workspace/models/simlingo/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt
- simlingo_result: CARLA server did not open port before route execution; route log: tickets/TASK-020/artifacts/task20-remote/run_one_route_with_carla.log
- blockers: 2026-05-05 17:07 +0800 | h100,carla,vulkan | TASK-020 stock SimLingo H100 route run cannot reach policy execution because CARLA 0.9.15 exits before opening port `20000` on the RunPod H100 container. CUDA is compatible for SimLingo (`sm_90`), but CARLA needs a working graphics/Vulkan runtime; diagnostics show default Vulkan only exposes `llvmpipe`, forcing the NVIDIA ICD fails with `ERROR_INCOMPATIBLE_DRIVER`, and CARLA exits with status `1`. Evidence: `tickets/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.md` and `tickets/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md`. Next unblock path: move the stock route to a graphics-capable Ampere host such as RTX 3090 / RTX A6000 / A40 / A10, or rebuild the SimLingo torch stack for the earlier RTX PRO 6000 Blackwell host where CARLA did launch.
