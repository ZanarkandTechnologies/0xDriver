from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig, ReasonerConfig
from driverx.pipeline.scene_run import run_scene
from driverx.submission.waymo_packager import (
    WaymoSubmissionDependencyError,
    package_run_dir,
)


class SubmissionPackagerTest(unittest.TestCase):
    def _run_dir(self, tmp: str, account_name: str = "") -> Path:
        config = DriverConfig(
            dataset=DatasetConfig(kind="fixture", name="construction_merge"),
            reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
            output=OutputConfig(root=Path(tmp), run_id="submission"),
            account_name=account_name,
        )
        run_scene(config)
        return Path(tmp) / "submission"

    def test_dry_run_package_reports_non_official_mode(self) -> None:
        with TemporaryDirectory() as tmp:
            package = package_run_dir(self._run_dir(tmp))
            self.assertFalse(package["official"])
            self.assertEqual(package["predictions"], 1)

    def test_official_package_without_waymo_deps_fails_clearly(self) -> None:
        with TemporaryDirectory() as tmp:
            with patch(
                "driverx.submission.waymo_packager.importlib.import_module",
                side_effect=ModuleNotFoundError("waymo_open_dataset"),
            ):
                with self.assertRaises(WaymoSubmissionDependencyError) as context:
                    package_run_dir(self._run_dir(tmp), official=True)
        self.assertIn("Official Waymo submission packaging requires", str(context.exception))

    def test_official_package_validates_required_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            with patch(
                "driverx.submission.waymo_packager.importlib.import_module",
                return_value=_fake_submission_module(),
            ):
                with self.assertRaises(ValueError) as context:
                    package_run_dir(self._run_dir(tmp), official=True)
        self.assertIn("account_name", str(context.exception))

    def test_official_package_writes_with_fake_waymo_module(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = self._run_dir(tmp, account_name="participant@example.com")
            with patch(
                "driverx.submission.waymo_packager.importlib.import_module",
                return_value=_fake_submission_module(),
            ):
                package = package_run_dir(run_dir, official=True)
            self.assertTrue(package["official"])
            self.assertEqual(package["predictions"], 1)
            self.assertEqual(Path(package["protobuf_shard"]).read_bytes(), b"official")


def _fake_submission_module() -> object:
    class FakeTrajectoryPrediction:
        def __init__(self, pos_x: list[float], pos_y: list[float]) -> None:
            self.pos_x = pos_x
            self.pos_y = pos_y

    class FakeFrameTrajectoryPredictions:
        def __init__(
            self,
            frame_name: str,
            trajectory: FakeTrajectoryPrediction,
        ) -> None:
            self.frame_name = frame_name
            self.trajectory = trajectory

    class FakeE2EDChallengeSubmission:
        class SubmissionType:
            E2ED_SUBMISSION = 1

        def __init__(self, predictions: list[FakeFrameTrajectoryPredictions]) -> None:
            self.predictions = predictions
            self.submission_type = 0
            self.authors: list[str] = []
            self.affiliation = ""
            self.account_name = ""
            self.unique_method_name = ""
            self.method_link = ""
            self.description = ""
            self.uses_public_model_pretraining = False
            self.public_model_names: list[str] = []
            self.num_model_parameters = ""

        def SerializeToString(self) -> bytes:
            return b"official"

    return SimpleNamespace(
        TrajectoryPrediction=FakeTrajectoryPrediction,
        FrameTrajectoryPredictions=FakeFrameTrajectoryPredictions,
        E2EDChallengeSubmission=FakeE2EDChallengeSubmission,
    )


if __name__ == "__main__":
    unittest.main()
