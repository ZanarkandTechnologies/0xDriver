# History

2026-05-02 05:23 +0800 | BOOTSTRAP | Initialized docs-first project scaffold for 0xDriver minimal-shot VLA autonomy planning.
2026-05-02 09:37 +0800 | TASK | started TASK-002 optional real Waymo E2E integration after fixture-backed v1 passed QA
2026-05-02 09:45 +0800 | SHIP | added optional Waymo TFRecord loading seam and official submission packaging mode behind lazy dependencies
2026-05-02 10:02 +0800 | QA | TASK-002 passed review and final QA with optional Waymo dependency paths kept non-blocking
2026-05-02 16:23 +0800 | TASK | started TASK-003 Waymo Linux Docker runtime after native macOS ARM dependency install failed
2026-05-02 19:05 +0800 | SHIP | built Linux amd64 Waymo Docker runtime and ran downloaded validation shard through inspect and baseline planner paths
2026-05-02 19:32 +0800 | QA | TASK-003 passed final runtime review with Docker, real-shard, and Linux requirements evidence
2026-05-02 20:42 +0800 | TASK | started TASK-004 real Waymo batch baseline after single-frame Docker proof passed
2026-05-02 20:50 +0800 | SHIP | added streaming Waymo batch execution with aggregate ADE and latency reporting
2026-05-02 21:02 +0800 | QA | TASK-004 passed final review and QA with real 10-frame Waymo batch baseline evidence
2026-05-02 21:34 +0800 | TASK | started TASK-005 batch experiment harness to compare current planner against deterministic baselines
2026-05-02 21:34 +0800 | SHIP | added rule trajectory baselines and cross-strategy experiment runner
2026-05-02 21:46 +0800 | QA | TASK-005 passed final review and QA with real Waymo experiment comparison evidence
2026-05-03 14:24 +0800 | TASK | started TASK-006 motion-prior hybrid planner after deterministic baselines beat mock intent planner
2026-05-03 14:27 +0800 | SHIP | routed main scene and batch pipeline through hybrid semantic-intent and motion-prior candidates
2026-05-03 14:34 +0800 | QA | TASK-006 passed review and QA with real hybrid Waymo batch and experiment evidence
2026-05-03 18:37 +0800 | PLAN | reframed project PRD around CARLA plus Fail2Drive scenario generation, retrieval memory, SimLingo-first policy proof, Alpamayo adapter extension, and later serving acceleration
2026-05-03 18:37 +0800 | PLAN | incorporated community Apple Silicon CARLA wrapper as optional local smoke-test path while preserving Linux NVIDIA as reproducible Fail2Drive/VLA runtime target
2026-05-03 19:31 +0800 | TASK | started TASK-007 local scenario forge and CARLA smoke adapter with Fail2Drive cloned externally
2026-05-03 19:50 +0800 | SHIP | added local scenario forge, failure memory bank, CARLA smoke check, and route-faithful Fail2Drive dry-run planning
2026-05-03 19:50 +0800 | QA | TASK-007 passed local review and QA with 57-test pre-push gate and explicit recipe-to-route evidence
2026-05-04 18:58 +0800 | PLAN | expanded roadmap through TASK-014 for live CARLA probing, entity tracking, regional behavior generation, asset generation, policy adapters, and retrieval-augmented VLA comparison
2026-05-04 18:58 +0800 | TASK | started TASK-008 live CARLA probe and Docker bridge after local CARLA app reached TCP smoke on port 2000
2026-05-04 18:58 +0800 | SHIP | TASK-008 live Docker probe reached CARLA 0.9.16 and recorded Town10HD_Opt with 23 actors
2026-05-04 19:00 +0800 | SHIP | TASK-009 live ego smoke spawned vehicle and RGB camera, captured a frame, logged entity tracks, and cleaned up actors
2026-05-04 19:02 +0800 | SHIP | TASK-010 added deterministic regional OOD behavior traces for no-signal cut-ins, sudden braking, motorcycle filtering, wrong-way creep, informal right-of-way pushes, and fast low-profile two-wheelers
2026-05-04 19:04 +0800 | SHIP | TASK-011 compiled scenario recipes and behavior traces into validated CARLA actor, sensor, tick, output, and cleanup script plans
2026-05-04 19:22 +0800 | SHIP | TASK-012 added generated OOD asset requests, dry-run manifests, Meshy setup blocking, manifest validation, and recipe asset references
2026-05-04 19:27 +0800 | SHIP | TASK-013 added policy adapter contracts, mock and memory-aware decisions, local hybrid fallback, and setup-checked VLM/SimLingo/Alpamayo stubs
2026-05-04 19:30 +0800 | SHIP | TASK-014 added retrieval-augmented policy comparison reports with matched no-memory and memory-guided runs plus live-model setup blocker logging
