#!/usr/bin/env python3
"""
Generate one SVG per shape, each partitioned with a linear direction (vertical, horizontal, or diagonal)
(picture-based-questions-guide.md §3.9).

For each shape:
  - Partition direction is chosen at random: vertical, horizontal, or diagonal (diagonal_slash or diagonal_backslash).
  - Circle and semicircle support only vertical or horizontal (diagonal requires a polygon).
  - Each partition has at least 3 sections (random 3–6 sections per shape).

Section fills use a variety: white, grey, grey_light, solid_black, diagonal_slash, horizontal_lines, vertical_lines, diagonal_backslash (cycled per section).

Outputs to script_dir/output/ with names: linear-<shape>.svg
Requires nvr-symbols (../nvr-symbols) for symbol shapes (plus, times, club, heart, diamond, spade, star).
"""

import random
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

# Shapes that are circle/semicircle: only vertical or horizontal partition
SHAPES_NO_DIAGONAL = {"circle", "semicircle"}

# All shapes (one output per shape)
SHAPES = [
    "circle",
    "triangle",
    "square",
    "pentagon",
    "hexagon",
    "heptagon",
    "octagon",
    "semicircle",
    "right_angled_triangle",
    "rectangle",
    "cross",
    "arrow",
    "plus",
    "times",
    "club",
    "heart",
    "diamond",
    "spade",
    "star",
]

MIN_SECTIONS = 3
MAX_SECTIONS = 6


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

    directions_all = ["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"]
    directions_no_diagonal = ["vertical", "horizontal"]

    print("Generating linear-partitioned shape samples (guide §3.9)...")

    for shape in SHAPES:
        if shape in SHAPES_NO_DIAGONAL:
            direction = random.choice(directions_no_diagonal)
        else:
            direction = random.choice(directions_all)

        num_sections = random.randint(MIN_SECTIONS, MAX_SECTIONS)
        bounds = section_bounds_string(num_sections)
        fills = section_fills_string(num_sections)
        out = OUTPUT_DIR / f"linear-{shape}.svg"
        cmd = [
            sys.executable,
            str(GENERATOR),
            "--partition",
            direction,
            "--shape",
            shape,
            "--partition-sections",
            bounds,
            "--section-fills",
            fills,
            "-o",
            str(out),
        ]
        if shape in SHAPES_SYMBOLS:
            cmd.extend(["--motifs-dir", str(MOTIFS_DIR)])
        subprocess.run(cmd, check=True, cwd=SCRIPT_DIR)
        print(f"  {out.name} ({direction}, {num_sections} sections)")

    print("Done.")


if __name__ == "__main__":
    main()
