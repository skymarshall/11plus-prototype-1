#!/usr/bin/env python3
"""
Generate a shape-container SVG (question-gen/QUESTION-GENERATION-DESIGN.md §4, Shape containers and Partitioned shapes).

Shape-container and partitioned-shape drawing for question-gen (question-gen/lib/).

Can output:
  - A shape container only (--empty), for use as part of a larger drawing.
  - A shape container with N motifs inside (default), for full NVR answer options.
  - A partitioned shape (--partition): horizontal, vertical, diagonal, concentric, or radial sections with per-section shading (guide §3.9). No motifs unless extended.

Supports all common shapes: regular (circle, triangle, square, pentagon, hexagon, heptagon, octagon),
common irregular (right_angled_triangle, rectangle, semicircle, cross, arrow),
and symbol containers (plus, times, club, heart, diamond, spade, star) loaded from shape-{symbol}.svg.
Motif content is loaded from ../nvr-symbols/shape-{motif}.svg when not --empty; motifs are rendered with --motif-fill (black or white) in layouts (guide §3.2).

Usage:
  python nvr_draw_container_svg.py club
  python nvr_draw_container_svg.py club -o option-a.svg -n 5 --shape square
  python nvr_draw_container_svg.py --empty --shape cross --fill diagonal_slash
  python nvr_draw_container_svg.py --partition horizontal --shape square --section-fills white,grey
  python nvr_draw_container_svg.py --partition concentric --shape circle --partition-sections 0,50,100
"""

import argparse
import math
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

# viewBox 0 0 100 100; placement rules per nvr-symbol-svg-design.md
CELL_HALF = 6.25
BORDER_MARGIN = 1.0
MIN_CENTRE_TO_CENTRE = 12.0
MIN_CENTRE = 12 + CELL_HALF + BORDER_MARGIN
MAX_CENTRE = 85 - CELL_HALF - BORDER_MARGIN
MIN_DISTANCE = MIN_CENTRE_TO_CENTRE
# Motif cell size in answer viewBox 0 0 100 100 is 1/8 = 12.5 units (nvr-symbol-svg-design.md)
MOTIF_CELL_SIZE = 12.5
MAX_PLACEMENT_ATTEMPTS = 2000
MAX_PLACEMENT_ATTEMPTS_SYMMETRIC = 6000  # symmetric layout needs more tries (canonical half + line spacing)

# Regular polygons (guide §3.1). Pentagon–octagon use 40 so 10 motifs fit with CELL_HALF margin (square/circle use 35/50).
POLYGON_RADIUS: dict[str, float] = {"triangle": 47.0, "pentagon": 38.0, "hexagon": 40.0, "heptagon": 40.0, "octagon": 40.0}  # pentagon tightened 2
DEFAULT_POLYGON_RADIUS = 40.0
POLYGON_CY: dict[str, float] = {"triangle": 62.5}
DEFAULT_POLYGON_CY = 50.0
# Equilateral triangle: require motif centres further from edges so motifs do not overlap the boundary.
TRIANGLE_EDGE_MARGIN = 7.0  # > CELL_HALF (6.25) for a small buffer
CIRCLE_RADIUS = 35.0
# Semicircle (default): larger radius than full circle so more motifs fit inside (guide §3.1).
SEMICIRCLE_RADIUS = 42.0
# Right-angled triangle (default): margin from viewBox edge; smaller margin = larger triangle so more motifs fit.
RIGHT_ANGLED_TRIANGLE_MARGIN = 8.0

# All common shapes (guide §3.1): regular + common irregular + symbols (as containers)
SHAPES_REGULAR = ["circle", "triangle", "square", "pentagon", "hexagon", "heptagon", "octagon"]
SHAPES_IRREGULAR = ["right_angled_triangle", "rectangle", "semicircle", "cross", "arrow"]
SHAPES_SYMBOLS = ["plus", "times", "club", "heart", "diamond", "spade", "star"]
SHAPES_ALL = SHAPES_REGULAR + SHAPES_IRREGULAR + SHAPES_SYMBOLS


def load_motif_content(motif_path: Path) -> tuple[str, float, float, float]:
    """Load motif SVG (e.g. shape-club.svg); return (inner content, scale, translate_x, translate_y).
    Scale/translate place the motif in a MOTIF_CELL_SIZE×MOTIF_CELL_SIZE cell in 0 0 100 100 space.
    Motifs are always rendered filled black in layouts (guide §3.2).
    """
    text = motif_path.read_text(encoding="utf-8")
    match = re.search(r"<svg([^>]*)>(.*)</svg>", text, re.DOTALL)
    if not match:
        raise SystemExit(f"Could not parse motif SVG: {motif_path}")
    attrs, inner = match.group(1), match.group(2).strip()
    # Parse viewBox: "0 0 W H" -> scale so motif fits in MOTIF_CELL_SIZE, centre at (W/2, H/2)
    vb = re.search(r'viewBox\s*=\s*["\']?\s*0\s+0\s+([\d.]+)\s+([\d.]+)', attrs)
    if vb:
        w, h = float(vb.group(1)), float(vb.group(2))
        size = max(w, h, 1.0)
        scale = MOTIF_CELL_SIZE / size
        tx, ty = -w / 2, -h / 2
    else:
        scale = MOTIF_CELL_SIZE / 10.0  # default 0 0 10 10
        tx, ty = -5.0, -5.0
    return inner, scale, tx, ty


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
            f"Could not place {count} motifs with min distance {min_dist} in {limit} attempts."
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
            # On the line: allowed (symmetric motif); check overlap with existing only
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
            f"Could not place {count} motifs with layout-symmetry {symmetry} in {max_attempts} attempts."
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
    """Right angle at bottom-left (guide §3.1). Size from RIGHT_ANGLED_TRIANGLE_MARGIN. Hypotenuse tightened 2 units toward diagonal."""
    m = RIGHT_ANGLED_TRIANGLE_MARGIN
    right_angle = (m, 100 - m)
    top_left = (m, m)
    bottom_right = (100 - m, 100 - m)
    # Tighten bounding box close to diagonal: move hypotenuse endpoints 2 units toward each other along diagonal
    diag_inset = 2.0
    u = 1.0 / math.sqrt(2)
    top_left = (top_left[0] + diag_inset * u, top_left[1] + diag_inset * u)
    bottom_right = (bottom_right[0] - diag_inset * u, bottom_right[1] - diag_inset * u)
    vertices = [right_angle, top_left, bottom_right]
    path_d = f"M {right_angle[0]:.2f} {right_angle[1]:.2f} L {top_left[0]:.2f} {top_left[1]:.2f} L {bottom_right[0]:.2f} {bottom_right[1]:.2f} Z"
    return vertices, path_d


def _rectangle_geometry() -> tuple[list[tuple[float, float]], str]:
    """Horizontal, width = 1.6 * height. Centred; height 43.75, width 70 (15..85 x 28.125..71.875)."""
    vertices = [(15, 28.125), (85, 28.125), (85, 71.875), (15, 71.875)]
    path_d = "M 15 28.125 L 85 28.125 L 85 71.875 L 15 71.875 Z"
    return vertices, path_d


