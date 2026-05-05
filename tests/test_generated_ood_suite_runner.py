import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline import GeneratedOodSuiteConfig, run_generated_ood_suite


def _fake_fail2drive_root(root: Path) -> None:
    (root / "leaderboard" / "leaderboard").mkdir(parents=True)
    (root / "leaderboard" / "leaderboard" / "leaderboard_evaluator_local.py").write_text(
        "# fake evaluator\n",
        encoding="utf-8",
    )
    (root / "team_code").mkdir()
    (root / "team_code" / "visu_agent.py").write_text("# fake agent\n", encoding="utf-8")
    (root / "tools").mkdir()
    (root / "tools" / "generate_video.py").write_text("# fake video\n", encoding="utf-8")
    (root / "fail2drive_split").mkdir()
    for name in [
        "Base_Animals_0076.xml",
        "Generalization_PedestriansOnRoad_1088.xml",
        "Generalization_CustomObstacles_1028.xml",
    ]:
        (root / "fail2drive_split" / name).write_text(
            (Path("tests/fixtures/fail2drive_like/fail2drive_split") / name).read_text(encoding="utf-8"),
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
                    "output_dir": str(path.parent / "unused"),
                    "track": "MAP",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_scenario_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "scenario": {
                    "seeds_path": "tests/fixtures/fail2drive_like/seeds.json",
                    "count": 3,
                    "random_seed": 11,
                    "mutations": "lane_blockage,occlusion,visual_noise",
                }
            }
        ),
        encoding="utf-8",
    )


class GeneratedOodSuiteRunnerTest(unittest.TestCase):
    def test_generated_ood_suite_runner_builds_limited_suite(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fail2drive = tmp_path / "fail2drive"
            _fake_fail2drive_root(fail2drive)
            scenario_config = tmp_path / "scenario.json"
            carla_config = tmp_path / "carla.json"
            _write_scenario_config(scenario_config)
            _write_carla_config(carla_config, fail2drive)

            summary = run_generated_ood_suite(
                GeneratedOodSuiteConfig(
                    scenario_config_path=scenario_config,
                    carla_config_path=carla_config,
                    output_root=tmp_path,
                    run_id="suite",
                    route_root=fail2drive,
                    limit=2,
                )
            )
            route_pack_exists = Path(summary["route_pack_path"]).exists()
            overlay_plan_exists = Path(summary["overlay_plan_path"]).exists()
            overlay_evidence_exists = Path(summary["overlay_evidence_path"]).exists()
            first_smoke_exists = Path(summary["recipe_records"][0]["video_smoke_plan_path"]).exists()
            first_evidence_exists = Path(summary["recipe_records"][0]["route_evidence_path"]).exists()

        self.assertEqual(summary["num_recipes"], 2)
        self.assertEqual(summary["readiness"]["recipe_count"], 2)
        self.assertEqual(len(summary["recipe_records"]), 2)
        self.assertTrue(route_pack_exists)
        self.assertTrue(overlay_plan_exists)
        self.assertTrue(overlay_evidence_exists)
        self.assertTrue(first_smoke_exists)
        self.assertTrue(first_evidence_exists)
        self.assertGreater(summary["readiness"]["blocker_count"], 0)

    def test_generated_ood_suite_cli_accepts_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fail2drive = tmp_path / "fail2drive"
            _fake_fail2drive_root(fail2drive)
            scenario_config = tmp_path / "scenario.json"
            carla_config = tmp_path / "carla.json"
            _write_scenario_config(scenario_config)
            _write_carla_config(carla_config, fail2drive)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-generated-ood-suite",
                        "--scenario-config",
                        str(scenario_config),
                        "--carla-config",
                        str(carla_config),
                        "--route-root",
                        str(fail2drive),
                        "--limit",
                        "1",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "suite-cli",
                    ]
                )
            summary = json.loads(stream.getvalue())
            json_exists = Path(summary["json_path"]).exists()
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["num_recipes"], 1)
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)


if __name__ == "__main__":
    unittest.main()
