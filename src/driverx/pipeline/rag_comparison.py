"""Retrieval-augmented policy comparison harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.behaviors import BehaviorTrace, default_behavior_plans, simulate_behavior
from driverx.core.artifacts import prepare_run_dir
from driverx.core.types import FrameBundle
from driverx.datasets.fixtures import load_fixture_frame
from driverx.policies import PolicyContext, PolicyDecision, PolicySetupError
from driverx.policies import sample_memory_entries, select_policy_adapter


@dataclass(frozen=True)
class ComparisonRecord:
    mode: str
    policy_id: str
    success_proxy: bool
    route_completion: float
    driving_score: float
    infractions: list[str]
    retrieved_memory_ids: list[str]
    behavior_metrics: dict[str, float]
    latency_ms: float | None
    decision: dict[str, Any] | None
    setup_blocker: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "policy_id": self.policy_id,
            "success_proxy": self.success_proxy,
            "route_completion": self.route_completion,
            "driving_score": self.driving_score,
            "infractions": self.infractions,
            "retrieved_memory_ids": self.retrieved_memory_ids,
            "behavior_metrics": self.behavior_metrics,
            "latency_ms": self.latency_ms,
            "decision": self.decision,
            "setup_blocker": self.setup_blocker,
        }


def run_rag_comparison(
    *,
    policy: str,
    fixture: str,
    behavior_id: str,
    output_root: Path,
    run_id: str,
) -> dict[str, Any]:
    frame = load_fixture_frame(fixture)
    behavior = _load_behavior(behavior_id)
    run_dir = prepare_run_dir(output_root, run_id)
    baseline = _run_mode(
        mode="policy",
        policy=policy,
        frame=frame,
        behavior=behavior,
        use_memory=False,
    )
    memory_guided = _run_mode(
        mode="policy+memory",
        policy=policy,
        frame=frame,
        behavior=behavior,
        use_memory=True,
    )
    summary = _summary(
        policy=policy,
        fixture=fixture,
        behavior=behavior,
        records=[baseline, memory_guided],
    )
    return write_rag_comparison(run_dir, summary)


def write_rag_comparison(run_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "rag_comparison.json"
    report_path = run_dir / "rag_comparison.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(_comparison_markdown(summary), encoding="utf-8")
    return {
        **summary,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _run_mode(
    *,
    mode: str,
    policy: str,
    frame: FrameBundle,
    behavior: BehaviorTrace,
    use_memory: bool,
) -> ComparisonRecord:
    memories = sample_memory_entries() if use_memory else []
    adapter = select_policy_adapter(policy, memory_aware=use_memory)
    try:
        decision = adapter.decide(PolicyContext(frame=frame, memories=memories))
    except PolicySetupError as exc:
        return ComparisonRecord(
            mode=mode,
            policy_id=policy,
            success_proxy=False,
            route_completion=0.0,
            driving_score=0.0,
            infractions=["policy_setup_blocked"],
            retrieved_memory_ids=[memory.entry_id for memory in memories],
            behavior_metrics=behavior.metrics,
            latency_ms=None,
            decision=None,
            setup_blocker=str(exc),
        )
    success, infractions = _score_decision(decision, behavior)
    route_completion = 0.92 if success else 0.74
    if decision.action.control.get("memory_guided"):
        route_completion += 0.03
    driving_score = route_completion * 100.0 - len(infractions) * 8.0
    return ComparisonRecord(
        mode=mode,
        policy_id=decision.policy_id,
        success_proxy=success,
        route_completion=round(route_completion, 4),
        driving_score=round(max(0.0, driving_score), 4),
        infractions=infractions,
        retrieved_memory_ids=decision.retrieved_memory_ids,
        behavior_metrics=behavior.metrics,
        latency_ms=decision.latency_ms,
        decision=decision.to_jsonable(),
    )


def _score_decision(
    decision: PolicyDecision,
    behavior: BehaviorTrace,
) -> tuple[bool, list[str]]:
    infractions: list[str] = []
    target_speed = float(decision.action.control.get("target_speed_mps", 0.0))
    lateral_pressure = behavior.metrics.get("max_lateral_speed_mps", 0.0)
    hard_brake = behavior.metrics.get("max_deceleration_mps2", 0.0)
    wrong_way = behavior.metrics.get("wrong_way_distance_m", 0.0)
    if lateral_pressure >= 4.0 and target_speed > 5.0:
        infractions.append("too_fast_near_lateral_ood_actor")
    if hard_brake >= 8.0 and decision.intent.target_behavior != "yield_then_proceed":
        infractions.append("did_not_yield_to_sudden_brake_pressure")
    if wrong_way > 5.0 and not decision.action.control.get("yield", False):
        infractions.append("did_not_yield_to_wrong_way_shoulder_actor")
    if not decision.action.control.get("memory_guided", False) and lateral_pressure >= 4.0:
        infractions.append("no_memory_for_regional_lateral_behavior")
    return len(infractions) == 0, infractions


def _summary(
    *,
    policy: str,
    fixture: str,
    behavior: BehaviorTrace,
    records: list[ComparisonRecord],
) -> dict[str, Any]:
    baseline = records[0]
    memory = records[1]
    improvement = {
        "success_proxy_delta": int(memory.success_proxy) - int(baseline.success_proxy),
        "driving_score_delta": round(memory.driving_score - baseline.driving_score, 4),
        "route_completion_delta": round(memory.route_completion - baseline.route_completion, 4),
        "infraction_delta": len(memory.infractions) - len(baseline.infractions),
    }
    note = (
        "memory improved the mock policy outcome"
        if improvement["driving_score_delta"] > 0
        else "memory did not improve the mock policy outcome"
    )
    if baseline.setup_blocker or memory.setup_blocker:
        note = "comparison blocked by selected live policy setup"
    return {
        "scenario_id": f"{fixture}::{behavior.plan.behavior_id}",
        "policy": policy,
        "fixture": fixture,
        "behavior_id": behavior.plan.behavior_id,
        "behavior_metrics": behavior.metrics,
        "records": [record.to_jsonable() for record in records],
        "improvement": improvement,
        "notes": note,
        "live_model_claim": False,
    }


def _load_behavior(behavior_id: str) -> BehaviorTrace:
    plans = {plan.behavior_id: plan for plan in default_behavior_plans()}
    if behavior_id not in plans:
        raise ValueError(f"Unknown behavior id: {behavior_id}")
    return simulate_behavior(plans[behavior_id])


def _comparison_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# RAG Policy Comparison",
        "",
        f"- scenario_id: `{summary['scenario_id']}`",
        f"- policy: `{summary['policy']}`",
        f"- behavior_id: `{summary['behavior_id']}`",
        f"- live_model_claim: `{summary['live_model_claim']}`",
        f"- notes: {summary['notes']}",
        "",
        "## Improvement",
        "",
    ]
    for key, value in dict(summary["improvement"]).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Runs", ""])
    for record in list(summary["records"]):
        lines.extend(
            [
                f"### {record['mode']}",
                "",
                f"- success_proxy: `{record['success_proxy']}`",
                f"- driving_score: `{record['driving_score']}`",
                f"- route_completion: `{record['route_completion']}`",
                f"- latency_ms: `{record['latency_ms']}`",
                f"- retrieved_memory_ids: `{', '.join(record['retrieved_memory_ids'])}`",
                f"- infractions: `{', '.join(record['infractions'])}`",
            ]
        )
        if record.get("setup_blocker"):
            lines.append(f"- setup_blocker: {record['setup_blocker']}")
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "ComparisonRecord",
    "run_rag_comparison",
    "write_rag_comparison",
]
