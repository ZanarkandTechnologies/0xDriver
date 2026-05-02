from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.core.config import DatasetConfig
from driverx.datasets.waymo_e2e import WaymoDependencyError, load_waymo_frame


class WaymoLoaderTest(unittest.TestCase):
    def test_load_waymo_json_fixture(self) -> None:
        frame = load_waymo_frame(
            DatasetConfig(
                kind="waymo",
                name="waymo_json_fixture",
                path=Path("tests/fixtures/waymo_e2e_frame.json"),
            )
        )
        self.assertEqual(frame.frame_name, "waymo_json_fixture_001")
        self.assertEqual(len(frame.front_images), 3)
        self.assertEqual(len(frame.future_xy or []), 20)

    def test_missing_waymo_path_fails_clearly(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_waymo_frame(DatasetConfig(kind="waymo", name="missing", path=None))

    def test_tfrecord_without_optional_deps_fails_with_install_hint(self) -> None:
        with TemporaryDirectory() as tmp:
            shard = Path(tmp) / "sample.tfrecord"
            shard.write_bytes(b"")
            with patch(
                "driverx.datasets.waymo_e2e.importlib.import_module",
                side_effect=ModuleNotFoundError("tensorflow"),
            ):
                with self.assertRaises(WaymoDependencyError) as context:
                    load_waymo_frame(
                        DatasetConfig(
                            kind="waymo",
                            name="sample",
                            path=shard,
                        )
                    )
        self.assertIn("Install optional Waymo dependencies", str(context.exception))

    def test_tfrecord_glob_reaches_optional_dependency_boundary(self) -> None:
        with TemporaryDirectory() as tmp:
            shard = Path(tmp) / "validation.tfrecord-00000"
            shard.write_bytes(b"")
            glob_path = Path(tmp) / "*.tfrecord*"
            with patch(
                "driverx.datasets.waymo_e2e.importlib.import_module",
                side_effect=ModuleNotFoundError("tensorflow"),
            ):
                with self.assertRaises(WaymoDependencyError):
                    load_waymo_frame(
                        DatasetConfig(
                            kind="waymo",
                            name="sample",
                            path=glob_path,
                        )
                    )


if __name__ == "__main__":
    unittest.main()
