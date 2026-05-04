"""Small live CARLA ego spawn/camera/entity-track smoke path."""

from __future__ import annotations

import importlib
import json
import queue
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CarlaEgoSmokeConfig:
    host: str
    port: int
    timeout_s: float
    tick_count: int = 5
    camera_width: int = 320
    camera_height: int = 180


@dataclass(frozen=True)
class EntityTrack:
    actor_id: int
    type_id: str
    role: str
    tick: int
    location: dict[str, float]
    rotation: dict[str, float]
    velocity: dict[str, float]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "type_id": self.type_id,
            "role": self.role,
            "tick": self.tick,
            "location": self.location,
            "rotation": self.rotation,
            "velocity": self.velocity,
        }


@dataclass(frozen=True)
class CarlaEgoSmokeResult:
    connected: bool
    host: str
    port: int
    map_name: str | None = None
    ego_actor_id: int | None = None
    camera_actor_id: int | None = None
    spawned_actor_ids: list[int] = field(default_factory=list)
    destroyed_actor_ids: list[int] = field(default_factory=list)
    image_path: str | None = None
    tracks_path: str | None = None
    track_count: int = 0
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "map_name": self.map_name,
            "ego_actor_id": self.ego_actor_id,
            "camera_actor_id": self.camera_actor_id,
            "spawned_actor_ids": self.spawned_actor_ids,
            "destroyed_actor_ids": self.destroyed_actor_ids,
            "image_path": self.image_path,
            "tracks_path": self.tracks_path,
            "track_count": self.track_count,
            "error": self.error,
        }


def _vector_payload(vector: object) -> dict[str, float]:
    return {
        "x": float(getattr(vector, "x", 0.0)),
        "y": float(getattr(vector, "y", 0.0)),
        "z": float(getattr(vector, "z", 0.0)),
    }


def _rotation_payload(rotation: object) -> dict[str, float]:
    return {
        "pitch": float(getattr(rotation, "pitch", 0.0)),
        "yaw": float(getattr(rotation, "yaw", 0.0)),
        "roll": float(getattr(rotation, "roll", 0.0)),
    }


def _track_for(actor: object, role: str, tick: int) -> EntityTrack:
    transform = actor.get_transform()
    return EntityTrack(
        actor_id=int(getattr(actor, "id")),
        type_id=str(getattr(actor, "type_id", "")),
        role=role,
        tick=tick,
        location=_vector_payload(transform.location),
        rotation=_rotation_payload(transform.rotation),
        velocity=_vector_payload(actor.get_velocity()),
    )


def _find_vehicle_blueprint(blueprints: object):
    preferred = [
        "vehicle.lincoln.mkz_2020",
        "vehicle.tesla.model3",
        "vehicle.audi.tt",
    ]
    for blueprint_id in preferred:
        try:
            return blueprints.find(blueprint_id)
        except Exception:
            pass
    matches = list(blueprints.filter("vehicle.*"))
    if not matches:
        raise ValueError("No CARLA vehicle blueprints found.")
    return matches[0]


def _spawn_ego(world: object, blueprint: object, spawn_points: list[object]):
    for spawn_point in spawn_points[:30]:
        actor = world.try_spawn_actor(blueprint, spawn_point)
        if actor is not None:
            return actor
    raise RuntimeError("Unable to spawn ego actor at any of the first 30 spawn points.")


def _ego_markdown(result: CarlaEgoSmokeResult) -> str:
    status = "connected" if result.connected else "failed"
    lines = [
        "# CARLA Ego Smoke",
        "",
        f"- status: {status}",
        f"- endpoint: `{result.host}:{result.port}`",
        f"- map: `{result.map_name}`",
        f"- ego_actor_id: `{result.ego_actor_id}`",
        f"- camera_actor_id: `{result.camera_actor_id}`",
        f"- track_count: `{result.track_count}`",
        f"- image_path: `{result.image_path}`",
        f"- tracks_path: `{result.tracks_path}`",
        f"- destroyed_actor_ids: `{result.destroyed_actor_ids}`",
    ]
    if result.error:
        lines.append(f"- error: `{result.error}`")
    lines.append("")
    return "\n".join(lines)


