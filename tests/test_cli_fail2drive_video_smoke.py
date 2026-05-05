import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main


def _write_fake_config(tmp_path: Path) -> Path:
    root = tmp_path / "fail2drive"
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
    (root / "tools").mkdir()
    (root / "tools" / "generate_video.py").write_text("# fake video tool\n", encoding="utf-8")
    config_path = tmp_path / "carla.json"
    config_path.write_text(
        json.dumps(
            {
                "carla": {"host": "host.docker.internal", "port": 2000, "timeout_s": 0.25},
                "fail2drive": {
                    "root": str(root),
                    "route_path": "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml",
                    "agent_path": "team_code/visu_agent.py",
                    "output_dir": str(tmp_path / "unused"),
                    "track": "MAP",
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


class Fail2DriveVideoSmokeCliTest(unittest.TestCase):
    def test_plan_fail2drive_video_smoke_cli_writes_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _write_fake_config(tmp_path)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "plan-fail2drive-video-smoke",
                        "--config",
                        str(config_path),
                        "--traffic-manager-port",
                        "8000",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "video-smoke",
                    ]
                )
            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["dry_run"])
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)
        self.assertIn("LIVE_VISU", result["env"])
        self.assertIn("--traffic-manager-port", result["run_command"])
        self.assertIn("-f", result["video_command"])
        self.assertIn("rgb_folder", result["expected_outputs"])
        self.assertIn("video", result["expected_outputs"])

    def test_plan_fail2drive_video_smoke_cli_can_disable_live_visu(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _write_fake_config(tmp_path)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "plan-fail2drive-video-smoke",
                        "--config",
                        str(config_path),
                        "--no-live-visu",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "video-smoke",
                    ]
                )
            result = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertNotIn("LIVE_VISU", result["env"])


if __name__ == "__main__":
    unittest.main()