def _semicircle_geometry() -> tuple[list[tuple[float, float]], str]:
    """Semicircle vertically centred (guide §3.1): flat at bottom, arc on top. Circle centre (50, 67.5), radius SEMICIRCLE_RADIUS."""
    r = SEMICIRCLE_RADIUS
    cx, cy_flat = 50.0, 67.5
    path_d = f"M {50 - r:.2f} {cy_flat} A {r} {r} 0 0 1 {50 + r:.2f} {cy_flat} Z"
    # Vertices for partition (concentric etc.): top arc sampled (flat at bottom)
    n_arc = 24
    vertices: list[tuple[float, float]] = [(cx - r, cy_flat)]
    for k in range(1, n_arc):
        t = k / n_arc
        angle = math.pi + math.pi * t  # pi (left) to 2pi (right), arc on top
        vertices.append((cx + r * math.cos(angle), cy_flat + r * math.sin(angle)))
    vertices.append((cx + r, cy_flat))
    vertices.append((cx - r, cy_flat))
    return vertices, path_d


# Cross (plus) scaled to match square (15–85); corners brought in by double (inset 21 each side)
CROSS_OUTER_LO = 15.0
CROSS_OUTER_HI = 85.0
CROSS_INNER_LO = 36.0   # 15 + 21 (was 10.5, doubled)
CROSS_INNER_HI = 64.0   # 85 - 21
# Keep motif centres at least CELL_HALF from boundary so motifs do not overlap the cross edge (arms are 21 deep so max 5 motifs: 1 center + 4 arms).
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


# ----- Symbol containers (guide §3.1): load from shape-{symbol}.svg, same outlines as motifs -----

def _path_d_tokenize(path_d: str) -> list[tuple[str, list[float]]]:
    """Parse SVG path d into list of (command, numbers). Handles M,L,H,V,C,Q,A,Z and repeated implicit commands."""
    tokens: list[tuple[str, list[float]]] = []
    rest = re.sub(r",", " ", path_d.strip())
    pos = 0
    while pos < len(rest):
        while pos < len(rest) and rest[pos] in " \t\n":
            pos += 1
        if pos >= len(rest):
            break
        if rest[pos] in "MLHVCSQTAZmlhvcsqtaz":
            cmd = rest[pos].upper()
            pos += 1
            nums: list[float] = []
            while pos < len(rest):
                while pos < len(rest) and rest[pos] in " \t\n":
                    pos += 1
                if pos >= len(rest) or rest[pos] in "MLHVCSQTAZmlhvcsqtaz":
                    break
                m = re.match(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", rest[pos:])
                if m:
                    nums.append(float(m.group(0)))
                    pos += m.end()
                else:
                    break
            tokens.append((cmd, nums))
            continue
        pos += 1
    return tokens


def _arc_endpoint_to_center(
    x1: float, y1: float, x2: float, y2: float,
    rx: float, ry: float, phi_deg: float, fa: int, fs: int,
) -> tuple[float, float, float, float, float, float, float] | None:
    """Convert SVG arc (endpoint parameterization) to center parameterization.
    Returns (cx, cy, theta1_rad, delta_theta_rad, rx, ry, phi_rad) or None if arc is degenerate (treat as line).
    W3C SVG impl note B.2.4 and B.2.5."""
    rx = abs(rx)
    ry = abs(ry)
    if rx == 0 or ry == 0:
        return None
    phi = math.radians(phi_deg)
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)
    # Step 1: (x1', y1') = R(-phi) * ((x1-x2)/2, (y1-y2)/2)
    mid_dx = (x1 - x2) * 0.5
    mid_dy = (y1 - y2) * 0.5
    x1p = cos_phi * mid_dx + sin_phi * mid_dy
    y1p = -sin_phi * mid_dx + cos_phi * mid_dy
    # Step 2 (B.2.5): ensure radii large enough
    lambda_ = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lambda_ > 1:
        scale = math.sqrt(lambda_)
        rx *= scale
        ry *= scale
    # Step 2: (cx', cy')
    denom = (rx * rx * y1p * y1p) + (ry * ry * x1p * x1p)
    if denom == 0:
        return None
    radicand = (rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p) / denom
    radicand = max(0.0, radicand)
    k = math.sqrt(radicand)
    sign = 1.0 if fa != fs else -1.0
    cxp = sign * k * (rx * y1p / ry)
    cyp = sign * k * (-ry * x1p / rx)
    # Step 3: (cx, cy)
    mid_x = (x1 + x2) * 0.5
    mid_y = (y1 + y2) * 0.5
    cx = cos_phi * cxp - sin_phi * cyp + mid_x
    cy = sin_phi * cxp + cos_phi * cyp + mid_y
    # Step 4: theta1 and delta_theta (in radians)
    theta1 = math.atan2((y1p - cyp) / ry, (x1p - cxp) / rx)
    x2p = -x1p
    y2p = -y1p
    theta2 = math.atan2((y2p - cyp) / ry, (x2p - cxp) / rx)
    delta_theta = theta2 - theta1
    if fs == 0 and delta_theta > 0:
        delta_theta -= 2 * math.pi
    if fs == 1 and delta_theta < 0:
        delta_theta += 2 * math.pi
    return (cx, cy, theta1, delta_theta, rx, ry, phi)


def _sample_path_to_points(path_d: str, n_cubic: int = 4, n_quad: int = 3, n_arc: int = 8) -> list[tuple[float, float]]:
    """Sample SVG path d to a polygon (list of points). Used for symbol containers (inside_check and flattened path)."""
    tokens = _path_d_tokenize(path_d)
    points: list[tuple[float, float]] = []
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    i = 0
    while i < len(tokens):
        cmd, nums = tokens[i]
        if cmd == "M":
            j = 0
            while j + 2 <= len(nums):
                cur = (nums[j], nums[j + 1])
                if j == 0:
                    start = cur
                    points.append(cur)
                else:
                    points.append(cur)
                j += 2
            i += 1
        elif cmd == "L":
            j = 0
            while j + 2 <= len(nums):
                cur = (nums[j], nums[j + 1])
                points.append(cur)
                j += 2
            i += 1
        elif cmd == "H":
            for x in nums:
                cur = (x, cur[1])
                points.append(cur)
            i += 1
        elif cmd == "V":
            for y in nums:
                cur = (cur[0], y)
                points.append(cur)
            i += 1
        elif cmd == "C":
            j = 0
            while j + 6 <= len(nums):
                x1, y1, x2, y2, x3, y3 = nums[j], nums[j + 1], nums[j + 2], nums[j + 3], nums[j + 4], nums[j + 5]
                for k in range(1, n_cubic + 1):
                    t = k / n_cubic
                    u = 1 - t
                    x = u * u * u * cur[0] + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x3
                    y = u * u * u * cur[1] + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y3
                    points.append((x, y))
                cur = (x3, y3)
                j += 6
            i += 1
        elif cmd == "Q":
            j = 0
            while j + 4 <= len(nums):
                x1, y1, x2, y2 = nums[j], nums[j + 1], nums[j + 2], nums[j + 3]
                for k in range(1, n_quad + 1):
                    t = k / n_quad
                    u = 1 - t
                    x = u * u * cur[0] + 2 * u * t * x1 + t * t * x2
                    y = u * u * cur[1] + 2 * u * t * y1 + t * t * y2
                    points.append((x, y))
                cur = (x2, y2)
                j += 4
            i += 1
        elif cmd == "A":
            # Arc: (rx, ry, x-axis-rotation, large-arc-flag, sweep-flag, x, y). Sample points along arc so clip path follows rounded ends.
            j = 0
            while j + 7 <= len(nums):
                rx, ry, phi_deg, fa, fs = nums[j], nums[j + 1], nums[j + 2], int(nums[j + 3]), int(nums[j + 4])
                x2, y2 = nums[j + 5], nums[j + 6]
                x1, y1 = cur[0], cur[1]
                conv = _arc_endpoint_to_center(x1, y1, x2, y2, rx, ry, phi_deg, fa, fs)
                if conv is None:
                    cur = (x2, y2)
                    points.append(cur)
                else:
                    cx, cy, theta1, delta_theta, rx_f, ry_f, phi = conv
                    cos_phi = math.cos(phi)
                    sin_phi = math.sin(phi)
                    for k in range(1, n_arc + 1):
                        t = k / n_arc
                        theta = theta1 + t * delta_theta
                        px = rx_f * math.cos(theta) * cos_phi - ry_f * math.sin(theta) * sin_phi + cx
                        py = rx_f * math.cos(theta) * sin_phi + ry_f * math.sin(theta) * cos_phi + cy
                        points.append((px, py))
                    cur = (x2, y2)
                j += 7
            i += 1
        elif cmd == "Z":
            cur = start
            points.append(cur)
            i += 1
        else:
            i += 1
    return points


