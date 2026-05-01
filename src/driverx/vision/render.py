"""SVG evidence rendering for fixture scenes and trajectories."""

from __future__ import annotations

from html import escape
from pathlib import Path

from driverx.core.types import ArtifactRef, FrameBundle, TrajectoryCandidate


def _map_topdown(point: tuple[float, float], origin_x: float, origin_y: float) -> tuple[float, float]:
    x, y = point
    return origin_x + x * 18.0, origin_y - y * 42.0


def _polyline(points: list[tuple[float, float]], origin_x: float, origin_y: float) -> str:
    mapped = [_map_topdown(point, origin_x, origin_y) for point in points]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in mapped)


def render_scene_svg(
    frame: FrameBundle,
    output_path: Path,
    selected: TrajectoryCandidate | None = None,
    candidates: list[TrajectoryCandidate] | None = None,
) -> ArtifactRef:
    """Render a compact inspection artifact as SVG."""

    candidates = candidates or []
    width = 980
    height = 620
    panel_w = 300
    panel_h = 170
    topdown_origin = (110.0, 500.0)
    hazard_text = frame.metadata.get("hazards", [])
    scenario = escape(str(frame.metadata.get("scenario", "unknown")))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#1f2933}",
        ".label{font-size:18px;font-weight:700}.small{font-size:13px}.tiny{font-size:11px}",
        "</style>",
        '<rect width="980" height="620" fill="#f7f8f5"/>',
        f'<text x="28" y="34" class="label">0xDriver scene: {escape(frame.frame_name)}</text>',
        f'<text x="28" y="58" class="small">scenario={scenario}</text>',
    ]

    for idx, image in enumerate(frame.front_images[:3]):
        x = 28 + idx * (panel_w + 12)
        y = 82
        color = image.pixels[image.height // 2][image.width // 2]
        fill = f"rgb({color[0]},{color[1]},{color[2]})"
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" rx="4" fill="{fill}" stroke="#27313a" stroke-width="1.5"/>',
                f'<rect x="{x}" y="{y + panel_h * 0.55:.1f}" width="{panel_w}" height="{panel_h * 0.45:.1f}" fill="#4b5560" opacity="0.58"/>',
                f'<line x1="{x + panel_w * 0.46:.1f}" y1="{y + panel_h}" x2="{x + panel_w * 0.50:.1f}" y2="{y + panel_h * 0.58:.1f}" stroke="#f3f4d7" stroke-width="3" stroke-dasharray="10 9"/>',
                f'<line x1="{x + panel_w * 0.58:.1f}" y1="{y + panel_h}" x2="{x + panel_w * 0.52:.1f}" y2="{y + panel_h * 0.58:.1f}" stroke="#f3f4d7" stroke-width="3" stroke-dasharray="10 9"/>',
                f'<text x="{x + 12}" y="{y + 24}" class="small">{escape(image.name)}</text>',
            ]
        )
        if idx == 1 and frame.metadata.get("objects"):
            objects = frame.metadata.get("objects", [])
            has_vehicle = any(obj.get("kind") == "stopped_vehicle" for obj in objects)
            has_cones = any(obj.get("kind") == "cone" for obj in objects)
            if has_vehicle:
                parts.extend(
                    [
                        f'<rect x="{x + 172}" y="{y + 103}" width="54" height="28" fill="#334155" stroke="#e5e7eb"/>',
                        f'<text x="{x + 170}" y="{y + 148}" class="tiny">service vehicle</text>',
                    ]
                )
            if has_cones:
                parts.extend(
                    [
                        f'<circle cx="{x + 112}" cy="{y + 132}" r="8" fill="#f97316"/>',
                        f'<circle cx="{x + 142}" cy="{y + 130}" r="8" fill="#f97316"/>',
                    ]
                )

    parts.extend(
        [
            '<text x="28" y="300" class="label">Top-down trajectory evidence</text>',
            '<rect x="28" y="320" width="620" height="245" rx="4" fill="#e7ece4" stroke="#3f4f46"/>',
            '<line x1="52" y1="500" x2="620" y2="500" stroke="#86938a" stroke-width="2"/>',
            '<line x1="52" y1="458" x2="620" y2="458" stroke="#ffffff" stroke-width="2" stroke-dasharray="12 10"/>',
            '<line x1="52" y1="542" x2="620" y2="542" stroke="#ffffff" stroke-width="2" stroke-dasharray="12 10"/>',
            '<text x="48" y="348" class="tiny">vehicle coordinates: x forward, y left/right</text>',
        ]
    )

    history_points = _polyline(frame.ego_history_xy, *topdown_origin)
    parts.append(f'<polyline points="{history_points}" fill="none" stroke="#111827" stroke-width="4"/>')
    if frame.future_xy is not None:
        future_points = _polyline(frame.future_xy, *topdown_origin)
        parts.append(f'<polyline points="{future_points}" fill="none" stroke="#2563eb" stroke-width="4" opacity="0.55"/>')

    for idx, candidate in enumerate(candidates):
        opacity = 0.22 if selected and candidate.source != selected.source else 0.38
        candidate_points = _polyline(candidate.points_xy, *topdown_origin)
        parts.append(
            f'<polyline points="{candidate_points}" fill="none" stroke="#8b5cf6" stroke-width="3" opacity="{opacity:.2f}"/>'
        )

    if selected is not None:
        selected_points = _polyline(selected.points_xy, *topdown_origin)
        parts.append(f'<polyline points="{selected_points}" fill="none" stroke="#dc2626" stroke-width="4"/>')

    for obj in frame.metadata.get("objects", []):
        ox, oy = _map_topdown((float(obj["x"]), float(obj["y"])), *topdown_origin)
        kind = escape(str(obj.get("kind", "object")))
        parts.extend(
            [
                f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="8" fill="#f97316" stroke="#7c2d12"/>',
                f'<text x="{ox + 10:.1f}" y="{oy - 8:.1f}" class="tiny">{kind}</text>',
            ]
        )

    parts.extend(
        [
            '<rect x="690" y="320" width="250" height="245" rx="4" fill="#ffffff" stroke="#c8d0c8"/>',
            '<text x="710" y="350" class="label">Hazards</text>',
        ]
    )
    if hazard_text:
        for idx, hazard in enumerate(hazard_text[:5]):
            parts.append(
                f'<text x="710" y="{382 + idx * 26}" class="small">{idx + 1}. {escape(str(hazard))}</text>'
            )
    else:
        parts.append('<text x="710" y="382" class="small">No fixture hazards.</text>')

    parts.extend(
        [
            '<text x="710" y="530" class="tiny">black=history, blue=fixture truth, red=selected</text>',
            "</svg>",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts), encoding="utf-8")
    return ArtifactRef(name=output_path.stem, path=output_path, kind="svg")
