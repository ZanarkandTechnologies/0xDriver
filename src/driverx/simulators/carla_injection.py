"""Run DriverX companion overlay actors beside a CARLA route."""

from __future__ import annotations

import importlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CarlaOverlayInjectionConfig:
    host: str
    port: int
    timeout_s: float
    route_limit: int | None = None
    tick_limit: int | None = None
    wait_for_tick: bool = True


@dataclass(frozen=True)
class OverlayActorTrack:
    route_index: int
    recipe_id: str
    actor_ref: str
    actor_id: int
    type_id: str
    tick_index: int
    t_s: float
    location: dict[str, float]
    rotation: dict[str, float]
    velocity: dict[str, float]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "route_index": self.route_index,
            "recipe_id": self.recipe_id,
            "actor_ref": self.actor_ref,
            "actor_id": self.actor_id,
            "type_id": self.type_id,
            "tick_index": self.tick_index,
            "t_s": self.t_s,
            "location": self.location,
            "rotation": self.rotation,
            "velocity": self.velocity,
        }


@dataclass(frozen=True)
class OverlayRouteInjectionResult:
    route_index: int
    recipe_id: str
    companion_actor_refs: list[str]
    spawned_actor_ids: list[int] = field(default_factory=list)
    destroyed_actor_ids: list[int] = field(default_factory=list)
    applied_tick_count: int = 0
    track_count: int = 0
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "route_index": self.route_index,
            "recipe_id": self.recipe_id,
            "companion_actor_refs": self.companion_actor_refs,
            "spawned_actor_ids": self.spawned_actor_ids,
            "destroyed_actor_ids": self.destroyed_actor_ids,
            "applied_tick_count": self.applied_tick_count,
            "track_count": self.track_count,
            "error": self.error,
        }


@dataclass(frozen=True)
class OverlayInjectionRunResult:
    connected: bool
    host: str
    port: int
    plan_path: str
    route_count: int = 0
    route_results: list[OverlayRouteInjectionResult] = field(default_factory=list)
    spawned_actor_ids: list[int] = field(default_factory=list)
    destroyed_actor_ids: list[int] = field(default_factory=list)
    tracks_path: str | None = None
    track_count: int = 0
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "plan_path": self.plan_path,
            "route_count": self.route_count,
            "route_results": [result.to_jsonable() for result in self.route_results],
            "spawned_actor_ids": self.spawned_actor_ids,
            "destroyed_actor_ids": self.destroyed_actor_ids,
            "tracks_path": self.tracks_path,
            "track_count": self.track_count,
            "error": self.error,
        }


def run_overlay_injection_plan(
    config: CarlaOverlayInjectionConfig,
    plan_path: Path,
    run_dir: Path,
    *,
    carla_module: object | None = None,
) -> OverlayInjectionRunResult:
    """Spawn and tick only companion actors from a TASK-021 plan."""

    plan_file = plan_path.expanduser().resolve()
    payload = json.loads(plan_file.read_text(encoding="utf-8"))
    routes = list(payload.get("routes", []))
    if config.route_limit is not None:
        routes = routes[: config.route_limit]
    try:
        carla = carla_module or importlib.import_module("carla")
    except ImportError as exc:
        return OverlayInjectionRunResult(
            connected=False,
            host=config.host,
            port=config.port,
            plan_path=str(plan_file),
            route_count=len(routes),
            error=(
                f"CARLA Python package is unavailable: {exc}. "
                "Run through scripts/run_carla_client_docker.sh or install carla==0.9.16."
            ),
        )

    run_dir.mkdir(parents=True, exist_ok=True)
    tracks_path = run_dir / "entity_tracks.json"
    all_tracks: list[OverlayActorTrack] = []
    route_results: list[OverlayRouteInjectionResult] = []
    all_spawned_ids: list[int] = []
    destroyed_ids: list[int] = []
    try:
        client = carla.Client(config.host, config.port)
        client.set_timeout(config.timeout_s)
        world = client.get_world()
        blueprints = world.get_blueprint_library()
        for route_index, route in enumerate(routes):
            result, route_spawned, route_tracks = _run_route_overlay(
                carla,
                world,
                blueprints,
                dict(route),
                route_index,
                config,
            )
            route_destroyed: list[int] = []
            _destroy_actors(reversed(route_spawned), route_destroyed)
            destroyed_ids.extend(route_destroyed)
            all_spawned_ids.extend(result.spawned_actor_ids)
            all_tracks.extend(route_tracks)
            route_results.append(_with_destroyed_ids(result, route_destroyed))
    except Exception as exc:
        return OverlayInjectionRunResult(
            connected=False,
            host=config.host,
            port=config.port,
            plan_path=str(plan_file),
            route_count=len(routes),
            route_results=route_results,
            spawned_actor_ids=all_spawned_ids,
            destroyed_actor_ids=destroyed_ids,
            track_count=len(all_tracks),
            error=f"CARLA overlay injection failed: {exc}",
        )

    tracks_path.write_text(
        json.dumps([track.to_jsonable() for track in all_tracks], indent=2),
        encoding="utf-8",
    )
    return OverlayInjectionRunResult(
        connected=True,
        host=config.host,
        port=config.port,
        plan_path=str(plan_file),
        route_count=len(routes),
        route_results=route_results,
        spawned_actor_ids=all_spawned_ids,
        destroyed_actor_ids=destroyed_ids,
        tracks_path=str(tracks_path),
        track_count=len(all_tracks),
    )


