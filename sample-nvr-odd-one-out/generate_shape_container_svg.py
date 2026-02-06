#!/usr/bin/env python3
"""
Generate a shape-container SVG (picture-based-questions-guide.md §3.1, §3.9).

Can output:
  - A shape container only (--empty), for use as part of a larger drawing.
  - A shape container with N symbols inside (default), for full NVR answer options.
  - A partitioned shape (--partition): horizontal, vertical, diagonal, concentric, or segmented (radial) sections with per-section shading (guide §3.9). No symbols unless extended.

Supports all common shapes: regular (circle, triangle, square, pentagon, hexagon, heptagon, octagon)
and common irregular (right_angled_triangle, rectangle, semicircle, cross, arrow).
Symbol content is loaded from ../nvr-symbols/{symbol}.svg when not --empty.

Usage:
  python generate_shape_container_svg.py club
  python generate_shape_container_svg.py club -o option-a.svg -n 5 --shape square
  python generate_shape_container_svg.py --empty --shape cross --fill diagonal_slash
  python generate_shape_container_svg.py --partition horizontal --shape square --section-fills white,grey
  python generate_shape_container_svg.py --partition concentric --shape circle --partition-sections 0,50,100
"""

import argparse
import math
import random
import re
from pathlib import Path
from typing import Callable

# viewBox 0 0 100 100; placement rules per nvr-symbol-svg-design.md
CELL_HALF = 6.25
BORDER_MARGIN = 1.0
MIN_CENTRE_TO_CENTRE = 15.0
MIN_CENTRE = 15 + CELL_HALF + BORDER_MARGIN
MAX_CENTRE = 85 - CELL_HALF - BORDER_MARGIN
MIN_DISTANCE = MIN_CENTRE_TO_CENTRE
SYMBOL_SCALE = 1.25
MAX_PLACEMENT_ATTEMPTS = 2000
MAX_PLACEMENT_ATTEMPTS_SYMMETRIC = 6000  # symmetric layout needs more tries (canonical half + line spacing)

# Regular polygons (guide §3.1)
POLYGON_RADIUS: dict[str, float] = {"triangle": 50.0, "pentagon": 35.0, "hexagon": 35.0, "heptagon": 35.0, "octagon": 35.0}
DEFAULT_POLYGON_RADIUS = 35.0
POLYGON_CY: dict[str, float] = {"triangle": 62.5}
DEFAULT_POLYGON_CY = 50.0
# Equilateral triangle: require symbol centres further from edges so symbols do not overlap the boundary.
TRIANGLE_EDGE_MARGIN = 7.0  # > CELL_HALF (6.25) for a small buffer
CIRCLE_RADIUS = 35.0
# Semicircle (default): larger radius than full circle so more symbols fit inside (guide §3.1).
SEMICIRCLE_RADIUS = 42.0
# Right-angled triangle (default): margin from viewBox edge; smaller margin = larger triangle so more symbols fit.
RIGHT_ANGLED_TRIANGLE_MARGIN = 8.0

# All common shapes (guide §3.1): regular + common irregular
SHAPES_REGULAR = ["circle", "triangle", "square", "pentagon", "hexagon", "heptagon", "octagon"]
SHAPES_IRREGULAR = ["right_angled_triangle", "rectangle", "semicircle", "cross", "arrow"]
SHAPES_ALL = SHAPES_REGULAR + SHAPES_IRREGULAR


def load_symbol_content(symbol_path: Path) -> tuple[str, str, str]:
    """Load symbol SVG; return (inner content, fill, stroke) for wrapper <g>."""
    text = symbol_path.read_text(encoding="utf-8")
    match = re.search(r"<svg([^>]*)>(.*)</svg>", text, re.DOTALL)
    if not match:
        raise SystemExit(f"Could not parse symbol SVG: {symbol_path}")
    attrs, inner = match.group(1), match.group(2).strip()
    fill = "#000"
    stroke = "#000"
    for m in re.finditer(r'\b(fill|stroke)=["\']([^"\']+)["\']', attrs):
        if m.group(1) == "fill":
            fill = m.group(2) if m.group(2) != "currentColor" else "#000"
        else:
            stroke = m.group(2) if m.group(2) != "currentColor" else "#000"
    return inner, fill, stroke


def _mirror_point(x: float, y: float, symmetry: str) -> tuple[float, float]:
    """Reflect (x, y) about the line of symmetry in viewBox 0 0 100 100. symmetry: vertical (|), horizontal (-), diagonal_slash (/), diagonal_backslash (\\)."""
    if symmetry == "vertical":
        return (100.0 - x, y)
    if symmetry == "horizontal":
        return (x, 100.0 - y)
    if symmetry == "diagonal_slash":
        return (y, x)
    if symmetry == "diagonal_backslash":
        return (100.0 - y, 100.0 - x)
    return (x, y)


def _distance_from_symmetry_line(x: float, y: float, symmetry: str) -> float:
    """Perpendicular distance from (x, y) to the symmetry line in viewBox 0 0 100 100."""
    if symmetry == "vertical":
        return abs(x - 50.0)
    if symmetry == "horizontal":
        return abs(y - 50.0)
    if symmetry == "diagonal_slash":
        return abs(x - y) / math.sqrt(2)
    if symmetry == "diagonal_backslash":
        return abs(x + y - 100.0) / math.sqrt(2)
    return 0.0


def _in_canonical_half(x: float, y: float, symmetry: str) -> bool:
    """True if (x, y) is in the canonical half (or on the line) for placing; mirror half is generated automatically."""
    if symmetry == "vertical":
        return x <= 50.0
    if symmetry == "horizontal":
        return y <= 50.0
    if symmetry == "diagonal_slash":
        return x <= y
    if symmetry == "diagonal_backslash":
        return x + y <= 100.0
    return True


def _sample_on_symmetry_line(
    rng: random.Random,
    symmetry: str,
    inside_check: Callable[[float, float], bool],
    bounds: tuple[float, float, float, float],
    min_dist: float,
    existing: list[tuple[float, float]],
) -> tuple[float, float] | None:
    """Return one point on the mirror line that is inside and not overlapping existing, or None."""
    def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    min_x, max_x, min_y, max_y = bounds[0], bounds[1], bounds[2], bounds[3]
    for _ in range(MAX_PLACEMENT_ATTEMPTS):
        if symmetry == "vertical":
            x, y = 50.0, rng.uniform(min_y, max_y)
        elif symmetry == "horizontal":
            x, y = rng.uniform(min_x, max_x), 50.0
        elif symmetry == "diagonal_slash":
            t = rng.uniform(max(min_x, min_y), min(max_x, max_y))
            x, y = t, t
        else:
            t = rng.uniform(max(min_x, 100 - max_y), min(max_x, 100 - min_y))
            x, y = t, 100.0 - t
        if not inside_check(x, y):
            continue
        if all(distance((x, y), p) >= min_dist for p in existing):
            return (x, y)
    return None


def random_positions(
    count: int,
    min_dist: float = MIN_DISTANCE,
    seed: int | None = None,
    inside_check: Callable[[float, float], bool] | None = None,
    bounds: tuple[float, float, float, float] | None = None,
    sample_point: Callable[[random.Random], tuple[float, float]] | None = None,
    max_attempts: int | None = None,
) -> list[tuple[float, float]]:
    """Generate `count` positions with no two closer than `min_dist`. Optional inside_check, bounds, or sample_point(rng) (e.g. cross-only)."""
    limit = max_attempts if max_attempts is not None else MAX_PLACEMENT_ATTEMPTS
    rng = random.Random(seed)
    positions: list[tuple[float, float]] = []
    min_x, max_x = (bounds[0], bounds[1]) if bounds else (MIN_CENTRE, MAX_CENTRE)
    min_y, max_y = (bounds[2], bounds[3]) if bounds else (MIN_CENTRE, MAX_CENTRE)

    def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def accept(cx: float, cy: float) -> bool:
        if inside_check is not None and not inside_check(cx, cy):
            return False
        return all(distance((cx, cy), p) >= min_dist for p in positions)

    def next_point() -> tuple[float, float]:
        if sample_point is not None:
            return sample_point(rng)
        return (rng.uniform(min_x, max_x), rng.uniform(min_y, max_y))

    attempts = 0
    while len(positions) < count and attempts < limit:
        cx, cy = next_point()
        if accept(cx, cy):
            positions.append((cx, cy))
        attempts += 1

    if len(positions) < count:
        raise SystemExit(
            f"Could not place {count} symbols with min distance {min_dist} in {limit} attempts."
        )
    return positions


