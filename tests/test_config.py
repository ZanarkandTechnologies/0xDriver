from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.core.config import load_config


class ConfigTest(unittest.TestCase):
    def test_load_mock_config(self) -> None:
        config = load_config(Path("configs/mock.yaml"))
        self.assertEqual(config.dataset.kind, "fixture")
        self.assertEqual(config.dataset.name, "construction_merge")
        self.assertEqual(config.reasoner.backend, "mock")

    def test_missing_config_fails_clearly(self) -> None:
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.yaml"
            with self.assertRaises(FileNotFoundError):
                load_config(missing)

    def test_load_waymo_fixture_config(self) -> None:
        config = load_config(Path("configs/waymo_fixture.yaml"))
        self.assertEqual(config.dataset.kind, "waymo")
        self.assertEqual(config.dataset.path, Path("tests/fixtures/waymo_e2e_frame.json"))


if __name__ == "__main__":
    unittest.main()
