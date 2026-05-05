"""Timed process runner for SimLingo plus DriverX sidecar plans."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SidecarProcessRecord:
    label: str
    command: list[str]
    cwd: Path
    start_after_s: float
    stdout_path: Path
    stderr_path: Path
    pid: int | None = None
    started_at_s: float | None = None
    finished_at_s: float | None = None
    exit_code: int | None = None
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "command": self.command,
            "cwd": str(self.cwd),
            "start_after_s": self.start_after_s,
            "stdout_path": str(self.stdout_path),
            "stderr_path": str(self.stderr_path),
            "pid": self.pid,
            "started_at_s": self.started_at_s,
            "finished_at_s": self.finished_at_s,
            "duration_s": (
                round(self.finished_at_s - self.started_at_s, 6)
                if self.started_at_s is not None and self.finished_at_s is not None
                else None
            ),
            "exit_code": self.exit_code,
            "error": self.error,
        }


@dataclass(frozen=True)
class SimLingoSidecarRunResult:
    plan_path: Path
    run_dir: Path
    dry_run: bool
    timeout_s: float | None
    success: bool
    started_at_monotonic_s: float
    finished_at_monotonic_s: float
    process_records: list[SidecarProcessRecord]
    plan_blockers: list[str]
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "plan_path": str(self.plan_path),
            "run_dir": str(self.run_dir),
            "dry_run": self.dry_run,
            "timeout_s": self.timeout_s,
            "success": self.success,
            "started_at_monotonic_s": self.started_at_monotonic_s,
            "finished_at_monotonic_s": self.finished_at_monotonic_s,
            "duration_s": round(self.finished_at_monotonic_s - self.started_at_monotonic_s, 6),
            "process_records": [record.to_jsonable() for record in self.process_records],
            "plan_blockers": self.plan_blockers,
            "error": self.error,
        }


def run_simlingo_sidecar_processes(
    plan_path: Path,
    run_dir: Path,
    *,
    timeout_s: float | None = None,
    dry_run: bool = False,
) -> SimLingoSidecarRunResult:
    """Execute commands from a TASK-023 sidecar plan with start delays."""

    plan_file = plan_path.expanduser().resolve()
    payload = json.loads(plan_file.read_text(encoding="utf-8"))
    commands = [dict(entry) for entry in list(payload.get("commands", []))]
    plan_blockers = [str(blocker) for blocker in list(payload.get("blockers", []))]
    run_dir = run_dir.expanduser().resolve()
    log_dir = run_dir / "process-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    started_at = time.monotonic()
    records: list[SidecarProcessRecord] = []
    running: list[tuple[subprocess.Popen[bytes], SidecarProcessRecord, Any, Any]] = []
    error: str | None = _plan_blocker_error(plan_blockers)

    for command_index, command_entry in enumerate(commands):
        label = _safe_label(str(command_entry.get("label", f"command-{command_index}")))
        command = [str(item) for item in list(command_entry.get("command", []))]
        cwd = Path(str(command_entry.get("cwd", "."))).expanduser()
        start_after_s = float(command_entry.get("start_after_s", 0.0))
        stdout_path = log_dir / f"{command_index:02d}-{label}.stdout.log"
        stderr_path = log_dir / f"{command_index:02d}-{label}.stderr.log"
        target_start = started_at + start_after_s
        if not dry_run:
            _sleep_until(target_start)
        record = SidecarProcessRecord(
            label=label,
            command=command,
            cwd=cwd,
            start_after_s=start_after_s,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
        validation_error = _validate_command_record(record)
        if validation_error is not None:
            records.append(_record_error(record, validation_error))
            continue
        if dry_run or error is not None:
            records.append(record)
            continue
        stdout_file = stdout_path.open("wb")
        stderr_file = stderr_path.open("wb")
        env = os.environ.copy()
        env.update({str(key): str(value) for key, value in dict(command_entry.get("env", {})).items()})
        try:
            process = subprocess.Popen(
                command,
                cwd=str(cwd),
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
            )
        except OSError as exc:
            stdout_file.close()
            stderr_file.close()
            records.append(_record_error(record, f"Failed to start command: {exc}"))
            continue
        running.append(
            (
                process,
                SidecarProcessRecord(
                    label=record.label,
                    command=record.command,
                    cwd=record.cwd,
                    start_after_s=record.start_after_s,
                    stdout_path=record.stdout_path,
                    stderr_path=record.stderr_path,
                    pid=process.pid,
                    started_at_s=round(time.monotonic() - started_at, 6),
                ),
                stdout_file,
                stderr_file,
            )
        )

    deadline = started_at + timeout_s if timeout_s is not None else None
    while running:
        next_running: list[tuple[subprocess.Popen[bytes], SidecarProcessRecord, Any, Any]] = []
        for process, record, stdout_file, stderr_file in running:
            exit_code = process.poll()
            if exit_code is None:
                if deadline is not None and time.monotonic() > deadline:
                    process.terminate()
                    error = f"Sidecar run timed out after {timeout_s} seconds."
                    exit_code = process.wait(timeout=5)
                else:
                    next_running.append((process, record, stdout_file, stderr_file))
                    continue
            stdout_file.close()
            stderr_file.close()
            records.append(
                SidecarProcessRecord(
                    label=record.label,
                    command=record.command,
                    cwd=record.cwd,
                    start_after_s=record.start_after_s,
                    stdout_path=record.stdout_path,
                    stderr_path=record.stderr_path,
                    pid=record.pid,
                    started_at_s=record.started_at_s,
                    finished_at_s=round(time.monotonic() - started_at, 6),
                    exit_code=exit_code,
                    error=record.error,
                )
            )
        running = next_running
        if running:
            time.sleep(0.05)

    records.sort(key=lambda record: (record.started_at_s is None, record.started_at_s or record.start_after_s))
    if not commands and error is None:
        error = "Sidecar plan contains no commands."
    success = bool(commands) and error is None and all(
        record.error is None and (dry_run or record.exit_code == 0)
        for record in records
    )
    return SimLingoSidecarRunResult(
        plan_path=plan_file,
        run_dir=run_dir,
        dry_run=dry_run,
        timeout_s=timeout_s,
        success=success,
        started_at_monotonic_s=started_at,
        finished_at_monotonic_s=time.monotonic(),
        process_records=records,
        plan_blockers=plan_blockers,
        error=error,
    )


def write_simlingo_sidecar_run(
    run_dir: Path,
    result: SimLingoSidecarRunResult,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "simlingo_sidecar_run.json"
    report_path = run_dir / "simlingo_sidecar_run.md"
    payload = result.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_run_markdown(result), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _record_error(record: SidecarProcessRecord, error: str) -> SidecarProcessRecord:
    return SidecarProcessRecord(
        label=record.label,
        command=record.command,
        cwd=record.cwd,
        start_after_s=record.start_after_s,
        stdout_path=record.stdout_path,
        stderr_path=record.stderr_path,
        error=error,
    )


def _validate_command_record(record: SidecarProcessRecord) -> str | None:
    if not record.command:
        return "Command entry is empty."
    if not record.cwd.exists():
        return f"Command cwd does not exist: {record.cwd}"
    return None


def _plan_blocker_error(plan_blockers: list[str]) -> str | None:
    if not plan_blockers:
        return None
    return "Sidecar plan has blockers: " + "; ".join(plan_blockers)


def _safe_label(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value)
    return cleaned.strip("-") or "command"


def _sleep_until(target: float) -> None:
    while True:
        remaining = target - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 0.1))


def _run_markdown(result: SimLingoSidecarRunResult) -> str:
    lines = [
        "# SimLingo Sidecar Run",
        "",
        f"- success: `{result.success}`",
        f"- dry_run: `{result.dry_run}`",
        f"- timeout_s: `{result.timeout_s}`",
        f"- duration_s: `{round(result.finished_at_monotonic_s - result.started_at_monotonic_s, 6)}`",
        f"- process_count: `{len(result.process_records)}`",
        f"- plan_blockers: `{len(result.plan_blockers)}`",
        f"- plan_path: `{result.plan_path}`",
        "",
        "## Processes",
        "",
    ]
    for record in result.process_records:
        lines.extend(
            [
                f"### {record.label}",
                "",
                f"- pid: `{record.pid}`",
                f"- exit_code: `{record.exit_code}`",
                f"- started_at_s: `{record.started_at_s}`",
                f"- finished_at_s: `{record.finished_at_s}`",
                f"- error: `{record.error}`",
                f"- stdout: `{record.stdout_path}`",
                f"- stderr: `{record.stderr_path}`",
                "",
            ]
        )
    if result.error:
        lines.extend(["## Run Error", "", result.error, ""])
    if result.plan_blockers:
        lines.extend(["## Plan Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in result.plan_blockers)
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "SidecarProcessRecord",
    "SimLingoSidecarRunResult",
    "run_simlingo_sidecar_processes",
    "write_simlingo_sidecar_run",
]