def _canonical_half_bounds_for_pairs(
    bounds: tuple[float, float, float, float],
    symmetry: str,
    min_dist_from_line: float,
) -> tuple[float, float, float, float]:
    """Return bounds restricted to the canonical half and inset from the symmetry line so pair sampling only hits valid off-line points."""
    min_x, max_x, min_y, max_y = bounds[0], bounds[1], bounds[2], bounds[3]
    if symmetry == "vertical":
        # Canonical half: x <= 50; off-line: x <= 50 - min_dist_from_line
        return (min_x, 50.0 - min_dist_from_line, min_y, max_y)
    if symmetry == "horizontal":
        return (min_x, max_x, min_y, 50.0 - min_dist_from_line)
    # Diagonal: keep full bounds; accept_pair still filters
    return bounds


def random_positions_symmetric(
    count: int,
    symmetry: str,
    min_dist: float,
    seed: int | None,
    inside_check: Callable[[float, float], bool],
    bounds: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
    """Generate `count` positions so the layout is symmetric about the given line (guide §3.9)."""
    rng = random.Random(seed)
    positions: list[tuple[float, float]] = []
    min_x, max_x, min_y, max_y = bounds[0], bounds[1], bounds[2], bounds[3]

    def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    # Off the line, a pair (point + mirror) must be at least min_dist apart, so point must be >= min_dist/2 from the line (guide: spacing with symmetry).
    min_dist_from_line = min_dist / 2.0
    # Sample pairs only in the canonical half inset from the line so we don't waste attempts
    pair_min_x, pair_max_x, pair_min_y, pair_max_y = _canonical_half_bounds_for_pairs(bounds, symmetry, min_dist_from_line)

    def accept_pair(cx: float, cy: float) -> bool:
        if not _in_canonical_half(cx, cy, symmetry):
            return False
        if not inside_check(cx, cy):
            return False
        mx, my = _mirror_point(cx, cy, symmetry)
        if not inside_check(mx, my):
            return False
        if (cx, cy) == (mx, my):
            # On the line: allowed (symmetric symbol); check overlap with existing only
            return all(distance((cx, cy), p) >= min_dist for p in positions)
        # Off the line: must be at least min_dist/2 from line so mirror does not overlap
        if _distance_from_symmetry_line(cx, cy, symmetry) < min_dist_from_line:
            return False
        for p in positions:
            if distance((cx, cy), p) < min_dist or distance((mx, my), p) < min_dist:
                return False
        return True

    need_pairs = count // 2
    need_on_line = count % 2
    max_attempts = MAX_PLACEMENT_ATTEMPTS_SYMMETRIC
    attempts = 0
    while len(positions) < count and attempts < max_attempts:
        if len(positions) < 2 * need_pairs:
            cx = rng.uniform(pair_min_x, pair_max_x)
            cy = rng.uniform(pair_min_y, pair_max_y)
            if accept_pair(cx, cy):
                positions.append((cx, cy))
                positions.append(_mirror_point(cx, cy, symmetry))
        elif need_on_line and len(positions) == count - 1:
            on_line = _sample_on_symmetry_line(rng, symmetry, inside_check, bounds, min_dist, positions)
            if on_line is not None:
                positions.append(on_line)
        attempts += 1

    if len(positions) < count:
        raise SystemExit(
            f"Could not place {count} symbols with layout-symmetry {symmetry} in {max_attempts} attempts."
        )
    return positions


def regular_polygon_vertices(
    sides: int,
    cx: float = 50,
    cy: float = 50,
    radius: float = 35,
    phase: float = 0,
) -> list[tuple[float, float]]:
    """Vertices of regular polygon, counterclockwise. phase=0 gives a vertex at top; phase=pi/(2*n) gives flat bottom (hexagon, octagon)."""
    if sides < 3:
        sides = 3
    points: list[tuple[float, float]] = []
    for k in range(sides):
        angle = -math.pi / 2 + phase + k * 2 * math.pi / sides
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    return points


def regular_polygon_path(
    sides: int,
    cx: float = 50,
    cy: float = 50,
    radius: float = 35,
    phase: float = 0,
) -> str:
    """SVG path for regular polygon."""
    points = regular_polygon_vertices(sides, cx, cy, radius, phase)
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in points) + " Z"


# Phase so hexagon and octagon have a horizontal edge at the bottom (not a point)
POLYGON_PHASE: dict[str, float] = {
    "hexagon": math.pi / 6,   # 30°
    "octagon": math.pi / 8,   # 22.5°
}


def point_in_convex_polygon(p: tuple[float, float], vertices: list[tuple[float, float]]) -> bool:
    """True if p is inside the convex polygon (vertices counterclockwise)."""
    px, py = p
    n = len(vertices)
    for i in range(n):
        ax, ay = vertices[i]
        bx, by = vertices[(i + 1) % n]
        cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        if cross < 0:
            return False
    return True


