#!/usr/bin/env bash
set -euo pipefail

docker build \
  --platform linux/amd64 \
  -f docker/waymo.Dockerfile \
  -t driverx-waymo:local \
  .
