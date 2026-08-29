"""Canvas rendering helpers for the ULTRON desktop UI."""

from __future__ import annotations

import math
from functools import lru_cache

_NODE_COUNT = 220
_NEIGHBORS_PER_NODE = 3


@lru_cache(maxsize=1)
def _sphere_geometry(n: int = _NODE_COUNT, k: int = _NEIGHBORS_PER_NODE) -> tuple[tuple, tuple]:
    """Evenly distributed unit-sphere points (Fibonacci sphere) and their
    nearest-neighbor edges. Computed once - the shape itself never changes,
    only its rotation and projection do.
    """

    points = []
    golden_angle = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        y = 1 - (i / (n - 1)) * 2
        radius_at_y = math.sqrt(max(0.0, 1 - y * y))
        theta = golden_angle * i
        points.append((math.cos(theta) * radius_at_y, y, math.sin(theta) * radius_at_y))

    edges = set()
    for i, point in enumerate(points):
        distances = sorted(
            (
                (px - point[0]) ** 2 + (py - point[1]) ** 2 + (pz - point[2]) ** 2,
                j,
            )
            for j, (px, py, pz) in enumerate(points)
            if j != i
        )
        for _, j in distances[:k]:
            edges.add((i, j) if i < j else (j, i))

    return tuple(points), tuple(sorted(edges))


def _rotate(point: tuple[float, float, float], yaw: float, pitch: float) -> tuple[float, float, float]:
    x, y, z = point
    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y
    cos_p, sin_p = math.cos(pitch), math.sin(pitch)
    y, z = y * cos_p - z * sin_p, y * sin_p + z * cos_p
    return x, y, z


def build_neural_sphere_layout(width: int, height: int, angle: float = 0, activity: float = 0.5) -> dict:
    """Return projected 2D geometry for a rotating 3D wireframe network sphere."""

    cx, cy = width // 2, height // 2
    radius = min(width, height) // 2 - 18
    yaw = math.radians(angle)
    pitch = math.radians(14 * math.sin(math.radians(angle * 0.35)))
    jitter_amp = max(0.0, activity - 0.5) * 5.0

    points, edges = _sphere_geometry()
    focal = 3.0

    nodes = []
    for index, point in enumerate(points):
        x, y, z = _rotate(point, yaw, pitch)
        scale = focal / (focal + z)
        jitter = jitter_amp * math.sin(math.radians(angle * 3 + index * 47))
        nodes.append(
            {
                "x": cx + x * scale * radius + jitter,
                "y": cy + y * scale * radius + jitter,
                "z": z,
                "size": 1.4 + 1.8 * ((z + 1) / 2),
            }
        )

    edge_lines = []
    for i, j in edges:
        a, b = nodes[i], nodes[j]
        edge_lines.append({"x1": a["x"], "y1": a["y"], "x2": b["x"], "y2": b["y"], "depth": (a["z"] + b["z"]) / 2})

    nodes_sorted = sorted(range(len(nodes)), key=lambda idx: nodes[idx]["z"])
    edges_sorted = sorted(range(len(edge_lines)), key=lambda idx: edge_lines[idx]["depth"])

    return {
        "center": (cx, cy),
        "radius": radius,
        "nodes": nodes,
        "node_order": nodes_sorted,
        "edges": edge_lines,
        "edge_order": edges_sorted,
    }


def _depth_color(depth: float, near: str, far: str) -> str:
    """Interpolate between a far-side and near-side color by depth in [-1, 1]."""

    t = max(0.0, min(1.0, (depth + 1) / 2))
    near_rgb = tuple(int(near[i : i + 2], 16) for i in (1, 3, 5))
    far_rgb = tuple(int(far[i : i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(round(far_rgb[c] + (near_rgb[c] - far_rgb[c]) * t) for c in range(3))
    return f"#{mixed[0]:02X}{mixed[1]:02X}{mixed[2]:02X}"


def draw_neural_sphere(canvas, angle: float, *, accent: str, speed: float = 1.0, activity: float = 0.5) -> float:
    """Draw a rotating 3D wireframe network sphere - a living, reactive core."""

    canvas.delete("all")
    width = int(canvas["width"])
    height = int(canvas["height"])
    layout = build_neural_sphere_layout(width, height, angle, activity)
    cx, cy = layout["center"]
    radius = layout["radius"]

    far_edge = "#3A050D"
    near_edge = accent
    far_node = "#5A0F1A"
    near_node = "#FFB3BA"

    pulse = 1.0 + 0.05 * activity * math.sin(math.radians(angle * 4))
    glow_radius = radius * (0.62 + 0.1 * activity) * pulse
    for glow, color in [(glow_radius * 1.55, "#170004"), (glow_radius * 1.2, "#2B0009"), (glow_radius * 0.9, "#3F0011")]:
        canvas.create_oval(cx - glow, cy - glow, cx + glow, cy + glow, fill=color, outline="")

    for index in layout["edge_order"]:
        edge = layout["edges"][index]
        color = _depth_color(edge["depth"], near_edge, far_edge)
        width_px = 2 if edge["depth"] > 0.3 else 1
        canvas.create_line(edge["x1"], edge["y1"], edge["x2"], edge["y2"], fill=color, width=width_px)

    for index in layout["node_order"]:
        node = layout["nodes"][index]
        color = _depth_color(node["z"], near_node, far_node)
        size = node["size"]
        canvas.create_oval(node["x"] - size, node["y"] - size, node["x"] + size, node["y"] + size, fill=color, outline="")

    core = 9 + 3 * activity * (0.6 + 0.4 * math.sin(math.radians(angle * 5)))
    canvas.create_oval(cx - core - 6, cy - core - 6, cx + core + 6, cy + core + 6, outline=accent, width=1)
    canvas.create_oval(cx - core, cy - core, cx + core, cy + core, fill="#FFD9DC", outline="")

    return (angle + 1.1 * speed) % 360


__all__ = ["build_neural_sphere_layout", "draw_neural_sphere"]
