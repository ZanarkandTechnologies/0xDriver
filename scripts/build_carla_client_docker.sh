#!/usr/bin/env bash
set -euo pipefail

CARLA_PYTHON_VERSION="${CARLA_PYTHON_VERSION:-0.9.16}"
IMAGE="${CARLA_CLIENT_DOCKER_IMAGE:-driverx-carla-client:${CARLA_PYTHON_VERSION}}"

docker build \
  --platform linux/amd64 \
  --build-arg "CARLA_PYTHON_VERSION=${CARLA_PYTHON_VERSION}" \
  -f docker/carla-client.Dockerfile \
  -t "${IMAGE}" \
  .
