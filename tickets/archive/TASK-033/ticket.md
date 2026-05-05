# TASK-033: Fail2Drive Route Video Smoke

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-032, external Fail2Drive checkout, graphics-capable CARLA
  runtime for live proof
- location: `src/driverx/simulators`, CLI, tests, configs, docs
- enter when: the project needs a route-level video proof before deeper policy
  adapter work
- leave when: one command can plan and report a Fail2Drive route-video smoke run
  with explicit live blockers and expected video artifacts
- blockers: live execution needs a CARLA host with graphics/Vulkan working;
  local/dry-run implementation is unblocked
- spawned follow-ups: TASK-034 video and telemetry evidence pipeline
- complexity: M

## Summary

Add a Fail2Drive route-video smoke surface. The command should identify the
route, policy/agent, result paths, optional `LIVE_VISU=1`, image-folder/video
generation command, and live runtime blockers without launching CARLA during
tests.

## Scope

In scope:

- Plan PDM-Lite/human/basic Fail2Drive route commands from config.
- Plan the companion video-generation command (`tools/generate_video.py -f ...`)
  once an RGB folder exists.
- Write JSON/Markdown evidence with expected result, RGB, and video outputs.
- Fail cleanly when Fail2Drive checkout files are missing.

Out of scope:

- Running CARLA from the local test suite.
- SimLingo/Alpamayo model execution.
- OOD overlay injection; that starts in TASK-035.

## Plan

### Change

Before: route-pack and sidecar plans exist, but there is no first-class route
video smoke plan.

After: `plan-fail2drive-video-smoke` writes a compact route execution and video
evidence plan that can run locally or on a GPU host once CARLA is ready.

### Signature Delta

```python
Fail2DriveVideoSmokeConfig(...)
plan_fail2drive_video_smoke(config: Fail2DriveVideoSmokeConfig) -> Fail2DriveVideoSmokePlan
write_fail2drive_video_smoke_plan(run_dir: Path, plan: Fail2DriveVideoSmokePlan) -> dict[str, Any]
```

### Type Sketch

```python
Fail2DriveVideoSmokePlan = {
  "route_path": str,
  "agent_path": str,
  "run_command": list[str],
  "video_command": list[str],
  "env": dict[str, str],
  "expected_outputs": {"result": str, "rgb_folder": str, "video": str},
  "live_blockers": list[str],
}
```

### Execution Steps

1. Add `driverx.simulators.fail2drive_video`.
2. Add CLI command and sample config fields.
3. Add unit/CLI tests with a fake Fail2Drive checkout.
4. Generate local evidence.
5. Update docs/progress/history.
6. Review and QA.

## Acceptance Criteria

- [x] AC-1: CLI writes JSON/Markdown route-video smoke plan.
- [x] AC-2: Plan includes Fail2Drive evaluator command and video-generation
  command.
- [x] AC-3: Plan records expected result, RGB folder, and video path.
- [x] AC-4: Missing checkout, route, agent, or video tool produces actionable
  blockers.
- [x] AC-5: Tests pass without CARLA, Fail2Drive runtime, or GPU.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_video_smoke tests.test_cli_fail2drive_video_smoke`
- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx plan-fail2drive-video-smoke --config configs/carla_local.sample.yaml --run-id task33-video-smoke`

## Autonomy Readiness

- Local code and fake-checkout tests are unblocked.
- Live proof needs a graphics-capable CARLA host; if unavailable, write the
  blocker and continue to TASK-034 mock/evidence work.

## Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_video_smoke tests.test_cli_fail2drive_video_smoke`
  passed with 5 tests.
- `PYTHONPATH=src python3 -m driverx plan-fail2drive-video-smoke --config configs/carla_local.sample.yaml --run-id task33-video-smoke`
  wrote `artifacts/runs/task33-video-smoke/fail2drive_video_smoke_plan.json`
  and `artifacts/runs/task33-video-smoke/fail2drive_video_smoke_plan.md`.
- `bash scripts/pre_push_check.sh` passed with 173 tests.
- Review pass:
  `tickets/TASK-033/artifacts/review/20260505T190014-review.json`
  scored `4.1` overall with no blocking findings.
- The local plan includes the Fail2Drive evaluator command, `LIVE_VISU=1`,
  `SAVE_PATH`, expected result/debug/RGB/video outputs, and two live blockers:
  missing `tools/generate_video.py` in the external Fail2Drive checkout plus
  missing RGB frames until a live route run produces them.

## Blockers

- Live route video capture requires a graphics-capable CARLA runtime.
- External Fail2Drive does not currently include `tools/generate_video.py`;
  TASK-034 should normalize evidence and can either consume an independently
  produced video or add a repo-local video assembler.
