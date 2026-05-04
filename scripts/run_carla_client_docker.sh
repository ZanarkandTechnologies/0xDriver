#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CARLA_PYTHON_VERSION="${CARLA_PYTHON_VERSION:-0.9.16}"
DEFAULT_IMAGE="driverx-carla-client:${CARLA_PYTHON_VERSION}"
IMAGE="${CARLA_CLIENT_DOCKER_IMAGE:-${DEFAULT_IMAGE}}"

if [ "$#" -eq 0 ]; then
  echo "usage: scripts/run_carla_client_docker.sh <command...>" >&2
  echo "example: scripts/run_carla_client_docker.sh python -m driverx probe-carla --host host.docker.internal --port 2000" >&2
  exit 2
fi

RUNNER='exec "$@"'
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  if [ -n "${CARLA_CLIENT_DOCKER_IMAGE:-}" ]; then
    echo "CARLA client Docker image not found: ${IMAGE}" >&2
    echo "Run scripts/build_carla_client_docker.sh or unset CARLA_CLIENT_DOCKER_IMAGE for the python:3.10-bullseye fallback." >&2
    exit 2
  fi
  IMAGE="python:3.10-bullseye"
  RUNNER='python -m pip install --quiet --disable-pip-version-check "carla==${CARLA_PYTHON_VERSION}" && exec "$@"'
fi

if [ -n "${DRIVERX_DOCKER_ENV_FILE:-}" ]; then
  docker run \
    --platform linux/amd64 \
    --rm \
    --env-file "${DRIVERX_DOCKER_ENV_FILE}" \
    -e "CARLA_PYTHON_VERSION=${CARLA_PYTHON_VERSION}" \
    -e PIP_ROOT_USER_ACTION=ignore \
    -e PYTHONPATH=/workspace/src \
    -v "${ROOT}:/workspace" \
    -w /workspace \
    "${IMAGE}" \
    bash -lc "${RUNNER}" \
    bash "$@"
else
  docker run \
    --platform linux/amd64 \
    --rm \
    -e "CARLA_PYTHON_VERSION=${CARLA_PYTHON_VERSION}" \
    -e PIP_ROOT_USER_ACTION=ignore \
    -e PYTHONPATH=/workspace/src \
    -v "${ROOT}:/workspace" \
    -w /workspace \
    "${IMAGE}" \
    bash -lc "${RUNNER}" \
    bash "$@"
fi
