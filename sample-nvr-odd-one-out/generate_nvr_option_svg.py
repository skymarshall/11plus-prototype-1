#!/usr/bin/env python3
"""
Generate an NVR answer-option SVG: empty square with N symbols (randomly spaced, no overlap).
Symbol type and output path are arguments; symbol content is loaded from ../nvr-symbols/{symbol}.svg.
See picture-based-questions-guide.md §4.6 (symbol layout) and nvr-symbol-svg-design.md.

Usage:
  python generate_nvr_option_svg.py club
  python generate_nvr_option_svg.py spade -o option-spades.svg
  python generate_nvr_option_svg.py heart -n 8 --seed 42

To generate an image for every symbol type, run from this directory:
  run_generate_all_symbols.bat   (Windows)
  or: for s in club spade heart diamond circle cross square triangle star; do python generate_nvr_option_svg.py $s; done
"""

import argparse
import math
import random
import re
from pathlib import Path
from typing import Callable


# Answer viewBox 0 0 100 100; square content 15..85; symbol cell 12.5×12.5 (1/8 of 100)
# Placement rules per nvr-symbol-svg-design.md §3: no touching; min centre-to-centre and border margin.
CELL_HALF = 6.25
BORDER_MARGIN = 1.0   # min gap between symbol cell edge and square inner edge (centres in [22.25, 77.75])
MIN_CENTRE_TO_CENTRE = 15.0   # minimum distance between symbol centres (spec: nvr-symbol-svg-design.md)
MIN_CENTRE = 15 + CELL_HALF + BORDER_MARGIN   # 22.25
MAX_CENTRE = 85 - CELL_HALF - BORDER_MARGIN   # 77.75
MIN_DISTANCE = MIN_CENTRE_TO_CENTRE
SYMBOL_SCALE = 1.25
MAX_PLACEMENT_ATTEMPTS = 2000

# Polygon radius from centre to vertex (guide §3: triangles must be large enough to fit symbols inside).
POLYGON_RADIUS: dict[str, float] = {"triangle": 50.0, "pentagon": 35.0, "hexagon": 35.0, "heptagon": 35.0, "octagon": 35.0}
DEFAULT_POLYGON_RADIUS = 35.0
# Polygon centre y (guide §3: triangles centred vertically by default — bbox vertical centre at 50).
# Triangle with vertex at top: bbox centre y = cy - radius/4; so cy = 50 + 12.5 = 62.5 for radius 50.
POLYGON_CY: dict[str, float] = {"triangle": 62.5}
DEFAULT_POLYGON_CY = 50.0
# Circle (regular shape, guide §3): radius for container; centred at (50, 50).
CIRCLE_RADIUS = 35.0


def load_symbol_content(symbol_path: Path) -> tuple[str, str, str]:
    """Load symbol SVG; return (inner content, fill, stroke) for wrapper <g>. Preserves fill/stroke from root <svg>."""
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


def random_positions(
    count: int,
    min_dist: float = MIN_DISTANCE,
    seed: int | None = None,
    inside_check: Callable[[float, float], bool] | None = None,
    bounds: tuple[float, float, float, float] | None = None,
) -> list[tuple[float, float]]:
    """Generate `count` positions with no two closer than `min_dist`. If inside_check and bounds are set, only accept points that pass inside_check (e.g. inside polygon with margin)."""
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

    attempts = 0
    while len(positions) < count and attempts < MAX_PLACEMENT_ATTEMPTS:
        cx = rng.uniform(min_x, max_x)
        cy = rng.uniform(min_y, max_y)
        if accept(cx, cy):
            positions.append((cx, cy))
        attempts += 1

    if len(positions) < count:
        raise SystemExit(
            f"Could not place {count} symbols with min distance {min_dist} in {MAX_PLACEMENT_ATTEMPTS} attempts. Try fewer symbols or ensure polygon is large enough."
        )
    return positions


def regular_polygon_vertices(sides: int, cx: float = 50, cy: float = 50, radius: float = 35) -> list[tuple[float, float]]:
    """Vertices of regular polygon (first at top), counterclockwise. For path and containment."""
    if sides < 3:
        sides = 3
    points: list[tuple[float, float]] = []
    for k in range(sides):
        angle = -math.pi / 2 + k * 2 * math.pi / sides
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    return points


