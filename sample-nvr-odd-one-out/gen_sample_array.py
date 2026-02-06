#!/usr/bin/env python3
"""
Generate sample array SVGs (picture-based-questions-guide.md, Arrays).

Calls nvr_draw_array_svg.py for presets including:
  - Homogeneous arrays (triangles, squares, etc.)
  - Heterogeneous shapes (mixed types)
  - Variety in type + fill + line type (shapes, fills, line-styles; all borders black)

Outputs go to script_dir/output/.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ARRAY_GENERATOR = SCRIPT_DIR / "lib" / "nvr_draw_array_svg.py"
OUTPUT_DIR = SCRIPT_DIR / "output"

# (rows, cols, shape_or_none, out_filename_override, shapes_csv, fills_csv, line_styles_csv)
SAMPLES = [
    (2, 2, "triangle", None, None, None, None),
    (3, 2, "regular", None, None, None, None),
    (1, 4, "pentagon", None, None, None, None),
    (2, 3, "square", None, None, None, None),
    (2, 2, None, "array-2x2-mixed.svg", "triangle,square,circle,pentagon", None, None),
    # Variety: type + fill + line type (solid, dashed, dotted; all black)
    (2, 2, None, "array-2x2-varied.svg", "triangle,square,circle,pentagon", "none,grey,white,grey", "solid,dashed,dotted,solid"),
    (2, 3, None, "array-2x3-varied.svg", "circle,square,triangle,hexagon,pentagon,octagon", "none,white,grey,none,white,grey", "solid,dashed,dotted,solid,dashed,dotted"),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating array samples (gap=8, margin=8; black-and-white, line types: solid/dashed/dotted)...")

    for row in SAMPLES:
        rows, cols, shape, name_override, shapes_csv, fills_csv, line_styles_csv = row
        if name_override:
            out_name = name_override
        else:
            out_name = f"array-{rows}x{cols}-{shape}.svg"
        out_path = OUTPUT_DIR / out_name
        cmd = [
            sys.executable,
            str(ARRAY_GENERATOR),
            str(rows),
            str(cols),
            "-o",
            str(out_path),
        ]
        if shapes_csv:
            cmd.extend(["--shapes", shapes_csv])
        else:
            cmd.append(shape)
            if shape == "regular":
                cmd.extend(["--seed", "42"])
        if fills_csv:
            cmd.extend(["--fills", fills_csv])
        if line_styles_csv:
            cmd.extend(["--line-styles", line_styles_csv])
        subprocess.run(cmd, check=True)
        print(f"  {out_path}")

    print("Done.")


if __name__ == "__main__":
    main()