def _apply_rotate_to_points(points: list[tuple[float, float]], angle_deg: float, cx: float, cy: float) -> list[tuple[float, float]]:
    """Rotate points about (cx, cy) by angle_deg (degrees counterclockwise)."""
    a = math.radians(angle_deg)
    cos_a = math.cos(a)
    sin_a = math.sin(a)
    out: list[tuple[float, float]] = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        out.append((cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a))
    return out


def _scale_path_d(path_d: str, cx: float, cy: float, scale: float) -> str:
    """Return path d with all coordinates scaled about (cx, cy). Used for symbol concentric rings (small copies from template)."""
    def scale_pt(x: float, y: float) -> tuple[float, float]:
        return (cx + (x - cx) * scale, cy + (y - cy) * scale)

    tokens = _path_d_tokenize(path_d)
    out: list[str] = []
    cur = (0.0, 0.0)
    cur_orig = (0.0, 0.0)  # current point in original (unscaled) space, for H/V
    start = (0.0, 0.0)
    for cmd, nums in tokens:
        if cmd == "M":
            j = 0
            while j + 2 <= len(nums):
                cur_orig = (nums[j], nums[j + 1])
                cur = scale_pt(cur_orig[0], cur_orig[1])
                if j == 0:
                    start = cur
                    out.append(f"M {cur[0]:.2f} {cur[1]:.2f}")
                else:
                    out.append(f"L {cur[0]:.2f} {cur[1]:.2f}")
                j += 2
        elif cmd == "L":
            j = 0
            while j + 2 <= len(nums):
                cur_orig = (nums[j], nums[j + 1])
                cur = scale_pt(cur_orig[0], cur_orig[1])
                out.append(f"L {cur[0]:.2f} {cur[1]:.2f}")
                j += 2
        elif cmd == "H":
            for x in nums:
                cur_orig = (x, cur_orig[1])
                cur = scale_pt(cur_orig[0], cur_orig[1])
                out.append(f"L {cur[0]:.2f} {cur[1]:.2f}")
        elif cmd == "V":
            for y in nums:
                cur_orig = (cur_orig[0], y)
                cur = scale_pt(cur_orig[0], cur_orig[1])
                out.append(f"L {cur[0]:.2f} {cur[1]:.2f}")
        elif cmd == "C":
            j = 0
            while j + 6 <= len(nums):
                p1 = scale_pt(nums[j], nums[j + 1])
                p2 = scale_pt(nums[j + 2], nums[j + 3])
                cur_orig = (nums[j + 4], nums[j + 5])
                cur = scale_pt(cur_orig[0], cur_orig[1])
                out.append(f"C {p1[0]:.2f} {p1[1]:.2f} {p2[0]:.2f} {p2[1]:.2f} {cur[0]:.2f} {cur[1]:.2f}")
                j += 6
        elif cmd == "Q":
            j = 0
            while j + 4 <= len(nums):
                p1 = scale_pt(nums[j], nums[j + 1])
                cur_orig = (nums[j + 2], nums[j + 3])
                cur = scale_pt(cur_orig[0], cur_orig[1])
                out.append(f"Q {p1[0]:.2f} {p1[1]:.2f} {cur[0]:.2f} {cur[1]:.2f}")
                j += 4
        elif cmd == "A":
            j = 0
            while j + 7 <= len(nums):
                rx, ry = nums[j] * scale, nums[j + 1] * scale
                xar, la, sw = nums[j + 2], nums[j + 3], nums[j + 4]
                cur_orig = (nums[j + 5], nums[j + 6])
                cur = scale_pt(cur_orig[0], cur_orig[1])
                out.append(f"A {rx:.2f} {ry:.2f} {xar:.2f} {int(la)} {int(sw)} {cur[0]:.2f} {cur[1]:.2f}")
                j += 7
        elif cmd == "Z":
            cur = start
            out.append("Z")
    return " ".join(out)


def _rotate_path_d(path_d: str, angle_deg: float, cx: float, cy: float) -> str:
    """Return path d with all coordinates rotated about (cx, cy) by angle_deg (degrees CCW). For symbol transform (e.g. times = plus rotated 45°)."""
    a = math.radians(angle_deg)
    cos_a = math.cos(a)
    sin_a = math.sin(a)

    def rot_pt(x: float, y: float) -> tuple[float, float]:
        dx, dy = x - cx, y - cy
        return (cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a)

    tokens = _path_d_tokenize(path_d)
    out: list[str] = []
    cur = (0.0, 0.0)
    cur_orig = (0.0, 0.0)  # current point in original (unrotated) space, for H/V
    start = (0.0, 0.0)
    for cmd, nums in tokens:
        if cmd == "M":
            j = 0
            while j + 2 <= len(nums):
                cur_orig = (nums[j], nums[j + 1])
                cur = rot_pt(cur_orig[0], cur_orig[1])
                if j == 0:
                    start = cur
                    out.append(f"M {cur[0]:.2f} {cur[1]:.2f}")
                else:
                    out.append(f"L {cur[0]:.2f} {cur[1]:.2f}")
                j += 2
        elif cmd == "L":
            j = 0
            while j + 2 <= len(nums):
                cur_orig = (nums[j], nums[j + 1])
                cur = rot_pt(cur_orig[0], cur_orig[1])
                out.append(f"L {cur[0]:.2f} {cur[1]:.2f}")
                j += 2
        elif cmd == "H":
            for x in nums:
                cur_orig = (x, cur_orig[1])
                cur = rot_pt(cur_orig[0], cur_orig[1])
                out.append(f"L {cur[0]:.2f} {cur[1]:.2f}")
        elif cmd == "V":
            for y in nums:
                cur_orig = (cur_orig[0], y)
                cur = rot_pt(cur_orig[0], cur_orig[1])
                out.append(f"L {cur[0]:.2f} {cur[1]:.2f}")
        elif cmd == "C":
            j = 0
            while j + 6 <= len(nums):
                p1 = rot_pt(nums[j], nums[j + 1])
                p2 = rot_pt(nums[j + 2], nums[j + 3])
                cur_orig = (nums[j + 4], nums[j + 5])
                cur = rot_pt(cur_orig[0], cur_orig[1])
                out.append(f"C {p1[0]:.2f} {p1[1]:.2f} {p2[0]:.2f} {p2[1]:.2f} {cur[0]:.2f} {cur[1]:.2f}")
                j += 6
        elif cmd == "Q":
            j = 0
            while j + 4 <= len(nums):
                p1 = rot_pt(nums[j], nums[j + 1])
                cur_orig = (nums[j + 2], nums[j + 3])
                cur = rot_pt(cur_orig[0], cur_orig[1])
                out.append(f"Q {p1[0]:.2f} {p1[1]:.2f} {cur[0]:.2f} {cur[1]:.2f}")
                j += 4
        elif cmd == "A":
            j = 0
            while j + 7 <= len(nums):
                rx, ry, xar, la, sw = nums[j], nums[j + 1], nums[j + 2], nums[j + 3], nums[j + 4]
                cur_orig = (nums[j + 5], nums[j + 6])
                cur = rot_pt(cur_orig[0], cur_orig[1])
                # Ellipse rotation angle changes when path is rotated
                xar_new = xar + angle_deg
                out.append(f"A {rx:.2f} {ry:.2f} {xar_new:.2f} {int(la)} {int(sw)} {cur[0]:.2f} {cur[1]:.2f}")
                j += 7
        elif cmd == "Z":
            cur = start
            out.append("Z")
    return " ".join(out)