def point_in_polygon_ray(p: tuple[float, float], vertices: list[tuple[float, float]]) -> bool:
    """True if p is inside the polygon (any); ray-casting from p to the right."""
    px, py = p
    n = len(vertices)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = vertices[i]
        xj, yj = vertices[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def distance_point_to_segment(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distance from point p to line segment a-b."""
    px, py = p
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    d2 = vx * vx + vy * vy
    if d2 <= 0:
        return math.hypot(wx, wy)
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / d2))
    qx = ax + t * vx
    qy = ay + t * vy
    return math.hypot(px - qx, py - qy)


def min_distance_to_edges(p: tuple[float, float], vertices: list[tuple[float, float]]) -> float:
    """Minimum distance from point p to any edge of the polygon."""
    n = len(vertices)
    return min(distance_point_to_segment(p, vertices[i], vertices[(i + 1) % n]) for i in range(n))


# ----- Irregular shapes (guide §3.1 common irregular) -----

def _right_angled_triangle_geometry() -> tuple[list[tuple[float, float]], str]:
    """Right angle at bottom-left (guide §3.1). Size from RIGHT_ANGLED_TRIANGLE_MARGIN."""
    m = RIGHT_ANGLED_TRIANGLE_MARGIN
    right_angle = (m, 100 - m)
    top_left = (m, m)
    bottom_right = (100 - m, 100 - m)
    vertices = [right_angle, top_left, bottom_right]
    path_d = f"M {right_angle[0]} {right_angle[1]} L {top_left[0]} {top_left[1]} L {bottom_right[0]} {bottom_right[1]} Z"
    return vertices, path_d


def _rectangle_geometry() -> tuple[list[tuple[float, float]], str]:
    """Horizontal, width = 1.6 * height. Centred; height 43.75, width 70 (15..85 x 28.125..71.875)."""
    vertices = [(15, 28.125), (85, 28.125), (85, 71.875), (15, 71.875)]
    path_d = "M 15 28.125 L 85 28.125 L 85 71.875 L 15 71.875 Z"
    return vertices, path_d


def _semicircle_geometry() -> tuple[list[tuple[float, float]], str]:
    """Semicircle vertically centred (guide §3.1): flat at bottom, arc on top. Circle centre (50, 67.5), radius SEMICIRCLE_RADIUS."""
    r = SEMICIRCLE_RADIUS
    cy_flat = 67.5
    path_d = f"M {50 - r:.2f} {cy_flat} A {r} {r} 0 0 1 {50 + r:.2f} {cy_flat} Z"
    return [], path_d  # no vertices list; use custom inside_check


# Cross (plus) scaled to match square (15–85); corners brought in by double (inset 21 each side)
CROSS_OUTER_LO = 15.0
CROSS_OUTER_HI = 85.0
CROSS_INNER_LO = 36.0   # 15 + 21 (was 10.5, doubled)
CROSS_INNER_HI = 64.0   # 85 - 21
# Keep symbol centers at least CELL_HALF from boundary so symbols do not overlap the cross edge (arms are 21 deep so max 5 symbols: 1 center + 4 arms).
CROSS_EDGE_MARGIN = CELL_HALF  # 6.25
CROSS_SAMPLE_INSET = CELL_HALF

# Path with corners brought in by double
CROSS_PATH_D = (
    "M 36 15 H 64 V 36 H 85 V 64 H 64 V 85 H 36 V 64 H 15 V 36 H 36 Z"
)


def _point_in_cross(x: float, y: float) -> bool:
    """True if (x,y) is inside the cross (center + 4 arms), excluding the four corner regions."""
    if CROSS_INNER_LO <= x <= CROSS_INNER_HI and CROSS_INNER_LO <= y <= CROSS_INNER_HI:
        return True  # center
    if CROSS_INNER_LO <= x <= CROSS_INNER_HI and CROSS_OUTER_LO <= y < CROSS_INNER_LO:
        return True  # top arm
    if CROSS_INNER_LO <= x <= CROSS_INNER_HI and CROSS_INNER_HI < y <= CROSS_OUTER_HI:
        return True  # bottom arm
    if CROSS_OUTER_LO <= x < CROSS_INNER_LO and CROSS_INNER_LO <= y <= CROSS_INNER_HI:
        return True  # left arm
    if CROSS_INNER_HI < x <= CROSS_OUTER_HI and CROSS_INNER_LO <= y <= CROSS_INNER_HI:
        return True  # right arm
    return False


# Five rectangles inset by CROSS_SAMPLE_INSET: (x_min, x_max, y_min, y_max)
_CROSS_RECTS = [
    (CROSS_INNER_LO + CROSS_SAMPLE_INSET, CROSS_INNER_HI - CROSS_SAMPLE_INSET, CROSS_INNER_LO + CROSS_SAMPLE_INSET, CROSS_INNER_HI - CROSS_SAMPLE_INSET),  # center
    (CROSS_INNER_LO + CROSS_SAMPLE_INSET, CROSS_INNER_HI - CROSS_SAMPLE_INSET, CROSS_OUTER_LO + CROSS_SAMPLE_INSET, CROSS_INNER_LO - CROSS_SAMPLE_INSET),  # top arm
    (CROSS_INNER_LO + CROSS_SAMPLE_INSET, CROSS_INNER_HI - CROSS_SAMPLE_INSET, CROSS_INNER_HI + CROSS_SAMPLE_INSET, CROSS_OUTER_HI - CROSS_SAMPLE_INSET),  # bottom arm
    (CROSS_OUTER_LO + CROSS_SAMPLE_INSET, CROSS_INNER_LO - CROSS_SAMPLE_INSET, CROSS_INNER_LO + CROSS_SAMPLE_INSET, CROSS_INNER_HI - CROSS_SAMPLE_INSET),  # left arm
    (CROSS_INNER_HI + CROSS_SAMPLE_INSET, CROSS_OUTER_HI - CROSS_SAMPLE_INSET, CROSS_INNER_LO + CROSS_SAMPLE_INSET, CROSS_INNER_HI - CROSS_SAMPLE_INSET),  # right arm
]


def _cross_sample_point(rng: random.Random) -> tuple[float, float]:
    """Return a random point inside the insetted cross rectangles (well clear of notches)."""
    x_lo, x_hi, y_lo, y_hi = rng.choice(_CROSS_RECTS)
    return (rng.uniform(x_lo, x_hi), rng.uniform(y_lo, y_hi))


def _cross_geometry() -> tuple[list[tuple[float, float]], str, None, None]:
    """Cross (plus): single path scaled 15–85, corners brought in by double; vertices for placement."""
    vertices = [
        (36, 15), (64, 15), (64, 36), (85, 36),
        (85, 64), (64, 64), (64, 85), (36, 85),
        (36, 64), (15, 64), (15, 36), (36, 36),
    ]
    return vertices, CROSS_PATH_D, None, None


def _arrow_geometry() -> tuple[list[tuple[float, float]], str]:
    """7-sided arrow pointing right. Stem 15..35, head 35..85; head 50% of total width (guide)."""
    vertices = [(15, 25), (35, 25), (35, 15), (85, 50), (35, 85), (35, 75), (15, 75)]
    path_d = "M 15 25 L 35 25 L 35 15 L 85 50 L 35 85 L 35 75 L 15 75 Z"
    return vertices, path_d


def get_shape_geometry(shape: str) -> tuple[list[tuple[float, float]], str, str | None, list[tuple[float, float, float, float]] | None]:
    """
    Return (vertices, path_d, path_d_stroke, stroke_lines) for the shape.
    For cross: path_d_stroke is None, stroke_lines is 12 (x1,y1,x2,y2) segments. Otherwise stroke_lines is None.
    """
    shape = (shape or "").strip().lower()
    if shape == "right_angled_triangle":
        v, p = _right_angled_triangle_geometry()
        return v, p, None, None
    if shape == "rectangle":
        v, p = _rectangle_geometry()
        return v, p, None, None
    if shape == "semicircle":
        v, p = _semicircle_geometry()
        return v, p, None, None
    if shape == "cross":
        v, p_fill, _p_stroke, stroke_lines = _cross_geometry()
        return v, p_fill, None, stroke_lines
    if shape == "arrow":
        v, p = _arrow_geometry()
        return v, p, None, None
    if shape == "square":
        vertices = [(15, 15), (85, 15), (85, 85), (15, 85)]
        path_d = "M15 15 L85 15 L85 85 L15 85 Z"
        return vertices, path_d, None, None
    if shape == "circle":
        r = CIRCLE_RADIUS
        path_d = f"M 50 {50 - r} A {r} {r} 0 0 1 50 {50 + r} A {r} {r} 0 0 1 50 {50 - r} Z"
        return [], path_d, None, None
    sides = {"triangle": 3, "pentagon": 5, "hexagon": 6, "heptagon": 7, "octagon": 8}.get(shape)
    if sides is None:
        raise ValueError(f"Unknown shape: {shape!r}. Supported: {SHAPES_ALL}")
    radius = POLYGON_RADIUS.get(shape, DEFAULT_POLYGON_RADIUS)
    poly_cy = POLYGON_CY.get(shape, DEFAULT_POLYGON_CY)
    phase = POLYGON_PHASE.get(shape, 0)
    vertices = regular_polygon_vertices(sides, 50, poly_cy, radius, phase)
    path_d = regular_polygon_path(sides, 50, poly_cy, radius, phase)
    return vertices, path_d, None, None


# Partition (guide §3.9): thin lines between sections
PARTITION_LINE_STROKE = 0.8

# Hatched fill (guide §3.5)
HATCH_SPACING = 3          # distance between hatch lines (viewBox units); finer = more lines
HATCH_SPACING_HV = 2.0       # finer for horizontal_lines and vertical_lines
HATCH_STROKE = 0.8


def get_shape_bbox(
    shape: str,
    vertices: list[tuple[float, float]],
    path_d: str,
) -> tuple[float, float, float, float]:
    """Return (x_min, x_max, y_min, y_max) for the shape in viewBox 0 0 100 100."""
    s = (shape or "").strip().lower()
    if s == "circle":
        return (50 - CIRCLE_RADIUS, 50 + CIRCLE_RADIUS, 50 - CIRCLE_RADIUS, 50 + CIRCLE_RADIUS)
    if s == "semicircle":
        r = SEMICIRCLE_RADIUS
        cy = 67.5
        return (50 - r, 50 + r, cy - r, cy + r)
    if vertices:
        return (
            min(v[0] for v in vertices),
            max(v[0] for v in vertices),
            min(v[1] for v in vertices),
            max(v[1] for v in vertices),
        )
    # Fallback: square-like
    return (15.0, 85.0, 15.0, 85.0)


def even_section_bounds(num_sections: int) -> list[tuple[float, float]]:
    """Return evenly distributed section bounds (lo, hi) from 0 to 100. E.g. 2 -> [(0,50), (50,100)]."""
    if num_sections < 1:
        return []
    step = 100.0 / num_sections
    return [(k * step, (k + 1) * step) for k in range(num_sections)]


def _clip_polygon_half_plane(
    vertices: list[tuple[float, float]],
    inside: Callable[[float, float], bool],
    intersect: Callable[[tuple[float, float], tuple[float, float]], tuple[float, float]],
) -> list[tuple[float, float]]:
    """Sutherland-Hodgman: clip polygon to half-plane. intersect(a,b) returns crossing point."""
    out: list[tuple[float, float]] = []
    n = len(vertices)
    for i in range(n):
        a, b = vertices[i], vertices[(i + 1) % n]
        a_in, b_in = inside(a[0], a[1]), inside(b[0], b[1])
        if a_in:
            out.append(a)
        if a_in != b_in:
            # Edge crosses boundary; intersect returns (x,y) on the clip line
            px, py = intersect(a, b)
            out.append((px, py))
    return out


def _clip_polygon_to_horizontal_band(
    vertices: list[tuple[float, float]],
    y_lo: float,
    y_hi: float,
) -> list[tuple[float, float]]:
    """Clip polygon to horizontal band y_lo <= y <= y_hi."""

    def intersect_y(a: tuple[float, float], b: tuple[float, float], y: float) -> tuple[float, float]:
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        if abs(by - ay) < 1e-9:
            return (ax + bx) / 2, y
        t = (y - ay) / (by - ay)
        t = max(0, min(1, t))
        return (ax + t * (bx - ax), y)

    step1 = _clip_polygon_half_plane(
        vertices,
        lambda x, y: y >= y_lo,
        lambda a, b: intersect_y(a, b, y_lo),
    )
    step2 = _clip_polygon_half_plane(
        step1,
        lambda x, y: y <= y_hi,
        lambda a, b: intersect_y(a, b, y_hi),
    )
    return step2


def _clip_polygon_to_vertical_band(
    vertices: list[tuple[float, float]],
    x_lo: float,
    x_hi: float,
) -> list[tuple[float, float]]:
    """Clip polygon to vertical band x_lo <= x <= x_hi."""

    def intersect_x(a: tuple[float, float], b: tuple[float, float], x: float) -> tuple[float, float]:
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        if abs(bx - ax) < 1e-9:
            return x, (ay + by) / 2
        t = (x - ax) / (bx - ax)
        t = max(0, min(1, t))
        return (x, ay + t * (by - ay))

    step1 = _clip_polygon_half_plane(
        vertices,
        lambda x, y: x >= x_lo,
        lambda a, b: intersect_x(a, b, x_lo),
    )
    step2 = _clip_polygon_half_plane(
        step1,
        lambda x, y: x <= x_hi,
        lambda a, b: intersect_x(a, b, x_hi),
    )
    return step2


def _clip_polygon_to_diagonal_slash_band(
    vertices: list[tuple[float, float]],
    k_lo: float,
    k_hi: float,
) -> list[tuple[float, float]]:
    """Clip polygon to diagonal slash band: k_lo <= (x+y) <= k_hi."""

    def intersect_slash(a: tuple[float, float], b: tuple[float, float], k: float) -> tuple[float, float]:
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        denom = (bx - ax) + (by - ay)
        if abs(denom) < 1e-9:
            return (ax + bx) / 2, (ay + by) / 2
        t = (k - ax - ay) / denom
        t = max(0.0, min(1.0, t))
        return (ax + t * (bx - ax), ay + t * (by - ay))

    step1 = _clip_polygon_half_plane(
        vertices,
        lambda x, y: (x + y) >= k_lo,
        lambda a, b: intersect_slash(a, b, k_lo),
    )
    step2 = _clip_polygon_half_plane(
        step1,
        lambda x, y: (x + y) <= k_hi,
        lambda a, b: intersect_slash(a, b, k_hi),
    )
    return step2


def _clip_polygon_to_diagonal_backslash_band(
    vertices: list[tuple[float, float]],
    k_lo: float,
    k_hi: float,
) -> list[tuple[float, float]]:
    """Clip polygon to diagonal backslash band: k_lo <= (x-y) <= k_hi."""

    def intersect_backslash(a: tuple[float, float], b: tuple[float, float], k: float) -> tuple[float, float]:
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        denom = (bx - ax) - (by - ay)
        if abs(denom) < 1e-9:
            return (ax + bx) / 2, (ay + by) / 2
        t = (k - ax + ay) / denom
        t = max(0.0, min(1.0, t))
        return (ax + t * (bx - ax), ay + t * (by - ay))

    step1 = _clip_polygon_half_plane(
        vertices,
        lambda x, y: (x - y) >= k_lo,
        lambda a, b: intersect_backslash(a, b, k_lo),
    )
    step2 = _clip_polygon_half_plane(
        step1,
        lambda x, y: (x - y) <= k_hi,
        lambda a, b: intersect_backslash(a, b, k_hi),
    )
    return step2


def _clip_segment_to_polygon(
    x1: float, y1: float, x2: float, y2: float,
    vertices: list[tuple[float, float]],
) -> list[tuple[float, float, float, float]]:
    """Clip the segment (x1,y1)-(x2,y2) to the interior of the polygon (counterclockwise). Returns list of (xa,ya,xb,yb) segments that lie inside (at most one for convex)."""
    if not vertices or len(vertices) < 3:
        return [(x1, y1, x2, y2)]
    p1, p2 = (x1, y1), (x2, y2)
    n = len(vertices)
    for i in range(n):
        e0 = vertices[i]
        e1 = vertices[(i + 1) % n]
        ex, ey = e1[0] - e0[0], e1[1] - e0[1]
        # inside: to the left of edge for CCW  =>  ex*(py - e0[1]) - ey*(px - e0[0]) >= 0
        def cross_sign(px: float, py: float) -> float:
            return ex * (py - e0[1]) - ey * (px - e0[0])
        c1, c2 = cross_sign(p1[0], p1[1]), cross_sign(p2[0], p2[1])
        if c1 >= -1e-9 and c2 >= -1e-9:
            continue
        if c1 < -1e-9 and c2 < -1e-9:
            return []
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        denom = ex * dy - ey * dx
        if abs(denom) < 1e-12:
            return []
        t = (ex * (e0[1] - p1[1]) - ey * (e0[0] - p1[0])) / denom
        t = max(0.0, min(1.0, t))
        mid = (p1[0] + t * dx, p1[1] + t * dy)
        # Avoid collapsing to a point when the segment passes through a vertex (mid equals p1 or p2)
        if c1 >= -1e-9:
            if (mid[0] - p1[0]) ** 2 + (mid[1] - p1[1]) ** 2 < 1e-18:
                p1 = mid  # keep p2 so a later edge clips to the other intersection
            else:
                p2 = mid
        else:
            if (mid[0] - p2[0]) ** 2 + (mid[1] - p2[1]) ** 2 < 1e-18:
                p2 = mid
            else:
                p1 = mid
    seg = (p1[0], p1[1], p2[0], p2[1])
    if (seg[2] - seg[0]) ** 2 + (seg[3] - seg[1]) ** 2 < 1e-18:
        return []
    return [seg]


def _clip_segment_to_circle(
    cx: float, cy: float, r: float,
    x1: float, y1: float, x2: float, y2: float,
) -> list[tuple[float, float, float, float]]:
    """Clip the segment (x1,y1)-(x2,y2) to the interior of the circle. Returns 0 or 1 segment (xa,ya,xb,yb)."""
    dx, dy = x2 - x1, y2 - y1
    fx, fy = x1 - cx, y1 - cy
    # (x1 + t*dx - cx)^2 + (y1 + t*dy - cy)^2 = r^2  =>  a*t^2 + 2*b*t + c = 0
    a = dx * dx + dy * dy
    if a < 1e-20:
        # Degenerate segment; inside if point in circle
        if fx * fx + fy * fy <= r * r + 1e-9:
            return [(x1, y1, x2, y2)]
        return []
    b = dx * fx + dy * fy
    c = fx * fx + fy * fy - r * r
    disc = b * b - a * c
    if disc < -1e-9:
        return []
    if disc < 1e-9:
        t = -b / a
        if 0 <= t <= 1:
            return [(x1 + t * dx, y1 + t * dy, x1 + t * dx, y1 + t * dy)]
        return []
    sqrt_d = math.sqrt(disc)
    t_lo = (-b - sqrt_d) / a
    t_hi = (-b + sqrt_d) / a
    # Segment is inside circle for t in [t_lo, t_hi] intersected with [0, 1]
    t_a = max(0.0, t_lo)
    t_b = min(1.0, t_hi)
    if t_a >= t_b - 1e-9:
        return []
    xa = x1 + t_a * dx
    ya = y1 + t_a * dy
    xb = x1 + t_b * dx
    yb = y1 + t_b * dy
    return [(xa, ya, xb, yb)]


def _polygon_path_d(vertices: list[tuple[float, float]]) -> str:
    """SVG path d for a polygon from vertices."""
    if not vertices:
        return ""
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in vertices) + " Z"


def _circle_annulus_path(cx: float, cy: float, r_outer: float, r_inner: float) -> str:
    """Path for annulus (ring): outer circle then inner circle, fill-rule evenodd."""
    d_outer = f"M {cx} {cy - r_outer} A {r_outer} {r_outer} 0 0 1 {cx} {cy + r_outer} A {r_outer} {r_outer} 0 0 1 {cx} {cy - r_outer} Z"
    d_inner = f" M {cx} {cy + r_inner} A {r_inner} {r_inner} 0 0 1 {cx} {cy - r_inner} A {r_inner} {r_inner} 0 0 1 {cx} {cy + r_inner} Z"
    return d_outer + d_inner


def _polygon_centroid(vertices: list[tuple[float, float]]) -> tuple[float, float]:
    """Centroid of polygon (vertices counterclockwise)."""
    n = len(vertices)
    if n == 0:
        return (50.0, 50.0)
    ax = sum(v[0] for v in vertices) / n
    ay = sum(v[1] for v in vertices) / n
    return (ax, ay)


def _scaled_polygon_vertices(
    vertices: list[tuple[float, float]],
    cx: float,
    cy: float,
    scale: float,
) -> list[tuple[float, float]]:
    """Vertices scaled from centre (cx, cy) by scale (0 = point, 1 = same)."""
    return [(cx + scale * (v[0] - cx), cy + scale * (v[1] - cy)) for v in vertices]


def _polygon_ring_path(
    vertices: list[tuple[float, float]],
    cx: float,
    cy: float,
    scale_lo: float,
    scale_hi: float,
) -> str:
    """Path for polygon ring (region between inner and outer scaled polygon), fill-rule evenodd."""
    outer = _scaled_polygon_vertices(vertices, cx, cy, scale_hi / 100.0)
    inner = _scaled_polygon_vertices(vertices, cx, cy, scale_lo / 100.0)
    d_outer = _polygon_path_d(outer)
    d_inner = " M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in inner) + " Z"
    return d_outer + d_inner


def _circle_wedge_path(cx: float, cy: float, r: float, angle_start: float, angle_end: float) -> str:
    """Path for one wedge of a circle (centre + arc). Angles in radians, standard (0 = east, pi/2 = south). North = -pi/2. Arc clockwise from start to end; sweep 1 = clockwise in SVG."""
    x0 = cx + r * math.cos(angle_start)
    y0 = cy + r * math.sin(angle_start)
    x1 = cx + r * math.cos(angle_end)
    y1 = cy + r * math.sin(angle_end)
    return f"M {cx:.2f} {cy:.2f} L {x0:.2f} {y0:.2f} A {r:.2f} {r:.2f} 0 0 1 {x1:.2f} {y1:.2f} Z"


def _clip_polygon_to_quadrant(
    vertices: list[tuple[float, float]],
    cx: float,
    cy: float,
    quadrant: int,
) -> list[tuple[float, float]]:
    """Clip polygon to quadrant (0=top-left x<=cx y<=cy, 1=top-right x>=cx y<=cy, 2=bottom-right x>=cx y>=cy, 3=bottom-left x<=cx y>=cy)."""
    if quadrant == 0:
        step1 = _clip_polygon_half_plane(
            vertices, lambda x, y: x <= cx,
            lambda a, b: _intersect_vertical(a, b, cx),
        )
        return _clip_polygon_half_plane(
            step1, lambda x, y: y <= cy,
            lambda a, b: _intersect_horizontal(a, b, cy),
        )
    if quadrant == 1:
        step1 = _clip_polygon_half_plane(
            vertices, lambda x, y: x >= cx,
            lambda a, b: _intersect_vertical(a, b, cx),
        )
        return _clip_polygon_half_plane(
            step1, lambda x, y: y <= cy,
            lambda a, b: _intersect_horizontal(a, b, cy),
        )
    if quadrant == 2:
        step1 = _clip_polygon_half_plane(
            vertices, lambda x, y: x >= cx,
            lambda a, b: _intersect_vertical(a, b, cx),
        )
        return _clip_polygon_half_plane(
            step1, lambda x, y: y >= cy,
            lambda a, b: _intersect_horizontal(a, b, cy),
        )
    # quadrant == 3
    step1 = _clip_polygon_half_plane(
        vertices, lambda x, y: x <= cx,
        lambda a, b: _intersect_vertical(a, b, cx),
    )
    return _clip_polygon_half_plane(
        step1, lambda x, y: y >= cy,
        lambda a, b: _intersect_horizontal(a, b, cy),
    )


def _intersect_vertical(a: tuple[float, float], b: tuple[float, float], x: float) -> tuple[float, float]:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    if abs(bx - ax) < 1e-9:
        return (x, (ay + by) / 2)
    t = (x - ax) / (bx - ax)
    t = max(0.0, min(1.0, t))
    return (x, ay + t * (by - ay))


def _intersect_horizontal(a: tuple[float, float], b: tuple[float, float], y: float) -> tuple[float, float]:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    if abs(by - ay) < 1e-9:
        return ((ax + bx) / 2, y)
    t = (y - ay) / (by - ay)
    t = max(0.0, min(1.0, t))
    return (ax + t * (bx - ax), y)


def build_partitioned_sections(
    shape: str,
    path_d: str,
    vertices: list[tuple[float, float]],
    bbox: tuple[float, float, float, float],
    partition_direction: str,
    section_bounds: list[tuple[float, float]],
    section_fills: list[str],
    shape_clip_id: str = "shapeClip",
) -> tuple[str, str, list[tuple[float, float, float, float]]]:
    """Build defs, fill group XML, and partition separator lines (x1,y1,x2,y2) for thin strokes. Guide §3.9."""
    x_min, x_max, y_min, y_max = bbox
    solid = {"solid_black": "#000", "grey": "#808080", "grey_light": "#d0d0d0", "white": "none"}
    hatch_keys = ("diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines")
    defs_parts: list[str] = [f'  <defs><clipPath id="{shape_clip_id}"><path d="{path_d}"/></clipPath></defs>']
    fill_parts: list[str] = []
    partition_lines: list[tuple[float, float, float, float]] = []

    for i, (lo, hi) in enumerate(section_bounds):
        fill_key = section_fills[i % len(section_fills)]
        if partition_direction == "horizontal":
            y_lo = y_min + (y_max - y_min) * lo / 100.0
            y_hi = y_min + (y_max - y_min) * hi / 100.0
            if i + 1 < len(section_bounds):
                if vertices and len(vertices) >= 3:
                    for seg in _clip_segment_to_polygon(x_min, y_hi, x_max, y_hi, vertices):
                        partition_lines.append(seg)
                elif shape == "circle":
                    cx, cy, r = 50.0, 50.0, CIRCLE_RADIUS
                    for seg in _clip_segment_to_circle(cx, cy, r, x_min, y_hi, x_max, y_hi):
                        partition_lines.append(seg)
                else:
                    partition_lines.append((x_min, y_hi, x_max, y_hi))
            if vertices and len(vertices) >= 3:
                clip_verts = _clip_polygon_to_horizontal_band(vertices, y_lo, y_hi)
                if clip_verts:
                    section_path = _polygon_path_d(clip_verts)
                    if fill_key in solid:
                        fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                    else:
                        cid = f"{shape_clip_id}_sec{i}"
                        defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                        _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                        fill_parts.append(hatch_el)
            else:
                # Fallback: rect clipped by shape
                h = y_hi - y_lo
                fill_parts.append(
                    f'  <g clip-path="url(#{shape_clip_id})">'
                    f'<rect x="0" y="{y_lo:.2f}" width="100" height="{h:.2f}" fill="{solid.get(fill_key, "none")}" stroke="none"/>'
                    "</g>"
                )
        elif partition_direction == "vertical":
            x_lo = x_min + (x_max - x_min) * lo / 100.0
            x_hi = x_min + (x_max - x_min) * hi / 100.0
            if i + 1 < len(section_bounds):
                if vertices and len(vertices) >= 3:
                    for seg in _clip_segment_to_polygon(x_hi, y_min, x_hi, y_max, vertices):
                        partition_lines.append(seg)
                elif shape == "circle":
                    cx, cy, r = 50.0, 50.0, CIRCLE_RADIUS
                    for seg in _clip_segment_to_circle(cx, cy, r, x_hi, y_min, x_hi, y_max):
                        partition_lines.append(seg)
                else:
                    partition_lines.append((x_hi, y_min, x_hi, y_max))
            if vertices and len(vertices) >= 3:
                clip_verts = _clip_polygon_to_vertical_band(vertices, x_lo, x_hi)
                if clip_verts:
                    section_path = _polygon_path_d(clip_verts)
                    if fill_key in solid:
                        fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                    else:
                        cid = f"{shape_clip_id}_sec{i}"
                        defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                        _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                        fill_parts.append(hatch_el)
            else:
                w = x_hi - x_lo
                fill_parts.append(
                    f'  <g clip-path="url(#{shape_clip_id})">'
                    f'<rect x="{x_lo:.2f}" y="0" width="{w:.2f}" height="100" fill="{solid.get(fill_key, "none")}" stroke="none"/>'
                    "</g>"
                )
        elif partition_direction == "diagonal_slash":
            # 0 = (x_min,y_min), 100 = (x_max,y_max); level = (x+y)
            sum_lo = (x_min + y_min) + ((x_max + y_max) - (x_min + y_min)) * lo / 100.0
            sum_hi = (x_min + y_min) + ((x_max + y_max) - (x_min + y_min)) * hi / 100.0
            if i + 1 < len(section_bounds):
                # Partition line: segment x+y=sum_hi clipped to bbox
                px1 = max(x_min, min(x_max, sum_hi - y_max))
                py1 = sum_hi - px1
                px2 = min(x_max, max(x_min, sum_hi - y_min))
                py2 = sum_hi - px2
                if abs(px2 - px1) + abs(py2 - py1) > 0.1:
                    if vertices and len(vertices) >= 3:
                        for seg in _clip_segment_to_polygon(px1, py1, px2, py2, vertices):
                            partition_lines.append(seg)
                    else:
                        partition_lines.append((px1, py1, px2, py2))
            if vertices and len(vertices) >= 3:
                s_lo, s_hi = min(sum_lo, sum_hi), max(sum_lo, sum_hi)
                clip_verts = _clip_polygon_to_diagonal_slash_band(vertices, s_lo, s_hi)
                if clip_verts:
                    section_path = _polygon_path_d(clip_verts)
                    if fill_key in solid:
                        fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                    else:
                        cid = f"{shape_clip_id}_sec{i}"
                        defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                        _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                        fill_parts.append(hatch_el)
        elif partition_direction == "diagonal_backslash":
            # 0 = (x_max,y_min), 100 = (x_min,y_max); level = (x - y)
            diff_min = x_max - y_min
            diff_max = x_min - y_max
            diff_lo = diff_min + (diff_max - diff_min) * lo / 100.0
            diff_hi = diff_min + (diff_max - diff_min) * hi / 100.0
            if i + 1 < len(section_bounds):
                # Partition line: segment x-y=diff_hi clipped to bbox
                px1 = max(x_min, min(x_max, diff_hi + y_min))
                py1 = px1 - diff_hi
                px2 = max(x_min, min(x_max, diff_hi + y_max))
                py2 = px2 - diff_hi
                if abs(px2 - px1) + abs(py2 - py1) > 0.1:
                    if vertices and len(vertices) >= 3:
                        for seg in _clip_segment_to_polygon(px1, py1, px2, py2, vertices):
                            partition_lines.append(seg)
                    else:
                        partition_lines.append((px1, py1, px2, py2))
            if vertices and len(vertices) >= 3:
                # (x-y) decreases from 0% to 100%, so diff_lo > diff_hi; band needs k_lo <= k_hi
                k_lo, k_hi = min(diff_lo, diff_hi), max(diff_lo, diff_hi)
                clip_verts = _clip_polygon_to_diagonal_backslash_band(vertices, k_lo, k_hi)
                if clip_verts:
                    section_path = _polygon_path_d(clip_verts)
                    if fill_key in solid:
                        fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                    else:
                        cid = f"{shape_clip_id}_sec{i}"
                        defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                        _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                        fill_parts.append(hatch_el)
        elif partition_direction == "concentric" and shape == "circle":
            r = CIRCLE_RADIUS
            cx, cy = 50.0, 50.0
            r_lo = r * lo / 100.0
            r_hi = r * hi / 100.0
            if i + 1 < len(section_bounds):
                # Partition line: circle at r_hi
                n_pts = 32
                for k in range(n_pts):
                    t0 = 2 * math.pi * k / n_pts
                    t1 = 2 * math.pi * (k + 1) / n_pts
                    partition_lines.append(
                        (cx + r_hi * math.cos(t0), cy + r_hi * math.sin(t0), cx + r_hi * math.cos(t1), cy + r_hi * math.sin(t1))
                    )
            if r_lo < 1e-6:
                section_path = f"M {cx} {cy - r_hi} A {r_hi} {r_hi} 0 0 1 {cx} {cy + r_hi} A {r_hi} {r_hi} 0 0 1 {cx} {cy - r_hi} Z"
            else:
                section_path = _circle_annulus_path(cx, cy, r_hi, r_lo)
            if fill_key in solid:
                fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none" fill-rule="evenodd"/>')
            else:
                cid = f"{shape_clip_id}_sec{i}"
                # Ring path (outer+inner) needs clip-rule="evenodd" so hatch is clipped to the band only
                clip_rule = ' clip-rule="evenodd"' if r_lo >= 1e-6 else ""
                defs_parts.append(f'  <defs><clipPath id="{cid}"{clip_rule}><path d="{section_path}"/></clipPath></defs>')
                _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                fill_parts.append(hatch_el)
        elif partition_direction == "segmented":
            # Radial segments from centre. Guide §3.9: circle any N; regular polygon when N divides sides; irregular exactly 4 (quadrants).
            num_segments = len(section_bounds)
            if shape == "circle":
                cx, cy, r = 50.0, 50.0, CIRCLE_RADIUS
                angle_north = -math.pi / 2
                angle_i = angle_north + i * 2 * math.pi / num_segments
                angle_i1 = angle_north + (i + 1) * 2 * math.pi / num_segments
                if i + 1 < num_segments:
                    x1 = cx + r * math.cos(angle_i1)
                    y1 = cy + r * math.sin(angle_i1)
                    partition_lines.append((cx, cy, x1, y1))
                elif i == num_segments - 1:
                    partition_lines.append((cx, cy, cx + r * math.cos(angle_north), cy + r * math.sin(angle_north)))
                section_path = _circle_wedge_path(cx, cy, r, angle_i, angle_i1)
                if fill_key in solid:
                    fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                else:
                    cid = f"{shape_clip_id}_sec{i}"
                    defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                    _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                    fill_parts.append(hatch_el)
            elif vertices and len(vertices) >= 3:
                cx, cy = _polygon_centroid(vertices)
                sides = len(vertices)
                if shape in ("triangle", "square", "pentagon", "hexagon", "heptagon", "octagon") and sides % num_segments == 0:
                    step = sides // num_segments
                    idx0 = (i * step) % sides
                    idx1 = (i * step + 1) % sides
                    v0, v1 = vertices[idx0], vertices[idx1]
                    # Radial line from centre to end of wedge (v1); add for every segment so the last wedge gets its closing line too
                    partition_lines.append((cx, cy, v1[0], v1[1]))
                    section_path = f"M {cx:.2f} {cy:.2f} L {v0[0]:.2f} {v0[1]:.2f} L {v1[0]:.2f} {v1[1]:.2f} Z"
                    if fill_key in solid:
                        fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                    else:
                        cid = f"{shape_clip_id}_sec{i}"
                        defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                        _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                        fill_parts.append(hatch_el)
                else:
                    if num_segments != 4:
                        raise ValueError("Segmented partition for irregular shape requires exactly 4 sections.")
                    if i == 0:
                        for seg in _clip_segment_to_polygon(cx, y_min, cx, y_max, vertices):
                            partition_lines.append(seg)
                        for seg in _clip_segment_to_polygon(x_min, cy, x_max, cy, vertices):
                            partition_lines.append(seg)
                    clip_verts = _clip_polygon_to_quadrant(vertices, cx, cy, i)
                    if not clip_verts:
                        continue
                    section_path = _polygon_path_d(clip_verts)
                    if fill_key in solid:
                        fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                    else:
                        cid = f"{shape_clip_id}_sec{i}"
                        defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                        _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                        fill_parts.append(hatch_el)
            else:
                raise ValueError("Segmented partition requires circle or polygon shape.")
        elif partition_direction == "concentric" and vertices and len(vertices) >= 3:
            # Polygon concentric: scaled copy of shape inside itself (0 = centre, 100 = outer)
            cx, cy = _polygon_centroid(vertices)
            scale_lo = lo / 100.0
            scale_hi = hi / 100.0
            if i + 1 < len(section_bounds):
                # Partition line: inner polygon boundary at scale_hi
                inner_verts = _scaled_polygon_vertices(vertices, cx, cy, scale_hi)
                for j in range(len(inner_verts)):
                    a = inner_verts[j]
                    b = inner_verts[(j + 1) % len(inner_verts)]
                    partition_lines.append((a[0], a[1], b[0], b[1]))
            if scale_lo < 1e-6:
                section_path = _polygon_path_d(_scaled_polygon_vertices(vertices, cx, cy, scale_hi))
            else:
                section_path = _polygon_ring_path(vertices, cx, cy, lo, hi)
            if fill_key in solid:
                fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none" fill-rule="evenodd"/>')
            else:
                cid = f"{shape_clip_id}_sec{i}"
                # Ring path (outer+inner) needs clip-rule="evenodd" so hatch is clipped to the band only
                clip_rule = ' clip-rule="evenodd"' if scale_lo >= 1e-6 else ""
                defs_parts.append(f'  <defs><clipPath id="{cid}"{clip_rule}><path d="{section_path}"/></clipPath></defs>')
                _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                fill_parts.append(hatch_el)

    return ("\n".join(defs_parts), "\n".join(fill_parts), partition_lines)


def _hatch_lines(fill_key: str) -> list[tuple[float, float, float, float]]:
    """Return list of (x1, y1, x2, y2) for full viewBox-spanning lines."""
    s = HATCH_SPACING_HV if fill_key in ("horizontal_lines", "vertical_lines") else HATCH_SPACING
    out: list[tuple[float, float, float, float]] = []
    if fill_key == "diagonal_slash":
        k = -100
        while k <= 200:
            out.append((0, -k, 100, 100 - k))
            k += s
    elif fill_key == "diagonal_backslash":
        k = 0
        while k <= 200:
            out.append((0, k, 100, k - 100))
            k += s
    elif fill_key == "horizontal_lines":
        k = 0
        while k <= 100:
            out.append((0, k, 100, k))
            k += s
    elif fill_key == "vertical_lines":
        k = 0
        while k <= 100:
            out.append((k, 0, k, 100))
            k += s
    return out


def hatch_continuous_defs_and_lines(clip_id: str, fill_key: str, path_d: str) -> tuple[str, str]:
    """Continuous hatch lines clipped to shape path."""
    line_coords = _hatch_lines(fill_key)
    stroke = HATCH_STROKE
    defs_str = f'  <defs><clipPath id="{clip_id}"><path d="{path_d}"/></clipPath></defs>'
    line_elts = "\n".join(
        f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#000" stroke-width="{stroke}" stroke-linecap="round"/>'
        for x1, y1, x2, y2 in line_coords
    )
    return defs_str, f'  <g clip-path="url(#{clip_id})" fill="none">\n{line_elts}\n  </g>'


def build_svg(
    symbol_content: str,
    positions: list[tuple[float, float]],
    symbol_name: str,
    shape: str,
    path_d: str,
    fill: str = "#000",
    stroke: str = "#000",
    line_style: str = "solid",
    polygon_fill: str = "none",
    polygon_fill_defs: str | None = None,
    polygon_hatch_lines: str | None = None,
    path_d_stroke: str | None = None,
    stroke_lines: list[tuple[float, float, float, float]] | None = None,
    partition_defs: str | None = None,
    partition_fill_content: str | None = None,
    partition_lines: list[tuple[float, float, float, float]] | None = None,
) -> str:
    """Build shape-container SVG. For cross use stroke_lines (12 segments); else path_d_stroke or single path. Partition (guide §3.9) optional."""
    stroke_dasharray = {"solid": "", "dashed": "8 4", "dotted": "2 4"}.get(line_style, "")
    dash_attr = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""
    is_cross = (shape or "").strip().lower() == "cross"
    fill_rule_attr = ' fill-rule="evenodd"' if is_cross else ""
    is_partitioned = partition_fill_content is not None

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">',
        f"  <!-- {shape} container, {line_style}, fill; {len(positions)} {symbol_name} symbols -->",
    ]
    if partition_defs:
        lines.append(partition_defs)
    elif polygon_fill_defs:
        lines.append(polygon_fill_defs)
    if partition_fill_content:
        # Draw shape outline first (underneath) so segment fills extend to the boundary on top
        if stroke_lines is not None:
            lines.append(f'  <path d="{path_d}" fill="none" stroke="none"{fill_rule_attr} />')
            for x1, y1, x2, y2 in stroke_lines:
                lines.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="2"{dash_attr} />')
        else:
            lines.append(f'  <path d="{path_d}" fill="none" stroke-width="2"{dash_attr}{fill_rule_attr} />')
        lines.append(partition_fill_content)
        # Clip partition lines to shape so they (and their stroke) do not extend beyond the boundary
        if partition_lines:
            lines.append('  <g clip-path="url(#shapeClip)">')
            for x1, y1, x2, y2 in partition_lines:
                lines.append(f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#000" stroke-width="{PARTITION_LINE_STROKE}" stroke-linecap="round"/>')
            lines.append("  </g>")
        # Draw shape outline again on top so the border is always the usual thickness (not hidden by dark fills)
        if stroke_lines is not None:
            for x1, y1, x2, y2 in stroke_lines:
                lines.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="2"{dash_attr} />')
        else:
            lines.append(f'  <path d="{path_d}" fill="none" stroke-width="2"{dash_attr}{fill_rule_attr} />')
    elif polygon_hatch_lines:
        lines.append(polygon_hatch_lines)
    if not is_partitioned:
        if stroke_lines is not None:
            # Cross: fill path then 12 explicit lines so outline is never interpreted as a square
            lines.append(f'  <path d="{path_d}" fill="{polygon_fill}" stroke="none"{fill_rule_attr} />')
            for x1, y1, x2, y2 in stroke_lines:
                lines.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="2"{dash_attr} />')
        elif path_d_stroke is not None:
            lines.append(f'  <path d="{path_d}" fill="{polygon_fill}" stroke="none"{fill_rule_attr} />')
            lines.append(
                f'  <path d="{path_d_stroke}" fill="none" stroke-width="2" stroke-linejoin="miter" stroke-linecap="butt"{dash_attr} />'
            )
        else:
            lines.append(f'  <path d="{path_d}" fill="{polygon_fill}" stroke-width="2"{dash_attr}{fill_rule_attr} />')
    for cx, cy in positions:
        lines.append(f'  <g transform="translate({cx:.2f}, {cy:.2f}) scale({SYMBOL_SCALE}) translate(-5,-5)" fill="{fill}" stroke="{stroke}">')
        for line in symbol_content.split("\n"):
            lines.append("    " + line)
        lines.append("  </g>")
    lines.append("</svg>")
    return "\n".join(lines)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Generate a shape-container SVG (optionally with symbols inside). Use --empty for container only."
    )
    parser.add_argument(
        "symbol",
        type=str,
        nargs="?",
        default=None,
        help="Symbol type (e.g. club, heart). Required unless --empty.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output SVG path.",
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=10,
        metavar="N",
        help="Number of symbols inside (default: 10). Ignored if --empty.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for symbol placement.",
    )
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Output only the shape container (no symbols). For use as part of a larger drawing.",
    )
    parser.add_argument(
        "--symbols-dir",
        type=Path,
        default=script_dir.parent / "nvr-symbols",
        help="Directory containing symbol SVGs.",
    )
    parser.add_argument(
        "--shape",
        type=str,
        default="square",
        choices=SHAPES_ALL,
        help="Shape container (guide §3.1). Default: square.",
    )
    parser.add_argument(
        "--line-style",
        type=str,
        default="solid",
        choices=["solid", "dashed", "dotted"],
        help="Outline style.",
    )
    parser.add_argument(
        "--fill",
        type=str,
        default="white",
        choices=[
            "solid_black", "grey", "grey_light", "white",
            "diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines",
        ],
        help="Shape fill / shading.",
    )
    parser.add_argument(
        "--layout-symmetry",
        type=str,
        default=None,
        choices=["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"],
        metavar="LINE",
        help="Force symbol layout symmetry about a line (guide §3.9). vertical (|), horizontal (-), diagonal_slash (/), diagonal_backslash (\\). Default: no symmetry.",
    )
    parser.add_argument(
        "--partition",
        type=str,
        default=None,
        choices=["horizontal", "vertical", "diagonal_slash", "diagonal_backslash", "concentric", "segmented"],
        help="Partition the shape into sections (guide §3.9). segmented = radial wedges. No symbols when partitioned unless --partition-symbols is set.",
    )
    parser.add_argument(
        "--partition-sections",
        type=str,
        default=None,
        metavar="BOUNDS",
        help="Section bounds as comma-separated percentages, e.g. 0,50,100 for two halves. Default: 2 even sections.",
    )
    parser.add_argument(
        "--section-fills",
        type=str,
        default=None,
        metavar="FILLS",
        help="Comma-separated fill keys per section (cycle if fewer than sections), e.g. white,grey,diagonal_slash.",
    )
    args = parser.parse_args()
    args.shape = (args.shape or "square").strip().lower()

    if not args.empty and args.symbol is None and not args.partition:
        raise SystemExit("Symbol is required unless --empty or --partition.")

    vertices, path_d, path_d_stroke, stroke_lines = get_shape_geometry(args.shape)
    bbox = get_shape_bbox(args.shape, vertices, path_d)

    # Partition (guide §3.9): section bounds and fills
    if args.partition:
        if args.partition in ("diagonal_slash", "diagonal_backslash") and not (vertices and len(vertices) >= 3):
            raise SystemExit("Diagonal partition requires a polygon shape (not circle/semicircle).")
        if args.partition == "concentric" and args.shape == "circle" and not vertices:
            pass  # circle concentric uses circle-specific path
        elif args.partition == "concentric" and not (vertices and len(vertices) >= 3):
            raise SystemExit("Concentric partition requires circle or a polygon shape.")
        if args.partition == "segmented":
            if args.shape == "semicircle":
                raise SystemExit("Segmented partition for semicircle is not yet implemented.")
            if not vertices and args.shape != "circle":
                raise SystemExit("Segmented partition requires circle or a polygon shape.")
        if args.partition_sections:
            parts = [float(p.strip()) for p in args.partition_sections.split(",")]
            if len(parts) < 2 or parts[0] != 0 or parts[-1] != 100:
                raise SystemExit("--partition-sections must be like 0,50,100 (start 0, end 100).")
            section_bounds = [(parts[i], parts[i + 1]) for i in range(len(parts) - 1)]
        else:
            section_bounds = even_section_bounds(4 if args.partition == "segmented" else 2)
        if args.partition == "segmented" and vertices and len(vertices) >= 3:
            num_seg = len(section_bounds)
            sides = len(vertices)
            if args.shape in ("triangle", "square", "pentagon", "hexagon", "heptagon", "octagon"):
                if sides % num_seg != 0:
                    raise SystemExit(
                        f"Segmented partition: for regular polygon with {sides} sides, number of segments ({num_seg}) must divide {sides}."
                    )
            elif num_seg != 4:
                raise SystemExit("Segmented partition for irregular shape requires exactly 4 sections (0,25,50,75,100).")
        section_fills = (args.section_fills or "white,grey").replace(" ", "").split(",")
        try:
            partition_defs, partition_fill_content, partition_lines = build_partitioned_sections(
                args.shape, path_d, vertices, bbox, args.partition, section_bounds, section_fills
            )
        except ValueError as e:
            raise SystemExit(str(e))
        polygon_fill = "none"
        polygon_fill_defs = None
        polygon_hatch_lines = None
        symbol_content = ""
        symbol_fill = "#000"
        symbol_stroke = "#000"
        symbol_name = "none"
        positions = []
    else:
        partition_defs = None
        partition_fill_content = None
        partition_lines = None

    solid_fills = {"solid_black": "#000", "grey": "#808080", "grey_light": "#d0d0d0", "white": "none"}
    hatch_keys = ("diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines")
    if not args.partition:
        if args.fill in solid_fills:
            polygon_fill = solid_fills[args.fill]
            polygon_fill_defs = None
            polygon_hatch_lines = None
        elif args.fill in hatch_keys:
            polygon_fill = "none"
            polygon_fill_defs, polygon_hatch_lines = hatch_continuous_defs_and_lines("hatchClip", args.fill, path_d)
        else:
            polygon_fill = "none"
            polygon_fill_defs = None
            polygon_hatch_lines = None

    if args.empty or args.partition:
        if not args.partition:
            symbol_content = ""
            symbol_fill = "#000"
            symbol_stroke = "#000"
            symbol_name = "none"
            positions = []
    else:
        symbol_path = args.symbols_dir / f"{args.symbol}.svg"
        if not symbol_path.exists():
            raise SystemExit(f"Symbol file not found: {symbol_path}")
        symbol_content, symbol_fill, symbol_stroke = load_symbol_content(symbol_path)
        symbol_name = args.symbol

        def inside_check(cx: float, cy: float) -> bool:
            if args.shape == "circle":
                return math.hypot(cx - 50, cy - 50) <= CIRCLE_RADIUS - CELL_HALF
            if args.shape == "semicircle":
                # Vertically centred: circle centre (50, 67.5), flat at bottom (y=67.5). Inside with margin.
                cy_centre = 67.5
                arc_top_y = cy_centre - SEMICIRCLE_RADIUS
                if math.hypot(cx - 50, cy - cy_centre) > SEMICIRCLE_RADIUS - CELL_HALF:
                    return False
                if cy > cy_centre - CELL_HALF or cy < arc_top_y + CELL_HALF:  # margin from flat and from arc top
                    return False
                return True
            if args.shape == "cross":
                # Only inside the cross (center + 4 arms); exclude corners; keep clear of notches (CROSS_EDGE_MARGIN)
                if not _point_in_cross(cx, cy):
                    return False
                return min_distance_to_edges((cx, cy), vertices) >= CROSS_EDGE_MARGIN
            if vertices:
                use_convex = args.shape in ("square", "triangle", "pentagon", "hexagon", "heptagon", "octagon", "right_angled_triangle", "rectangle")
                margin = TRIANGLE_EDGE_MARGIN if args.shape == "triangle" else CELL_HALF
                if use_convex:
                    ok = point_in_convex_polygon((cx, cy), vertices) and min_distance_to_edges((cx, cy), vertices) >= margin
                else:
                    ok = point_in_polygon_ray((cx, cy), vertices) and min_distance_to_edges((cx, cy), vertices) >= margin
                return ok
            return False

        if args.shape == "circle":
            bounds = (50 - CIRCLE_RADIUS, 50 + CIRCLE_RADIUS, 50 - CIRCLE_RADIUS, 50 + CIRCLE_RADIUS)
        elif args.shape == "semicircle":
            # Vertically centred: arc top at 67.5 - SEMICIRCLE_RADIUS, flat at 67.5; use inner bounds with margin for sampling
            arc_top_y = 67.5 - SEMICIRCLE_RADIUS
            bounds = (50 - SEMICIRCLE_RADIUS, 50 + SEMICIRCLE_RADIUS, arc_top_y + CELL_HALF, 67.5 - CELL_HALF)
        elif vertices:
            bounds = (
                min(v[0] for v in vertices),
                max(v[0] for v in vertices),
                min(v[1] for v in vertices),
                max(v[1] for v in vertices),
            )
        else:
            bounds = (MIN_CENTRE, MAX_CENTRE, MIN_CENTRE, MAX_CENTRE)
        if args.layout_symmetry:
            positions = random_positions_symmetric(
                args.count,
                args.layout_symmetry,
                MIN_DISTANCE,
                args.seed,
                inside_check,
                bounds,
            )
        else:
            # Cross: sample only from the five rectangles so symbols never land in the missing corners
            sample_pt = _cross_sample_point if args.shape == "cross" else None
            cross_attempts = 8000 if args.shape == "cross" else None  # cross has tight regions, need more tries
            positions = random_positions(
                args.count, seed=args.seed, inside_check=inside_check, bounds=bounds, sample_point=sample_pt, max_attempts=cross_attempts
            )

    svg = build_svg(
        symbol_content,
        positions,
        symbol_name,
        shape=args.shape,
        path_d=path_d,
        path_d_stroke=path_d_stroke,
        stroke_lines=stroke_lines,
        fill=symbol_fill,
        stroke=symbol_stroke,
        line_style=args.line_style,
        polygon_fill=polygon_fill,
        polygon_fill_defs=polygon_fill_defs,
        polygon_hatch_lines=polygon_hatch_lines,
        partition_defs=partition_defs,
        partition_fill_content=partition_fill_content,
        partition_lines=partition_lines,
    )

    out = args.output
    if out is None:
        out_dir = script_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        if args.partition:
            out = out_dir / f"partition-{args.shape}-{args.partition}.svg"
        elif args.empty:
            out = out_dir / f"shape-{args.shape}.svg"
        else:
            out_name = {"club": "clubs", "spade": "spades"}.get(args.symbol, args.symbol)
            out = out_dir / f"option-{args.shape}-{args.count}-{out_name}.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    if args.empty:
        print(f"Wrote {out} (shape only).")
    else:
        print(f"Wrote {out} ({len(positions)} symbols).")


if __name__ == "__main__":
    main()
