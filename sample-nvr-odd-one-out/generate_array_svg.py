#!/usr/bin/env python3
"""
Generate an SVG of an array of shape containers (picture-based-questions-guide.md, Concepts → Arrays).

An array is a regular grid of shapes with even spacing, horizontally aligned. Shapes are scaled
uniformly so the array fits inside the diagram bounding box (viewBox 0 0 100 100).

Usage:
  python generate_array_svg.py 2 2 triangle -o output/array-2x2-triangles.svg
  python generate_array_svg.py 3 2 regular -o output/array-3x2-regular.svg
  python generate_array_svg.py 2 2 --shapes "triangle,square,circle,pentagon" -o output/array-2x2-mixed.svg

Heterogeneous: use --shapes "s1,s2,..." (row-major, length = rows*cols).
Per-cell style: --fills "f1,f2,..." (none, white, grey); --line-styles "solid,dashed,dotted,..." (guide §3.3). All borders black.
Spacing: --gap and --margin (defaults: 8).
"""

import argparse
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR_NAME = "output"

# Line types from guide §3.3; stroke-dasharray matches generate_shape_container_svg
LINE_STYLES = ("solid", "dashed", "dotted")
STROKE_DASHARRAY = {"solid": "", "dashed": "8 4", "dotted": "2 4"}


def _import_shape_generator():
    """Import shape geometry from generate_shape_container_svg (same directory)."""
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    import generate_shape_container_svg as gen
    return gen


def _normalize_fill(s: str) -> str:
    """Map fill keyword to SVG value (solid only)."""
    s = (s or "").strip().lower()
    if s in ("none", ""):
        return "none"
    if s == "white":
        return "#fff"
    if s == "grey":
        return "#808080"
    return s  # assume #hex or other valid SVG


def _parse_list_arg(value: str | None, n_cells: int, default_single: str) -> list[str]:
    """Parse comma-separated list; length must be 1 or n_cells. Return list of length n_cells."""
    if not value:
        return [default_single] * n_cells
    parts = [p.strip() for p in value.split(",")]
    if len(parts) == 1:
        return parts * n_cells
    if len(parts) != n_cells:
        raise ValueError(f"Expected 1 or {n_cells} values, got {len(parts)}")
    return parts


def build_array_svg(
    rows: int,
    cols: int,
    shape: str | None = None,
    shapes: list[str] | None = None,
    fill: str = "none",
    fills: list[str] | None = None,
    line_style: str = "solid",
    line_styles: list[str] | None = None,
    stroke_width: float = 2.0,
    margin: float = 8.0,
    gap: float = 8.0,
) -> str:
    """
    Build SVG for an array of shapes in viewBox 0 0 100 100. All borders black; line type per cell: solid, dashed, dotted (guide §3.3).
    Either shape (single shape for all cells) or shapes (one per cell, row-major) must be set.
    fills / line_styles: length 1 or rows*cols for per-cell style.
    """
    gen = _import_shape_generator()
    get_shape_geometry = gen.get_shape_geometry
    get_shape_bbox = gen.get_shape_bbox

    n_cells = rows * cols
    if shapes is not None:
        if len(shapes) != n_cells:
            raise ValueError(f"shapes length {len(shapes)} != rows*cols {n_cells}")
        if shape is not None:
            raise ValueError("Provide either shape or shapes, not both.")
    elif shape is not None:
        shapes = [shape] * n_cells
    else:
        raise ValueError("Provide shape or shapes.")

    fill_list = fills if fills is not None else [fill] * n_cells
    if len(fill_list) == 1:
        fill_list = fill_list * n_cells
    if len(fill_list) != n_cells:
        raise ValueError(f"fills length {len(fill_list)} must be 1 or {n_cells}")
    fill_list = [_normalize_fill(f) for f in fill_list]

    style_list = line_styles if line_styles is not None else [line_style] * n_cells
    if len(style_list) == 1:
        style_list = style_list * n_cells
    if len(style_list) != n_cells:
        raise ValueError(f"line_styles length {len(style_list)} must be 1 or {n_cells}")
    for s in style_list:
        if s not in STROKE_DASHARRAY:
            raise ValueError(f"line_style must be one of {list(LINE_STYLES)}, got {s!r}")

    # Usable area after margin
    usable_w = 100.0 - 2 * margin
    usable_h = 100.0 - 2 * margin
    cell_w = (usable_w - (cols - 1) * gap) / cols if cols else 0
    cell_h = (usable_h - (rows - 1) * gap) / rows if rows else 0

    stroke = "#000"
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">',
        f"  <!-- array {rows}x{cols} -->",
    ]

    for idx in range(n_cells):
        row, col = divmod(idx, cols)
        cell_shape = shapes[idx].strip().lower()
        cell_fill = fill_list[idx]
        cell_line_style = style_list[idx].strip().lower()
        dash = STROKE_DASHARRAY.get(cell_line_style, "")
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        vertices, path_d, _path_d_stroke, stroke_lines = get_shape_geometry(cell_shape)
        x_min, x_max, y_min, y_max = get_shape_bbox(cell_shape, vertices, path_d)
        shape_w = x_max - x_min
        shape_h = y_max - y_min
        shape_cx = 50.0
        shape_cy = 50.0
        scale = min(cell_w / shape_w, cell_h / shape_h) if (shape_w > 0 and shape_h > 0) else 1.0

        cx = margin + col * (cell_w + gap) + cell_w / 2
        cy = margin + row * (cell_h + gap) + cell_h / 2
        lines.append(f'  <g transform="translate({cx:.2f},{cy:.2f}) scale({scale:.4f}) translate({-shape_cx:.2f},{-shape_cy:.2f})">')
        lines.append(f'    <path d="{path_d}" fill="{cell_fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr}/>')
        if stroke_lines:
            for x1, y1, x2, y2 in stroke_lines:
                lines.append(f'    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr}/>')
        lines.append("  </g>")

    lines.append("</svg>")
    return "\n".join(lines)


