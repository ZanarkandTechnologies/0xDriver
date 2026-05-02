"""Shared Waymo runtime guidance."""

from __future__ import annotations

WAYMO_RUNTIME_HINT = (
    "On Apple Silicon, build and run the Linux amd64 Docker runtime with "
    "`scripts/build_waymo_docker.sh` and `scripts/run_waymo_docker.sh`. "
    "On Linux x86_64 without Docker, install with "
    "`python -m pip install -r requirements/waymo-linux.txt` so pip uses the "
    "required JAX wheel index. Otherwise keep using dataset.kind=fixture / "
    "configs/waymo_fixture.yaml."
)
