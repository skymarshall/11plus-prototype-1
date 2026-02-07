#!/usr/bin/env python3
"""
Generate 2×2 and 3×2 arrays of partitioned shapes with varied shape, partition type,
and shading per cell (question-gen/QUESTION-GENERATION-DESIGN.md §4, Partitioned shapes). Solid outlines only.

Each cell is generated as a separate SVG (viewBox 0 0 100 100), then inlined into
array-2x2-partitioned.svg and array-3x2-partitioned.svg so one file shows all shapes
(viewers often only load one external <image> when opening from file).

Outputs to script_dir/output/:
  - array-2x2-partitioned-0.svg .. array-2x2-partitioned-3.svg (cell assets)
  - array-2x2-partitioned.svg (single SVG with all 4 cells inlined)
  - array-3x2-partitioned-0.svg .. array-3x2-partitioned-5.svg (cell assets)
  - array-3x2-partitioned.svg (single SVG with all 6 cells inlined)
"""

import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR = SCRIPT_DIR / "nvr_draw_container_svg.py"
# When in lib/, write arrays to sample-nvr-odd-one-out/output.
OUTPUT_DIR = SCRIPT_DIR.parent / "output"

CELL_SIZE = 100
GAP = 8
MARGIN = 8

# 2×2: (partition, shape, partition_sections, section_fills)
ARRAY_2X2 = [
    ("horizontal", "square", "0,33.33,66.67,100", "white,grey,diagonal_slash"),
    ("concentric", "circle", "0,50,100", "white,grey"),
    ("diagonal_slash", "hexagon", "0,50,100", "grey,white"),
    ("radial", "triangle", "0,33.33,66.67,100", "white,grey,horizontal_lines"),
]

# 3×2: (partition, shape, partition_sections, section_fills)
ARRAY_3X2 = [
    ("horizontal", "square", "0,33.33,66.67,100", "white,grey,diagonal_slash"),
    ("concentric", "circle", "0,40,60,100", "grey,white,diagonal_slash"),
    ("diagonal_backslash", "hexagon", "0,50,100", "white,grey"),
    ("vertical", "octagon", "0,33.33,66.67,100", "grey,white,vertical_lines"),
    ("radial", "triangle", "0,33.33,66.67,100", "white,grey,white"),
    ("diagonal_slash", "pentagon", "0,50,100", "white,grey"),
]


def run_cell(
    partition: str,
    shape: str,
    output: Path,
    partition_sections: str | None,
    section_fills: str,
) -> None:
    cmd = [
        sys.executable,
        str(GENERATOR),
        "--partition", partition,
        "--shape", shape,
        "--line-style", "solid",
        "-o", str(output),
    ]
    if partition_sections:
        cmd.extend(["--partition-sections", partition_sections])
    cmd.extend(["--section-fills", section_fills])
    subprocess.run(cmd, check=True, cwd=SCRIPT_DIR)


def _inline_cell_svg(cell_path: Path, cell_idx: int, x: float, y: float) -> str:
    """Read cell SVG, prefix def IDs and url(#...) refs, return <g transform="...">...</g>."""
    text = cell_path.read_text(encoding="utf-8")
    match = re.search(r"<svg[^>]*>(.*)</svg>", text, re.DOTALL)
    if not match:
        return f'  <!-- cell {cell_idx}: failed to parse -->'
    inner = match.group(1).strip()
    prefix = f"cell{cell_idx}_"
    inner = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{prefix}{m.group(1)}"', inner)
    inner = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{prefix}{m.group(1)})", inner)
    return f'  <g transform="translate({x:.0f},{y:.0f})">\n' + "\n".join("    " + line for line in inner.split("\n")) + "\n  </g>"


def write_grid_svg(cols: int, rows: int, cell_filenames: list[str], out_path: Path) -> None:
    width = 2 * MARGIN + cols * CELL_SIZE + (cols - 1) * GAP
    height = 2 * MARGIN + rows * CELL_SIZE + (rows - 1) * GAP
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">',
        f"  <!-- {cols}×{rows} array of partitioned shapes, varied shading, solid outlines (inlined) -->",
    ]
    for idx, name in enumerate(cell_filenames):
        row, col = divmod(idx, cols)
        x = MARGIN + col * (CELL_SIZE + GAP)
        y = MARGIN + row * (CELL_SIZE + GAP)
        cell_path = out_path.parent / name
        lines.append(_inline_cell_svg(cell_path, idx, x, y))
    lines.append("</svg>")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating 2×2 array of partitioned shapes (varied shape, partition, shading)...")
    names_2x2 = []
    for i, (partition, shape, sections, fills) in enumerate(ARRAY_2X2):
        name = f"array-2x2-partitioned-{i}.svg"
        out = OUTPUT_DIR / name
        names_2x2.append(name)
        run_cell(partition, shape, out, sections, fills)
        print(f"  {name} ({shape}, {partition})")
    write_grid_svg(2, 2, names_2x2, OUTPUT_DIR / "array-2x2-partitioned.svg")
    print("  array-2x2-partitioned.svg")

    print("Generating 3×2 array of partitioned shapes (varied shape, partition, shading)...")
    names_3x2 = []
    for i, (partition, shape, sections, fills) in enumerate(ARRAY_3X2):
        name = f"array-3x2-partitioned-{i}.svg"
        out = OUTPUT_DIR / name
        names_3x2.append(name)
        run_cell(partition, shape, out, sections, fills)
        print(f"  {name} ({shape}, {partition})")
    write_grid_svg(2, 3, names_3x2, OUTPUT_DIR / "array-3x2-partitioned.svg")
    print("  array-3x2-partitioned.svg")

    print("Done.")


if __name__ == "__main__":
    main()
