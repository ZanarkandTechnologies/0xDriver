import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from driverx.simulators import CarlaProbeConfig, probe_carla_client, write_carla_probe


class _FakeActorList:
    def __len__(self) -> int:
        return 23


class _FakeWorld:
    def get_map(self):
        return SimpleNamespace(name="Carla/Maps/Town10HD_Opt")

    def get_actors(self):
        return _FakeActorList()

    def get_weather(self):
        return SimpleNamespace(cloudiness=10.0, precipitation=0.0, wetness=2.0)

    def get_settings(self):
        return SimpleNamespace(synchronous_mode=False, fixed_delta_seconds=None)

    def get_snapshot(self):
        return SimpleNamespace(timestamp=SimpleNamespace(elapsed_seconds=123.5))


class _FakeClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.timeout = 0.0

    def set_timeout(self, timeout_s: float) -> None:
        self.timeout = timeout_s

    def get_world(self):
        return _FakeWorld()

    def get_server_version(self) -> str:
        return "0.9.16-server"

    def get_client_version(self) -> str:
        return "0.9.16-client"


class CarlaProbeTest(unittest.TestCase):
    def test_probe_carla_client_collects_world_state(self) -> None:
        fake_carla = SimpleNamespace(Client=_FakeClient, __version__="0.9.16")
        with patch.dict(sys.modules, {"carla": fake_carla}):
            result = probe_carla_client(CarlaProbeConfig("host.docker.internal", 2000, 1.5))

        self.assertTrue(result.connected)
        self.assertEqual(result.map_name, "Carla/Maps/Town10HD_Opt")
        self.assertEqual(result.actor_count, 23)
        self.assertEqual(result.server_version, "0.9.16-server")
        self.assertEqual(result.weather["cloudiness"], 10.0)
        self.assertFalse(result.settings["synchronous_mode"])

    def test_probe_carla_client_missing_package_is_actionable(self) -> None:
        with patch.dict(sys.modules):
            sys.modules.pop("carla", None)
            with patch("importlib.import_module", side_effect=ImportError("no carla")):
                result = probe_carla_client(CarlaProbeConfig("127.0.0.1", 2000, 0.1))

        self.assertFalse(result.connected)
        self.assertIn("carla==0.9.16", result.error)

    def test_write_carla_probe_artifacts_are_readable(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = write_carla_probe(
                Path(tmp),
                result=probe_carla_client(CarlaProbeConfig("127.0.0.1", 1, 0.01)),
            )
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertIn("connected", payload)
        self.assertIn("# CARLA Probe", report)


if __name__ == "__main__":
    unittest.main()
