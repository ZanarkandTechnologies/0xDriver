# Bench2Drive Route Pack

- suite_id: `route-pack`
- behavior_id: `motorcycle_filtering`
- routes: `2`
- route_suite_path: `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/external-fail2drive/route-pack/bench2drive_routes/generated_routes.xml`
- injection_strategy: `stock_bench2drive_xml_plus_driverx_sidecar_overlay`

The route XML stays stock-compatible for SimLingo/Bench2Drive. Generated actors, assets, and regional behaviors are recorded in DriverX sidecar overlays for companion injection or later scenario-runner adapters.

## Routes

| recipe | route id | town | scenarios | overlay |
|---|---|---|---|---|
| generated-base-animals-0075-regional-driving-behavior-000 | 75 | Town13 | DynamicObjectCrossing | tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/external-fail2drive/route-pack/driverx_overlays/000_generated-base-animals-0075-regional-driving-behavior-000.json |
| generated-base-animals-0076-regional-driving-behavior-001 | 76 | Town13 | PriorityAtJunction, VehicleTurningRoutePedestrian | tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/external-fail2drive/route-pack/driverx_overlays/001_generated-base-animals-0076-regional-driving-behavior-001.json |
