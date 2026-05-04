import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.simulators import (
    CarlaOverlayInjectionConfig,
    run_overlay_injection_plan,
    write_overlay_injection_run,
)


def _write_plan(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "routes": [
                    _route(
                        "route-occlusion",
                        "occluder",
                        "static.prop.streetbarrier",
                        {"x": 8.0, "y": -1.75, "z": 0.2},
                    ),
                    _route(
                        "route-noise",
                        "distractor",
                        "static.prop.trafficwarning",
                        {"x": 12.0, "y": 4.5, "z": 0.2},
                    ),
                ]
            }
        ),
        encoding="utf-8",
    )


def _route(recipe_id: str, role: str, blueprint: str, location: dict[str, float]) -> dict:
    transform = {
        "location": location,
        "rotation": {"pitch": 0.0, "yaw": 90.0, "roll": 0.0},
    }
    return {
        "recipe_id": recipe_id,
        "script_plan": {
            "actors": [
                {"actor_ref": "ego", "role": "ego", "blueprint_filter": "vehicle.lincoln.mkz_2020"},
                {"actor_ref": "ood_actor_0", "role": "motorcycle", "blueprint_filter": "vehicle.kawasaki.ninja"},
                {
                    "actor_ref": "companion_actor_0",
                    "role": role,
                    "blueprint_filter": blueprint,
                    "spawn_transform": transform,
                },
            ],
            "ticks": [
                {
                    "actor_ref": "companion_actor_0",
                    "t_s": 0.0,
                    "target_transform": transform,
                    "target_speed_mps": 0.0,
                },
                {
                    "actor_ref": "ood_actor_0",
                    "t_s": 0.0,
                    "target_transform": transform,
                    "target_speed_mps": 3.0,
                },
            ],
        },
    }


class FakeBlueprint:
    def __init__(self, blueprint_id: str) -> None:
        self.id = blueprint_id
        self.attributes: dict[str, str] = {}

    def set_attribute(self, key: str, value: str) -> None:
        self.attributes[key] = value


class FakeBlueprintLibrary:
    def find(self, blueprint_id: str) -> FakeBlueprint:
        return FakeBlueprint(blueprint_id)

    def filter(self, blueprint_filter: str) -> list[FakeBlueprint]:
        return [FakeBlueprint(blueprint_filter.replace("*", "fake"))]


class FakeActor:
    def __init__(self, actor_id: int, blueprint: FakeBlueprint, transform: object) -> None:
        self.id = actor_id
        self.type_id = blueprint.id
        self.transform = transform
        self.velocity = FakeVector3D(0.0, 0.0, 0.0)
        self.destroyed = False

    def set_transform(self, transform: object) -> None:
        self.transform = transform

    def set_target_velocity(self, velocity: object) -> None:
        self.velocity = velocity

    def get_transform(self) -> object:
        return self.transform

    def get_velocity(self) -> object:
        return self.velocity

    def destroy(self) -> None:
        self.destroyed = True


class FakeWorld:
    def __init__(self) -> None:
        self.spawned: list[FakeActor] = []
        self.waits = 0
        self.live_actor_counts_before_spawn: list[int] = []

    def get_blueprint_library(self) -> FakeBlueprintLibrary:
        return FakeBlueprintLibrary()

    def try_spawn_actor(self, blueprint: FakeBlueprint, transform: object) -> FakeActor:
        self.live_actor_counts_before_spawn.append(
            len([actor for actor in self.spawned if not actor.destroyed])
        )
        actor = FakeActor(len(self.spawned) + 1, blueprint, transform)
        self.spawned.append(actor)
        return actor

    def spawn_actor(self, blueprint: FakeBlueprint, transform: object) -> FakeActor:
        return self.try_spawn_actor(blueprint, transform)

    def wait_for_tick(self, timeout_s: float | None = None) -> None:
        self.waits += 1


class FakeClient:
    def __init__(self, world: FakeWorld) -> None:
        self.world = world
        self.timeout_s: float | None = None

    def set_timeout(self, timeout_s: float) -> None:
        self.timeout_s = timeout_s

    def get_world(self) -> FakeWorld:
        return self.world


class FakeVector3D:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


class FakeLocation(FakeVector3D):
    pass


class FakeRotation:
    def __init__(self, pitch: float, yaw: float, roll: float) -> None:
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll


class FakeTransform:
    def __init__(self, location: FakeLocation, rotation: FakeRotation) -> None:
        self.location = location
        self.rotation = rotation


class FakeCarlaModule:
    Location = FakeLocation
    Rotation = FakeRotation
    Transform = FakeTransform
    Vector3D = FakeVector3D

    def __init__(self) -> None:
        self.world = FakeWorld()

    def Client(self, host: str, port: int) -> FakeClient:
        return FakeClient(self.world)


