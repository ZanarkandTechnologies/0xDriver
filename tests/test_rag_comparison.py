import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.pipeline.rag_comparison import run_rag_comparison


class RagComparisonHarnessTest(unittest.TestCase):
    def test_mock_comparison_pairs_same_scenario_with_and_without_memory(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_rag_comparison(
                policy="mock",
                fixture="construction_merge",
                behavior_id="motorcycle_filtering",
                output_root=Path(tmp),
                run_id="rag",
            )
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))

        self.assertEqual(payload["scenario_id"], "construction_merge::motorcycle_filtering")
        self.assertEqual([record["mode"] for record in payload["records"]], ["policy", "policy+memory"])
        self.assertFalse(payload["records"][0]["success_proxy"])
        self.assertTrue(payload["records"][1]["success_proxy"])
        self.assertGreater(payload["improvement"]["driving_score_delta"], 0)
        self.assertEqual(payload["live_model_claim"], False)

    def test_report_includes_memory_ids_behavior_metrics_and_latency(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_rag_comparison(
                policy="mock",
                fixture="construction_merge",
                behavior_id="motorcycle_filtering",
                output_root=Path(tmp),
                run_id="rag",
            )
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertIn("mem-sample-motorcycle-filtering", report)
        self.assertIn("driving_score_delta", report)
        self.assertIn("latency_ms", report)
        self.assertIn("motorcycle_filtering", report)

    def test_live_policy_blocker_is_logged_without_breaking_harness(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_rag_comparison(
                policy="alpamayo",
                fixture="construction_merge",
                behavior_id="motorcycle_filtering",
                output_root=Path(tmp),
                run_id="rag",
            )

        self.assertIn("setup", summary["notes"])
        self.assertEqual(summary["records"][0]["infractions"], ["policy_setup_blocked"])
        self.assertIn("Alpamayo", summary["records"][0]["setup_blocker"])


if __name__ == "__main__":
    unittest.main()