def _points_to_path_d(points: list[tuple[float, float]]) -> str:
    """Flatten polygon to path M x0 y0 L x1 y1 ... Z."""
    if not points:
        return ""
    parts = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    for x, y in points[1:]:
        parts.append(f"L {x:.2f} {y:.2f}")
    parts.append("Z")
    return " ".join(parts)


def _serialize_path_el(path_el: ET.Element) -> str:
    """Serialize path element to XML string with local tag (no namespace) for embedding."""
    def escape_attr(v: str) -> str:
        return v.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    attrs = " ".join(f'{k}="{escape_attr(v)}"' for k, v in path_el.attrib.items())
    return f"<path {attrs}/>" if attrs else "<path/>"


def _load_symbol_svg(motifs_dir: Path, shape: str) -> tuple[str, str | None, str]:
    """Load shape-{shape}.svg; return (path_d, transform_attr or None, path_element_xml). path_element_xml is the template <path .../> for drawing/concentric. Handles <g transform="rotate(...)"><path/></g>."""
    path = motifs_dir / f"shape-{shape}.svg"
    if not path.exists():
        raise FileNotFoundError(f"Symbol shape SVG not found: {path}")
    tree = ET.parse(path)
    root = tree.getroot()
    path_el = None
    for el in root.iter():
        if el.tag.endswith("}path") or el.tag == "path":
            path_el = el
            break
    if path_el is None:
        raise ValueError(f"No path in {path}")
    path_d = path_el.get("d") or ""
    transform: str | None = None
    parent = next((n for n in root.iter() if path_el in list(n)), None)
    if parent is not None and parent != root:
        transform = parent.get("transform")
    path_element_xml = _serialize_path_el(path_el)
    return path_d, transform, path_element_xml


def _parse_rotate_transform(transform_attr: str | None) -> tuple[float, float, float] | None:
    """If transform is 'rotate(angle cx cy)' or 'rotate(angle, cx, cy)', return (angle, cx, cy). Else None."""
    if not transform_attr or "rotate" not in transform_attr:
        return None
    # Match rotate(angle cx cy) or rotate(angle, cx, cy)
    m = re.search(r"rotate\s*\(\s*([-\d.]+)\s*[, ]\s*([-\d.]+)\s*[, ]\s*([-\d.]+)\s*\)", transform_attr, re.IGNORECASE)
    if not m:
        return None
    angle = float(m.group(1))
    cx = float(m.group(2))
    cy = float(m.group(3))
    return (angle, cx, cy)


def _scale_points_about_bbox_center(points: list[tuple[float, float]], inset_per_side: float) -> list[tuple[float, float]]:
    """Scale points about bbox center so bbox is inset by inset_per_side on each side (2 units = 4 total per dimension)."""
    if not points or inset_per_side <= 0:
        return points
    x_min = min(p[0] for p in points)
    x_max = max(p[0] for p in points)
    y_min = min(p[1] for p in points)
    y_max = max(p[1] for p in points)
    cx = (x_min + x_max) / 2
    cy = (y_min + y_max) / 2
    w = x_max - x_min
    h = y_max - y_min
    if w < 1e-9 or h < 1e-9:
        return points
    sx = (w - 2 * inset_per_side) / w
    sy = (h - 2 * inset_per_side) / h
    return [(cx + (p[0] - cx) * sx, cy + (p[1] - cy) * sy) for p in points]


def _symbol_geometry(shape: str, motifs_dir: Path) -> tuple[list[tuple[float, float]], str, str | None, str]:
    """Load symbol from shape-{shape}.svg; return (vertices, path_d, symbol_transform, path_element_xml). path_element_xml is the template <path .../> for drawing. vertices from sampling used only for bbox (and motif inside_check); never for displayed geometry."""
    path_d, transform_attr, path_element_xml = _load_symbol_svg(motifs_dir, shape)
    points = _sample_path_to_points(path_d)
    if not points:
        raise ValueError(f"Symbol {shape!r}: path produced no points")
    rot = _parse_rotate_transform(transform_attr)
    if rot is not None:
        angle, cx, cy = rot
        points = _apply_rotate_to_points(points, angle, cx, cy)
    return points, path_d, transform_attr, path_element_xml


def get_shape_geometry(shape: str, motifs_dir: Path | None = None) -> tuple[list[tuple[float, float]], str, str | None, list[tuple[float, float, float, float]] | None, str | None, str | None]:
    """
    Return (vertices, path_d, path_d_stroke, stroke_lines, symbol_transform, symbol_path_element) for the shape.
    For cross: path_d_stroke is None, stroke_lines is 12 (x1,y1,x2,y2) segments. Otherwise stroke_lines is None.
    For symbol containers, symbol_transform is the parent <g> transform from the SVG when present; symbol_path_element is the template <path .../> from the file for concentric/drawing.
    For symbol containers (plus, times, club, heart, diamond, spade, star), motifs_dir is required to load shape-{symbol}.svg.
    """
    shape = (shape or "").strip().lower()
    if shape in SHAPES_SYMBOLS:
        if motifs_dir is None:
            script_dir = Path(__file__).resolve().parent
            _repo_root = script_dir.parent.parent if script_dir.name == "lib" else script_dir.parent
            motifs_dir = _repo_root / "nvr-symbols"
        vertices, path_d, symbol_transform, symbol_path_element = _symbol_geometry(shape, motifs_dir)
        return vertices, path_d, None, None, symbol_transform, symbol_path_element
    if shape == "right_angled_triangle":
        v, p = _right_angled_triangle_geometry()
        return v, p, None, None, None, None
    if shape == "rectangle":
        v, p = _rectangle_geometry()
        return v, p, None, None, None, None
    if shape == "semicircle":
        v, p = _semicircle_geometry()
        return v, p, None, None, None, None
    if shape == "cross":
        v, p_fill, _p_stroke, stroke_lines = _cross_geometry()
        return v, p_fill, None, stroke_lines, None, None
    if shape == "arrow":
        v, p = _arrow_geometry()
        return v, p, None, None, None, None
    if shape == "square":
        # Tightened 2 units per side (17–83 instead of 15–85)
        vertices = [(17, 17), (83, 17), (83, 83), (17, 83)]
        path_d = "M17 17 L83 17 L83 83 L17 83 Z"
        return vertices, path_d, None, None, None, None
    if shape == "circle":
        r = CIRCLE_RADIUS
        path_d = f"M 50 {50 - r} A {r} {r} 0 0 1 50 {50 + r} A {r} {r} 0 0 1 50 {50 - r} Z"
        return [], path_d, None, None, None, None
    sides = {"triangle": 3, "pentagon": 5, "hexagon": 6, "heptagon": 7, "octagon": 8}.get(shape)
    if sides is None:
        raise ValueError(f"Unknown shape: {shape!r}. Supported: {SHAPES_ALL}")
    radius = POLYGON_RADIUS.get(shape, DEFAULT_POLYGON_RADIUS)
    poly_cy = POLYGON_CY.get(shape, DEFAULT_POLYGON_CY)
    phase = POLYGON_PHASE.get(shape, 0)
    vertices = regular_polygon_vertices(sides, 50, poly_cy, radius, phase)
    path_d = regular_polygon_path(sides, 50, poly_cy, radius, phase)
    return vertices, path_d, None, None, None, None


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


