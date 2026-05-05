"""Assess whether a GPU host is suitable for SimLingo plus CARLA runs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HostSuitabilityCheck:
    name: str
    status: str
    summary: str
    details: dict[str, Any]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "details": self.details,
        }


@dataclass(frozen=True)
class GpuHostSuitability:
    overall_state: str
    blockers: list[str]
    warnings: list[str]
    recommendation: str
    inputs: dict[str, str | None]
    checks: list[HostSuitabilityCheck]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "overall_state": self.overall_state,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "recommendation": self.recommendation,
            "inputs": self.inputs,
            "checks": [check.to_jsonable() for check in self.checks],
        }


def assess_gpu_host_suitability(
    *,
    gpu_snapshot_path: Path | None = None,
    torch_compatibility_path: Path | None = None,
    carla_diagnostics_path: Path | None = None,
    simlingo_evidence_path: Path | None = None,
) -> GpuHostSuitability:
    """Build a local suitability verdict from remote host evidence artifacts."""

    compatibility = _load_json(torch_compatibility_path)
    diagnostics_text = _read_text(carla_diagnostics_path)
    evidence = _load_json(simlingo_evidence_path)
    snapshot_text = _read_text(gpu_snapshot_path)
    checks = [
        _cuda_model_check(compatibility),
        _carla_graphics_check(diagnostics_text, evidence),
        _storage_check(snapshot_text),
    ]
    blockers = _unique(check.summary for check in checks if check.status == "blocked")
    warnings = _unique(check.summary for check in checks if check.status == "warning")
    overall_state = _overall_state(checks)
    return GpuHostSuitability(
        overall_state=overall_state,
        blockers=blockers,
        warnings=warnings,
        recommendation=_recommendation(checks, compatibility),
        inputs={
            "gpu_snapshot_path": _path_str(gpu_snapshot_path),
            "torch_compatibility_path": _path_str(torch_compatibility_path),
            "carla_diagnostics_path": _path_str(carla_diagnostics_path),
            "simlingo_evidence_path": _path_str(simlingo_evidence_path),
        },
        checks=checks,
    )


def write_gpu_host_suitability_report(
    run_dir: Path,
    assessment: GpuHostSuitability,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = assessment.to_jsonable()
    json_path = run_dir / "gpu_host_suitability.json"
    report_path = run_dir / "gpu_host_suitability.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _cuda_model_check(compatibility: dict[str, Any] | None) -> HostSuitabilityCheck:
    if compatibility is None:
        return HostSuitabilityCheck(
            name="cuda_model",
            status="unknown",
            summary="No torch/CUDA compatibility artifact was provided.",
            details={},
        )
    compatible = compatibility.get("compatible")
    device_name = compatibility.get("device_name")
    required_arch = compatibility.get("required_arch")
    compiled_arches = list(compatibility.get("compiled_arches", []))
    details = {
        "device_name": device_name,
        "required_arch": required_arch,
        "compiled_arches": compiled_arches,
        "torch_version": compatibility.get("torch_version"),
        "torch_cuda": compatibility.get("torch_cuda"),
    }
    if compatible is True:
        return HostSuitabilityCheck(
            name="cuda_model",
            status="ready",
            summary=f"SimLingo torch stack supports {required_arch} on {device_name}.",
            details=details,
        )
    return HostSuitabilityCheck(
        name="cuda_model",
        status="blocked",
        summary=(
            f"SimLingo torch stack does not support required GPU arch {required_arch}; "
            f"compiled arches are {', '.join(str(arch) for arch in compiled_arches) or 'unknown'}."
        ),
        details=details,
    )


def _carla_graphics_check(
    diagnostics_text: str | None,
    evidence: dict[str, Any] | None,
) -> HostSuitabilityCheck:
    blockers = [str(blocker) for blocker in list(_mapping(evidence).get("blockers", []))]
    state = _mapping(evidence).get("state")
    text = diagnostics_text or ""
    details = {
        "evidence_state": state,
        "evidence_blockers": blockers,
        "llvmpipe_detected": "llvmpipe" in text,
        "nvidia_icd_error": "ERROR_INCOMPATIBLE_DRIVER" in text,
        "carla_port_timeout": "did not open port" in text or any("did not open port" in b for b in blockers),
    }
    if details["nvidia_icd_error"] or details["carla_port_timeout"]:
        return HostSuitabilityCheck(
            name="carla_graphics",
            status="blocked",
            summary=(
                "CARLA graphics runtime is blocked: Vulkan/graphics diagnostics or route logs "
                "show the server did not become reachable."
            ),
            details=details,
        )
    if diagnostics_text is None and evidence is None:
        return HostSuitabilityCheck(
            name="carla_graphics",
            status="unknown",
            summary="No CARLA graphics diagnostics or remote evidence was provided.",
            details=details,
        )
    return HostSuitabilityCheck(
        name="carla_graphics",
        status="ready",
        summary="No CARLA graphics blocker was detected in the provided evidence.",
        details=details,
    )


def _storage_check(snapshot_text: str | None) -> HostSuitabilityCheck:
    if snapshot_text is None:
        return HostSuitabilityCheck(
            name="host_storage",
            status="unknown",
            summary="No GPU host snapshot was provided.",
            details={},
        )
    root_disk_gb = _root_disk_size_gb(snapshot_text)
    details = {"root_disk_gb": root_disk_gb}
    if root_disk_gb is not None and root_disk_gb < 100:
        return HostSuitabilityCheck(
            name="host_storage",
            status="warning",
            summary=(
                f"Root disk is only {root_disk_gb:.0f}GB; keep conda, CARLA, models, "
                "cache, and artifacts on a persistent workspace volume."
            ),
            details=details,
        )
    return HostSuitabilityCheck(
        name="host_storage",
        status="ready",
        summary="No small-root-disk warning was detected.",
        details=details,
    )


def _overall_state(checks: list[HostSuitabilityCheck]) -> str:
    if any(check.status == "blocked" for check in checks):
        return "blocked"
    core = [check for check in checks if check.name in {"cuda_model", "carla_graphics"}]
    if core and all(check.status == "ready" for check in core):
        return "ready"
    return "unknown"


def _recommendation(checks: list[HostSuitabilityCheck], compatibility: dict[str, Any] | None) -> str:
    by_name = {check.name: check for check in checks}
    cuda = by_name.get("cuda_model")
    carla = by_name.get("carla_graphics")
    required_arch = _mapping(compatibility).get("required_arch")
    if carla and carla.status == "blocked":
        return (
            "Use a graphics-capable NVIDIA host with working Vulkan/OpenGL exposure for CARLA; "
            "avoid compute-only H100/H200 containers for closed-loop CARLA route proof."
        )
    if cuda and cuda.status == "blocked":
        return (
            f"Use a GPU architecture already covered by the SimLingo torch stack or rebuild "
            f"the torch/extension stack for {required_arch}."
        )
    if all(check.status == "ready" for check in checks if check.name in {"cuda_model", "carla_graphics"}):
        return "This host is suitable for the next SimLingo/CARLA route run."
    return "Collect torch compatibility and CARLA graphics diagnostics before spending more live route time."


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _read_text(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.expanduser().read_text(encoding="utf-8", errors="replace")


def _root_disk_size_gb(snapshot_text: str) -> float | None:
    for line in snapshot_text.splitlines():
        if line.startswith("overlay"):
            parts = line.split()
            if len(parts) >= 2:
                return _size_to_gb(parts[1])
    return None


def _size_to_gb(value: str) -> float | None:
    match = re.fullmatch(r"([0-9.]+)([TGMK]?)", value.strip())
    if match is None:
        return None
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "T":
        return number * 1024
    if unit == "G" or unit == "":
        return number
    if unit == "M":
        return number / 1024
    if unit == "K":
        return number / (1024 * 1024)
    return None


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _path_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _unique(values: Any) -> list[str]:
    output: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in output:
            output.append(text)
    return output


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# GPU Host Suitability Report",
        "",
        f"- overall_state: `{payload['overall_state']}`",
        f"- recommendation: {payload['recommendation']}",
        "",
        "## Blockers",
        "",
    ]
    blockers = list(payload.get("blockers", []))
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("None.")
    lines.extend(["", "## Warnings", ""])
    warnings = list(payload.get("warnings", []))
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("None.")
    lines.extend(["", "## Checks", "", "| Check | Status | Summary |", "| --- | --- | --- |"])
    for check in list(payload.get("checks", [])):
        lines.append(f"| `{check['name']}` | `{check['status']}` | {check['summary']} |")
    return "\n".join(lines) + "\n"


__all__ = [
    "GpuHostSuitability",
    "HostSuitabilityCheck",
    "assess_gpu_host_suitability",
    "write_gpu_host_suitability_report",
]
