import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.datasets.fixtures import load_fixture_frame
from driverx.policies import (
    PolicyContext,
    PolicySetupError,
    run_policy_fixture,
    sample_memory_entries,
    select_policy_adapter,
)


class PolicyAdapterTest(unittest.TestCase):
    def test_mock_adapter_returns_structured_intent_action_and_latency(self) -> None:
        frame = load_fixture_frame("construction_merge")
        adapter = select_policy_adapter("mock")

        decision = adapter.decide(PolicyContext(frame=frame))

        self.assertEqual(decision.policy_id, "mock")
        self.assertEqual(decision.action.mode, "trajectory_chunk")
        self.assertEqual(len(decision.action.trajectory.points_xy), 20)
        self.assertGreaterEqual(decision.latency_ms, 0.0)
        self.assertIn("No memory", decision.reason_summary)

    def test_mock_adapter_memory_changes_behavior(self) -> None:
        frame = load_fixture_frame("construction_merge")
        adapter = select_policy_adapter("mock", memory_aware=True)

        decision = adapter.decide(
            PolicyContext(frame=frame, memories=sample_memory_entries())
        )

        self.assertEqual(decision.intent.target_behavior, "yield_then_proceed")
        self.assertEqual(decision.intent.speed_profile, "decelerate_then_creep")
        self.assertTrue(decision.action.control["memory_guided"])
        self.assertEqual(decision.retrieved_memory_ids, ["mem-sample-motorcycle-filtering"])

    def test_hybrid_planner_adapter_acts_as_fallback(self) -> None:
        frame = load_fixture_frame("construction_merge")
        adapter = select_policy_adapter("hybrid")

        decision = adapter.decide(PolicyContext(frame=frame))

        self.assertEqual(decision.adapter_kind, "local_hybrid")
        self.assertIsNotNone(decision.action.trajectory)
        self.assertIn("hybrid", decision.reason_summary.lower())

    def test_setup_checked_stubs_raise_guidance(self) -> None:
        frame = load_fixture_frame("construction_merge")
        adapter = select_policy_adapter("alpamayo")

        with self.assertRaisesRegex(PolicySetupError, "Alpamayo"):
            adapter.decide(PolicyContext(frame=frame))

    def test_policy_fixture_runner_writes_decision(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_policy_fixture(
                policy="mock",
                fixture="construction_merge",
                output_root=Path(tmp),
                run_id="policy",
                memory_entries=sample_memory_entries(),
                memory_aware=True,
            )
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))

        self.assertEqual(payload["adapter_kind"], "mock_memory")
        self.assertEqual(payload["retrieved_memory_ids"], ["mem-sample-motorcycle-filtering"])

    def test_policy_fixture_runner_writes_setup_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_policy_fixture(
                policy="simlingo",
                fixture="construction_merge",
                output_root=Path(tmp),
                run_id="policy",
            )
            path_exists = Path(summary["json_path"]).exists()

        self.assertIn("setup_blocker", summary)
        self.assertTrue(path_exists)


if __name__ == "__main__":
    unittest.main()
