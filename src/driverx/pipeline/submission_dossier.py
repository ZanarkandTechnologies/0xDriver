"""Build a compact submission-facing dossier from project evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_submission_dossier(
    run_dir: Path,
    *,
    ood_suite_manifest_path: Path | None = None,
    gpu_host_suitability_path: Path | None = None,
    progress_path: Path | None = None,
    blockers_path: Path | None = None,
) -> dict[str, Any]:
    """Write a JSON and Markdown dossier for the current submission state."""

    ood = _load_json(ood_suite_manifest_path)
    gpu = _load_json(gpu_host_suitability_path)
    progress_tail = _latest_progress_lines(_read_text(progress_path), limit=18)
    blockers = _parse_open_blockers(_read_text(blockers_path))
    payload = {
        "title": "0xDriver Minimal-Shot OOD Driving Harness",
        "thesis": (
            "Use generated long-tail CARLA/Bench2Drive scenarios, retrieved safety memory, "
            "and frozen VLA policy adapters to test minimal-shot driving behavior without "
            "fine-tuning on the generated cases."
        ),
        "ood_readiness": _mapping(_mapping(ood).get("readiness")),
        "metric_highlights": _mapping(_mapping(ood).get("metric_highlights")),
        "gpu_host": {
            "overall_state": _mapping(gpu).get("overall_state"),
            "recommendation": _mapping(gpu).get("recommendation"),
            "blockers": list(_mapping(gpu).get("blockers", [])),
            "warnings": list(_mapping(gpu).get("warnings", [])),
        },
        "open_blockers": blockers,
        "demo_outline": _demo_outline(_mapping(ood), _mapping(gpu), blockers),
        "progress_tail": progress_tail,
        "inputs": {
            "ood_suite_manifest_path": _path_str(ood_suite_manifest_path),
            "gpu_host_suitability_path": _path_str(gpu_host_suitability_path),
            "progress_path": _path_str(progress_path),
            "blockers_path": _path_str(blockers_path),
        },
    }
    return write_submission_dossier(run_dir, payload)


def write_submission_dossier(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "submission_dossier.json"
    report_path = run_dir / "submission_dossier.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _demo_outline(ood: dict[str, Any], gpu: dict[str, Any], blockers: list[str]) -> list[str]:
    readiness = _mapping(ood.get("readiness"))
    metrics = _mapping(ood.get("metric_highlights"))
    gpu_state = gpu.get("overall_state")
    outline = [
        "Show generated OOD recipes and Bench2Drive route pack.",
        "Show overlay/sidecar plan that injects companion actors into CARLA.",
        (
            "Show RAG comparison result "
            f"(driving score delta: {metrics.get('rag_driving_score_delta', 'unknown')})."
        ),
        (
            "Show live-policy readiness honestly "
            f"(live_policy_result_passed={readiness.get('live_policy_result_passed')}, "
            f"gpu_host={gpu_state})."
        ),
    ]
    if blockers:
        outline.append("Close with the current blocker and the next graphics-capable NVIDIA host run.")
    else:
        outline.append("Close with the first successful closed-loop SimLingo route video.")
    return outline


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _read_text(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.expanduser().read_text(encoding="utf-8", errors="replace")


def _latest_progress_lines(text: str | None, *, limit: int) -> list[str]:
    if text is None:
        return []
    lines = text.splitlines()
    latest = _section_lines(lines, "Latest Evidence")
    if latest:
        return _first_complete_bullets(latest, max_bullets=8, max_lines=limit)
    return lines[-limit:]


def _first_complete_bullets(lines: list[str], *, max_bullets: int, max_lines: int) -> list[str]:
    bullets: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("- "):
            if current:
                bullets.append(current)
            current = [line]
        elif current and (line.startswith("  ") or line.startswith("\t")):
            current.append(line)
    if current:
        bullets.append(current)
    output: list[str] = []
    for bullet in bullets[:max_bullets]:
        if len(output) + len(bullet) > max_lines:
            break
        output.extend(bullet)
    return output


def _section_lines(lines: list[str], heading: str) -> list[str]:
    target = f"## {heading}".lower()
    in_section = False
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == target:
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section and stripped:
            output.append(line)
    return output


def _parse_open_blockers(text: str | None) -> list[str]:
    if text is None:
        return []
    lines = text.splitlines()
    in_open = False
    blockers: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and stripped.lstrip("#").strip().lower() in {"open", "open blockers"}:
            in_open = True
            continue
        if in_open and stripped.startswith("#"):
            break
        if not in_open:
            continue
        if stripped.startswith(("- ", "* ")):
            if current:
                blockers.append(" ".join(current).strip())
            current = [stripped[2:].strip()]
        elif current and (line.startswith("  ") or line.startswith("\t")):
            current.append(stripped)
    if current:
        blockers.append(" ".join(current).strip())
    return [blocker for blocker in blockers if blocker and blocker.lower() != "none currently."]


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _path_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _markdown(payload: dict[str, Any]) -> str:
    gpu_host = _mapping(payload.get("gpu_host"))
    lines = [
        f"# {payload['title']}",
        "",
        "## Thesis",
        "",
        str(payload["thesis"]),
        "",
        "## Readiness",
        "",
    ]
    for key, value in _mapping(payload.get("ood_readiness")).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Metric Highlights", ""])
    for key, value in _mapping(payload.get("metric_highlights")).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## GPU Host",
            "",
            f"- overall_state: `{gpu_host.get('overall_state')}`",
            f"- recommendation: {gpu_host.get('recommendation')}",
            "",
            "## Open Blockers",
            "",
        ]
    )
    blockers = list(payload.get("open_blockers", []))
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("None.")
    lines.extend(["", "## Demo Outline", ""])
    for index, step in enumerate(list(payload.get("demo_outline", [])), start=1):
        lines.append(f"{index}. {step}")
    lines.extend(["", "## Recent Progress", ""])
    for line in list(payload.get("progress_tail", [])):
        lines.append(f"> {line}")
    return "\n".join(lines) + "\n"


__all__ = ["build_submission_dossier", "write_submission_dossier"]
