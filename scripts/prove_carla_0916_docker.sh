#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CARLA_HOST="${CARLA_HOST:-host.docker.internal}"
CARLA_PORT="${CARLA_PORT:-2000}"
CARLA_TIMEOUT_S="${CARLA_TIMEOUT_S:-1.0}"
CARLA_TICK_COUNT="${CARLA_TICK_COUNT:-5}"
RUN_ID="${1:-task16-proof}"

cd "${ROOT}"

scripts/build_carla_client_docker.sh

scripts/run_carla_client_docker.sh \
  python -c 'import carla; from importlib.metadata import version; print("CARLA Python API:", version("carla"))'

scripts/run_carla_client_docker.sh \
  python -m driverx probe-carla \
  --host "${CARLA_HOST}" \
  --port "${CARLA_PORT}" \
  --timeout-s "${CARLA_TIMEOUT_S}" \
  --run-id "${RUN_ID}-probe"

scripts/run_carla_client_docker.sh \
  python -m driverx spawn-ego-smoke \
  --host "${CARLA_HOST}" \
  --port "${CARLA_PORT}" \
  --timeout-s "${CARLA_TIMEOUT_S}" \
  --tick-count "${CARLA_TICK_COUNT}" \
  --run-id "${RUN_ID}-ego"