def _clip_polygon_to_polygon(
    subject: list[tuple[float, float]],
    clip_vertices: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """Clip subject polygon to the interior of clip_vertices (Sutherland–Hodgman). Assumes clip_vertices in path order with interior to the left when traversing (SVG convention)."""
    if not clip_vertices or len(clip_vertices) < 3:
        return subject[:]
    out = subject
    n = len(clip_vertices)
    for i in range(n):
        e0 = clip_vertices[i]
        e1 = clip_vertices[(i + 1) % n]
        ex, ey = e1[0] - e0[0], e1[1] - e0[1]
        # Interior to the left of edge e0->e1 in SVG (y down): (p - e0) · (ey, -ex) >= 0
        def inside(px: float, py: float) -> bool:
            return ex * (e0[1] - py) + ey * (px - e0[0]) >= -1e-9

        def intersect_seg_line(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
            ax, ay, bx, by = a[0], a[1], b[0], b[1]
            denom = (bx - ax) * ey - (by - ay) * ex
            if abs(denom) < 1e-12:
                return (ax + bx) / 2, (ay + by) / 2
            t = ((e0[0] - ax) * ey - (e0[1] - ay) * ex) / denom
            t = max(0.0, min(1.0, t))
            return (ax + t * (bx - ax), ay + t * (by - ay))

        out = _clip_polygon_half_plane(out, inside, intersect_seg_line)
        if not out:
            return []
    return out


def _polygon_signed_area(vertices: list[tuple[float, float]]) -> float:
    """Signed area (shoelace). Positive = counterclockwise in viewBox (y down)."""
    if len(vertices) < 3:
        return 0.0
    n = len(vertices)
    return 0.5 * sum(
        vertices[i][0] * vertices[(i + 1) % n][1] - vertices[(i + 1) % n][0] * vertices[i][1]
        for i in range(n)
    )


def _ensure_ccw(vertices: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Return vertices in counterclockwise order (new list). Required for _clip_segment_to_polygon and consistent band clipping."""
    if len(vertices) < 3:
        return list(vertices)
    if _polygon_signed_area(vertices) >= 0:
        return list(vertices)
    return list(reversed(vertices))


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
    """Area centroid (center of mass) of polygon; vertices counterclockwise. Falls back to vertex average if area ~0."""
    n = len(vertices)
    if n == 0:
        return (50.0, 50.0)
    if n < 3:
        return (
            (vertices[0][0] + vertices[1][0]) / 2,
            (vertices[0][1] + vertices[1][1]) / 2,
        )
    # Shoelace: A = (1/2)*sum(x_i*y_{i+1} - x_{i+1}*y_i), Cx = (1/(6A))*sum((x_i+x_{i+1})*(x_i*y_{i+1}-x_{i+1}*y_i))
    area = 0.0
    cx_sum = 0.0
    cy_sum = 0.0
    for i in range(n):
        j = (i + 1) % n
        xi, yi = vertices[i][0], vertices[i][1]
        xj, yj = vertices[j][0], vertices[j][1]
        cross = xi * yj - xj * yi
        area += cross
        cx_sum += (xi + xj) * cross
        cy_sum += (yi + yj) * cross
    area *= 0.5
    if abs(area) < 1e-12:
        return (
            sum(v[0] for v in vertices) / n,
            sum(v[1] for v in vertices) / n,
        )
    inv_6a = 1.0 / (6.0 * area)
    return (cx_sum * inv_6a, cy_sum * inv_6a)


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


def _quadrant_rect(cx: float, cy: float, quadrant: int) -> list[tuple[float, float]]:
    """Full viewBox quadrant rectangle (0–100) for quadrant i. 0=top-left, 1=top-right, 2=bottom-right, 3=bottom-left. Use with shape clip so shading reaches boundary."""
    if quadrant == 0:
        return [(0, 0), (cx, 0), (cx, cy), (0, cy)]
    if quadrant == 1:
        return [(cx, 0), (100, 0), (100, cy), (cx, cy)]
    if quadrant == 2:
        return [(cx, cy), (100, cy), (100, 100), (cx, 100)]
    # quadrant == 3
    return [(0, cy), (cx, cy), (cx, 100), (0, 100)]


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
    symbol_transform: str | None = None,
    symbol_path_element: str | None = None,
) -> tuple[str, str, list[tuple[float, float, float, float]], list[str]]:
    """Build defs, fill group XML, partition separator lines (x1,y1,x2,y2), and partition separator paths (path d). Guide §3.9. For symbol concentric, internal boundaries use the scaled shape path (not polygon approximation)."""
    x_min, x_max, y_min, y_max = bbox
    cx_bbox = (x_min + x_max) / 2.0
    cy_bbox = (y_min + y_max) / 2.0
    # Normalize to CCW so _clip_segment_to_polygon (and band clipping) treats interior correctly; symbol paths are often clockwise.
    if vertices and len(vertices) >= 3:
        vertices = _ensure_ccw(vertices)
    solid = {"solid_black": "#000", "grey": "#808080", "grey_light": "#d0d0d0", "white": "none", "white_fill": "#fff"}
    hatch_keys = ("diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines")
    # ClipPath: use path in viewBox space. Sampling/vertices are never used for display (bbox only).
    rot = _parse_rotate_transform(symbol_transform) if symbol_transform else None
    if rot is not None:
        angle, rcx, rcy = rot
        display_path_d = _rotate_path_d(path_d, angle, rcx, rcy)
        path_el = f'<path d="{display_path_d}"/>'
    elif symbol_path_element:
        path_el = symbol_path_element
    else:
        path_el = f'<path d="{path_d}"/>'
    if rot is None and symbol_transform:
        path_el = f'<g transform="{symbol_transform}">{path_el}</g>'
    defs_parts: list[str] = [f'  <defs><clipPath id="{shape_clip_id}">{path_el}</clipPath></defs>']
    fill_parts: list[str] = []
    partition_lines: list[tuple[float, float, float, float]] = []
    partition_paths: list[str] = []

    for i, (lo, hi) in enumerate(section_bounds):
        fill_key = section_fills[i % len(section_fills)]
        if partition_direction == "horizontal":
            y_lo = y_min + (y_max - y_min) * lo / 100.0
            y_hi = y_min + (y_max - y_min) * hi / 100.0
            if i + 1 < len(section_bounds):
                if vertices and len(vertices) >= 3:
                    partition_lines.append((x_min, y_hi, x_max, y_hi))
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
                h = y_hi - y_lo
                section_path = f"M 0 {y_lo:.2f} h 100 v {h:.2f} h -100 Z"
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
                    partition_lines.append((x_hi, y_min, x_hi, y_max))
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
                section_path = f"M {x_lo:.2f} 0 v 100 h {w:.2f} v -100 Z"
                fill_parts.append(
                    f'  <g clip-path="url(#{shape_clip_id})">'
                    f'<rect x="{x_lo:.2f}" y="0" width="{w:.2f}" height="100" fill="{solid.get(fill_key, "none")}" stroke="none"/>'
                    "</g>"
                )
        elif partition_direction == "diagonal_slash":
            sum_lo = (x_min + y_min) + ((x_max + y_max) - (x_min + y_min)) * lo / 100.0
            sum_hi = (x_min + y_min) + ((x_max + y_max) - (x_min + y_min)) * hi / 100.0
            if i + 1 < len(section_bounds):
                px1 = max(x_min, min(x_max, sum_hi - y_max))
                py1 = sum_hi - px1
                px2 = min(x_max, max(x_min, sum_hi - y_min))
                py2 = sum_hi - px2
                if abs(px2 - px1) + abs(py2 - py1) > 0.1:
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
            diff_min = x_max - y_min
            diff_max = x_min - y_max
            diff_lo = diff_min + (diff_max - diff_min) * lo / 100.0
            diff_hi = diff_min + (diff_max - diff_min) * hi / 100.0
            if i + 1 < len(section_bounds):
                px1 = max(x_min, min(x_max, diff_hi + y_min))
                py1 = px1 - diff_hi
                px2 = max(x_min, min(x_max, diff_hi + y_max))
                py2 = px2 - diff_hi
                if abs(px2 - px1) + abs(py2 - py1) > 0.1:
                    partition_lines.append((px1, py1, px2, py2))
            if vertices and len(vertices) >= 3:
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
                n_pts = 32
                for k in range(n_pts):
                    t0 = 2 * math.pi * k / n_pts
                    t1 = 2 * math.pi * (k + 1) / n_pts
                    seg = (cx + r_hi * math.cos(t0), cy + r_hi * math.sin(t0), cx + r_hi * math.cos(t1), cy + r_hi * math.sin(t1))
                    partition_lines.append(seg)
            if r_lo < 1e-6:
                section_path = f"M {cx} {cy - r_hi} A {r_hi} {r_hi} 0 0 1 {cx} {cy + r_hi} A {r_hi} {r_hi} 0 0 1 {cx} {cy - r_hi} Z"
            else:
                section_path = _circle_annulus_path(cx, cy, r_hi, r_lo)
            if fill_key in solid:
                fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none" fill-rule="evenodd"/>')
            else:
                cid = f"{shape_clip_id}_sec{i}"
                clip_rule = ' clip-rule="evenodd"' if r_lo >= 1e-6 else ""
                defs_parts.append(f'  <defs><clipPath id="{cid}"{clip_rule}><path d="{section_path}"/></clipPath></defs>')
                _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                fill_parts.append(hatch_el)
        elif partition_direction == "radial":
            num_sections = len(section_bounds)
            if shape == "circle":
                cx, cy, r = 50.0, 50.0, CIRCLE_RADIUS
                angle_north = -math.pi / 2
                angle_i = angle_north + i * 2 * math.pi / num_sections
                angle_i1 = angle_north + (i + 1) * 2 * math.pi / num_sections
                if i + 1 < num_sections:
                    x1 = cx + r * math.cos(angle_i1)
                    y1 = cy + r * math.sin(angle_i1)
                    partition_lines.append((cx, cy, x1, y1))
                elif i == num_sections - 1:
                    partition_lines.append((cx, cy, cx + r * math.cos(angle_north), cy + r * math.sin(angle_north)))
                section_path = _circle_wedge_path(cx, cy, r, angle_i, angle_i1)
                if fill_key in solid:
                    fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                else:
                    cid = f"{shape_clip_id}_sec{i}"
                    defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                    _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                    fill_parts.append(hatch_el)
            elif shape == "semicircle":
                cx, cy = 50.0, 67.5
                r = SEMICIRCLE_RADIUS
                angle_start = math.pi
                angle_i = angle_start + i * math.pi / num_sections
                angle_i1 = angle_start + (i + 1) * math.pi / num_sections
                if i + 1 < num_sections:
                    x1 = cx + r * math.cos(angle_i1)
                    y1 = cy + r * math.sin(angle_i1)
                    partition_lines.append((cx, cy, x1, y1))
                elif i == num_sections - 1:
                    partition_lines.append((cx, cy, cx + r * math.cos(angle_start), cy + r * math.sin(angle_start)))
                section_path = _circle_wedge_path(cx, cy, r, angle_i, angle_i1)
                if fill_key in solid:
                    fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                else:
                    cid = f"{shape_clip_id}_sec{i}"
                    defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                    _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                    fill_parts.append(hatch_el)
            elif shape == "star" and num_sections == 5 and vertices and len(vertices) >= 3:
                cx, cy = _polygon_centroid(vertices)
                r = max(math.hypot(v[0] - cx, v[1] - cy) for v in vertices)
                angle_north = -math.pi / 2
                angle_i = angle_north + i * 2 * math.pi / 5
                angle_i1 = angle_north + (i + 1) * 2 * math.pi / 5
                if i + 1 < 5:
                    x1 = cx + r * math.cos(angle_i1)
                    y1 = cy + r * math.sin(angle_i1)
                    partition_lines.append((cx, cy, x1, y1))
                elif i == 4:
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
                if shape in ("triangle", "square", "pentagon", "hexagon", "heptagon", "octagon") and sides % num_sections == 0:
                    step = sides // num_sections
                    idx0 = (i * step) % sides
                    idx1 = (i * step + 1) % sides
                    v0, v1 = vertices[idx0], vertices[idx1]
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
                    if num_sections != 4:
                        raise ValueError("Radial partition for irregular shape requires exactly 4 sections.")
                    if i == 0:
                        partition_lines.append((cx, 0, cx, 100))
                        partition_lines.append((0, cy, 100, cy))
                    if i == 1:
                        partition_lines.append((0, cy, 100, cy))
                    if i == 2:
                        partition_lines.append((cx, 0, cx, 100))
                    quad_verts = _quadrant_rect(cx, cy, i)
                    section_path = _polygon_path_d(quad_verts)
                    if fill_key in solid:
                        fill_parts.append(f'  <path d="{section_path}" fill="{solid[fill_key]}" stroke="none"/>')
                    else:
                        cid = f"{shape_clip_id}_sec{i}"
                        defs_parts.append(f'  <defs><clipPath id="{cid}"><path d="{section_path}"/></clipPath></defs>')
                        _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                        fill_parts.append(hatch_el)
            else:
                raise ValueError("Segmented partition requires circle or polygon shape.")
        elif partition_direction == "concentric" and shape in SHAPES_SYMBOLS:
            scale_cx, scale_cy = cx_bbox, cy_bbox
            scale_lo = lo / 100.0
            scale_hi = hi / 100.0
            rot = _parse_rotate_transform(symbol_transform)
            display_path_d = _rotate_path_d(path_d, rot[0], rot[1], rot[2]) if rot else path_d
            outer_d = _scale_path_d(display_path_d, scale_cx, scale_cy, scale_hi)
            inner_d = _scale_path_d(display_path_d, scale_cx, scale_cy, scale_lo)
            def esc(s: str) -> str:
                return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
            outer_el = f'<path d="{esc(outer_d)}"/>'
            inner_el = f'<path d="{esc(inner_d)}"/>'
            # Internal boundary: use scaled shape path (same as fill), not polygon approximation.
            if i + 1 < len(section_bounds):
                partition_paths.append(outer_d)
            cid = f"{shape_clip_id}_sec{i}"
            if scale_lo < 1e-6:
                defs_parts.append(f'  <defs><clipPath id="{cid}">{outer_el}</clipPath></defs>')
            else:
                clip_rule = ' clip-rule="evenodd"'
                defs_parts.append(
                    f'  <defs><clipPath id="{cid}"{clip_rule}>{outer_el}{inner_el}</clipPath></defs>'
                )
            section_path_d = outer_d if scale_lo < 1e-6 else (outer_d + " " + inner_d)
            fill_color = "#fff" if (fill_key == "white" and scale_lo < 1e-6) else solid.get(fill_key, "none")
            fill_el = (
                f'  <rect x="0" y="0" width="100" height="100" fill="{fill_color}" stroke="none" clip-path="url(#{cid})"/>'
                if fill_key in solid
                else hatch_continuous_defs_and_lines(cid, fill_key, "")[1]
            )
            fill_parts.insert(0, fill_el)
        elif partition_direction == "concentric" and vertices and len(vertices) >= 3:
            cx, cy = _polygon_centroid(vertices)
            scale_lo = lo / 100.0
            scale_hi = hi / 100.0
            if i + 1 < len(section_bounds):
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
                clip_rule = ' clip-rule="evenodd"' if scale_lo >= 1e-6 else ""
                defs_parts.append(f'  <defs><clipPath id="{cid}"{clip_rule}><path d="{section_path}"/></clipPath></defs>')
                _, hatch_el = hatch_continuous_defs_and_lines(cid, fill_key, section_path)
                fill_parts.append(hatch_el)

    return ("\n".join(defs_parts), "\n".join(fill_parts), partition_lines, partition_paths)


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
    motif_content: str,
    positions: list[tuple[float, float]],
    motif_name: str,
    shape: str,
    path_d: str,
    motif_scale: float,
    motif_tx: float,
    motif_ty: float,
    line_style: str = "solid",
    polygon_fill: str = "none",
    polygon_fill_defs: str | None = None,
    polygon_hatch_lines: str | None = None,
    path_d_stroke: str | None = None,
    stroke_lines: list[tuple[float, float, float, float]] | None = None,
    partition_defs: str | None = None,
    partition_fill_content: str | None = None,
    partition_lines: list[tuple[float, float, float, float]] | None = None,
    partition_paths: list[str] | None = None,
    motif_fill: str = "#000",
    symbol_transform: str | None = None,
    shape_clip_id: str = "shapeClip",
) -> str:
    """Build shape-container SVG. For cross use stroke_lines (12 segments); else path_d_stroke or single path. symbol_transform wraps the shape path when present (e.g. times = plus rotated 45°). Partition (guide §3.9) optional; partition_paths are path d strings for curved separators (e.g. symbol concentric). Motifs are rendered with motif_fill (default black; guide §3.2 allows fill variation)."""
    stroke_dasharray = {"solid": "", "dashed": "8 4", "dotted": "2 4"}.get(line_style, "")
    dash_attr = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""
    is_cross = (shape or "").strip().lower() == "cross"
    fill_rule_attr = ' fill-rule="evenodd"' if is_cross else ""
    is_partitioned = partition_fill_content is not None

    def path_line(fill: str, stroke: str = "stroke-width=\"2\"") -> str:
        return f'  <path d="{path_d}" fill="{fill}" {stroke} {dash_attr}{fill_rule_attr} />'

    def wrap_shape(content: list[str]) -> list[str]:
        if symbol_transform:
            return [f'  <g transform="{symbol_transform}">'] + content + ["  </g>"]
        return content

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">',
        f"  <!-- {shape} container, {line_style}, fill; {len(positions)} {motif_name} motifs -->",
    ]
    if partition_defs:
        lines.append(partition_defs)
    elif polygon_fill_defs:
        lines.append(polygon_fill_defs)
    if partition_fill_content:
        if stroke_lines is not None:
            lines.extend(wrap_shape([path_line("none", "stroke=\"none\"")]) + [f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="2"{dash_attr} />' for x1, y1, x2, y2 in stroke_lines])
        else:
            lines.extend(wrap_shape([path_line("none")]))
        # Clip section fills to shape (e.g. star radial wedges extend as circle sectors; shapeClip clips them)
        lines.append(f'  <g clip-path="url(#{shape_clip_id})">')
        lines.append(partition_fill_content)
        lines.append("  </g>")
        # Draw shape outline again so the border is the usual thickness (not hidden by dark fills).
        if stroke_lines is not None:
            lines.extend([f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="2"{dash_attr} />' for x1, y1, x2, y2 in stroke_lines])
        else:
            lines.extend(wrap_shape([path_line("none")]))
        if partition_lines or partition_paths:
            lines.append(f'  <g clip-path="url(#{shape_clip_id})">')
            for x1, y1, x2, y2 in (partition_lines or []):
                lines.append(f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#000" stroke-width="{PARTITION_LINE_STROKE}" stroke-linecap="round"/>')
            for path_d in (partition_paths or []):
                esc = path_d.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
                lines.append(f'  <path d="{esc}" fill="none" stroke="#000" stroke-width="{PARTITION_LINE_STROKE}" stroke-linecap="round" stroke-linejoin="round"/>')
            lines.append("  </g>")
    elif polygon_hatch_lines:
        lines.append(polygon_hatch_lines)
    if not is_partitioned:
        if stroke_lines is not None:
            # Cross: fill path then 12 explicit lines so outline is never interpreted as a square
            lines.append(path_line(polygon_fill, "stroke=\"none\""))
            for x1, y1, x2, y2 in stroke_lines:
                lines.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="2"{dash_attr} />')
        elif path_d_stroke is not None:
            lines.append(path_line(polygon_fill, "stroke=\"none\""))
            lines.append(
                f'  <path d="{path_d_stroke}" fill="none" stroke-width="2" stroke-linejoin="miter" stroke-linecap="butt"{dash_attr} />'
            )
        else:
            lines.extend(wrap_shape([path_line(polygon_fill)]))
    # Motifs: fill and stroke per --motif-fill. White motifs = white fill, black outline; black motifs = black fill and stroke.
    motif_stroke = "#000" if motif_fill == "#fff" else motif_fill
    motif_fill_override = re.compile(r'\bfill="none"', re.IGNORECASE)
    for cx, cy in positions:
        lines.append(f'  <g transform="translate({cx:.2f}, {cy:.2f}) scale({motif_scale:.4f}) translate({motif_tx:.2f},{motif_ty:.2f})" fill="{motif_fill}" stroke="{motif_stroke}">')
        for line in motif_content.split("\n"):
            line = motif_fill_override.sub(f'fill="{motif_fill}"', line)
            lines.append("    " + line)
        lines.append("  </g>")
    lines.append("</svg>")
    return "\n".join(lines)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    # When run from lib/, nvr-symbols is at repo root.
    _repo_root = script_dir.parent.parent if script_dir.name == "lib" else script_dir.parent
    default_motifs_dir = _repo_root / "nvr-symbols"
    parser = argparse.ArgumentParser(
        description="Generate a shape-container SVG (optionally with motifs inside). Use --empty for container only."
    )
    parser.add_argument(
        "motif",
        type=str,
        nargs="?",
        default=None,
        help="Motif type (e.g. club, heart). Required unless --empty. Loads shape-{motif}.svg from --motifs-dir.",
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
        help="Number of motifs inside (default: 10). Ignored if --empty.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for motif placement.",
    )
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Output only the shape container (no motifs). For use as part of a larger drawing.",
    )
    parser.add_argument(
        "--motifs-dir",
        type=Path,
        default=default_motifs_dir,
        help="Directory containing motif SVGs (shape-{motif}.svg).",
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
            "solid_black", "grey", "grey_light", "white", "white_fill",
            "diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines",
        ],
        help="Shape fill / shading. white = none (unshaded); white_fill = solid #fff.",
    )
    parser.add_argument(
        "--motif-fill",
        type=str,
        default="black",
        choices=["black", "white"],
        help="Fill (and stroke) for motifs inside the shape. Default: black (guide §3.2). Use white for light-on-dark or asset checks.",
    )
    parser.add_argument(
        "--layout-symmetry",
        type=str,
        default=None,
        choices=["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"],
        metavar="LINE",
        help="Force motif layout symmetry about a line (guide §3.9). vertical (|), horizontal (-), diagonal_slash (/), diagonal_backslash (\\). Default: no symmetry.",
    )
    parser.add_argument(
        "--partition",
        type=str,
        default=None,
        choices=["horizontal", "vertical", "diagonal_slash", "diagonal_backslash", "concentric", "radial"],
        help="Partition the shape into sections (guide §3.9). radial = radial sections (wedges). No motifs when partitioned unless --partition-motifs is set.",
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
        help="Comma-separated fill keys per section (cycle if fewer than sections), e.g. white,grey,null,diagonal_slash. null = section not drawn (guide §3.9).",
    )
    args = parser.parse_args()
    args.shape = (args.shape or "square").strip().lower()

    if not args.empty and args.motif is None and not args.partition:
        raise SystemExit("Motif is required unless --empty or --partition.")

    vertices, path_d, path_d_stroke, stroke_lines, symbol_transform, symbol_path_element = get_shape_geometry(args.shape, args.motifs_dir)
    bbox = get_shape_bbox(args.shape, vertices, path_d)

    # Partition (guide §3.9): section bounds and fills
    if args.partition:
        if args.partition in ("diagonal_slash", "diagonal_backslash") and not (vertices and len(vertices) >= 3):
            raise SystemExit("Diagonal partition requires a polygon shape (not circle/semicircle).")
        if args.partition == "concentric" and args.shape == "circle" and not vertices:
            pass  # circle concentric uses circle-specific path
        elif args.partition == "concentric" and not (vertices and len(vertices) >= 3):
            raise SystemExit("Concentric partition requires circle or a polygon shape.")
        if args.partition == "radial":
            if not vertices and args.shape not in ("circle", "semicircle"):
                raise SystemExit("Radial partition requires circle or a polygon shape.")
        if args.partition_sections:
            parts = [float(p.strip()) for p in args.partition_sections.split(",")]
            if len(parts) < 2 or parts[0] != 0 or parts[-1] != 100:
                raise SystemExit("--partition-sections must be like 0,50,100 (start 0, end 100).")
            section_bounds = [(parts[i], parts[i + 1]) for i in range(len(parts) - 1)]
        else:
            section_bounds = even_section_bounds(4 if args.partition == "radial" else 2)
        if args.partition == "radial" and vertices and len(vertices) >= 3:
            num_radial = len(section_bounds)
            sides = len(vertices)
            if args.shape in ("triangle", "square", "pentagon", "hexagon", "heptagon", "octagon"):
                if sides % num_radial != 0:
                    raise SystemExit(
                        f"Radial partition: for regular polygon with {sides} sides, number of radial sections ({num_radial}) must divide {sides}."
                    )
            elif args.shape == "semicircle":
                pass  # any number of radial sections allowed
            elif args.shape == "star" and num_radial == 5:
                pass  # star has rotational symmetry order 5 (guide §3.9)
            elif num_radial != 4:
                raise SystemExit("Radial partition for irregular shape requires exactly 4 sections (0,25,50,75,100).")
        section_fills = (args.section_fills or "white,grey").replace(" ", "").split(",")
        try:
            partition_defs, partition_fill_content, partition_lines, partition_paths = build_partitioned_sections(
                args.shape, path_d, vertices, bbox, args.partition, section_bounds, section_fills,
                symbol_transform=symbol_transform,
                symbol_path_element=symbol_path_element,
            )
        except ValueError as e:
            raise SystemExit(str(e))
        polygon_fill = "none"
        polygon_fill_defs = None
        polygon_hatch_lines = None
        motif_content = ""
        motif_scale = 1.25
        motif_tx = motif_ty = -5.0
        motif_name = "none"
        positions = []
    else:
        partition_defs = None
        partition_fill_content = None
        partition_lines = None
        partition_paths = None

    solid_fills = {"solid_black": "#000", "grey": "#808080", "grey_light": "#d0d0d0", "white": "none", "white_fill": "#fff"}
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
            motif_content = ""
            motif_scale = 1.25
            motif_tx = motif_ty = -5.0
            motif_name = "none"
            positions = []
    else:
        motif_path = args.motifs_dir / f"shape-{args.motif}.svg"
        if not motif_path.exists():
            raise SystemExit(f"Motif file not found: {motif_path}")
        motif_content, motif_scale, motif_tx, motif_ty = load_motif_content(motif_path)
        motif_name = args.motif

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
            # Cross: sample only from the five rectangles so motifs never land in the missing corners
            sample_pt = _cross_sample_point if args.shape == "cross" else None
            cross_attempts = 8000 if args.shape == "cross" else None  # cross has tight regions, need more tries
            positions = random_positions(
                args.count, seed=args.seed, inside_check=inside_check, bounds=bounds, sample_point=sample_pt, max_attempts=cross_attempts
            )

    motif_fill_hex = "#000" if args.motif_fill == "black" else "#fff"
    svg = build_svg(
        motif_content,
        positions,
        motif_name,
        shape=args.shape,
        path_d=path_d,
        motif_scale=motif_scale,
        motif_tx=motif_tx,
        motif_ty=motif_ty,
        path_d_stroke=path_d_stroke,
        stroke_lines=stroke_lines,
        line_style=args.line_style,
        polygon_fill=polygon_fill,
        polygon_fill_defs=polygon_fill_defs,
        polygon_hatch_lines=polygon_hatch_lines,
        partition_defs=partition_defs,
        partition_fill_content=partition_fill_content,
        partition_lines=partition_lines,
        partition_paths=partition_paths,
        motif_fill=motif_fill_hex,
        symbol_transform=symbol_transform,
    )

    out = args.output
    if out is None:
        out_dir = (script_dir.parent / "output") if script_dir.name == "lib" else (script_dir / "output")
        out_dir.mkdir(parents=True, exist_ok=True)
        if args.partition:
            out = out_dir / f"partition-{args.shape}-{args.partition}.svg"
        elif args.empty:
            out = out_dir / f"shape-{args.shape}.svg"
        else:
            out_name = {"club": "clubs", "spade": "spades"}.get(args.motif, args.motif)
            out = out_dir / f"option-{args.shape}-{args.count}-{out_name}.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    if args.empty:
        print(f"Wrote {out} (shape only).")
    else:
        print(f"Wrote {out} ({len(positions)} motifs).")


if __name__ == "__main__":
    main()
