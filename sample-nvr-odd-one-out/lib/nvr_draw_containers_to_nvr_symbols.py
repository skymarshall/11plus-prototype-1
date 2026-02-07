#!/usr/bin/env python3
"""
Generate one SVG per shape container (question-gen/QUESTION-GENERATION-DESIGN.md §4, Shape containers) and write
them into the nvr-symbols directory. Files are named shape-<key>.svg (outline only).
Motif and container outlines both use shape-*.svg (e.g. shape-club.svg, shape-square.svg).

Shape containers: circle, triangle, square, pentagon, hexagon, heptagon, octagon,
right_angled_triangle, rectangle, semicircle, cross, arrow.

Usage: run from sample-nvr-odd-one-out; output goes to ../nvr-symbols/shape-*.svg
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR = SCRIPT_DIR / "nvr_draw_container_svg.py"
# When in lib/, nvr-symbols is at repo root (parent of sample-nvr-odd-one-out).
NVR_SYMBOLS_DIR = SCRIPT_DIR.parent.parent / "nvr-symbols"

# All shape containers from guide §3.1 (must match nvr_draw_container_svg.SHAPES_ALL)
SHAPES = [
    "circle", "triangle", "square", "pentagon", "hexagon", "heptagon", "octagon",
    "right_angled_triangle", "rectangle", "semicircle", "cross", "arrow",
]


def main() -> None:
    NVR_SYMBOLS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating shape container SVGs into {NVR_SYMBOLS_DIR}...")
    for shape in SHAPES:
        out = NVR_SYMBOLS_DIR / f"shape-{shape}.svg"
        cmd = [
            sys.executable,
            str(GENERATOR),
            "--empty",
            "--shape", shape,
            "--line-style", "solid",
            "-o", str(out),
        ]
        subprocess.run(cmd, check=True, cwd=SCRIPT_DIR.parent)
        print(f"  {out.name}")
    print("Done.")


if __name__ == "__main__":
    main()
