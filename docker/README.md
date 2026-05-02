# Docker Runtimes

## Purpose

This directory contains compatibility runtimes for dependencies that do not
install cleanly on the local Mac. The first image targets official Waymo E2E
TFRecord parsing on Linux amd64.

## Entrypoints

- `waymo.Dockerfile`: builds `driverx-waymo:local` with TensorFlow and the
  official Waymo Open Dataset package. The base image digest and pip version are
  pinned; the Waymo package still controls its own transitive dependency set.
- `../scripts/build_waymo_docker.sh`: builds the image.
- `../scripts/run_waymo_docker.sh`: runs a command inside the image with the repo
  mounted at `/workspace`.

## Minimal Example

```bash
scripts/build_waymo_docker.sh
scripts/run_waymo_docker.sh
```

To run a different command:

```bash
scripts/run_waymo_docker.sh python -m driverx --help
```

## How To Test

Use the repo-level checks for fixture-backed behavior:

```bash
bash scripts/pre_push_check.sh
```

Use the Docker smoke path for real Waymo dependencies:

```bash
scripts/build_waymo_docker.sh
scripts/run_waymo_docker.sh
```
