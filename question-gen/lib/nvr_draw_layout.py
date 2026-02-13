#!/usr/bin/env python3
"""
Render question/diagrams XML to SVG: all layout types (shape, scatter, stack, array).

Supports diagram roots: shape (single), scatter, stack, array. Nesting supported:
array and stack may contain shape or nested stack/array/scatter; scatter only shapes.
Uses nvr_draw_single_shape for single-shape diagrams and nvr_draw_container_svg
for geometry; composes multiple shapes for scatter, stack, and array.

Usage (from question-gen):
  python lib/nvr_draw_layout.py sample/sample-layouts-simple.xml -o output
  python lib/nvr_draw_layout.py path/to/file.xml [-o output_dir] [--prefix name]

Output: one SVG per diagram (diagram-0.svg, diagram-1.svg, ... or diagram-{id}.svg).
"""

from __future__ import annotations

import argparse
import math
import random
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

import nvr_draw_container_svg as container
import nvr_draw_single_shape as single_shape

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
_REPO_ROOT = _PROJECT_ROOT.parent

VIEWBOX = (0, 0, 100, 100)
# Element size when placed in layout (e.g. scatter): scale so shape fits in this "cell"
ELEMENT_SCALE_SCATTER = 0.2   # 20% of viewBox so several fit
ELEMENT_SCALE_STACK = 0.28   # used for stack spacing (positions)
STACK_DRAW_SCALE_FACTOR = 1.6   # draw shapes much larger; capped by _stack_scale_max_in_viewbox
ELEMENT_SCALE_ARRAY = 0.22   # unused; loop/triangular use _array_scale_max_no_overlap_*
LOOP_SCALE_FACTOR = 0.85    # draw loop shapes slightly smaller than max; radius (loop size) unchanged
# Rectangular arrays: square cells; cell_size = min(100/cols, 100/rows); grid centred in viewBox.
def _array_scale_max_no_overlap(rows: int, cols: int) -> float:
    """Largest scale for a rectangular array so shapes do not overlap. Square cells using minimum required spacing; grid centred in 0 0 100 100."""
    cell_size = min(100.0 / cols, 100.0 / rows)
    return cell_size / 100.0


# Motif standardized sizes (design doc §3.4.1): viewBox cell size → scale = cell/100
MOTIF_SCALE_SMALL = 0.075   # ~7.5 units
MOTIF_SCALE_MEDIUM = 0.125  # ~12.5 units
MOTIF_SCALE_LARGE = 0.175   # ~17.5 units

MIN_CENTRE_TO_CENTRE = 16.0   # scatter: fallback min centre-to-centre
# Non-motif scatter scale: design doc "generous, no overlap" — scale(n) = SAFETY / (1 + √n), min_dist = 100×scale, margin = 50×scale + ε
SCATTER_SCALE_SAFETY = 0.99  # safety factor for random placement and floating point
# Margin from shape boundary when placing scatter inside a shape (so placed shapes do not overlap the outline)
SCATTER_INSIDE_SHAPE_MARGIN = 10.0
# Scale factor for scatter inside a shape: use scale * this so placement has room (avoids render failure in tight regions)
SCATTER_INSIDE_SHAPE_SCALE_FACTOR = 0.55
STACK_OFFSET = 0.52           # fraction of element size for overlap (higher = tighter stack, allows larger scale)
STACK_STEP_CROSS = 0.2       # cross-axis step per item (fraction of size); smaller = less fan-out


def _iter_diagrams(root: ET.Element):
    """Yield (diagram_element, label) for each diagram in the document."""
    tag = root.tag
    if tag == "diagrams":
        for i, diagram in enumerate(root.findall("diagram")):
            did = diagram.get("id") or f"diagram-{i}"
            yield diagram, did
    elif tag == "question":
        for opt in root.findall("options/option"):
            diagram = opt.find("diagram")
            if diagram is not None:
                idx = opt.get("index", "")
                yield diagram, f"option-{idx}"
    elif tag == "questions":
        for q in root.findall("question"):
            qid = q.get("id", "")
            for opt in q.findall("options/option"):
                diagram = opt.find("diagram")
                if diagram is not None:
                    idx = opt.get("index", "")
                    yield diagram, f"{qid}-option-{idx}"
    else:
        raise ValueError(f"Unsupported root element: {tag!r}. Use question, questions, or diagrams.")


def _get_diagram_root(diagram_el: ET.Element) -> ET.Element | None:
    """Return the single child that is the diagram root (shape | scatter | stack | array), or None."""
    for tag in ("shape", "scatter", "stack", "array"):
        child = diagram_el.find(tag)
        if child is not None:
            return child
    return None


def _has_nested_layout(el: ET.Element) -> bool:
    """True if element has scatter, stack, or array as a child."""
    for tag in ("scatter", "stack", "array"):
        if el.find(tag) is not None:
            return True
    return False