def write_overlay_injection_run(run_dir: Path, result: OverlayInjectionRunResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "overlay_injection_run.json"
    report_path = run_dir / "overlay_injection_run.md"
    payload = result.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_run_markdown(result), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _run_route_overlay(
    carla: object,
    world: object,
    blueprints: object,
    route: dict[str, Any],
    route_index: int,
    config: CarlaOverlayInjectionConfig,
) -> tuple[OverlayRouteInjectionResult, list[object], list[OverlayActorTrack]]:
    recipe_id = str(route.get("recipe_id", "unknown-route"))
    script_plan = dict(route.get("script_plan", {}))
    actor_specs = [
        dict(actor)
        for actor in list(script_plan.get("actors", []))
        if str(actor.get("actor_ref", "")).startswith("companion_actor_")
    ]
    companion_refs = [str(actor.get("actor_ref")) for actor in actor_specs]
    spawned: list[object] = []
    actor_by_ref: dict[str, object] = {}
    try:
        for actor_spec in actor_specs:
            actor = _spawn_actor_from_spec(carla, world, blueprints, actor_spec)
            spawned.append(actor)
            actor_by_ref[str(actor_spec["actor_ref"])] = actor
        ticks = [
            dict(tick)
            for tick in list(script_plan.get("ticks", []))
            if str(tick.get("actor_ref")) in actor_by_ref
        ]
        if config.tick_limit is not None:
            ticks = ticks[: config.tick_limit]
        tracks = _apply_ticks(carla, world, ticks, actor_by_ref, route_index, recipe_id, config)
        return (
            OverlayRouteInjectionResult(
                route_index=route_index,
                recipe_id=recipe_id,
                companion_actor_refs=companion_refs,
                spawned_actor_ids=_actor_ids(spawned),
                applied_tick_count=len(ticks),
                track_count=len(tracks),
            ),
            spawned,
            tracks,
        )
    except Exception as exc:
        return (
            OverlayRouteInjectionResult(
                route_index=route_index,
                recipe_id=recipe_id,
                companion_actor_refs=companion_refs,
                spawned_actor_ids=_actor_ids(spawned),
                error=str(exc),
            ),
            spawned,
            [],
        )


def _spawn_actor_from_spec(
    carla: object,
    world: object,
    blueprints: object,
    actor_spec: dict[str, Any],
) -> object:
    blueprint = _find_blueprint(blueprints, str(actor_spec["blueprint_filter"]))
    if hasattr(blueprint, "set_attribute"):
        blueprint.set_attribute("role_name", f"driverx_{actor_spec['actor_ref']}")
    transform = _carla_transform(carla, dict(actor_spec["spawn_transform"]))
    actor = None
    if hasattr(world, "try_spawn_actor"):
        actor = world.try_spawn_actor(blueprint, transform)
    if actor is None:
        actor = world.spawn_actor(blueprint, transform)
    if actor is None:
        raise RuntimeError(f"Unable to spawn companion actor {actor_spec['actor_ref']}")
    return actor


def _find_blueprint(blueprints: object, blueprint_filter: str) -> object:
    if "*" not in blueprint_filter:
        return blueprints.find(blueprint_filter)
    matches = list(blueprints.filter(blueprint_filter))
    if not matches:
        raise ValueError(f"No CARLA blueprints matched {blueprint_filter}")
    return matches[0]


def _apply_ticks(
    carla: object,
    world: object,
    ticks: list[dict[str, Any]],
    actor_by_ref: dict[str, object],
    route_index: int,
    recipe_id: str,
    config: CarlaOverlayInjectionConfig,
) -> list[OverlayActorTrack]:
    tracks: list[OverlayActorTrack] = []
    for tick_index, tick in enumerate(ticks):
        actor_ref = str(tick["actor_ref"])
        actor = actor_by_ref[actor_ref]
        transform = _carla_transform(carla, dict(tick["target_transform"]))
        if hasattr(actor, "set_transform"):
            actor.set_transform(transform)
        speed = float(tick.get("target_speed_mps", 0.0))
        if speed and hasattr(actor, "set_target_velocity"):
            actor.set_target_velocity(_velocity_for(carla, transform.rotation, speed))
        if config.wait_for_tick:
            _wait_for_tick(world, config.timeout_s)
        tracks.append(
            _track_for(
                actor,
                route_index=route_index,
                recipe_id=recipe_id,
                actor_ref=actor_ref,
                tick_index=tick_index,
                t_s=float(tick.get("t_s", tick_index)),
            )
        )
    return tracks


def _carla_transform(carla: object, transform: dict[str, Any]) -> object:
    location = dict(transform.get("location", {}))
    rotation = dict(transform.get("rotation", {}))
    return carla.Transform(
        carla.Location(
            x=float(location.get("x", 0.0)),
            y=float(location.get("y", 0.0)),
            z=float(location.get("z", 0.0)),
        ),
        carla.Rotation(
            pitch=float(rotation.get("pitch", 0.0)),
            yaw=float(rotation.get("yaw", 0.0)),
            roll=float(rotation.get("roll", 0.0)),
        ),
    )


def _velocity_for(carla: object, rotation: object, speed_mps: float) -> object:
    yaw = math.radians(float(getattr(rotation, "yaw", 0.0)))
    return carla.Vector3D(
        x=math.cos(yaw) * speed_mps,
        y=math.sin(yaw) * speed_mps,
        z=0.0,
    )


def _wait_for_tick(world: object, timeout_s: float) -> None:
    try:
        world.wait_for_tick(timeout_s)
    except TypeError:
        world.wait_for_tick()


def _track_for(
    actor: object,
    *,
    route_index: int,
    recipe_id: str,
    actor_ref: str,
    tick_index: int,
    t_s: float,
) -> OverlayActorTrack:
    transform = actor.get_transform()
    return OverlayActorTrack(
        route_index=route_index,
        recipe_id=recipe_id,
        actor_ref=actor_ref,
        actor_id=int(getattr(actor, "id")),
        type_id=str(getattr(actor, "type_id", "")),
        tick_index=tick_index,
        t_s=t_s,
        location=_vector_payload(transform.location),
        rotation=_rotation_payload(transform.rotation),
        velocity=_vector_payload(actor.get_velocity()),
    )


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


def _actor_ids(actors: list[object]) -> list[int]:
    return [int(getattr(actor, "id")) for actor in actors if hasattr(actor, "id")]


def _destroy_actors(actors: object, destroyed_ids: list[int]) -> None:
    for actor in actors:
        try:
            actor_id = int(getattr(actor, "id"))
            actor.destroy()
            destroyed_ids.append(actor_id)
        except Exception:
            pass


def _with_destroyed_ids(
    result: OverlayRouteInjectionResult,
    destroyed_ids: list[int],
) -> OverlayRouteInjectionResult:
    return OverlayRouteInjectionResult(
        route_index=result.route_index,
        recipe_id=result.recipe_id,
        companion_actor_refs=result.companion_actor_refs,
        spawned_actor_ids=result.spawned_actor_ids,
        destroyed_actor_ids=list(destroyed_ids),
        applied_tick_count=result.applied_tick_count,
        track_count=result.track_count,
        error=result.error,
    )


def _run_markdown(result: OverlayInjectionRunResult) -> str:
    status = "connected" if result.connected else "failed"
    lines = [
        "# Overlay Injection Run",
        "",
        f"- status: `{status}`",
        f"- endpoint: `{result.host}:{result.port}`",
        f"- plan_path: `{result.plan_path}`",
        f"- routes: `{result.route_count}`",
        f"- spawned_actor_ids: `{result.spawned_actor_ids}`",
        f"- destroyed_actor_ids: `{result.destroyed_actor_ids}`",
        f"- track_count: `{result.track_count}`",
        f"- tracks_path: `{result.tracks_path}`",
    ]
    if result.error:
        lines.append(f"- error: `{result.error}`")
    lines.extend(["", "## Routes", ""])
    for route in result.route_results:
        lines.append(
            f"- `{route.recipe_id}`: spawned `{route.spawned_actor_ids}`, "
            f"ticks `{route.applied_tick_count}`, tracks `{route.track_count}`, "
            f"error `{route.error}`"
        )
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "CarlaOverlayInjectionConfig",
    "OverlayActorTrack",
    "OverlayInjectionRunResult",
    "OverlayRouteInjectionResult",
    "run_overlay_injection_plan",
    "write_overlay_injection_run",
]
