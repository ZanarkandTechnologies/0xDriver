import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.cli import main
from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig, ReasonerConfig
from driverx.pipeline.batch_run import run_batch
from driverx.pipeline.scene_run import run_scene
from driverx.simulators import CarlaEgoSmokeResult, CarlaProbeResult


def _write_fake_carla_config(tmp: Path) -> Path:
    root = tmp / "fail2drive"
    (root / "leaderboard" / "leaderboard").mkdir(parents=True)
    (root / "leaderboard" / "leaderboard" / "leaderboard_evaluator_local.py").write_text(
        "# fake evaluator\n",
        encoding="utf-8",
    )
    (root / "team_code").mkdir()
    (root / "team_code" / "visu_agent.py").write_text("# fake agent\n", encoding="utf-8")
    (root / "fail2drive_split").mkdir()
    route = root / "fail2drive_split" / "Generalization_PedestriansOnRoad_1088.xml"
    route.write_text("<routes />\n", encoding="utf-8")
    config_path = tmp / "carla.json"
    config_path.write_text(
        json.dumps(
            {
                "carla": {"host": "127.0.0.1", "port": 2000, "timeout_s": 0.01},
                "fail2drive": {
                    "root": str(root),
                    "route_path": "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml",
                    "agent_path": "team_code/visu_agent.py",
                    "output_dir": str(tmp / "carla_outputs"),
                    "track": "MAP",
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


class CliTest(unittest.TestCase):
    def test_fixture_batch_cli_and_api_defaults_agree(self) -> None:
        with TemporaryDirectory() as tmp:
            api_config = DriverConfig(
                dataset=DatasetConfig(kind="fixture", name="construction_merge"),
                reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
                output=OutputConfig(root=Path(tmp), run_id="api-batch"),
            )
            api_summary = run_batch(api_config)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-batch",
                        "--config",
                        "configs/mock.yaml",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "cli-batch",
                    ]
                )
            cli_summary = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(cli_summary["num_scenes"], api_summary["num_scenes"])
        self.assertEqual(
            [scene["fixture"] for scene in cli_summary["scenes"]],
            [scene["fixture"] for scene in api_summary["scenes"]],
        )

    def test_run_batch_accepts_waymo_frame_range_flags(self) -> None:
        with patch(
            "driverx.pipeline.batch_run.run_batch",
            return_value={"ok": True},
        ) as run_batch:
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "run-batch",
                        "--config",
                        "configs/waymo_fixture.yaml",
                        "--frame-start",
                        "4",
                        "--frame-count",
                        "2",
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertEqual(run_batch.call_args.kwargs["frame_start"], 4)
        self.assertEqual(run_batch.call_args.kwargs["frame_count"], 2)
        self.assertIsNone(run_batch.call_args.kwargs["fixture_names"])

    def test_run_experiment_accepts_waymo_frame_range_flags(self) -> None:
        with patch(
            "driverx.pipeline.experiment_run.run_experiment",
            return_value={"ok": True},
        ) as run_experiment:
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "run-experiment",
                        "--config",
                        "configs/waymo_fixture.yaml",
                        "--frame-start",
                        "4",
                        "--frame-count",
                        "2",
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertEqual(run_experiment.call_args.kwargs["frame_start"], 4)
        self.assertEqual(run_experiment.call_args.kwargs["frame_count"], 2)

    def test_official_packaging_missing_dependency_is_operator_facing(self) -> None:
        with TemporaryDirectory() as tmp:
            config = DriverConfig(
                dataset=DatasetConfig(kind="fixture", name="construction_merge"),
                reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
                output=OutputConfig(root=Path(tmp), run_id="cli"),
            )
            run_scene(config)
            stream = StringIO()
            with patch(
                "driverx.submission.waymo_packager.importlib.import_module",
                side_effect=ModuleNotFoundError("waymo_open_dataset"),
            ), redirect_stderr(stream):
                exit_code = main(
                    [
                        "package-submission",
                        "--run-dir",
                        str(Path(tmp) / "cli"),
                        "--official",
                    ]
                )
        self.assertEqual(exit_code, 2)
        self.assertIn("driverx error:", stream.getvalue())
        self.assertNotIn("Traceback", stream.getvalue())

    def test_forge_scenarios_cli_writes_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "forge-scenarios",
                        "--config",
                        "configs/scenario_forge.sample.yaml",
                        "--count",
                        "2",
                        "--seed",
                        "3",
                    ]
                )
            summary = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["num_recipes"], 2)
        self.assertTrue(Path(summary["recipes_path"]).exists())

    def test_build_memory_cli_writes_bank(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-memory",
                        "--results",
                        "tests/fixtures/fail2drive_like/results.json",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "memory",
                    ]
                )
            summary = json.loads(stream.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(summary["num_entries"], 2)
            self.assertTrue(Path(summary["json_path"]).exists())

    def test_plan_carla_run_cli_writes_dry_run_plan(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _write_fake_carla_config(tmp_path)
            recipe_path = tmp_path / "recipe.json"
            recipe_path.write_text(
                json.dumps(
                    {
                        "recipe_id": "generated-test",
                        "parent_seed_id": "seed",
                        "mutation": "occlusion",
                        "actors": [],
                        "environment": {},
                        "expected_failure_mode": "hidden pedestrian",
                        "memory_query": ["occlusion"],
                        "route_path": "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml",
                    }
                ),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "plan-carla-run",
                        "--config",
                        str(config_path),
                        "--recipe",
                        str(recipe_path),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "plan",
                    ]
                )
            plan = json.loads(stream.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertTrue(plan["dry_run"])
            self.assertTrue(Path(plan["plan_path"]).exists())

    def test_plan_carla_run_cli_requires_recipe_id_for_suite(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _write_fake_carla_config(tmp_path)
            recipe_path = tmp_path / "recipes.json"
            recipe_path.write_text(
                json.dumps(
                    {
                        "recipes": [
                            {
                                "recipe_id": "one",
                                "parent_seed_id": "seed",
                                "mutation": "occlusion",
                                "actors": [],
                                "environment": {},
                                "expected_failure_mode": "hidden pedestrian",
                                "memory_query": ["occlusion"],
                                "route_path": "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml",
                            },
                            {
                                "recipe_id": "two",
                                "parent_seed_id": "seed",
                                "mutation": "visual_noise",
                                "actors": [],
                                "environment": {},
                                "expected_failure_mode": "distractor",
                                "memory_query": ["visual_noise"],
                                "route_path": "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stderr(stream):
                exit_code = main(
                    [
                        "plan-carla-run",
                        "--config",
                        str(config_path),
                        "--recipe",
                        str(recipe_path),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "plan",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("pass --recipe-id", stream.getvalue())

    def test_plan_carla_run_cli_selects_explicit_recipe_id(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _write_fake_carla_config(tmp_path)
            recipe_path = tmp_path / "recipes.json"
            recipe_path.write_text(
                json.dumps(
                    {
                        "recipes": [
                            {
                                "recipe_id": "one",
                                "parent_seed_id": "seed",
                                "mutation": "occlusion",
                                "actors": [],
                                "environment": {},
                                "expected_failure_mode": "hidden pedestrian",
                                "memory_query": ["occlusion"],
                                "route_path": "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml",
                            },
                            {
                                "recipe_id": "two",
                                "parent_seed_id": "seed",
                                "mutation": "visual_noise",
                                "actors": [],
                                "environment": {},
                                "expected_failure_mode": "distractor",
                                "memory_query": ["visual_noise"],
                                "route_path": "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "plan-carla-run",
                        "--config",
                        str(config_path),
                        "--recipe",
                        str(recipe_path),
                        "--recipe-id",
                        "two",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "plan",
                    ]
                )
            plan = json.loads(stream.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertIn("two", plan["command"][-1] if plan["command"] else "")
            self.assertTrue(Path(plan["plan_path"]).exists())

    def test_smoke_carla_cli_reports_unreachable_without_traceback(self) -> None:
        stream = StringIO()
        with redirect_stdout(stream):
            exit_code = main(["smoke-carla", "--config", "configs/carla_local.sample.yaml"])
        result = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertIn("reachable", result)

    def test_probe_carla_cli_writes_probe_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with patch(
                "driverx.simulators.probe_carla_client",
                return_value=CarlaProbeResult(
                    connected=True,
                    host="host.docker.internal",
                    port=2000,
                    map_name="Carla/Maps/Town10HD_Opt",
                    actor_count=23,
                ),
            ), redirect_stdout(stream):
                exit_code = main(
                    [
                        "probe-carla",
                        "--config",
                        "configs/carla_local.sample.yaml",
                        "--host",
                        "host.docker.internal",
                        "--port",
                        "2000",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "probe",
                    ]
                )
            result = json.loads(stream.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertTrue(result["connected"])
            self.assertEqual(result["map_name"], "Carla/Maps/Town10HD_Opt")
            self.assertTrue(Path(result["json_path"]).exists())
            self.assertTrue(Path(result["report_path"]).exists())

    def test_spawn_ego_smoke_cli_writes_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with patch(
                "driverx.simulators.run_ego_spawn_smoke",
                return_value=CarlaEgoSmokeResult(
                    connected=True,
                    host="host.docker.internal",
                    port=2000,
                    map_name="Carla/Maps/Town10HD_Opt",
                    ego_actor_id=101,
                    camera_actor_id=202,
                    spawned_actor_ids=[101, 202],
                    destroyed_actor_ids=[202, 101],
                    track_count=10,
                ),
            ), redirect_stdout(stream):
                exit_code = main(
                    [
                        "spawn-ego-smoke",
                        "--config",
                        "configs/carla_local.sample.yaml",
                        "--host",
                        "host.docker.internal",
                        "--port",
                        "2000",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "ego",
                    ]
                )
            result = json.loads(stream.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertTrue(result["connected"])
            self.assertEqual(result["destroyed_actor_ids"], [202, 101])
            self.assertTrue(Path(result["json_path"]).exists())


if __name__ == "__main__":
    unittest.main()
