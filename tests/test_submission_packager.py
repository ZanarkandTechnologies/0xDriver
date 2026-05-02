from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig, ReasonerConfig
from driverx.pipeline.scene_run import run_scene
from driverx.submission.waymo_packager import (
    WaymoSubmissionDependencyError,
    package_run_dir,
)


class SubmissionPackagerTest(unittest.TestCase):
    def _run_dir(self, tmp: str) -> Path:
        config = DriverConfig(
            dataset=DatasetConfig(kind="fixture", name="construction_merge"),
            reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
            output=OutputConfig(root=Path(tmp), run_id="submission"),
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


if __name__ == "__main__":
    unittest.main()
