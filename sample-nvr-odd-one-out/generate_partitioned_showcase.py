#!/usr/bin/env python3
"""
Generate a showcase of partition types with varied shading (picture-based-questions-guide.md §3.9).
All shapes use solid outlines only. Produces individual SVGs per partition type and one combined
grid SVG (partitioned-showcase.svg) that displays them together.

Outputs to script_dir/output/:
  - partitioned-showcase-horizontal.svg, -vertical.svg, -diagonal_slash.svg, -diagonal_backslash.svg,
    -concentric.svg, -segmented.svg
  - partitioned-showcase.svg (2×3 grid referencing the above)
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR = SCRIPT_DIR / "generate_shape_container_svg.py"
OUTPUT_DIR = SCRIPT_DIR / "output"

# (partition, shape, partition_sections, section_fills) — varied shading per type
SHOWCASE_CELLS = [
    ("horizontal", "square", "0,33.33,66.67,100", "white,grey,diagonal_slash,vertical_lines"),
    ("vertical", "triangle", "0,50,100", "grey,white,horizontal_lines"),
    ("diagonal_slash", "hexagon", "0,33.33,66.67,100", "white,grey,diagonal_backslash"),
    ("diagonal_backslash", "octagon", "0,50,100", "diagonal_slash,white,grey"),
    ("concentric", "circle", "0,40,60,100", "white,grey,diagonal_slash,grey"),
    ("segmented", "circle", "0,16.67,33.33,50,66.67,83.33,100", "white,grey,vertical_lines,grey,white,grey"),
]


def run_cell(partition: str, shape: str, output: Path, partition_sections: str | None, section_fills: str) -> None:
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
    print(f"  {output.name}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating partitioned showcase (solid outlines, varied shading)...")

    filenames = []
    for partition, shape, partition_sections, section_fills in SHOWCASE_CELLS:
        name = f"partitioned-showcase-{partition}.svg"
        out = OUTPUT_DIR / name
        filenames.append(name)
        run_cell(partition, shape, out, partition_sections, section_fills)

    # Combined 2×3 grid: each cell 100×100, gap 8, margin 8. viewBox 0 0 (2*100 + 2*8 + 2*margin) (3*100 + 2*8 + 2*margin)
    cols, rows = 2, 3
    cell_size = 100
    gap = 8
    margin = 8
    width = 2 * margin + cols * cell_size + (cols - 1) * gap
    height = 2 * margin + rows * cell_size + (rows - 1) * gap

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {width:.0f} {height:.0f}">',
        "  <!-- Showcase: partition types with varied shading, solid outlines -->",
    ]
    for idx, name in enumerate(filenames):
        row, col = divmod(idx, cols)
        x = margin + col * (cell_size + gap)
        y = margin + row * (cell_size + gap)
        lines.append(f'  <image xlink:href="{name}" x="{x:.0f}" y="{y:.0f}" width="{cell_size}" height="{cell_size}"/>')
    lines.append("</svg>")

    combined = OUTPUT_DIR / "partitioned-showcase.svg"
    combined.write_text("\n".join(lines), encoding="utf-8")
    print(f"  {combined.name} (grid of {len(filenames)} shapes)")

    print("Done.")


if __name__ == "__main__":
    main()
