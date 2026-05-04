# Docker Runtimes

## Purpose

This directory contains compatibility runtimes for dependencies that do not
install cleanly on the local Mac. Runtime boundaries are intentionally split:
Waymo parsing stays separate from the CARLA Python client bridge.

## Entrypoints

- `waymo.Dockerfile`: builds `driverx-waymo:local` with TensorFlow and the
  official Waymo Open Dataset package. The base image digest and pip version are
  pinned; the Waymo package still controls its own transitive dependency set.
- `carla-client.Dockerfile`: builds `driverx-carla-client:0.9.16` with the
  Linux amd64 `carla==0.9.16` Python package for connecting to a host CARLA
  server from Apple Silicon Docker.
- `../scripts/build_waymo_docker.sh`: builds the image.
- `../scripts/run_waymo_docker.sh`: runs a command inside the image with the repo
  mounted at `/workspace`.
- `../scripts/build_carla_client_docker.sh`: builds the reusable CARLA client
  image.
- `../scripts/run_carla_client_docker.sh`: runs a command inside the CARLA
  client image, loading an explicit `DRIVERX_DOCKER_ENV_FILE` when set and
  falling back to on-the-fly install only when the built image is missing.
- `../scripts/prove_carla_0916_docker.sh`: builds the client image, verifies the
  CARLA Python package version, probes the host server, and attempts the
  ego-camera smoke run.

## Minimal Example

```bash
scripts/build_waymo_docker.sh
scripts/run_waymo_docker.sh
```

To run a different command:

```bash
scripts/run_waymo_docker.sh python -m driverx --help
```

For local CARLA 0.9.16 development, keep the CARLA app open on the host and run:

```bash
scripts/build_carla_client_docker.sh
scripts/run_carla_client_docker.sh python -m driverx probe-carla \
  --host host.docker.internal \
  --port 2000
```

To capture both the API probe and the ego-camera smoke artifacts:

```bash
scripts/prove_carla_0916_docker.sh
```

To pass local environment variables into the container, opt in explicitly:

```bash
DRIVERX_DOCKER_ENV_FILE=.env scripts/run_carla_client_docker.sh python -m driverx --help
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

Use the CARLA Docker proof for local simulator connectivity:

```bash
scripts/build_carla_client_docker.sh
scripts/run_carla_client_docker.sh python -c 'import carla; from importlib.metadata import version; print(version("carla"))'
```