def regular_polygon_path(sides: int, cx: float = 50, cy: float = 50, radius: float = 35) -> str:
    """SVG path for regular polygon (first vertex at top). sides=3 triangle, 4 square (use rect instead), 5 pentagon, etc."""
    points = regular_polygon_vertices(sides, cx, cy, radius)
    d = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in points) + " Z"
    return d


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


# Hatched fill: continuous lines across viewBox, clipped to polygon (guide §4.5)
HATCH_SPACING = 4
HATCH_STROKE = 0.8


def _hatch_lines(fill_key: str) -> list[tuple[float, float, float, float]]:
    """Return list of (x1, y1, x2, y2) for full viewBox-spanning lines. viewBox 0 0 100 100."""
    s = HATCH_SPACING
    out: list[tuple[float, float, float, float]] = []
    if fill_key == "diagonal_slash":
        # Top-left to bottom-right: x - y = k. Segment (0, -k) to (100, 100-k); k so line crosses 0..100
        for k in range(-100, 201, s):
            out.append((0, -k, 100, 100 - k))
    elif fill_key == "diagonal_backslash":
        # Top-right to bottom-left: x + y = k. (0, k) to (100, k-100)
        for k in range(0, 201, s):
            out.append((0, k, 100, k - 100))
    elif fill_key == "horizontal_lines":
        for k in range(0, 101, s):
            out.append((0, k, 100, k))
    elif fill_key == "vertical_lines":
        for k in range(0, 101, s):
            out.append((k, 0, k, 100))
    return out


def hatch_continuous_defs_and_lines(clip_id: str, fill_key: str, path_d: str) -> tuple[str, str]:
    """Continuous hatch lines clipped to polygon. Returns (defs with clipPath, g with lines)."""
    line_coords = _hatch_lines(fill_key)
    stroke = HATCH_STROKE
    defs_str = f'  <defs><clipPath id="{clip_id}"><path d="{path_d}"/></clipPath></defs>'
    line_elts = "\n".join(
        f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#000" stroke-width="{stroke}" stroke-linecap="round"/>'
        for x1, y1, x2, y2 in line_coords
    )
    lines_g = f'  <g clip-path="url(#{clip_id})" fill="none">\n{line_elts}\n  </g>'
    return defs_str, lines_g


