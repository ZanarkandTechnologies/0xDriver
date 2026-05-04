# Overlay Injection Plan

- runtime_mode: `dry_run_companion_plan`
- routes: `2`
- route_pack_path: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_route_pack.json`
- route_suite_path: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_routes/generated_routes.xml`
- validation_errors: `0`

This plan compiles DriverX sidecar overlays into CARLA actor/sensor/tick plans. It does not launch CARLA or modify stock SimLingo behavior until a live companion injector runs beside the benchmark route.

## Routes

| recipe | mutation | overlay roles | companion blueprints | behavior | ticks | validation |
|---|---|---|---|---|---|---|
| generated-base-animals-0076-occlusion-000 | occlusion | occluder | static.prop.streetbarrier | motorcycle_filtering | 26 | ok |
| generated-generalization-customobstacles-1028-visual-noise-001 | visual_noise | distractor | static.prop.trafficwarning | motorcycle_filtering | 26 | ok |
