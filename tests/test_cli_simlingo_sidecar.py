import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main


class SimLingoSidecarCliTest(unittest.TestCase):
    def test_plan_simlingo_sidecar_cli_writes_plan(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            simlingo_plan = root / "simlingo_command_plan.json"
            overlay_plan = root / "overlay_injection_plan.json"
            simlingo_plan.write_text(
                json.dumps(
                    {
                        "command": ["python", "leaderboard_evaluator.py"],
                        "cwd": str(root / "simlingo"),
                        "env": {"PYTHONPATH": "simlingo"},
                        "expected_outputs": [str(root / "out" / "seed_1_res.json")],
                        "live_blockers": [],
                    }
                ),
                encoding="utf-8",
            )
            overlay_plan.write_text(
                json.dumps({"num_routes": 1, "validation_errors": [], "routes": [{"recipe_id": "one"}]}),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "plan-simlingo-sidecar",
                        "--simlingo-plan",
                        str(simlingo_plan),
                        "--overlay-plan",
                        str(overlay_plan),
                        "--docker-carla-client",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "sidecar",
                    ]
                )
            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["route_count"], 1)
        self.assertEqual(result["commands"][0]["label"], "simlingo_bench2drive")
        self.assertEqual(result["commands"][1]["label"], "driverx_overlay_injector")
        self.assertIn("scripts/run_carla_client_docker.sh", result["commands"][1]["command"])
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)


if __name__ == "__main__":
    unittest.main()
