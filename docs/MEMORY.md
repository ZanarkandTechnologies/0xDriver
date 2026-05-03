# Memory

2026-05-02 05:23 +0800 | RESOURCE | MEM-0001 | challenge,sota | SoTA Commission I asks for a minimal-shot autonomy submission with repo, analysis notebook, 1-5 minute video or slide deck, motivation/write-up, and optional Waymo E2E driving deliverable; prompt-captured deadline is May 10, 2026.

2026-05-02 05:23 +0800 | RESOURCE | MEM-0002 | flashdrive,vla,latency | FlashDrive inspiration should be treated as algorithm-system design guidance, not copied wholesale: streaming cache reuse, compact reasoning, speculative decoding, adaptive action generation, quantization, CUDA graphs, and kernel fusion all target different VLA latency stages.

2026-05-02 05:23 +0800 | RESOURCE | MEM-0003 | realtime-vla-v2,robotics,deployment | Realtime-VLA V2 inspiration should guide deployment structure: server/client split, time-axis action planning, action chunking/prefill, local smoothing or MPC, aligned logs, async video/log recording, and mock runtime paths.

2026-05-02 05:23 +0800 | RESOURCE | MEM-0004 | waymo,e2e,dataset | Waymo E2E tutorial shows the practical target shape: load E2EDFrame TFRecords, inspect front cameras, use future ego states, predict a single 5-second trajectory at 4 Hz as 20 `(x, y)` points, package E2EDChallengeSubmission shards, and use ADE as a local proxy metric.

2026-05-02 05:23 +0800 | RULE | MEM-0005 | architecture,vla,planning | 0xDriver v1 must not depend on training a new VLA from scratch; it should use VLA/VLM reasoning as structured scene-intent input to deterministic trajectory generation, smoothing, safety checks, and ranking.

2026-05-02 05:23 +0800 | RULE | MEM-0006 | hardware,cloud,latency | Local Mac development is suitable for docs, dataset parsing, notebooks, mock runs, and light experiments; heavy CUDA/Triton VLA inference should remain optional cloud GPU work and must be timed separately from local offline evaluation.

2026-05-02 05:23 +0800 | RULE | MEM-0007 | artifacts,data | Do not commit Waymo dataset shards, generated videos, submission archives, model weights, or credentials unless a later ticket explicitly defines an artifact policy change.

2026-05-02 19:05 +0800 | RULE | MEM-0008 | waymo,runtime,docker | Official Waymo E2E dependencies must be treated as a Linux x86_64 runtime boundary; on Apple Silicon, use the Docker bridge for real TFRecord parsing and keep fixture/mock paths dependency-light.

2026-05-02 20:50 +0800 | RULE | MEM-0009 | waymo,baseline,evaluation | Before adding or comparing VLA/GPU backends, establish a small real Waymo batch baseline with `batch_summary.json`, `batch_report.md`, per-frame artifacts, mean ADE, mean timings, and best/worst ADE scenes.

2026-05-02 21:34 +0800 | RULE | MEM-0010 | waymo,baselines,vla | Future VLA/GPU comparisons must include deterministic rule baselines from TASK-005; on the first 10-frame validation slice, `constant_acceleration` mean ADE `3.73323` beat the mock `intent_planner` mean ADE `6.204769`.

2026-05-03 14:27 +0800 | RULE | MEM-0011 | planning,realtime-vla,hybrid | The default main planner must stay hybrid: structured VLA/VLM intent can steer semantic candidates, but the deployable local action layer must include motion-prior candidates, smoothing, and label-free ranking; future VLA/GPU backends should beat this hybrid baseline rather than bypass it.

2026-05-03 18:37 +0800 | RULE | MEM-0012 | carla,fail2drive,simulation | The main simulation path for the SoTA pivot is CARLA plus Fail2Drive scenario generation and OOD evaluation; the local Mac is the default authoring, fixture, report, and dry-run environment, with an optional community Wine/Kegworks Apple Silicon CARLA smoke-test path, while reproducible Fail2Drive runtime and heavy VLA inference should target Linux NVIDIA GPU infrastructure unless the Mac wrapper proves stable end to end.