def _shape_to_svg_fragment(
    shape_el: ET.Element,
    motifs_dir: Path,
    unique_id: str,
) -> str:
    """
    Return SVG fragment for one shape (path + fill + stroke) in 0 0 100 100 coords.
    unique_id used for any defs (e.g. hatch clip). No <svg> wrapper.
    When shape has a partition child, delegates to single_shape so partitions are drawn.
    """
    partition_el = shape_el.find("partition")
    has_nested_layout = any(shape_el.find(tag) is not None for tag in ("scatter", "stack", "array"))
    if partition_el is not None and not has_nested_layout:
        full_svg = single_shape.render_shape_to_svg(
            shape_el, motifs_dir=motifs_dir, shape_clip_id=f"shapeClip{unique_id}"
        )
        return _unwrap_svg(full_svg)
    key = (shape_el.get("key") or "").strip().lower()
    if not key or key not in container.SHAPES_ALL:
        raise ValueError(f"Invalid or unknown shape key: {key!r}")
    line_type = (shape_el.get("line_type") or "solid").strip().lower()
    if line_type not in ("solid", "dashed", "dotted"):
        line_type = "solid"
    shading = (shape_el.get("shading") or "black").strip().lower()

    vertices, path_d, path_d_stroke, stroke_lines, symbol_transform, _ = container.get_shape_geometry(
        key, motifs_dir
    )
    stroke_dasharray = {"solid": "", "dashed": "8 4", "dotted": "2 4"}.get(line_type, "")
    dash_attr = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""
    is_cross = key == "cross"
    fill_rule_attr = ' fill-rule="evenodd"' if is_cross else ""

    def path_line(fill: str, stroke: str = 'stroke-width="2"') -> str:
        return f'  <path d="{path_d}" fill="{fill}" {stroke} {dash_attr}{fill_rule_attr} />'

    def wrap(content: list[str]) -> list[str]:
        if symbol_transform:
            return [f'  <g transform="{symbol_transform}">'] + content + ["  </g>"]
        return content

    # Default: opaque fill so stacks display correctly (white = #fff). Set opaque="false" for transparent when needed.
    opaque = (shape_el.get("opaque") or "true").strip().lower() not in ("false", "0")
    solid = {"solid_black": "#000", "black": "#000", "grey": "#808080", "grey_light": "#d0d0d0", "white_fill": "#fff"}
    solid["white"] = "#fff" if opaque else "none"
    hatch_keys = ("diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines")
    if shading in solid:
        polygon_fill = solid[shading]
        lines: list[str] = wrap([path_line(polygon_fill, 'stroke="none"')])
        if stroke_lines is not None:
            lines += [f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="2"{dash_attr} />' for x1, y1, x2, y2 in stroke_lines]
        elif path_d_stroke is not None:
            lines.append(f'  <path d="{path_d_stroke}" fill="none" stroke-width="2" stroke-linejoin="miter" stroke-linecap="butt"{dash_attr} />')
        else:
            lines = wrap([path_line(polygon_fill)])
        return "\n".join(lines)
    if shading in hatch_keys:
        polygon_fill_defs, polygon_hatch_lines = container.hatch_continuous_defs_and_lines(
            f"hatchClip{unique_id}", shading, path_d
        )
        # Defs + path (fill url) + stroke
        clip_id = f"hatchClip{unique_id}"
        path_fill = path_line(f"url(#{clip_id})", 'stroke="none"')
        parts = [polygon_fill_defs]
        parts.extend(wrap([path_fill]))
        if stroke_lines is not None:
            parts += [f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="2"{dash_attr} />' for x1, y1, x2, y2 in stroke_lines]
        elif path_d_stroke is not None:
            parts.append(f'  <path d="{path_d_stroke}" fill="none" stroke-width="2" stroke-linejoin="miter" stroke-linecap="butt"{dash_attr} />')
        parts.append(polygon_hatch_lines)
        if stroke_lines is None and path_d_stroke is None:
             parts.extend(wrap([path_line("none", 'stroke="#000" stroke-width="2"')]))
        return "\n".join(parts)
    # fallback
    return "\n".join(wrap([path_line("none")]))


def _placement_scale(el: ET.Element, layout_scale: float) -> float:
    """Return scale for placing this element: motif_scale (small/medium/large) if set on a shape, else layout_scale."""
    if el.tag != "shape":
        return layout_scale
    motif_scale_attr = (el.get("motif_scale") or "").strip().lower()
    if motif_scale_attr == "small":
        return MOTIF_SCALE_SMALL
    if motif_scale_attr == "medium":
        return MOTIF_SCALE_MEDIUM
    if motif_scale_attr == "large":
        return MOTIF_SCALE_LARGE
    return layout_scale


def _has_motif_scale(shape_el: ET.Element) -> bool:
    """True if this shape has motif_scale set (small/medium/large)."""
    if shape_el.tag != "shape":
        return False
    v = (shape_el.get("motif_scale") or "").strip().lower()
    return v in ("small", "medium", "large")


def _scatter_scale_for_count(n: int) -> float:
    """Scale for non-motif scatter with n elements. Design doc: scale(n) = 0.99/(1+√n), generous, no overlap."""
    n = max(1, n)
    return SCATTER_SCALE_SAFETY / (1.0 + math.sqrt(n))


def _scatter_effective_count(scatter_el: ET.Element, actual_count: int) -> int:
    """Count used for scale: scale_as_count if set (uniform scaling across diagrams), else actual_count.
    Spec: scale_as_count must be >= actual count; we clamp so effective_count >= actual_count to avoid placement failure."""
    raw = scatter_el.get("scale_as_count")
    if raw is None or raw.strip() == "":
        return actual_count
    return max(actual_count, 1, int(raw))


def _place_fragment(fragment: str, cx: float, cy: float, scale: float) -> str:
    """Wrap fragment in a group translated and scaled so shape centre is at (cx, cy) with given scale."""
    indented = "\n".join("    " + line for line in fragment.split("\n"))
    return f'  <g transform="translate({cx:.2f}, {cy:.2f}) scale({scale:.4f}) translate(-50, -50)">\n{indented}\n  </g>'


def _unwrap_svg(svg: str) -> str:
    """Return inner content of a full SVG document (for use as a fragment)."""
    start = svg.index(">", svg.index("<svg")) + 1
    end = svg.rindex("</svg>")
    return svg[start:end].strip()


def _layout_effective_scale(
    el: ET.Element,
    motifs_dir: Path,
    *,
    seed: int | None = None,
) -> float:
    """Return the scale at which this layout's content is drawn (in its 0 0 100 100 space). Used so array cells apply only the smaller of array scale and nested scale."""
    if el.tag == "stack":
        children = [c for c in el if c.tag in ("shape", "stack", "array", "scatter")]
        if len(children) < 2:
            return ELEMENT_SCALE_STACK
        n = len(children)
        direction = (el.get("direction") or "up").strip().lower()
        if direction not in ("up", "down", "left", "right"):
            direction = "up"
        scale_max = _stack_scale_max_in_viewbox(n, direction, ELEMENT_SCALE_STACK)
        return min(ELEMENT_SCALE_STACK * STACK_DRAW_SCALE_FACTOR, scale_max)
    if el.tag == "array":
        atype = (el.get("type") or "rectangular").strip().lower()
        if atype == "rectangular":
            rows = int(el.get("rows", "2"))
            cols = int(el.get("cols", "2"))
            return _array_scale_max_no_overlap(rows, cols)
        if atype == "loop":
            count = int(el.get("count", "6"))
            per_edge = int(el.get("per_edge", "1"))
            scale_max = _array_scale_max_no_overlap_loop(count, per_edge)
            return scale_max * LOOP_SCALE_FACTOR
        if atype == "triangular":
            count = int(el.get("count", "6"))
            return _array_scale_max_no_overlap_triangular(count)
        rows, cols = 2, 2
        return _array_scale_max_no_overlap(rows, cols)
    if el.tag == "scatter":
        return ELEMENT_SCALE_SCATTER
    return 0.5  # fallback


def _element_to_fragment(
    el: ET.Element,
    motifs_dir: Path,
    *,
    seed: int | None = None,
    unique_id: str = "",
) -> str:
    """Return SVG fragment (0 0 100 100 content) for one element: shape or nested layout."""
    if el.tag == "shape":
        return _shape_to_svg_fragment(el, motifs_dir, unique_id)
    if el.tag == "stack":
        return _unwrap_svg(render_stack(el, motifs_dir, seed=seed))
    if el.tag == "array":
        return _unwrap_svg(render_array(el, motifs_dir, seed=seed))
    if el.tag == "scatter":
        return _unwrap_svg(render_scatter(el, motifs_dir, seed=seed or 0))
    raise ValueError(f"Unknown element for fragment: {el.tag!r}")


def _collect_shape_children(root: ET.Element) -> list[ET.Element]:
    """Return list of direct layout children (shape, stack, array, scatter). For array, repeated is handled by caller."""
    children: list[ET.Element] = []
    repeated = root.find("repeated")
    if repeated is not None:
        # Caller handles repeated via array type
        return []
    for child in root:
        if child.tag in ("shape", "stack", "array", "scatter"):
            children.append(child)
    return children


def _scatter_positions(n: int, margin: float, min_dist: float, rng: random.Random) -> list[tuple[float, float]]:
    """Place n centres in [margin, 100-margin] with min_dist between them. Simple rejection sampling."""
    positions: list[tuple[float, float]] = []
    max_attempts = 2000
    for _ in range(n):
        for _ in range(max_attempts):
            cx = rng.uniform(margin, 100 - margin)
            cy = rng.uniform(margin, 100 - margin)
            if all(math.hypot(cx - px, cy - py) >= min_dist for px, py in positions):
                positions.append((cx, cy))
                break
        else:
            # fallback: place on a loose grid
            row = len(positions) // 4
            col = len(positions) % 4
            cx = margin + (100 - 2 * margin) * (col + 1) / 5
            cy = margin + (100 - 2 * margin) * (row + 1) / 3
            positions.append((cx, cy))
    return positions


def _stack_positions(n: int, direction: str, scale: float) -> list[tuple[float, float]]:
    """Positions for n elements in a stack (bottom to top). direction: up, down, left, right. scale = element scale."""
    size = 100 * scale
    offset = size * (1 - STACK_OFFSET)
    step_cross = size * STACK_STEP_CROSS
    cx, cy = 50.0, 50.0
    positions = []
    for i in range(n):
        positions.append((cx, cy))
        if direction == "up":
            cy -= offset
            cx += step_cross
        elif direction == "down":
            cy += offset
            cx += step_cross
        elif direction == "right":
            cx += offset
            cy += step_cross
        elif direction == "left":
            cx -= offset
            cy += step_cross
        else:
            cy -= offset
            cx += step_cross
    # Centre the stack in the viewBox
    if not positions:
        return positions
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    mid_x = (min(xs) + max(xs)) / 2
    mid_y = (min(ys) + max(ys)) / 2
    return [(x - mid_x + 50, y - mid_y + 50) for x, y in positions]


def _stack_scale_max_in_viewbox(n: int, direction: str, position_scale: float) -> float:
    """Largest scale for stack shapes so no shape extends outside the viewBox 0 0 100 100.
    Shape at (cx, cy) with scale s extends to cx±50s, cy±50s; we need min(cx, 100-cx, cy, 100-cy) >= 50s."""
    positions = _stack_positions(n, direction, position_scale)
    if not positions:
        return position_scale
    margin = min(
        min(cx, 100 - cx, cy, 100 - cy) for cx, cy in positions
    )
    return margin / 50.0


def _array_positions_rectangular(rows: int, cols: int) -> list[tuple[float, float]]:
    """Cell centres for rows×cols grid in 0 0 100 100. Square cells: cell_size = min(100/cols, 100/rows); grid centred in viewBox."""
    cell_size = min(100.0 / cols, 100.0 / rows)
    origin_x = 50.0 - (cols * cell_size) / 2.0
    origin_y = 50.0 - (rows * cell_size) / 2.0
    positions = []
    for r in range(rows):
        for c in range(cols):
            cx = origin_x + cell_size * (c + 0.5)
            cy = origin_y + cell_size * (r + 0.5)
            positions.append((cx, cy))
    return positions


def _mesh_segments_rectangular(
    rows: int,
    cols: int,
    positions: list[tuple[float, float]],
    is_non_null: list[bool],
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Line segments between adjacent cell centres (horizontal and vertical). draw_full_grid false: only between non-null cells."""
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    n = rows * cols
    for i in range(n):
        r, c = i // cols, i % cols
        # right neighbour
        if c + 1 < cols:
            j = i + 1
            if is_non_null[i] and is_non_null[j]:
                segments.append((positions[i], positions[j]))
        # down neighbour
        if r + 1 < rows:
            j = i + cols
            if is_non_null[i] and is_non_null[j]:
                segments.append((positions[i], positions[j]))
    return segments


def _mesh_segments_triangular(
    positions: list[tuple[float, float]],
    rows_list: list[int],
    is_non_null: list[bool],
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Line segments between adjacent cell centres in triangular formation."""
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    n = len(positions)
    start = 0
    for r, row_len in enumerate(rows_list):
        for c in range(row_len):
            i = start + c
            if i >= n:
                break
            # right (same row)
            if c + 1 < row_len:
                j = i + 1
                if j < n and is_non_null[i] and is_non_null[j]:
                    segments.append((positions[i], positions[j]))
            # up-left (row above, col c-1)
            if r > 0 and c > 0:
                j = start - row_len + c - 1
                if 0 <= j < n and is_non_null[i] and is_non_null[j]:
                    segments.append((positions[i], positions[j]))
            # up-right (row above, col c)
            if r > 0 and c < row_len - 1:
                j = start - row_len + c
                if 0 <= j < n and is_non_null[i] and is_non_null[j]:
                    segments.append((positions[i], positions[j]))
        start += row_len
    return segments


def _mesh_svg_group(
    segments: list[tuple[tuple[float, float], tuple[float, float]]],
    mesh_line_type: str,
) -> str:
    """Return SVG group of lines for mesh. mesh_line_type: solid, dashed, dotted, bold."""
    dash_map = {"solid": "", "dashed": "8 4", "dotted": "2 4", "bold": ""}
    dash_attr = dash_map.get(mesh_line_type, "")
    stroke_width = "3" if mesh_line_type == "bold" else "2"
    dash_str = f' stroke-dasharray="{dash_attr}"' if dash_attr else ""
    lines = []
    for (x1, y1), (x2, y2) in segments:
        lines.append(f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#000" stroke-width="{stroke_width}"{dash_str} />')
    return "\n".join(lines)


def _array_scale_max_no_overlap_loop(count: int, per_edge: int = 1) -> float:
    """Largest scale for loop array so shapes do not overlap. Circle as large as possible in viewBox (centre 50,50).
    Chord between adjacent points = 2*R*sin(π/n); need chord >= 100*scale => scale_max = sin(π/n) / (1 + sin(π/n)).
    When per_edge > 1 (multiple shapes on each polygon edge), spacing along edge = edge_length/(per_edge+1);
    edge_length = 2*R*sin(π/n_sides) => scale_max = sin(π/n_sides) / ((per_edge+1) + sin(π/n_sides))."""
    if count < 2:
        return 0.5
    if per_edge > 1:
        n_sides = max(1, count // per_edge)
        s = math.sin(math.pi / n_sides)
        return s / ((per_edge + 1) + s)
    n = count
    s = math.sin(math.pi / n)
    return s / (1.0 + s)


def _loop_count_and_positions_params(
    array_el: ET.Element,
    path_shape: str,
    motifs_dir: Path | None,
) -> tuple[int, str | None, int]:
    """Return (count, positions_attr, per_edge) for a loop array. For polygon path, count is derived from vertices/edges."""
    path_shape_lower = (path_shape or "circle").strip().lower()
    positions_attr = (array_el.get("positions") or "").strip().lower() or None
    per_edge = int(array_el.get("per_edge", "1"))
    if path_shape_lower == "circle" or path_shape_lower not in container.SHAPES_ALL or not motifs_dir:
        return int(array_el.get("count", "6")), None, per_edge
    if positions_attr not in ("vertices", "edges"):
        return int(array_el.get("count", "6")), positions_attr or None, per_edge
    try:
        vertices, *_ = container.get_shape_geometry(path_shape_lower, motifs_dir)
    except Exception:
        return int(array_el.get("count", "6")), positions_attr, per_edge
    n = len(vertices) if vertices else 0
    if n == 0:
        return int(array_el.get("count", "6")), positions_attr, per_edge
    if positions_attr == "vertices":
        count = n
    else:
        count = n * per_edge
    return count, positions_attr, per_edge


def _loop_scaled_vertices(
    path_shape: str,
    radius: float,
    motifs_dir: Path,
) -> list[tuple[float, float]]:
    """Return polygon vertices scaled so bounding radius equals radius (centre 50,50). Empty if not a polygon."""
    path_shape_lower = (path_shape or "circle").strip().lower()
    if path_shape_lower == "circle" or path_shape_lower not in container.SHAPES_ALL:
        return []
    try:
        vertices, _path_d, *_ = container.get_shape_geometry(path_shape_lower, motifs_dir)
    except Exception:
        return []
    if not vertices:
        return []
    max_radius = max(math.hypot(v[0] - 50.0, v[1] - 50.0) for v in vertices)
    if max_radius < 1e-6:
        return []
    scale_factor = radius / max_radius
    return [
        (50.0 + (v[0] - 50.0) * scale_factor, 50.0 + (v[1] - 50.0) * scale_factor)
        for v in vertices
    ]


def _array_positions_loop(
    count: int,
    scale: float,
    path_shape: str = "circle",
    positions_attr: str | None = None,
    per_edge: int = 1,
    motifs_dir: Path | None = None,
) -> list[tuple[float, float]]:
    """Positions for loop: on circle (path_shape=circle) or on polygon path (vertices or edges)."""
    cx, cy = 50.0, 50.0
    radius = 50.0 * (1.0 - scale)
    path_shape_lower = (path_shape or "circle").strip().lower()
    positions_attr = (positions_attr or "").strip().lower() if positions_attr else ""
    # Polygon path: vertices or edges
    if path_shape_lower != "circle" and path_shape_lower in container.SHAPES_ALL and motifs_dir is not None:
        scaled = _loop_scaled_vertices(path_shape_lower, radius, motifs_dir)
        if not scaled:
            pass  # fall through to circle
        elif positions_attr == "vertices":
            # One element per vertex
            return scaled[:count]
        elif positions_attr == "edges":
            # per_edge points on each edge (evenly spaced, no duplicate at vertex)
            n = len(scaled)
            result: list[tuple[float, float]] = []
            for i in range(n):
                v0 = scaled[i]
                v1 = scaled[(i + 1) % n]
                for k in range(1, per_edge + 1):
                    t = k / (per_edge + 1)
                    x = v0[0] + t * (v1[0] - v0[0])
                    y = v0[1] + t * (v1[1] - v0[1])
                    result.append((x, y))
            return result[:count]
    # Circle (default): evenly spaced on circumference
    positions = []
    for i in range(count):
        angle = 2 * math.pi * i / count - math.pi / 2  # start at top
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        positions.append((x, y))
    return positions


def _loop_path_svg(
    path_shape: str,
    radius: float,
    path_line_type: str,
    motifs_dir: Path,
) -> str:
    """Return SVG for the loop path outline (circle or polygon). Drawn behind elements; fill none, stroke only."""
    dash_map = {"solid": "", "dashed": "8 4", "dotted": "2 4", "bold": ""}
    dash_attr = dash_map.get(path_line_type, "")
    dash_str = f' stroke-dasharray="{dash_attr}"' if dash_attr else ""
    stroke_width = "2"
    path_shape_lower = (path_shape or "circle").strip().lower()
    if path_shape_lower == "circle":
        return f'  <circle cx="50" cy="50" r="{radius:.2f}" fill="none" stroke="#000" stroke-width="{stroke_width}"{dash_str} />'
    if path_shape_lower not in container.SHAPES_ALL:
        return f'  <circle cx="50" cy="50" r="{radius:.2f}" fill="none" stroke="#000" stroke-width="{stroke_width}"{dash_str} />'
    try:
        vertices, path_d, _path_d_stroke, _stroke_lines, symbol_transform, _ = container.get_shape_geometry(
            path_shape_lower, motifs_dir
        )
    except Exception:
        return f'  <circle cx="50" cy="50" r="{radius:.2f}" fill="none" stroke="#000" stroke-width="{stroke_width}"{dash_str} />'
    # Scale so the path's bounding radius equals our loop radius (matches circle used for placement)
    if vertices:
        max_radius = max(math.hypot(v[0] - 50.0, v[1] - 50.0) for v in vertices)
    else:
        max_radius = 50.0
    if max_radius < 1e-6:
        max_radius = 50.0
    scale_factor = radius / max_radius
    scaled_d = container._scale_path_d(path_d, 50.0, 50.0, scale_factor)
    path_el = f'  <path d="{scaled_d}" fill="none" stroke="#000" stroke-width="{stroke_width}"{dash_str} />'
    if symbol_transform:
        return f'  <g transform="{symbol_transform}">\n{path_el}\n  </g>'
    return path_el


def _triangular_rows_and_cols(count: int) -> tuple[list[int], int, int]:
    """Return (rows_list, num_rows, max_cols) for triangular formation (row 1 has 1, row 2 has 2, ...)."""
    rows_list: list[int] = []
    k = 0
    r = 1
    while k + r <= count:
        rows_list.append(r)
        k += r
        r += 1
    if k < count:
        rows_list.append(count - k)
    num_rows = len(rows_list)
    max_cols = max(rows_list) if rows_list else 1
    return rows_list, num_rows, max_cols


def _array_scale_max_no_overlap_triangular(count: int) -> float:
    """Largest scale for triangular array so shapes do not overlap. No spacing at boundaries (margin=0)."""
    rows_list, num_rows, max_cols = _triangular_rows_and_cols(count)
    cell = min(100.0 / max_cols, 100.0 / num_rows)
    return cell / 100.0


def _array_positions_triangular(count: int, direction: str = "up") -> list[tuple[float, float]]:
    """Positions for triangular array (row 1 has 1, row 2 has 2, ...). No spacing at boundaries (margin=0). direction: up, down, left, right."""
    rows_list, num_rows, max_cols = _triangular_rows_and_cols(count)
    cell = min(100.0 / max_cols, 100.0 / num_rows)
    positions = []
    for ri, nc in enumerate(rows_list):
        row_width = nc * cell
        start_x = 50 - row_width / 2 + cell / 2
        for c in range(nc):
            cx = start_x + c * cell
            cy = ri * cell
            positions.append((cx, cy))
    # Centre the formation in the viewBox (formation spans 0 to num_rows*cell in y; 50 ± row_width/2 in x)
    if positions:
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        mid_x = (min(xs) + max(xs)) / 2
        mid_y = (min(ys) + max(ys)) / 2
        positions = [(x - mid_x + 50, y - mid_y + 50) for x, y in positions]
    if direction == "down":
        positions = [(x, 100 - y) for x, y in positions]
    elif direction == "left":
        positions = [(100 - x, y) for x, y in positions]
    return positions


def _scatter_shape_children(scatter_el: ET.Element) -> list[ET.Element]:
    """Return list of shape elements for scatter: either from repeated (count times) or explicit children."""
    repeated = scatter_el.find("repeated")
    if repeated is not None:
        repeated_el = repeated.find("shape")
        if repeated_el is None or _has_nested_layout(repeated_el):
            raise ValueError("Scatter repeated must contain a single shape (no nested layout)")
        count = int(scatter_el.get("count", "5"))
        if count < 1:
            count = 5
        return [repeated_el] * count
    children = list(scatter_el)
    shape_children = [c for c in children if c.tag == "shape" and not _has_nested_layout(c)]
    return shape_children


def render_scatter(scatter_el: ET.Element, motifs_dir: Path, seed: int | None = None) -> str:
    """Render scatter layout (no nesting): children placed randomly. Supports repeated with count.
    When shapes have motif_scale: size and spacing from motif size. When not: scale and spacing
    from effective count (scale_as_count or actual count). Use scale_as_count to unify scale across diagrams."""
    shape_children = _scatter_shape_children(scatter_el)
    if not shape_children:
        raise ValueError("Scatter has no shape children (use <repeated><shape .../></repeated> with count=\"n\" or explicit shapes)")
    actual_count = len(shape_children)
    effective_count = _scatter_effective_count(scatter_el, actual_count)
    uses_motifs = any(_has_motif_scale(c) for c in shape_children)
    rng = random.Random(seed)
    if uses_motifs:
        max_motif_scale = max(_placement_scale(c, ELEMENT_SCALE_SCATTER) for c in shape_children)
        margin = 50.0 * max_motif_scale + 1.0
        min_dist = 100.0 * max_motif_scale
        layout_scale = ELEMENT_SCALE_SCATTER
    else:
        layout_scale = _scatter_scale_for_count(effective_count)
        margin = 50.0 * layout_scale + 1.0
        min_dist = 100.0 * layout_scale
    positions = _scatter_positions(actual_count, margin, min_dist, rng)
    fragments: list[str] = []
    for i, (shape_el, (cx, cy)) in enumerate(zip(shape_children, positions)):
        frag = _shape_to_svg_fragment(shape_el, motifs_dir, str(i))
        place_scale = _placement_scale(shape_el, layout_scale)
        fragments.append(_place_fragment(frag, cx, cy, place_scale))
    body = "\n".join(fragments)
    return _svg_wrapper(body, "scatter")


def _scatter_inside_shape_inside_check(
    key: str,
    vertices: list[tuple[float, float]],
    margin: float,
) -> tuple[object, tuple[float, float, float, float]]:
    """Build (inside_check, bounds) for placing scatter inside a shape. Uses container helpers (circle/polygon inside + edge margin)."""
    key = (key or "square").strip().lower()
    bbox = container.get_shape_bbox(key, vertices, "")
    x_min, x_max, y_min, y_max = bbox

    if key == "circle":
        # Centre (50, 50), radius from bbox
        r = (x_max - x_min) / 2.0
        cx_centre, cy_centre = 50.0, 50.0

        def inside_check(cx: float, cy: float) -> bool:
            return math.hypot(cx - cx_centre, cy - cy_centre) <= r - margin

        bounds = (x_min, x_max, y_min, y_max)
        return inside_check, bounds
    if key == "semicircle":
        # Vertically centred: circle centre (50, 67.5), flat at bottom
        cy_centre = 67.5
        r = container.SEMICIRCLE_RADIUS
        arc_top_y = cy_centre - r

        def inside_check(cx: float, cy: float) -> bool:
            if math.hypot(cx - 50, cy - cy_centre) > r - margin:
                return False
            if cy > cy_centre - margin or cy < arc_top_y + margin:
                return False
            return True

        bounds = (50 - r, 50 + r, arc_top_y + margin, cy_centre - margin)
        return inside_check, bounds
    if key == "cross":
        # Cross: centre + 4 arms only (exclude corner notches); keep margin from edges
        if not vertices:
            bounds = (x_min, x_max, y_min, y_max)
            return (lambda cx, cy: x_min + margin <= cx <= x_max - margin and y_min + margin <= cy <= y_max - margin), bounds
        dist_margin = getattr(container, "CROSS_EDGE_MARGIN", margin)

        def inside_check(cx: float, cy: float) -> bool:
            if not container._point_in_cross(cx, cy):
                return False
            return container.min_distance_to_edges((cx, cy), vertices) >= dist_margin

        bounds = (x_min, x_max, y_min, y_max)
        return inside_check, bounds
    # Polygon (regular or symbol)
    if vertices:
        use_convex = key in (
            "square", "triangle", "pentagon", "hexagon", "heptagon", "octagon",
            "right_angled_triangle", "rectangle",
        )
        # Use at least margin (needed so shape fits); triangle may add extra buffer via TRIANGLE_EDGE_MARGIN
        edge_margin = max(margin, container.TRIANGLE_EDGE_MARGIN if key == "triangle" else 0)

        def inside_check(cx: float, cy: float) -> bool:
            if use_convex:
                ok = container.point_in_convex_polygon((cx, cy), vertices)
            else:
                ok = container.point_in_polygon_ray((cx, cy), vertices)
            if not ok:
                return False
            return container.min_distance_to_edges((cx, cy), vertices) >= edge_margin

        bounds = (x_min, x_max, y_min, y_max)
        return inside_check, bounds
    # Fallback: rectangle inset by margin
    bounds = (x_min, x_max, y_min, y_max)

    def inside_check(cx: float, cy: float) -> bool:
        return (x_min + margin <= cx <= x_max - margin and
                y_min + margin <= cy <= y_max - margin)

    return inside_check, bounds


def render_shape_with_scatter(
    shape_el: ET.Element, motifs_dir: Path, *, seed: int | None = None
) -> str:
    """Render a shape (polygon/circle) whose content is a scatter of shapes. Positions are chosen
    so every shape fits entirely inside the boundary (no clipping unless XML supports it later)."""
    scatter_el = shape_el.find("scatter")
    if scatter_el is None:
        raise ValueError("Shape has no scatter child")
    shape_children = _scatter_shape_children(scatter_el)
    if not shape_children:
        raise ValueError("Scatter inside shape has no shape children (use repeated or explicit shapes)")
    key = (shape_el.get("key") or "square").strip().lower()
    if key not in container.SHAPES_ALL:
        raise ValueError(f"Unknown shape key: {key!r}")
    vertices, path_d, path_d_stroke, stroke_lines, symbol_transform, _ = container.get_shape_geometry(
        key, motifs_dir
    )
    bbox = container.get_shape_bbox(key, vertices, path_d)
    x_min, x_max, y_min, y_max = bbox
    # Margin and min_dist: when motifs, from motif size; else from effective count (scale_as_count or actual).
    actual_count = len(shape_children)
    effective_count = _scatter_effective_count(scatter_el, actual_count)
    uses_motifs = any(_has_motif_scale(c) for c in shape_children)
    if uses_motifs:
        layout_scale = ELEMENT_SCALE_SCATTER
        max_scale = max(_placement_scale(c, layout_scale) for c in shape_children)
    else:
        layout_scale = _scatter_scale_for_count(effective_count) * SCATTER_INSIDE_SHAPE_SCALE_FACTOR
        max_scale = layout_scale
    shape_radius = 50.0 * max_scale
    margin = shape_radius + 1.0  # buffer so shape fits inside boundary; we do not clip
    min_dist = 100.0 * max_scale
    inside_check, bounds = _scatter_inside_shape_inside_check(key, vertices, margin)
    try:
        positions = container.random_positions(
            actual_count,
            min_dist=min_dist,
            seed=seed,
            inside_check=inside_check,
            bounds=bounds,
            max_attempts=12000,
        )
    except SystemExit as e:
        raise ValueError(f"Could not place {actual_count} shapes inside {key!r}: {e}") from e
    # Single scale per shape from layout or motif_scale (XML); no position-based variation.
    shading = (shape_el.get("shading") or "black").strip().lower()
    opaque = (shape_el.get("opaque") or "true").strip().lower() not in ("false", "0")
    solid = {"solid_black": "#000", "black": "#000", "grey": "#808080", "grey_light": "#d0d0d0", "white_fill": "#fff"}
    solid["white"] = "#fff" if opaque else "none"
    hatch_keys = ("diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines")

    fill_attr = "none"
    shape_parts = []
    
    if shading in solid:
        fill_attr = solid[shading]
    elif shading in hatch_keys:
        unique_id = f"scatter_{seed or 0}"
        polygon_fill_defs, polygon_hatch_lines = container.hatch_continuous_defs_and_lines(
            f"hatchClip{unique_id}", shading, path_d
        )
        shape_parts.append(polygon_fill_defs)
        fill_attr = f"url(#hatchClip{unique_id})"
    
    line_type = (shape_el.get("line_type") or "solid").strip().lower()
    dash_attr = ' stroke-dasharray="8 4"' if line_type == "dashed" else (' stroke-dasharray="2 4"' if line_type == "dotted" else "")
    
    # Use path_d_stroke if present, else path_d
    stroke_d = path_d_stroke if path_d_stroke is not None else path_d
    stroke_esc = stroke_d.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    shape_parts.append(f'  <path d="{stroke_esc}" fill="{fill_attr}" stroke="#000" stroke-width="2" stroke-linejoin="miter" stroke-linecap="butt"{dash_attr} />')
    
    if stroke_lines is not None:
        shape_parts.extend([
            f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke-width="2"{dash_attr} />'
            for x1, y1, x2, y2 in stroke_lines
        ])
    
    if shading in hatch_keys:
        shape_parts.append(polygon_hatch_lines)
        
    shape_svg = "\n".join(shape_parts)
    if symbol_transform:
        shape_svg = f'  <g transform="{symbol_transform}">\n{shape_svg}\n  </g>'

    # Render motifs (fragments)
    fragments = []
    for i, (child_el, (cx, cy)) in enumerate(zip(shape_children, positions)):
        place_scale = _placement_scale(child_el, layout_scale)
        frag = _shape_to_svg_fragment(child_el, motifs_dir, str(i))
        fragments.append(_place_fragment(frag, cx, cy, place_scale))

    # Body: Shape (Background) -> Fragments (Motifs)
    body = shape_svg + "\n" + "\n".join(fragments)
    return _svg_wrapper(body, "shape-scatter")


def render_stack(stack_el: ET.Element, motifs_dir: Path, *, seed: int | None = None) -> str:
    """Render stack layout: shapes or nested stack/array/scatter, bottom to top with overlap."""
    children = [c for c in stack_el if c.tag in ("shape", "stack", "array", "scatter")]
    if len(children) < 2:
        raise ValueError("Stack must have at least 2 children")
    direction = (stack_el.get("direction") or "up").strip().lower()
    if direction not in ("up", "down", "left", "right"):
        direction = "up"
    n = len(children)
    positions = _stack_positions(n, direction, ELEMENT_SCALE_STACK)
    scale_max = _stack_scale_max_in_viewbox(n, direction, ELEMENT_SCALE_STACK)
    scale_draw = min(ELEMENT_SCALE_STACK * STACK_DRAW_SCALE_FACTOR, scale_max)
    fragments: list[str] = []
    for i, (child_el, (cx, cy)) in enumerate(zip(children, positions)):
        frag = _element_to_fragment(child_el, motifs_dir, seed=seed, unique_id=str(i))
        place_scale = _placement_scale(child_el, scale_draw)
        fragments.append(_place_fragment(frag, cx, cy, place_scale))
    body = "\n".join(fragments)
    return _svg_wrapper(body, "stack")


def render_array(array_el: ET.Element, motifs_dir: Path, *, seed: int | None = None) -> str:
    """Render array layout: rectangular, loop, or triangular; cells may be shape or nested layout."""
    atype = (array_el.get("type") or "rectangular").strip().lower()
    repeated = array_el.find("repeated")
    if repeated is not None:
        repeated_el = repeated.find("shape")
        if repeated_el is None:
            repeated_el = repeated.find("array")
        if repeated_el is None:
            repeated_el = repeated.find("stack")
        if repeated_el is None:
            repeated_el = repeated.find("scatter")
        if repeated_el is not None:
            if atype == "rectangular":
                rows = int(array_el.get("rows", "2"))
                cols = int(array_el.get("cols", "2"))
                positions = _array_positions_rectangular(rows, cols)
                scale = _array_scale_max_no_overlap(rows, cols)
            elif atype == "loop":
                path_shape = (array_el.get("path_shape") or "circle").strip().lower()
                count, positions_attr, per_edge = _loop_count_and_positions_params(array_el, path_shape, motifs_dir)
                scale_max = _array_scale_max_no_overlap_loop(count, per_edge)
                positions = _array_positions_loop(count, scale_max, path_shape=path_shape, positions_attr=positions_attr, per_edge=per_edge, motifs_dir=motifs_dir)
                scale = scale_max * LOOP_SCALE_FACTOR
            elif atype == "triangular":
                count = int(array_el.get("count", "6"))
                direction = (array_el.get("direction") or "up").strip().lower()
                positions = _array_positions_triangular(count, direction)
                scale = _array_scale_max_no_overlap_triangular(count)
            else:
                rows, cols = 2, 2
                positions = _array_positions_rectangular(rows, cols)
                scale = _array_scale_max_no_overlap(rows, cols)
            # Perpendicular rule: only for rectangular arrays (not loop/triangular); use smaller scale for nested layout
            use_perpendicular_rule = atype == "rectangular" and repeated_el.tag != "shape"
            if use_perpendicular_rule:
                nested_scale = _layout_effective_scale(repeated_el, motifs_dir, seed=seed)
                place_scale = min(scale, nested_scale) / nested_scale
            else:
                place_scale = scale
            place_scale = _placement_scale(repeated_el, place_scale)
            fragments = [
                _place_fragment(_element_to_fragment(repeated_el, motifs_dir, seed=(seed + i) if seed is not None else i, unique_id=str(i)), cx, cy, place_scale)
                for i, (cx, cy) in enumerate(positions)
            ]
            # Loop path (circle or path_shape outline) behind elements
            if atype == "loop":
                draw_path = (array_el.get("draw_path") or "false").strip().lower() == "true"
                if draw_path:
                    radius = 50.0 * (1.0 - scale_max)
                    path_line_type = (array_el.get("path_line_type") or "solid").strip().lower()
                    path_svg = _loop_path_svg(path_shape, radius, path_line_type, motifs_dir)
                    fragments.insert(0, '  <g id="loop-path">\n' + path_svg + '\n  </g>')
            # Mesh for repeated rectangular/triangular (no nulls)
            draw_mesh = (array_el.get("draw_mesh") or "false").strip().lower() == "true"
            if draw_mesh and atype in ("rectangular", "triangular") and positions:
                mesh_line_type = (array_el.get("mesh_line_type") or "solid").strip().lower()
                if mesh_line_type not in ("solid", "dashed", "dotted", "bold"):
                    mesh_line_type = "solid"
                is_non_null = [True] * len(positions)
                if atype == "rectangular":
                    r, c = int(array_el.get("rows", "2")), int(array_el.get("cols", "2"))
                    segments = _mesh_segments_rectangular(r, c, positions, is_non_null)
                else:
                    rows_list, _, _ = _triangular_rows_and_cols(len(positions))
                    segments = _mesh_segments_triangular(positions, rows_list, is_non_null)
                mesh_svg = _mesh_svg_group(segments, mesh_line_type)
                fragments.insert(0, '  <g id="array-mesh">\n' + mesh_svg + '\n  </g>')
            return _svg_wrapper("\n".join(fragments), "array")
    # Explicit children (shape, stack, array, scatter, or null — null reserves slot, nothing drawn)
    children = [c for c in array_el if c.tag in ("shape", "stack", "array", "scatter", "null")]
    if atype == "rectangular":
        rows = int(array_el.get("rows", "2"))
        cols = int(array_el.get("cols", "2"))
        positions = _array_positions_rectangular(rows, cols)
        scale = _array_scale_max_no_overlap(rows, cols)
        n_positions = rows * cols
    elif atype == "loop":
        path_shape = (array_el.get("path_shape") or "circle").strip().lower()
        count, positions_attr, per_edge = _loop_count_and_positions_params(array_el, path_shape, motifs_dir)
        scale_max = _array_scale_max_no_overlap_loop(count, per_edge)
        positions = _array_positions_loop(count, scale_max, path_shape=path_shape, positions_attr=positions_attr, per_edge=per_edge, motifs_dir=motifs_dir)
        scale = scale_max * LOOP_SCALE_FACTOR
        n_positions = count
    elif atype == "triangular":
        count = int(array_el.get("count", "6"))
        direction = (array_el.get("direction") or "up").strip().lower()
        positions = _array_positions_triangular(count, direction)
        scale = _array_scale_max_no_overlap_triangular(count)
        n_positions = count
    else:
        rows, cols = 2, 2
        positions = _array_positions_rectangular(rows, cols)
        scale = _array_scale_max_no_overlap(rows, cols)
        n_positions = rows * cols
    # Align children to positions by index (null skips placing; one position per child)
    positions = positions[: n_positions]
    children = children[: n_positions]
    fragments = []
    for i, (child_el, (cx, cy)) in enumerate(zip(children, positions)):
        if child_el.tag == "null":
            continue
        frag = _element_to_fragment(child_el, motifs_dir, seed=(seed + i) if seed is not None else i, unique_id=str(i))
        # Perpendicular rule: only for rectangular arrays (not loop/triangular); use smaller scale for nested layout
        use_perpendicular_rule = atype == "rectangular" and child_el.tag != "shape"
        if use_perpendicular_rule:
            nested_scale = _layout_effective_scale(child_el, motifs_dir, seed=(seed + i) if seed is not None else i)
            place_scale = min(scale, nested_scale) / nested_scale
        else:
            place_scale = scale
        place_scale = _placement_scale(child_el, place_scale)
        fragments.append(_place_fragment(frag, cx, cy, place_scale))
    # Loop path (circle or path_shape outline) behind elements
    if atype == "loop" and positions:
        draw_path = (array_el.get("draw_path") or "false").strip().lower() == "true"
        if draw_path:
            scale_max = _array_scale_max_no_overlap_loop(n_positions, per_edge)
            radius = 50.0 * (1.0 - scale_max)
            path_line_type = (array_el.get("path_line_type") or "solid").strip().lower()
            path_svg = _loop_path_svg(path_shape, radius, path_line_type, motifs_dir)
            fragments.insert(0, '  <g id="loop-path">\n' + path_svg + '\n  </g>')
    # Mesh (rectangular and triangular only): centre-to-centre lines, behind content
    draw_mesh = (array_el.get("draw_mesh") or "false").strip().lower() == "true"
    if draw_mesh and atype in ("rectangular", "triangular") and positions:
        draw_full_grid = (array_el.get("draw_full_grid") or "true").strip().lower() == "true"
        mesh_line_type = (array_el.get("mesh_line_type") or "solid").strip().lower()
        if mesh_line_type not in ("solid", "dashed", "dotted", "bold"):
            mesh_line_type = "solid"
        is_non_null = [True] * len(positions) if draw_full_grid else [children[i].tag != "null" for i in range(len(children))]
        if atype == "rectangular":
            segments = _mesh_segments_rectangular(rows, cols, positions, is_non_null)
        else:
            rows_list, _, _ = _triangular_rows_and_cols(n_positions)
            segments = _mesh_segments_triangular(positions, rows_list, is_non_null)
        mesh_svg = _mesh_svg_group(segments, mesh_line_type)
        fragments.insert(0, '  <g id="array-mesh">\n' + mesh_svg + '\n  </g>')
    return _svg_wrapper("\n".join(fragments), "array")


def _svg_wrapper(body: str, comment: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">\n'
        f"  <!-- {comment} -->\n"
        f"{body}\n"
        "</svg>"
    )


def render_diagram_to_svg(
    diagram_el: ET.Element,
    *,
    motifs_dir: Path | None = None,
    seed: int | None = None,
) -> str:
    """
    Render one diagram (single shape, scatter, stack, or array) to SVG string.
    Array and stack may contain nested layout (stack/array/scatter).
    """
    root = _get_diagram_root(diagram_el)
    if root is None:
        raise ValueError("Diagram has no shape, scatter, stack, or array root")
    if motifs_dir is None:
        motifs_dir = _REPO_ROOT / "nvr-symbols"

    if root.tag == "shape":
        if root.find("scatter") is not None:
            return render_shape_with_scatter(root, motifs_dir, seed=seed)
        if _has_nested_layout(root):
            raise ValueError("Shape has nested layout (other than scatter); not supported in this version")
        return single_shape.render_shape_to_svg(root, motifs_dir=motifs_dir)
    if root.tag == "scatter":
        return render_scatter(root, motifs_dir, seed=seed)
    if root.tag == "stack":
        return render_stack(root, motifs_dir, seed=seed)
    if root.tag == "array":
        return render_array(root, motifs_dir, seed=seed)
    raise ValueError(f"Unsupported diagram root: {root.tag}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render question/diagrams XML to SVG (all layout types, nesting supported)."
    )
    parser.add_argument("xml_path", type=Path, help="Path to question XML or diagrams XML.")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output path: .svg file (single diagram) or directory (multiple).",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="diagram",
        help="Filename prefix when writing multiple SVGs (default: diagram).",
    )
    parser.add_argument(
        "--motifs-dir",
        type=Path,
        default=None,
        help="Directory for symbol shape SVGs (default: repo nvr-symbols).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for scatter placement.",
    )
    args = parser.parse_args()

    xml_path = args.xml_path
    if not xml_path.is_file():
        xml_path = _PROJECT_ROOT / xml_path
    if not xml_path.is_file():
        print(f"Error: not a file: {xml_path}", file=sys.stderr)
        return 1

    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        return 1

    root = tree.getroot()
    diagrams = list(_iter_diagrams(root))
    if not diagrams:
        print("No diagrams found in document.", file=sys.stderr)
        return 0

    motifs_dir = args.motifs_dir
    if motifs_dir is None:
        motifs_dir = _REPO_ROOT / "nvr-symbols"
    out = args.output
    if out is None:
        out = _PROJECT_ROOT / "output"
    out = out.resolve()
    prefix = args.prefix
    seed = args.seed

    if len(diagrams) == 1 and out.suffix.lower() == ".svg":
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            svg = render_diagram_to_svg(diagrams[0][0], motifs_dir=motifs_dir, seed=seed)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        out.write_text(svg, encoding="utf-8")
        print(f"Wrote {out}")
        return 0

    if out.suffix.lower() == ".svg":
        out = out.parent
    out.mkdir(parents=True, exist_ok=True)

    for i, (diagram_el, label) in enumerate(diagrams):
        safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(label))
        path = out / f"{prefix}-{safe_label}.svg"
        try:
            svg = render_diagram_to_svg(diagram_el, motifs_dir=motifs_dir, seed=seed)
        except ValueError as e:
            print(f"Skipping {label}: {e}", file=sys.stderr)
            continue
        path.write_text(svg, encoding="utf-8")
        print(f"Wrote {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
