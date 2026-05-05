#!/usr/bin/env bash
set -euo pipefail
if [ -f "/workspace/artifacts/task20/carla/carla.pid" ]; then
  pid="$(cat "/workspace/artifacts/task20/carla/carla.pid")"
  kill "${pid}" 2>/dev/null || true
  rm -f "/workspace/artifacts/task20/carla/carla.pid"
fi