def main() -> None:
    gen = _import_shape_generator()
    shapes_all = gen.SHAPES_ALL
    shapes_regular = gen.SHAPES_REGULAR

    parser = argparse.ArgumentParser(
        description="Generate an SVG array of shape containers (grid with even spacing, scaled to fit)."
    )
    parser.add_argument("rows", type=int, help="Number of rows")
    parser.add_argument("cols", type=int, help="Number of columns")
    parser.add_argument(
        "shape",
        type=str,
        nargs="?",
        default=None,
        help="Shape name (e.g. triangle, square, circle) or 'regular' for random; omit if using --shapes",
    )
    parser.add_argument("--shapes", type=str, default=None, help="Heterogeneous: comma-separated shapes (row-major), length = rows*cols")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output path (default: output/array-{rows}x{cols}-{shape}.svg)")
    parser.add_argument("--gap", type=float, default=8.0, help="Gap between cells (default: 8)")
    parser.add_argument("--margin", type=float, default=8.0, help="Margin around array (default: 8)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (for shape=regular)")
    parser.add_argument("--fill", type=str, default="none", help="Fill for all shapes (default: none)")
    parser.add_argument("--fills", type=str, default=None, help="Per-cell fill: comma-separated (none, white, grey), length 1 or rows*cols")
    parser.add_argument("--line-style", type=str, default="solid", choices=list(LINE_STYLES), help="Outline style for all (default: solid)")
    parser.add_argument("--line-styles", type=str, default=None, help="Per-cell line type: comma-separated solid,dashed,dotted, length 1 or rows*cols")
    parser.add_argument("--stroke-width", type=float, default=2.0, help="Border width for all (default: 2)")
    args = parser.parse_args()

    if args.rows < 1 or args.cols < 1:
        raise SystemExit("Rows and cols must be at least 1.")

    shapes_arg = None
    single_shape = None
    if args.shapes:
        shapes_arg = [s.strip().lower() for s in args.shapes.split(",")]
        n_cells = args.rows * args.cols
        if len(shapes_arg) != n_cells:
            raise SystemExit(f"--shapes has {len(shapes_arg)} items; need rows*cols = {n_cells}.")
        for s in shapes_arg:
            if s not in shapes_all:
                raise SystemExit(f"Unknown shape in --shapes: {s!r}. Use: {', '.join(shapes_all)}.")
    elif args.shape:
        single_shape = (args.shape or "").strip().lower()
        if single_shape == "regular":
            rng = random.Random(args.seed)
            single_shape = rng.choice(shapes_regular)
            if args.seed is not None:
                print(f"Seed {args.seed} → shape={single_shape}")
        elif single_shape not in shapes_all:
            raise SystemExit(f"Unknown shape: {args.shape}. Use one of: {', '.join(shapes_all)}, or 'regular'.")
    else:
        raise SystemExit("Provide a shape name or --shapes for heterogeneous array.")

    fills_list = None
    if args.fills:
        fills_list = _parse_list_arg(args.fills, args.rows * args.cols, args.fill)
    line_styles_list = None
    if args.line_styles:
        line_styles_list = _parse_list_arg(args.line_styles, args.rows * args.cols, args.line_style)
        for s in line_styles_list:
            if s not in LINE_STYLES:
                raise SystemExit(f"Unknown line style {s!r}. Use: {', '.join(LINE_STYLES)}.")

    svg = build_array_svg(
        rows=args.rows,
        cols=args.cols,
        shape=single_shape,
        shapes=shapes_arg,
        fill=args.fill,
        fills=fills_list,
        line_style=args.line_style,
        line_styles=line_styles_list,
        stroke_width=args.stroke_width,
        margin=args.margin,
        gap=args.gap,
    )

    out = args.output
    if out is None:
        out_dir = SCRIPT_DIR / OUTPUT_DIR_NAME
        out_dir.mkdir(parents=True, exist_ok=True)
        label = "mixed" if shapes_arg else single_shape
        out = out_dir / f"array-{args.rows}x{args.cols}-{label}.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    desc = "mixed shapes" if shapes_arg else single_shape
    print(f"Wrote {out} ({args.rows}x{args.cols} array of {desc}).")


if __name__ == "__main__":
    main()
