# Memory

2026-05-02 05:23 +0800 | RESOURCE | MEM-0001 | challenge,sota | SoTA Commission I asks for a minimal-shot autonomy submission with repo, analysis notebook, 1-5 minute video or slide deck, motivation/write-up, and optional Waymo E2E driving deliverable; prompt-captured deadline is May 10, 2026.

2026-05-02 05:23 +0800 | RESOURCE | MEM-0002 | flashdrive,vla,latency | FlashDrive inspiration should be treated as algorithm-system design guidance, not copied wholesale: streaming cache reuse, compact reasoning, speculative decoding, adaptive action generation, quantization, CUDA graphs, and kernel fusion all target different VLA latency stages.

2026-05-02 05:23 +0800 | RESOURCE | MEM-0003 | realtime-vla-v2,robotics,deployment | Realtime-VLA V2 inspiration should guide deployment structure: server/client split, time-axis action planning, action chunking/prefill, local smoothing or MPC, aligned logs, async video/log recording, and mock runtime paths.

2026-05-02 05:23 +0800 | RESOURCE | MEM-0004 | waymo,e2e,dataset | Waymo E2E tutorial shows the practical target shape: load E2EDFrame TFRecords, inspect front cameras, use future ego states, predict a single 5-second trajectory at 4 Hz as 20 `(x, y)` points, package E2EDChallengeSubmission shards, and use ADE as a local proxy metric.

2026-05-02 05:23 +0800 | RULE | MEM-0005 | architecture,vla,planning | 0xDriver v1 must not depend on training a new VLA from scratch; it should use VLA/VLM reasoning as structured scene-intent input to deterministic trajectory generation, smoothing, safety checks, and ranking.

2026-05-02 05:23 +0800 | RULE | MEM-0006 | hardware,cloud,latency | Local Mac development is suitable for docs, dataset parsing, notebooks, mock runs, and light experiments; heavy CUDA/Triton VLA inference should remain optional cloud GPU work and must be timed separately from local offline evaluation.

2026-05-02 05:23 +0800 | RULE | MEM-0007 | artifacts,data | Do not commit Waymo dataset shards, generated videos, submission archives, model weights, or credentials unless a later ticket explicitly defines an artifact policy change.

2026-05-02 19:05 +0800 | RULE | MEM-0008 | waymo,runtime,docker | Official Waymo E2E dependencies must be treated as a Linux x86_64 runtime boundary; on Apple Silicon, use the Docker bridge for real TFRecord parsing and keep fixture/mock paths dependency-light.
