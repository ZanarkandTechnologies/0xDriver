import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.pipeline.ood_suite_report import build_ood_suite_report


class OodSuiteReportTest(unittest.TestCase):
    def test_build_report_normalizes_suite_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_fixture_inputs(root)
            summary = build_ood_suite_report(
                root / "report",
                scenario_summary_path=paths["scenario_summary"],
                route_pack_path=paths["route_pack"],
                overlay_plan_path=paths["overlay_plan"],
                sidecar_plan_path=paths["sidecar_plan"],
                sidecar_run_path=paths["sidecar_run"],
                rag_comparison_path=paths["rag_comparison"],
                simlingo_result_path=paths["simlingo_result"],
                blockers_path=paths["blockers"],
            )
            json_exists = Path(summary["json_path"]).exists()
            report_exists = Path(summary["report_path"]).exists()

        self.assertTrue(json_exists)
        self.assertTrue(report_exists)
        self.assertEqual(summary["metric_highlights"]["generated_recipe_count"], 2)
        self.assertEqual(summary["metric_highlights"]["bench2drive_route_count"], 2)
        self.assertEqual(summary["metric_highlights"]["companion_actor_count"], 1)
        self.assertEqual(summary["metric_highlights"]["rag_driving_score_delta"], 37.0)
        self.assertTrue(summary["metric_highlights"]["simlingo_success"])
        self.assertEqual(summary["metric_highlights"]["simlingo_driving_score"], 88.0)
        self.assertTrue(summary["readiness"]["sidecar_run_passed"])
        self.assertFalse(summary["readiness"]["has_open_blockers"])

    def test_remote_simlingo_evidence_shape_surfaces_route_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario_summary = root / "scenario_summary.json"
            simlingo_evidence = root / "remote_simlingo_evidence.json"
            scenario_summary.write_text(json.dumps({"num_seeds": 1, "num_recipes": 1}), encoding="utf-8")
            simlingo_evidence.write_text(
                json.dumps(
                    {
                        "state": "route_infrastructure_blocked",
                        "blockers": [
                            "CARLA server did not open port before route execution; route log: run.log"
                        ],
                        "selected_result_path": None,
                        "route_log_path": "run.log",
                        "compatibility_path": "torch_cuda_compatibility.json",
                        "diagnostics_path": "carla_runtime_diagnostics.md",
                        "result_report": None,
                    }
                ),
                encoding="utf-8",
            )
            summary = build_ood_suite_report(
                root / "report",
                scenario_summary_path=scenario_summary,
                simlingo_result_path=simlingo_evidence,
            )

        simlingo_component = summary["components"][1]
        self.assertEqual(simlingo_component["status"], "blocked")
        self.assertFalse(simlingo_component["metrics"]["success"])
        self.assertEqual(summary["metric_highlights"]["simlingo_state"], "route_infrastructure_blocked")
        self.assertEqual(simlingo_component["metrics"]["route_log_path"], "run.log")
        self.assertEqual(simlingo_component["metrics"]["diagnostics_path"], "carla_runtime_diagnostics.md")
        self.assertFalse(summary["readiness"]["live_policy_result_passed"])
        self.assertIn("simlingo_result: CARLA server did not open port", summary["open_blockers"][0])

    def test_missing_optional_input_is_reported_as_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario_summary = root / "scenario_summary.json"
            scenario_summary.write_text(json.dumps({"num_seeds": 1, "num_recipes": 1}), encoding="utf-8")
            summary = build_ood_suite_report(
                root / "report",
                scenario_summary_path=scenario_summary,
                sidecar_run_path=root / "missing_sidecar_run.json",
            )

        self.assertIn("sidecar_run", summary["missing_components"])
        self.assertTrue(summary["readiness"]["has_open_blockers"])
        self.assertIn("Missing artifact", summary["open_blockers"][0])

    def test_no_inputs_fails_clearly(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "At least one"):
                build_ood_suite_report(Path(tmp) / "report")

    def test_blocker_parser_accepts_common_open_heading_variants(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            blockers = root / "blockers.md"
            blockers.write_text(
                "# Blockers\n\n### Open Blockers\n\n* first blocker\n  with detail\n- second blocker\n\n## Resolved\n\n- done\n",
                encoding="utf-8",
            )
            scenario_summary = root / "scenario_summary.json"
            scenario_summary.write_text(json.dumps({"num_seeds": 1, "num_recipes": 1}), encoding="utf-8")
            summary = build_ood_suite_report(
                root / "report",
                scenario_summary_path=scenario_summary,
                blockers_path=blockers,
            )

        self.assertEqual(summary["components"][1]["metrics"]["open_blocker_count"], 2)
        self.assertIn("first blocker with detail", summary["open_blockers"][0])
        self.assertTrue(summary["readiness"]["has_open_blockers"])


def _write_fixture_inputs(root: Path) -> dict[str, Path]:
    payloads = {
        "scenario_summary": {
            "num_seeds": 2,
            "num_recipes": 2,
            "mutation_counts": {"regional_driving_behavior": 1, "visual_noise": 1},
        },
        "route_pack": {
            "num_routes": 2,
            "route_suite_path": "/tmp/routes.xml",
            "simlingo_command_plan_path": "/tmp/simlingo_command_plan.json",
        },
        "overlay_plan": {
            "num_routes": 2,
            "routes": [
                {
                    "script_plan": {
                        "actors": [
                            {"actor_ref": "ego", "role": "ego"},
                            {"actor_ref": "companion_actor_0", "role": "companion_actor_static"},
                        ]
                    }
                }
            ],
            "validation_errors": [],
        },
        "sidecar_plan": {
            "commands": [{"label": "simlingo"}, {"label": "overlay"}],
            "expected_outputs": ["/tmp/result.json"],
            "blockers": [],
        },
        "sidecar_run": {
            "success": True,
            "duration_s": 1.25,
            "process_records": [{"label": "simlingo"}, {"label": "overlay"}],
            "plan_blockers": [],
            "error": None,
        },
        "rag_comparison": {
            "policy": "mock",
            "scenario_id": "construction_merge::motorcycle_filtering",
            "improvement": {"driving_score_delta": 37.0, "infraction_delta": -2},
            "live_model_claim": False,
        },
        "simlingo_result": {
            "record": {
                "success": True,
                "status": "Completed",
                "driving_score": 88.0,
                "route_completion": 97.0,
                "primary_route": {"route_id": "75"},
            },
            "blocker": None,
        },
    }
    paths: dict[str, Path] = {}
    for label, payload in payloads.items():
        path = root / f"{label}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths[label] = path
    blocker_path = root / "blockers.md"
    blocker_path.write_text("# Blockers\n\n## Open\n\n- None currently.\n", encoding="utf-8")
    paths["blockers"] = blocker_path
    return paths


if __name__ == "__main__":
    unittest.main()