def run_ego_spawn_smoke(
    config: CarlaEgoSmokeConfig,
    run_dir: Path,
) -> CarlaEgoSmokeResult:
    try:
        carla = importlib.import_module("carla")
    except ImportError as exc:
        return CarlaEgoSmokeResult(
            connected=False,
            host=config.host,
            port=config.port,
            error=(
                f"CARLA Python package is unavailable: {exc}. "
                "Run through scripts/run_carla_client_docker.sh or install carla==0.9.16."
            ),
        )

    spawned: list[object] = []
    destroyed: list[int] = []
    tracks: list[EntityTrack] = []
    image_path = run_dir / "ego_camera.png"
    tracks_path = run_dir / "entity_tracks.json"
    success_payload: dict[str, Any] | None = None
    error: str | None = None
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        client = carla.Client(config.host, config.port)
        client.set_timeout(config.timeout_s)
        world = client.get_world()
        world_map = world.get_map()
        blueprints = world.get_blueprint_library()
        ego_blueprint = _find_vehicle_blueprint(blueprints)
        if hasattr(ego_blueprint, "set_attribute"):
            ego_blueprint.set_attribute("role_name", "driverx_ego_smoke")
        spawn_points = list(world_map.get_spawn_points())
        if not spawn_points:
            raise RuntimeError("CARLA map has no spawn points.")
        ego = _spawn_ego(world, ego_blueprint, spawn_points)
        spawned.append(ego)

        camera_blueprint = blueprints.find("sensor.camera.rgb")
        camera_blueprint.set_attribute("image_size_x", str(config.camera_width))
        camera_blueprint.set_attribute("image_size_y", str(config.camera_height))
        camera_blueprint.set_attribute("fov", "90")
        camera_transform = carla.Transform(
            carla.Location(x=1.5, z=2.4),
            carla.Rotation(pitch=-10.0),
        )
        camera = world.spawn_actor(camera_blueprint, camera_transform, attach_to=ego)
        spawned.append(camera)

        images: "queue.Queue[object]" = queue.Queue()
        camera.listen(images.put)
        for tick in range(config.tick_count):
            try:
                world.wait_for_tick(config.timeout_s)
            except TypeError:
                world.wait_for_tick()
            tracks.append(_track_for(ego, "ego", tick))
            tracks.append(_track_for(camera, "camera", tick))

        image = images.get(timeout=config.timeout_s)
        image.save_to_disk(str(image_path))
        tracks_path.write_text(
            json.dumps([track.to_jsonable() for track in tracks], indent=2),
            encoding="utf-8",
        )
        success_payload = {
            "map_name": str(getattr(world_map, "name", "")) or None,
            "ego_actor_id": int(getattr(ego, "id")),
            "camera_actor_id": int(getattr(camera, "id")),
            "image_path": str(image_path),
            "tracks_path": str(tracks_path),
        }
    except Exception as exc:
        error = f"CARLA ego smoke failed: {exc}"
    finally:
        for actor in reversed(spawned):
            try:
                actor_id = int(getattr(actor, "id"))
                actor.destroy()
                destroyed.append(actor_id)
            except Exception:
                pass
    spawned_ids = [int(getattr(actor, "id")) for actor in spawned if hasattr(actor, "id")]
    if success_payload is not None:
        return CarlaEgoSmokeResult(
            connected=True,
            host=config.host,
            port=config.port,
            map_name=success_payload["map_name"],
            ego_actor_id=success_payload["ego_actor_id"],
            camera_actor_id=success_payload["camera_actor_id"],
            spawned_actor_ids=spawned_ids,
            destroyed_actor_ids=destroyed,
            image_path=success_payload["image_path"],
            tracks_path=success_payload["tracks_path"],
            track_count=len(tracks),
        )
    return CarlaEgoSmokeResult(
        connected=False,
        host=config.host,
        port=config.port,
        spawned_actor_ids=spawned_ids,
        destroyed_actor_ids=destroyed,
        track_count=len(tracks),
        error=error,
    )


def write_ego_smoke(run_dir: Path, result: CarlaEgoSmokeResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "ego_smoke.json"
    report_path = run_dir / "ego_smoke.md"
    payload = result.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_ego_markdown(result), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


__all__ = [
    "CarlaEgoSmokeConfig",
    "CarlaEgoSmokeResult",
    "EntityTrack",
    "run_ego_spawn_smoke",
    "write_ego_smoke",
]
