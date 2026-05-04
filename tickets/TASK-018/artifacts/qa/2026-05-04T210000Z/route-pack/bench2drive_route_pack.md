# Bench2Drive Route Pack

- suite_id: `route-pack`
- behavior_id: `motorcycle_filtering`
- routes: `2`
- route_suite_path: `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_routes/generated_routes.xml`
- injection_strategy: `stock_bench2drive_xml_plus_driverx_sidecar_overlay`

The route XML stays stock-compatible for SimLingo/Bench2Drive. Generated actors, assets, and regional behaviors are recorded in DriverX sidecar overlays for companion injection or later scenario-runner adapters.

## Routes

| recipe | route id | town | scenarios | overlay |
|---|---|---|---|---|
| generated-base-animals-0076-occlusion-000 | 0076 | Town12 | Animals | tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/driverx_overlays/000_generated-base-animals-0076-occlusion-000.json |
| generated-generalization-customobstacles-1028-visual-noise-001 | 1028 | Town12 | CustomObstacles | tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/driverx_overlays/001_generated-generalization-customobstacles-1028-visual-noise-001.json |

## SimLingo Plan

- command_plan: `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_command_plan.json`
- live_blockers: `3`
