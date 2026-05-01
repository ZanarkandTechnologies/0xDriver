from pathlib import Path
import unittest

from driverx.core.config import DatasetConfig
from driverx.datasets.waymo_e2e import load_waymo_frame


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


if __name__ == "__main__":
    unittest.main()
