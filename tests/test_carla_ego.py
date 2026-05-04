import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from driverx.simulators import CarlaEgoSmokeConfig, run_ego_spawn_smoke, write_ego_smoke


class _FakeBlueprint:
    def __init__(self, blueprint_id: str) -> None:
        self.id = blueprint_id
        self.attributes: dict[str, str] = {}

    def set_attribute(self, key: str, value: str) -> None:
        self.attributes[key] = value


class _FakeBlueprints:
    def find(self, blueprint_id: str) -> _FakeBlueprint:
        return _FakeBlueprint(blueprint_id)

    def filter(self, pattern: str):
        return [_FakeBlueprint("vehicle.tesla.model3")]


class _FakeActor:
    def __init__(self, actor_id: int, type_id: str) -> None:
        self.id = actor_id
        self.type_id = type_id
        self.destroyed = False

    def get_transform(self):
        return SimpleNamespace(
            location=SimpleNamespace(x=float(self.id), y=2.0, z=3.0),
            rotation=SimpleNamespace(pitch=0.0, yaw=90.0, roll=0.0),
        )

    def get_velocity(self):
        return SimpleNamespace(x=1.0, y=0.0, z=0.0)

    def destroy(self) -> None:
        self.destroyed = True


class _FakeCamera(_FakeActor):
    def listen(self, callback) -> None:
        callback(_FakeImage())


class _FakeImage:
    def save_to_disk(self, path: str) -> None:
        Path(path).write_bytes(b"fake-png")


class _FakeMap:
    name = "Carla/Maps/Town10HD_Opt"

    def get_spawn_points(self):
        return [object()]


class _FakeWorld:
    def __init__(self) -> None:
        self.ego = _FakeActor(101, "vehicle.tesla.model3")
        self.camera = _FakeCamera(202, "sensor.camera.rgb")

    def get_map(self):
        return _FakeMap()

    def get_blueprint_library(self):
        return _FakeBlueprints()

    def try_spawn_actor(self, blueprint, spawn_point):
        return self.ego

    def spawn_actor(self, blueprint, transform, attach_to=None):
        return self.camera

    def wait_for_tick(self, timeout_s=None):
        return None


class _FakeClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def set_timeout(self, timeout_s: float) -> None:
        self.timeout_s = timeout_s

    def get_world(self):
        return _FakeWorld()


class _FakeCarla:
    Client = _FakeClient

    class Location:
        def __init__(self, x=0.0, y=0.0, z=0.0) -> None:
            self.x = x
            self.y = y
            self.z = z

    class Rotation:
        def __init__(self, pitch=0.0, yaw=0.0, roll=0.0) -> None:
            self.pitch = pitch
            self.yaw = yaw
            self.roll = roll

    class Transform:
        def __init__(self, location, rotation) -> None:
            self.location = location
            self.rotation = rotation


class CarlaEgoSmokeTest(unittest.TestCase):
    def test_run_ego_spawn_smoke_captures_tracks_and_cleans_up(self) -> None:
        with TemporaryDirectory() as tmp, patch.dict(sys.modules, {"carla": _FakeCarla}):
            result = run_ego_spawn_smoke(
                CarlaEgoSmokeConfig("host.docker.internal", 2000, 1.0, tick_count=3),
                Path(tmp),
            )

        self.assertTrue(result.connected)
        self.assertEqual(result.ego_actor_id, 101)
        self.assertEqual(result.camera_actor_id, 202)
        self.assertEqual(result.track_count, 6)
        self.assertEqual(result.destroyed_actor_ids, [202, 101])

    def test_write_ego_smoke_writes_summary(self) -> None:
        with TemporaryDirectory() as tmp, patch.dict(sys.modules, {"carla": _FakeCarla}):
            run_dir = Path(tmp)
            result = run_ego_spawn_smoke(
                CarlaEgoSmokeConfig("host.docker.internal", 2000, 1.0, tick_count=1),
                run_dir,
            )
            summary = write_ego_smoke(run_dir, result)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(payload["track_count"], 2)
        self.assertIn("# CARLA Ego Smoke", report)

    def test_missing_carla_package_is_actionable(self) -> None:
        with patch.dict(sys.modules):
            sys.modules.pop("carla", None)
            with patch("importlib.import_module", side_effect=ImportError("no carla")):
                result = run_ego_spawn_smoke(
                    CarlaEgoSmokeConfig("127.0.0.1", 2000, 0.1),
                    Path("unused"),
                )

        self.assertFalse(result.connected)
        self.assertIn("carla==0.9.16", result.error)


if __name__ == "__main__":
    unittest.main()
