import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main


class OodSuiteReportCliTest(unittest.TestCase):
    def test_build_ood_suite_report_cli_writes_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario_summary = root / "scenario_summary.json"
            sidecar_run = root / "sidecar_run.json"
            scenario_summary.write_text(
                json.dumps({"num_seeds": 1, "num_recipes": 3, "mutation_counts": {"occlusion": 3}}),
                encoding="utf-8",
            )
            sidecar_run.write_text(
                json.dumps(
                    {
                        "success": True,
                        "duration_s": 0.5,
                        "process_records": [{"label": "simlingo"}],
                        "plan_blockers": [],
                    }
                ),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-ood-suite-report",
                        "--scenario-summary",
                        str(scenario_summary),
                        "--sidecar-run",
                        str(sidecar_run),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "ood-report",
                    ]
                )
            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)
        self.assertEqual(result["metric_highlights"]["generated_recipe_count"], 3)
        self.assertTrue(result["metric_highlights"]["sidecar_run_success"])


if __name__ == "__main__":
    unittest.main()
