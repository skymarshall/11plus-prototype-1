"""
Render a single shape container (optionally partitioned) to SVG.

Uses nvr_draw_container_svg in this directory for drawing. Supports only shapes
with no nested layout (no chaotic, stack, or array inside). See question-gen
QUESTION-XML-SPECIFICATION.md §6 (Shape) and §7 (Partition).
"""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

import nvr_draw_container_svg as container

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent


# XML partition type "diagonal" → container uses diagonal_slash / diagonal_backslash; default slash
PARTITION_TYPE_MAP = {
    "horizontal": "horizontal",
    "vertical": "vertical",
    "diagonal": "diagonal_slash",
    "concentric": "concentric",
    "radial": "radial",
}


def _has_nested_layout(shape_el: ET.Element) -> bool:
    """True if shape has chaotic, stack, or array as a child."""
    for tag in ("chaotic", "stack", "array"):
        if shape_el.find(tag) is not None:
            return True
    return False


def _parse_partition(partition_el: ET.Element) -> tuple[str, list[tuple[float, float]], list[str]]:
    """Extract partition type, section_bounds (lo, hi), and section_fills (shading keys)."""
    ptype = (partition_el.get("type") or "").strip().lower()
    if ptype not in PARTITION_TYPE_MAP and ptype not in ("diagonal_slash", "diagonal_backslash"):
        raise ValueError(f"Unknown partition type: {ptype!r}")
    partition_direction = PARTITION_TYPE_MAP.get(ptype, ptype)

    section_bounds: list[tuple[float, float]] = []
    section_fills: list[str] = []
    for sec in partition_el.findall("section"):
        low = float(sec.get("low", 0))
        high = float(sec.get("high", 100))
        shading = (sec.get("shading") or "white").strip().lower()
        if shading == "null":
            shading = "null"
        section_bounds.append((low, high))
        section_fills.append(shading)

    if not section_bounds:
        raise ValueError("Partition must have at least one section")
    return partition_direction, section_bounds, section_fills


def render_shape_to_svg(
    shape_el: ET.Element,
    *,
    motifs_dir: Path | None = None,
) -> str:
    """
    Render a single <shape> element (no nested layout) to an SVG string.

    - shape_el: XML Element with tag "shape", attributes key, optional line_type, shading.
    - Optional partition child: type + section(s) with low, high, shading.
    - motifs_dir: Passed to container for symbol shapes (plus, times, club, etc.). Default: repo root nvr-symbols.

    Returns SVG document string (viewBox 0 0 100 100).
    """
    if shape_el.tag != "shape":
        raise ValueError(f"Expected <shape>, got <{shape_el.tag}>")
    if _has_nested_layout(shape_el):
        raise ValueError("Shape has nested layout (chaotic/stack/array); only single shape (optionally partitioned) is supported")

    key = (shape_el.get("key") or "").strip().lower()
    if not key:
        raise ValueError("Shape key is required")
    if key not in container.SHAPES_ALL:
        raise ValueError(f"Unknown shape key: {key!r}. Supported: {', '.join(container.SHAPES_ALL)}")

    line_type = (shape_el.get("line_type") or "solid").strip().lower()
    if line_type not in ("solid", "dashed", "dotted"):
        line_type = "solid"
    shading = (shape_el.get("shading") or "white").strip().lower()

    if motifs_dir is None:
        motifs_dir = _REPO_ROOT / "nvr-symbols"

    vertices, path_d, path_d_stroke, stroke_lines, symbol_transform, symbol_path_element = container.get_shape_geometry(
        key, motifs_dir
    )
    bbox = container.get_shape_bbox(key, vertices, path_d)

    partition_el = shape_el.find("partition")
    if partition_el is not None:
        partition_direction, section_bounds, section_fills = _parse_partition(partition_el)
        partition_defs, partition_fill_content, partition_lines, partition_paths = container.build_partitioned_sections(
            key,
            path_d,
            vertices,
            bbox,
            partition_direction,
            section_bounds,
            section_fills,
            symbol_transform=symbol_transform,
            symbol_path_element=symbol_path_element,
        )
        polygon_fill = "none"
        polygon_fill_defs = None
        polygon_hatch_lines = None
    else:
        partition_defs = None
        partition_fill_content = None
        partition_lines = None
        partition_paths = None
        solid = {"solid_black": "#000", "grey": "#808080", "grey_light": "#d0d0d0", "white": "none", "white_fill": "#fff"}
        hatch_keys = ("diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines")
        if shading in solid:
            polygon_fill = solid[shading]
            polygon_fill_defs = None
            polygon_hatch_lines = None
        elif shading in hatch_keys:
            polygon_fill = "none"
            polygon_fill_defs, polygon_hatch_lines = container.hatch_continuous_defs_and_lines(
                "hatchClip", shading, path_d
            )
        else:
            polygon_fill = "none"
            polygon_fill_defs = None
            polygon_hatch_lines = None

    return container.build_svg(
        motif_content="",
        positions=[],
        motif_name="none",
        shape=key,
        path_d=path_d,
        motif_scale=1.25,
        motif_tx=-5.0,
        motif_ty=-5.0,
        path_d_stroke=path_d_stroke,
        stroke_lines=stroke_lines,
        line_style=line_type,
        polygon_fill=polygon_fill or "none",
        polygon_fill_defs=polygon_fill_defs,
        polygon_hatch_lines=polygon_hatch_lines,
        partition_defs=partition_defs,
        partition_fill_content=partition_fill_content,
        partition_lines=partition_lines,
        partition_paths=partition_paths,
        motif_fill="#000",
        symbol_transform=symbol_transform,
    )


def shape_element_from_diagram(diagram_el: ET.Element) -> ET.Element | None:
    """
    If the diagram is a single <shape> with no nested layout, return that shape element; else None.
    diagram_el is the <diagram> element whose single child is the diagram root (shape | stack | array).
    """
    if diagram_el.tag != "diagram":
        # Allow passing the diagram root (shape/stack/array) directly
        if diagram_el.tag == "shape" and not _has_nested_layout(diagram_el):
            return diagram_el
        return None
    root = next((c for c in diagram_el if c.tag in ("shape", "stack", "array")), None)
    if root is None or root.tag != "shape":
        return None
    if _has_nested_layout(root):
        return None
    return root
