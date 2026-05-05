import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.simulators import (
    scan_simlingo_evidence,
    write_simlingo_evidence_report,
)


def _write_result(path: Path, *, status: str = "Completed") -> None:
    success = status == "Completed"
    payload = {
        "_checkpoint": {
            "global_record": {
                "status": status,
                "scores_mean": {
                    "score_route": 95.0 if success else 0.0,
                    "score_penalty": 1.0,
                    "score_composed": 95.0 if success else 0.0,
                },
                "meta": {
                    "duration_game": 12.0,
                    "duration_system": 18.0,
                    "exceptions": [] if success else [["route-1", 0, "Failed - Agent crashed"]],
                },
            },
            "progress": [1, 1],
            "records": [
                {
                    "route_id": "route-1",
                    "scenario_name": "ParkingCutIn_1",
                    "town_name": "Town12",
                    "status": status,
                    "scores": {
                        "score_route": 95.0 if success else 0.0,
                        "score_penalty": 1.0,
                        "score_composed": 95.0 if success else 0.0,
                    },
                    "infractions": {"route_timeout": []},
                    "meta": {"duration_game": 12.0, "duration_system": 18.0},
                }
            ],
        },
        "entry_status": "Finished",
        "eligible": True,
        "sensors": ["carla_camera"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class SimLingoEvidenceTest(unittest.TestCase):
    def test_missing_artifact_root_is_clean_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "missing"

            scan = scan_simlingo_evidence(root)

        self.assertEqual(scan.state, "artifact_root_missing")
        self.assertIn("does not exist", scan.blockers[0])
        self.assertFalse(scan.has_route_result)

    def test_running_bootstrap_without_result_is_incomplete(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bootstrap.log").write_text(
                "== remote SimLingo bootstrap ==\nInstalling pip dependencies:",
                encoding="utf-8",
            )

            scan = scan_simlingo_evidence(root)

        self.assertEqual(scan.state, "bootstrap_incomplete")
        self.assertFalse(scan.bootstrap_complete)
        self.assertIn("incomplete or still running", scan.blockers[0])

    def test_cuda_route_result_is_precise_runtime_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bootstrap.log").write_text("bootstrap complete: /workspace/artifacts/task20\n", encoding="utf-8")
            _write_result(root / "res" / "seed_1_res.json", status="Failed - Agent crashed")
            (root / "run_one_route_with_carla.log").write_text(
                "\n".join(
                    [
                        "load_world success",
                        "traffic_manager init success",
                        "> Running the route",
                        "CUDA error: no kernel image is available for execution on the device",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "torch_cuda_compatibility.json").write_text(
                json.dumps(
                    {
                        "device_name": "NVIDIA RTX PRO 6000 Blackwell Server Edition",
                        "required_arch": "sm_120",
                        "compiled_arches": ["sm_86", "sm_90"],
                        "compatible": False,
                    }
                ),
                encoding="utf-8",
            )

            scan = scan_simlingo_evidence(root)

        self.assertEqual(scan.state, "route_result_blocked")
        self.assertEqual(scan.selected_result_path.name, "seed_1_res.json")
        self.assertIn("CUDA no-kernel-image", scan.blockers[0])
        self.assertIn("sm_120", scan.blockers[0])
        self.assertEqual(scan.result_summary["primary_route"]["route_id"], "route-1")

    def test_route_log_carla_port_timeout_is_infrastructure_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bootstrap.log").write_text("== next manual/live command ==\n", encoding="utf-8")
            (root / "run_one_route_with_carla.log").write_text(
                "CARLA did not open port 20000 within 120s: [Errno 111] Connection refused\n",
                encoding="utf-8",
            )
            (root / "carla_runtime_diagnostics.md").write_text(
                "ERROR_INCOMPATIBLE_DRIVER\n",
                encoding="utf-8",
            )

            scan = scan_simlingo_evidence(root)

        self.assertEqual(scan.state, "route_infrastructure_blocked")
        self.assertIn("CARLA server did not open port", scan.blockers[0])
        self.assertEqual(scan.route_log_path.name, "run_one_route_with_carla.log")
        self.assertEqual(scan.diagnostics_path.name, "carla_runtime_diagnostics.md")

    def test_successful_route_result_writes_json_and_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "pulled"
            out = Path(tmp) / "out"
            root.mkdir()
            (root / "bootstrap.log").write_text("bootstrap complete: /workspace/artifacts/task20\n", encoding="utf-8")
            _write_result(root / "res" / "seed_1_res.json")

            summary = write_simlingo_evidence_report(out, scan_simlingo_evidence(root))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

            self.assertEqual(summary["state"], "route_result_success")
            self.assertEqual(summary["blockers"], [])
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertIn("Remote SimLingo Evidence", report)
            self.assertIn("route-1", report)
            self.assertTrue(Path(summary["result_report"]["json_path"]).exists())

    def test_cli_summarizes_pulled_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "pulled"
            root.mkdir()
            _write_result(root / "res" / "seed_1_res.json")
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "summarize-simlingo-evidence",
                        "--artifact-root",
                        str(root),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "remote-evidence",
                    ]
                )

            result = json.loads(stream.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["state"], "route_result_success")
            self.assertEqual(result["blockers"], [])
            self.assertTrue(Path(result["json_path"]).exists())
            self.assertTrue(Path(result["report_path"]).exists())


if __name__ == "__main__":
    unittest.main()
