import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.simulators import inspect_simlingo_checkout, load_simlingo_run_config
from driverx.simulators import plan_simlingo_run, write_simlingo_plan


def _make_fake_simlingo_root(root: Path) -> None:
    for path in [
        "team_code",
        "Bench2Drive/leaderboard/leaderboard",
        "Bench2Drive/scenario_runner",
        "simlingo_training",
    ]:
        (root / path).mkdir(parents=True, exist_ok=True)
    for path in [
        "README.md",
        "environment.yaml",
        "team_code/agent_simlingo.py",
        "team_code/config_simlingo.py",
        "Bench2Drive/leaderboard/leaderboard/leaderboard_evaluator.py",
    ]:
        (root / path).write_text("# fake\n", encoding="utf-8")


class SimLingoAdapterTest(unittest.TestCase):
    def test_inspect_fake_checkout_reports_cuda_and_apple_silicon_limits(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "simlingo"
            _make_fake_simlingo_root(root)

            readiness = inspect_simlingo_checkout(root)

        self.assertTrue(readiness.exists)
        self.assertEqual(readiness.carla_version, "0.9.15")
        self.assertEqual(readiness.python_version, "3.8")
        self.assertTrue(readiness.requires_cuda)
        self.assertFalse(readiness.apple_silicon_live_supported)
        self.assertEqual(readiness.blockers, [])

    def test_inspect_missing_checkout_reports_blockers(self) -> None:
        readiness = inspect_simlingo_checkout(Path("/tmp/definitely-not-simlingo"))

        self.assertFalse(readiness.exists)
        self.assertTrue(any("checkout not found" in blocker for blocker in readiness.blockers))
        self.assertFalse(readiness.required_files["agent"])

    def test_plan_simlingo_run_builds_bench2drive_evaluation_command(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "simlingo"
            _make_fake_simlingo_root(root)
            carla_root = Path(tmp) / "carla0915"
            (carla_root / "carla" / "dist").mkdir(parents=True, exist_ok=True)
            (carla_root / "carla" / "dist" / "carla-0.9.15-py3.7-linux-x86_64.egg").write_text(
                "",
                encoding="utf-8",
            )
            config_path = Path(tmp) / "simlingo.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "simlingo:",
                        f"  root: {root}",
                        "  checkpoint_path: checkpoints/model.pt",
                        "  route_path: routes/route.xml",
                        f"  output_dir: {Path(tmp) / 'out'}",
                        "  seed: 3",
                        "  world_port: 21000",
                        "  traffic_manager_port: 11000",
                        "carla:",
                        f"  root: {carla_root}",
                    ]
                ),
                encoding="utf-8",
            )
            config = load_simlingo_run_config(config_path)
            plan = plan_simlingo_run(config)

        self.assertEqual(plan.cwd, root.resolve())
        self.assertIn("--track=SENSORS", plan.command)
        self.assertIn("--traffic-manager-seed=3", plan.command)
        self.assertTrue(any(item.endswith("agent_simlingo.py") for item in plan.command))
        self.assertEqual(plan.env["SCENARIO_RUNNER_ROOT"], str(root.resolve() / "Bench2Drive" / "scenario_runner"))
        self.assertIn("carla-0.9.15-py3.7-linux-x86_64.egg", plan.env["PYTHONPATH"])

    def test_plan_simlingo_run_reports_non_linux_runtime_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "simlingo"
            _make_fake_simlingo_root(root)
            config_path = Path(tmp) / "simlingo.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "simlingo:",
                        f"  root: {root}",
                        f"  output_dir: {Path(tmp) / 'out'}",
                        "carla:",
                        f"  root: {Path(tmp) / 'carla0915'}",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("driverx.simulators.simlingo.platform.system", return_value="Darwin"):
                plan = plan_simlingo_run(load_simlingo_run_config(config_path))

        self.assertTrue(
            any("Linux NVIDIA" in blocker for blocker in plan.live_blockers),
            msg=plan.live_blockers,
        )

    def test_plan_simlingo_run_reports_missing_nvidia_runtime_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "simlingo"
            _make_fake_simlingo_root(root)
            config_path = Path(tmp) / "simlingo.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "simlingo:",
                        f"  root: {root}",
                        f"  output_dir: {Path(tmp) / 'out'}",
                        "carla:",
                        f"  root: {Path(tmp) / 'carla0915'}",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("driverx.simulators.simlingo.platform.system", return_value="Linux"):
                with patch("driverx.simulators.simlingo.shutil.which", return_value=None):
                    plan = plan_simlingo_run(load_simlingo_run_config(config_path))

        self.assertTrue(
            any("NVIDIA GPU" in blocker for blocker in plan.live_blockers),
            msg=plan.live_blockers,
        )

    def test_default_checkpoint_path_matches_remote_model_layout(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "simlingo"
            _make_fake_simlingo_root(root)
            config_path = Path(tmp) / "simlingo.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "simlingo:",
                        f"  root: {root}",
                        f"  output_dir: {Path(tmp) / 'out'}",
                        "carla:",
                        f"  root: {Path(tmp) / 'carla0915'}",
                    ]
                ),
                encoding="utf-8",
            )
            config = load_simlingo_run_config(config_path)
            plan = plan_simlingo_run(config)

        self.assertEqual(
            config.checkpoint_path,
            Path("/workspace/models/simlingo/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt"),
        )
        self.assertIn(
            "--agent-config=/workspace/models/simlingo/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt",
            plan.command,
        )

    def test_write_simlingo_plan_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "simlingo"
            _make_fake_simlingo_root(root)
            config_path = Path(tmp) / "simlingo.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "simlingo:",
                        f"  root: {root}",
                        f"  output_dir: {Path(tmp) / 'out'}",
                        "carla:",
                        f"  root: {Path(tmp) / 'carla0915'}",
                    ]
                ),
                encoding="utf-8",
            )
            plan = plan_simlingo_run(load_simlingo_run_config(config_path))
            summary = write_simlingo_plan(Path(tmp) / "run", plan)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertIn("leaderboard_evaluator.py", " ".join(payload["command"]))
        self.assertIn("# SimLingo Command Plan", report)


if __name__ == "__main__":
    unittest.main()
