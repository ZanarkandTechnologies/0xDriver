from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.cli import main
from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig, ReasonerConfig
from driverx.pipeline.scene_run import run_scene


class CliTest(unittest.TestCase):
    def test_run_batch_accepts_waymo_frame_range_flags(self) -> None:
        with patch(
            "driverx.pipeline.batch_run.run_batch",
            return_value={"ok": True},
        ) as run_batch:
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


if __name__ == "__main__":
    unittest.main()
