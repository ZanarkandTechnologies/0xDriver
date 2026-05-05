import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.policies import build_policy_runtime_matrix


def _fake_fail2drive_root(root: Path) -> None:
    (root / "leaderboard" / "leaderboard").mkdir(parents=True)
    (root / "leaderboard" / "leaderboard" / "leaderboard_evaluator_local.py").write_text(
        "# fake evaluator\n",
        encoding="utf-8",
    )
    (root / "team_code").mkdir()
    (root / "team_code" / "visu_agent.py").write_text("# fake agent\n", encoding="utf-8")
    (root / "fail2drive_split").mkdir()
    (root / "fail2drive_split" / "Generalization_PedestriansOnRoad_1088.xml").write_text(
        "<routes />\n",
        encoding="utf-8",
    )


def _write_carla_config(path: Path, root: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "carla": {"host": "127.0.0.1", "port": 2000, "timeout_s": 0.25},
                "fail2drive": {
                    "root": str(root),
                    "route_path": "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml",
                    "agent_path": "team_code/visu_agent.py",
                    "output_dir": str(path.parent / "out"),
                    "track": "MAP",
                },
            }
        ),
        encoding="utf-8",
    )


class PolicyRuntimeMatrixTest(unittest.TestCase):
    def test_matrix_marks_local_and_fail2drive_rows_ready_independently(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "fail2drive"
            _fake_fail2drive_root(root)
            carla_config = tmp_path / "carla.json"
            suite_path = root / "fail2drive_split" / "Generalization_PedestriansOnRoad_1088.xml"
            _write_carla_config(carla_config, root)

            summary = build_policy_runtime_matrix(
                tmp_path / "matrix",
                carla_config_path=carla_config,
                suite_path=suite_path,
            )
            rows = {row["policy"]: row for row in summary["rows"]}

        self.assertEqual(rows["mock"]["ready_state"], "ready")
        self.assertEqual(rows["mock-memory"]["ready_state"], "ready")
        self.assertEqual(rows["hybrid"]["ready_state"], "ready")
        self.assertEqual(rows["fail2drive-basic"]["ready_state"], "dry_run_ready")
        self.assertEqual(rows["fail2drive-expert"]["ready_state"], "dry_run_ready")
        self.assertIsNone(rows["fail2drive-basic"]["blocker"])
        self.assertEqual(rows["simlingo"]["ready_state"], "blocked")
        self.assertIn("Pass --simlingo-config", rows["simlingo"]["blocker"])
        self.assertIn("TASK-038", rows["alpamayo"]["blocker"])

    def test_matrix_blocks_missing_fail2drive_without_blocking_mock(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            carla_config = tmp_path / "carla.json"
            _write_carla_config(carla_config, tmp_path / "missing-fail2drive")

            summary = build_policy_runtime_matrix(tmp_path / "matrix", carla_config_path=carla_config)
            rows = {row["policy"]: row for row in summary["rows"]}

        self.assertEqual(rows["mock"]["ready_state"], "ready")
        self.assertEqual(rows["fail2drive-basic"]["ready_state"], "blocked")
        self.assertIn("Missing", rows["fail2drive-basic"]["blocker"])

    def test_policy_runtime_matrix_cli_writes_report(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "fail2drive"
            _fake_fail2drive_root(root)
            carla_config = tmp_path / "carla.json"
            _write_carla_config(carla_config, root)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-policy-runtime-matrix",
                        "--carla-config",
                        str(carla_config),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "matrix",
                    ]
                )
            summary = json.loads(stream.getvalue())
            json_exists = Path(summary["json_path"]).exists()
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)
        self.assertGreaterEqual(summary["ready_count"], 5)


if __name__ == "__main__":
    unittest.main()