def build_svg(
    symbol_content: str,
    positions: list[tuple[float, float]],
    symbol_name: str,
    fill: str = "#000",
    stroke: str = "#000",
    shape: str = "square",
    line_style: str = "solid",
    polygon_fill: str = "none",
    polygon_fill_defs: str | None = None,
    polygon_hatch_lines: str | None = None,
) -> str:
    """Build full answer-option SVG with polygon container and one symbol group per position."""
    stroke_dasharray = {"solid": "", "dashed": "8 4", "dotted": "2 4"}.get(line_style, "")
    dash_attr = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">',
        f"  <!-- {shape} container, {line_style}, fill; {len(positions)} {symbol_name} symbols -->",
    ]
    if polygon_fill_defs:
        lines.append(polygon_fill_defs)
    if polygon_hatch_lines:
        lines.append(polygon_hatch_lines)
    # Polygon or circle: fill (or none when hatch); stroke for outline
    if shape == "square":
        lines.append(f'  <rect x="15" y="15" width="70" height="70" fill="{polygon_fill}" stroke-width="2"{dash_attr} />')
    elif shape == "circle":
        lines.append(f'  <circle cx="50" cy="50" r="{CIRCLE_RADIUS}" fill="{polygon_fill}" stroke-width="2"{dash_attr} />')
    else:
        sides = {"triangle": 3, "pentagon": 5, "hexagon": 6, "heptagon": 7, "octagon": 8}.get(shape, 4)
        radius = POLYGON_RADIUS.get(shape, DEFAULT_POLYGON_RADIUS)
        poly_cy = POLYGON_CY.get(shape, DEFAULT_POLYGON_CY)
        path_d = regular_polygon_path(sides, 50, poly_cy, radius)
        lines.append(f'  <path d="{path_d}" fill="{polygon_fill}" stroke-width="2"{dash_attr} />')
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
        description="Generate NVR option SVG: empty square with randomly spaced symbols (no overlap)."
    )
    parser.add_argument(
        "symbol",
        type=str,
        help="Symbol type (filename without .svg in nvr-symbols/, e.g. club, spade, heart, circle).",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output SVG path (default: option-square-10-{symbol}.svg in this directory).",
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=10,
        metavar="N",
        help="Number of symbols (default: 10).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible placement (default: random).",
    )
    parser.add_argument(
        "--symbols-dir",
        type=Path,
        default=script_dir.parent / "nvr-symbols",
        help="Directory containing symbol SVGs (default: ../nvr-symbols).",
    )
    parser.add_argument(
        "--shape",
        type=str,
        default="square",
        choices=["triangle", "square", "pentagon", "hexagon", "heptagon", "octagon", "circle"],
        help="Container shape: polygon or circle (default: square).",
    )
    parser.add_argument(
        "--line-style",
        type=str,
        default="solid",
        choices=["solid", "dashed", "dotted"],
        help="Polygon outline style (default: solid).",
    )
    parser.add_argument(
        "--fill",
        type=str,
        default="white",
        choices=[
            "solid_black", "grey", "white",
            "diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines",
        ],
        help="Polygon fill / shading (guide §4.5). Default: white.",
    )
    args = parser.parse_args()

    symbol_path = args.symbols_dir / f"{args.symbol}.svg"
    if not symbol_path.exists():
        raise SystemExit(f"Symbol file not found: {symbol_path}")

    # Solid fills (guide §4.5); hatched fills use continuous lines clipped to shape
    solid_fills = {"solid_black": "#000", "grey": "#808080", "white": "none"}
    hatch_keys = ("diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines")
    if args.shape == "square":
        vertices = [(15, 15), (85, 15), (85, 85), (15, 85)]
        path_d = "M15 15 L85 15 L85 85 L15 85 Z"
    elif args.shape == "circle":
        r = CIRCLE_RADIUS
        path_d = f"M 50 {50 - r} A {r} {r} 0 0 1 50 {50 + r} A {r} {r} 0 0 1 50 {50 - r} Z"
        vertices = []  # not used for circle
    else:
        sides = {"triangle": 3, "pentagon": 5, "hexagon": 6, "heptagon": 7, "octagon": 8}.get(args.shape, 4)
        radius = POLYGON_RADIUS.get(args.shape, DEFAULT_POLYGON_RADIUS)
        poly_cy = POLYGON_CY.get(args.shape, DEFAULT_POLYGON_CY)
        vertices = regular_polygon_vertices(sides, 50, poly_cy, radius)
        path_d = regular_polygon_path(sides, 50, poly_cy, radius)

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
    symbol_content, symbol_fill, symbol_stroke = load_symbol_content(symbol_path)

    def inside_check(cx: float, cy: float) -> bool:
        if args.shape == "circle":
            return math.hypot(cx - 50, cy - 50) <= CIRCLE_RADIUS - CELL_HALF
        p = (cx, cy)
        return point_in_convex_polygon(p, vertices) and min_distance_to_edges(p, vertices) >= CELL_HALF

    if args.shape == "circle":
        bounds = (50 - CIRCLE_RADIUS, 50 + CIRCLE_RADIUS, 50 - CIRCLE_RADIUS, 50 + CIRCLE_RADIUS)
    else:
        bounds = (
            min(v[0] for v in vertices),
            max(v[0] for v in vertices),
            min(v[1] for v in vertices),
            max(v[1] for v in vertices),
        )
    positions = random_positions(args.count, seed=args.seed, inside_check=inside_check, bounds=bounds)
    svg = build_svg(
        symbol_content,
        positions,
        args.symbol,
        fill=symbol_fill,
        stroke=symbol_stroke,
        shape=args.shape,
        line_style=args.line_style,
        polygon_fill=polygon_fill,
        polygon_fill_defs=polygon_fill_defs,
        polygon_hatch_lines=polygon_hatch_lines,
    )

    out = args.output
    if out is None:
        # Use plural output filename for club/spade to match original option-square-10-clubs.svg / option-square-10-spades.svg
        out_name = {"club": "clubs", "spade": "spades"}.get(args.symbol, args.symbol)
        out = script_dir / f"option-square-10-{out_name}.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out} ({len(positions)} symbols).")


if __name__ == "__main__":
    main()
