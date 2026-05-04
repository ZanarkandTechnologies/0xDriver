import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.simulators import (
    compact_simlingo_result_summary,
    parse_simlingo_result,
    write_simlingo_result_report,
)


def _write_result(path: Path) -> None:
    payload = {
        "_checkpoint": {
            "global_record": {
                "status": "Failed",
                "scores_mean": {
                    "score_route": 0,
                    "score_penalty": 1.0,
                    "score_composed": 0.0,
                },
                "meta": {
                    "duration_game": 0.05,
                    "duration_system": 3.004,
                    "exceptions": [["RouteScenario_1711_rep0", 0, "Failed - Agent crashed"]]
                },
            },
            "progress": [1, 1],
            "records": [
                {
                    "route_id": "RouteScenario_1711_rep0",
                    "scenario_name": "ParkingCutIn_1",
                    "town_name": "Town12",
                    "status": "Failed - Agent crashed",
                    "infractions": {"collisions_vehicle": [], "route_timeout": []},
                    "scores": {
                        "score_route": 0,
                        "score_penalty": 1.0,
                        "score_composed": 0.0,
                    },
                    "meta": {"duration_game": 0.05, "duration_system": 3.004},
                }
            ],
        },
        "entry_status": "Finished",
        "eligible": True,
        "sensors": ["carla_camera", "carla_imu"],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class SimLingoResultIngestionTest(unittest.TestCase):
    def test_parse_simlingo_failure_result(self) -> None:
        with TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "seed_1_res.json"
            _write_result(result_path)

            record = parse_simlingo_result(result_path)

        self.assertEqual(record.route_id, "RouteScenario_1711_rep0")
        self.assertEqual(record.scenario_name, "ParkingCutIn_1")
        self.assertEqual(record.town_name, "Town12")
        self.assertFalse(record.success)
        self.assertEqual(record.driving_score, 0.0)
        self.assertEqual(record.route_completion, 0.0)
        self.assertEqual(record.exception_summary, "RouteScenario_1711_rep0: Failed - Agent crashed")
        self.assertEqual(record.sensors, ["carla_camera", "carla_imu"])
        self.assertEqual(record.progress_completed, 1)
        self.assertEqual(record.progress_total, 1)
        self.assertEqual(record.route_count, 1)

    def test_parse_completed_multi_route_result_uses_global_averages(self) -> None:
        with TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "multi_route_res.json"
            result_path.write_text(
                json.dumps(
                    {
                        "_checkpoint": {
                            "global_record": {
                                "status": "Completed",
                                "scores_mean": {
                                    "score_route": 90.0,
                                    "score_penalty": 0.9,
                                    "score_composed": 81.0,
                                },
                                "infractions": {"collisions_vehicle": 0.0},
                                "meta": {"duration_game": 30.0, "duration_system": 60.0},
                            },
                            "progress": [2, 2],
                            "records": [
                                {
                                    "route_id": "route-a",
                                    "scenario_name": "ParkingCutIn_1",
                                    "town_name": "Town12",
                                    "status": "Completed",
                                    "scores": {
                                        "score_route": 100,
                                        "score_penalty": 1.0,
                                        "score_composed": 100.0,
                                    },
                                    "infractions": {},
                                    "meta": {"duration_game": 10.0, "duration_system": 20.0},
                                },
                                {
                                    "route_id": "route-b",
                                    "scenario_name": "HazardAtSideLane_1",
                                    "town_name": "Town12",
                                    "status": "Completed",
                                    "scores": {
                                        "score_route": 80,
                                        "score_penalty": 0.8,
                                        "score_composed": 64.0,
                                    },
                                    "infractions": {},
                                    "meta": {"duration_game": 20.0, "duration_system": 40.0},
                                },
                            ],
                        },
                        "entry_status": "Finished",
                        "eligible": True,
                        "sensors": ["carla_camera"],
                    }
                ),
                encoding="utf-8",
            )

            record = parse_simlingo_result(result_path)

        self.assertTrue(record.success)
        self.assertEqual(record.status, "Completed")
        self.assertEqual(record.route_count, 2)
        self.assertEqual(record.progress_completed, 2)
        self.assertEqual(record.progress_total, 2)
        self.assertEqual(record.driving_score, 81.0)
        self.assertEqual(record.route_completion, 90.0)
        self.assertEqual(record.infraction_penalty, 0.9)
        self.assertEqual(record.routes[0].driving_score, 100.0)
        self.assertEqual(record.routes[1].driving_score, 64.0)

    def test_write_report_summarizes_cuda_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_path = root / "seed_1_res.json"
            compat_path = root / "torch_cuda_compatibility.json"
            log_path = root / "run_one_route.log"
            _write_result(result_path)
            compat_path.write_text(
                json.dumps(
                    {
                        "torch_version": "2.2.0+cu121",
                        "device_name": "NVIDIA RTX PRO 6000 Blackwell Server Edition",
                        "required_arch": "sm_120",
                        "compiled_arches": ["sm_86", "sm_90"],
                        "compatible": False,
                    }
                ),
                encoding="utf-8",
            )
            log_path.write_text(
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
            summary = write_simlingo_result_report(
                root / "out",
                parse_simlingo_result(result_path),
                compatibility_path=compat_path,
                route_log_path=log_path,
            )
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertIn("CUDA no-kernel-image", summary["blocker"])
        self.assertIn("sm_120", summary["blocker"])
        self.assertIn("RouteScenario_1711_rep0", report)
        self.assertIn("CUDA Compatibility", report)
        self.assertFalse(summary["record"]["success"])
        compact = compact_simlingo_result_summary(summary)
        self.assertNotIn("route_log", compact)
        self.assertNotIn("tail", json.dumps(compact))
        self.assertEqual(compact["primary_route"]["route_id"], "RouteScenario_1711_rep0")
        self.assertNotIn("infractions", compact["primary_route"])


if __name__ == "__main__":
    unittest.main()
