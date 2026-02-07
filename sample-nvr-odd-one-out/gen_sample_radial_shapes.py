#!/usr/bin/env python3
"""
Generate one SVG per shape, each partitioned into radial sections (question-gen/QUESTION-GENERATION-DESIGN.md §4, Partitioned shapes).

Uses the most natural number of radial sections per shape:
  - Regular polygons: same as side count (triangle→3, square→4, pentagon→5, hexagon→6, heptagon→7, octagon→8).
  - Circle: 6 sections.
  - Semicircle: 3 sections (from circle centre on chord; arc from pi to 2*pi).
  - Irregular (right_angled_triangle, rectangle, cross, arrow): 4 quadrants.
  - Star (symbol): 5 radial sections (rotational symmetry order 5).
  - Other symbols (plus, times, club, heart, diamond, spade): 4 quadrants.

Section fills use a variety: white, grey, grey_light, solid_black, diagonal_slash, horizontal_lines, vertical_lines, diagonal_backslash (cycled per section).

Outputs to script_dir/output/ with names: radial-<shape>.svg
Requires nvr-symbols (../nvr-symbols) for symbol shapes (plus, times, club, heart, diamond, spade, star).
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR = SCRIPT_DIR / "lib" / "nvr_draw_container_svg.py"
OUTPUT_DIR = SCRIPT_DIR / "output"
MOTIFS_DIR = SCRIPT_DIR.parent / "nvr-symbols"

# Fill keys for variety (cycle per section)
SECTION_FILLS = [
    "white",
    "grey",
    "grey_light",
    "solid_black",
    "diagonal_slash",
    "horizontal_lines",
    "vertical_lines",
    "diagonal_backslash",
]

# Shapes that need --motifs-dir (load from nvr-symbols)
SHAPES_SYMBOLS = {"plus", "times", "club", "heart", "diamond", "spade", "star"}

# (shape, num_radial_sections) — natural count per shape; irregulars and symbols (except star) use 4 quadrants; star uses 5
RADIAL_SHAPES = [
    ("circle", 6),
    ("triangle", 3),
    ("square", 4),
    ("pentagon", 5),
    ("hexagon", 6),
    ("heptagon", 7),
    ("octagon", 8),
    ("semicircle", 3),
    ("right_angled_triangle", 4),
    ("rectangle", 4),
    ("cross", 4),
    ("arrow", 4),
    ("plus", 4),
    ("times", 4),
    ("club", 4),
    ("heart", 4),
    ("diamond", 4),
    ("spade", 4),
    ("star", 5),
]


def section_bounds_string(n: int) -> str:
    """Return comma-separated bounds 0, step, 2*step, ..., 100 for n sections."""
    if n < 1:
        return "0,100"
    step = 100.0 / n
    points = [0.0] + [round(k * step, 2) for k in range(1, n)] + [100.0]
    return ",".join(str(int(p)) if p == int(p) else f"{p:.2f}" for p in points)


def section_fills_string(n: int) -> str:
    """Return n fill keys cycled from SECTION_FILLS."""
    return ",".join(SECTION_FILLS[i % len(SECTION_FILLS)] for i in range(n))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating radial-partitioned shape samples (guide §3.9)...")

    for shape, num_sections in RADIAL_SHAPES:
        bounds = section_bounds_string(num_sections)
        fills = section_fills_string(num_sections)
        out = OUTPUT_DIR / f"radial-{shape}.svg"
        cmd = [
            sys.executable,
            str(GENERATOR),
            "--partition", "radial",
            "--shape", shape,
            "--partition-sections", bounds,
            "--section-fills", fills,
            "-o", str(out),
        ]
        if shape in SHAPES_SYMBOLS:
            cmd.extend(["--motifs-dir", str(MOTIFS_DIR)])
        subprocess.run(cmd, check=True, cwd=SCRIPT_DIR)
        print(f"  {out.name}")

    print("Done.")


if __name__ == "__main__":
    main()