class CarlaInjectionTest(unittest.TestCase):
    def test_run_overlay_injection_plan_spawns_only_companions(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "overlay_injection_plan.json"
            _write_plan(plan_path)
            carla = FakeCarlaModule()
            result = run_overlay_injection_plan(
                CarlaOverlayInjectionConfig("127.0.0.1", 2000, 1.0),
                plan_path,
                tmp_path / "run",
                carla_module=carla,
            )
            summary = write_overlay_injection_run(tmp_path / "run", result)
            tracks = json.loads(Path(result.tracks_path or "").read_text(encoding="utf-8"))
            json_exists = Path(summary["json_path"]).exists()
            report_exists = Path(summary["report_path"]).exists()

        self.assertTrue(result.connected)
        self.assertEqual(result.route_count, 2)
        self.assertEqual(result.spawned_actor_ids, [1, 2])
        self.assertEqual(result.destroyed_actor_ids, [1, 2])
        self.assertEqual(result.track_count, 2)
        self.assertEqual([actor.type_id for actor in carla.world.spawned], [
            "static.prop.streetbarrier",
            "static.prop.trafficwarning",
        ])
        self.assertTrue(all(actor.destroyed for actor in carla.world.spawned))
        self.assertEqual(carla.world.waits, 2)
        self.assertEqual(carla.world.live_actor_counts_before_spawn, [0, 0])
        self.assertEqual(result.route_results[0].destroyed_actor_ids, [1])
        self.assertEqual(result.route_results[1].destroyed_actor_ids, [2])
        self.assertEqual([track["actor_ref"] for track in tracks], ["companion_actor_0", "companion_actor_0"])
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)

    def test_run_overlay_injection_plan_honors_limits(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "overlay_injection_plan.json"
            _write_plan(plan_path)
            carla = FakeCarlaModule()
            result = run_overlay_injection_plan(
                CarlaOverlayInjectionConfig(
                    "127.0.0.1",
                    2000,
                    1.0,
                    route_limit=1,
                    tick_limit=0,
                    wait_for_tick=False,
                ),
                plan_path,
                tmp_path / "run",
                carla_module=carla,
            )

        self.assertTrue(result.connected)
        self.assertEqual(result.route_count, 1)
        self.assertEqual(result.spawned_actor_ids, [1])
        self.assertEqual(result.track_count, 0)
        self.assertEqual(carla.world.waits, 0)

    def test_run_overlay_injection_plan_reports_multi_companion_cleanup_order(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "overlay_injection_plan.json"
            _write_plan(plan_path)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            companion = dict(plan["routes"][0]["script_plan"]["actors"][2])
            companion["actor_ref"] = "companion_actor_1"
            companion["role"] = "distractor"
            companion["blueprint_filter"] = "static.prop.trafficwarning"
            plan["routes"][0]["script_plan"]["actors"].append(companion)
            plan["routes"][0]["script_plan"]["ticks"].append(
                {
                    "actor_ref": "companion_actor_1",
                    "t_s": 0.0,
                    "target_transform": companion["spawn_transform"],
                    "target_speed_mps": 0.0,
                }
            )
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            carla = FakeCarlaModule()
            result = run_overlay_injection_plan(
                CarlaOverlayInjectionConfig("127.0.0.1", 2000, 1.0),
                plan_path,
                tmp_path / "run",
                carla_module=carla,
            )

        self.assertTrue(result.connected)
        self.assertEqual(result.spawned_actor_ids, [1, 2, 3])
        self.assertEqual(result.destroyed_actor_ids, [2, 1, 3])
        self.assertEqual(result.route_results[0].spawned_actor_ids, [1, 2])
        self.assertEqual(result.route_results[0].destroyed_actor_ids, [2, 1])
        self.assertEqual(result.route_results[1].destroyed_actor_ids, [3])
        self.assertEqual(carla.world.live_actor_counts_before_spawn, [0, 1, 0])

    def test_run_overlay_injection_plan_reports_missing_carla_package(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "overlay_injection_plan.json"
            _write_plan(plan_path)

            with patch(
                "driverx.simulators.carla_injection.importlib.import_module",
                side_effect=ImportError("no carla"),
            ):
                result = run_overlay_injection_plan(
                    CarlaOverlayInjectionConfig("127.0.0.1", 2000, 1.0),
                    plan_path,
                    tmp_path / "run",
                )

        self.assertFalse(result.connected)
        self.assertIn("CARLA Python package is unavailable", result.error or "")


if __name__ == "__main__":
    unittest.main()
