import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.submission_dossier import build_submission_dossier


class SubmissionDossierTest(unittest.TestCase):
    def test_build_submission_dossier_combines_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)

            dossier = build_submission_dossier(
                root / "dossier",
                ood_suite_manifest_path=paths["ood"],
                gpu_host_suitability_path=paths["gpu"],
                progress_path=paths["progress"],
                blockers_path=paths["blockers"],
            )
            report = Path(dossier["report_path"]).read_text(encoding="utf-8")
            json_exists = Path(dossier["json_path"]).exists()

        self.assertTrue(json_exists)
        self.assertEqual(dossier["metric_highlights"]["rag_driving_score_delta"], 37.0)
        self.assertEqual(dossier["gpu_host"]["overall_state"], "blocked")
        self.assertIn("current blocker", dossier["demo_outline"][-1])
        self.assertIn("0xDriver Minimal-Shot OOD Driving Harness", report)
        self.assertIn("graphics-capable NVIDIA host", report)
        self.assertIn("TASK-020 CARLA graphics blocker", report)

    def test_build_submission_dossier_cli_writes_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-submission-dossier",
                        "--ood-suite-manifest",
                        str(paths["ood"]),
                        "--gpu-host-suitability",
                        str(paths["gpu"]),
                        "--progress",
                        str(paths["progress"]),
                        "--blockers",
                        str(paths["blockers"]),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "dossier",
                    ]
                )
            result = json.loads(stream.getvalue())
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(report_exists)
        self.assertFalse(result["ood_readiness"]["live_policy_result_passed"])


def _write_inputs(root: Path) -> dict[str, Path]:
    ood = root / "ood_suite_manifest.json"
    ood.write_text(
        json.dumps(
            {
                "readiness": {
                    "scenario_generation_ready": True,
                    "live_policy_result_passed": False,
                    "has_open_blockers": True,
                },
                "metric_highlights": {
                    "generated_recipe_count": 2,
                    "rag_driving_score_delta": 37.0,
                },
            }
        ),
        encoding="utf-8",
    )
    gpu = root / "gpu_host_suitability.json"
    gpu.write_text(
        json.dumps(
            {
                "overall_state": "blocked",
                "recommendation": "Use a graphics-capable NVIDIA host.",
                "blockers": ["CARLA graphics runtime is blocked."],
                "warnings": ["Root disk is small."],
            }
        ),
        encoding="utf-8",
    )
    progress = root / "progress.md"
    progress.write_text("# Progress\n\n- recent item\n", encoding="utf-8")
    blockers = root / "blockers.md"
    blockers.write_text(
        "# Blockers\n\n## Open\n\n- TASK-020 CARLA graphics blocker\n",
        encoding="utf-8",
    )
    return {"ood": ood, "gpu": gpu, "progress": progress, "blockers": blockers}


if __name__ == "__main__":
    unittest.main()
