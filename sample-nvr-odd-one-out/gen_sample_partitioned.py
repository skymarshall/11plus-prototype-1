#!/usr/bin/env python3
"""
Generate sample partitioned-shape SVGs (picture-based-questions-guide.md §3.9).

Calls nvr_draw_container_svg.py with --partition to produce:
  - Horizontal partition: square, hexagon, octagon (two or three sections)
  - Vertical partition: square, triangle, octagon
  - Diagonal partition (slash and backslash): square, hexagon, octagon (polygons only)
  - Concentric partition: circle, square, octagon (disc/ring or polygon rings and bands)
  - Radial partition (radial sections): circle (6), square (4), hexagon (6), rectangle (4)

Outputs go to script_dir/output/ with names like:
  partitioned-horizontal-square.svg, partitioned-diagonal_slash-octagon.svg,
  partitioned-concentric-octagon-bands.svg, partitioned-radial-circle.svg
"""

import os
import subprocess
import sys
from pathlib import Path


def run(
    partition: str,
    shape: str,
    output: Path | str,
    partition_sections: str | None = None,
    section_fills: str | None = None,
) -> None:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "lib" / "nvr_draw_container_svg.py"),
        "--partition",
        partition,
        "--shape",
        shape,
        "-o",
        str(output),
    ]
    if partition_sections:
        cmd.extend(["--partition-sections", partition_sections])
    if section_fills:
        cmd.extend(["--section-fills", section_fills])
    subprocess.run(cmd, check=True)
    print(f"  {output}")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(script_dir)

    print("Generating partitioned shape samples (guide §3.9)...")

    # --- Horizontal ---
    run(
        "horizontal",
        "square",
        output_dir / "partitioned-horizontal-square.svg",
        section_fills="white,grey",
    )
    run(
        "horizontal",
        "hexagon",
        output_dir / "partitioned-horizontal-hexagon.svg",
        partition_sections="0,33.33,66.67,100",
        section_fills="white,grey,diagonal_slash",
    )
    run(
        "horizontal",
        "octagon",
        output_dir / "partitioned-horizontal-octagon.svg",
        section_fills="grey,white",
    )

    # --- Vertical ---
    run(
        "vertical",
        "square",
        output_dir / "partitioned-vertical-square.svg",
        section_fills="grey,white",
    )
    run(
        "vertical",
        "triangle",
        output_dir / "partitioned-vertical-triangle.svg",
        section_fills="white,vertical_lines",
    )
    run(
        "vertical",
        "octagon",
        output_dir / "partitioned-vertical-octagon.svg",
        partition_sections="0,50,100",
        section_fills="white,grey",
    )

    # --- Diagonal slash (/) ---
    run(
        "diagonal_slash",
        "square",
        output_dir / "partitioned-diagonal_slash-square.svg",
        section_fills="white,grey",
    )
    run(
        "diagonal_slash",
        "hexagon",
        output_dir / "partitioned-diagonal_slash-hexagon.svg",
        partition_sections="0,33.33,66.67,100",
        section_fills="white,grey,diagonal_slash",
    )
    run(
        "diagonal_slash",
        "octagon",
        output_dir / "partitioned-diagonal_slash-octagon.svg",
        section_fills="grey,white",
    )

    # --- Diagonal backslash (\) ---
    run(
        "diagonal_backslash",
        "square",
        output_dir / "partitioned-diagonal_backslash-square.svg",
        section_fills="white,grey",
    )
    run(
        "diagonal_backslash",
        "hexagon",
        output_dir / "partitioned-diagonal_backslash-hexagon.svg",
        section_fills="grey,white",
    )
    run(
        "diagonal_backslash",
        "octagon",
        output_dir / "partitioned-diagonal_backslash-octagon.svg",
        partition_sections="0,50,100",
        section_fills="white,grey",
    )

    # --- Concentric: circle ---
    run(
        "concentric",
        "circle",
        output_dir / "partitioned-concentric-circle.svg",
        section_fills="grey,white",
    )
    run(
        "concentric",
        "circle",
        output_dir / "partitioned-concentric-circle-bands.svg",
        partition_sections="0,40,50,60,100",
        section_fills="white,grey,diagonal_slash,grey,white",
    )

    # --- Concentric: square (polygon rings) ---
    run(
        "concentric",
        "square",
        output_dir / "partitioned-concentric-square.svg",
        section_fills="white,grey",
    )
    run(
        "concentric",
        "square",
        output_dir / "partitioned-concentric-square-bands.svg",
        partition_sections="0,30,40,60,100",
        section_fills="white,grey,diagonal_slash,grey,white",
    )

    # --- Concentric: octagon (polygon rings and bands) ---
    run(
        "concentric",
        "octagon",
        output_dir / "partitioned-concentric-octagon.svg",
        section_fills="grey,white",
    )
    run(
        "concentric",
        "octagon",
        output_dir / "partitioned-concentric-octagon-bands.svg",
        partition_sections="0,35,45,55,100",
        section_fills="white,grey,vertical_lines,grey,white",
    )

    # --- Radial (radial sections; guide §3.9) ---
    run(
        "radial",
        "circle",
        output_dir / "partitioned-radial-circle.svg",
        partition_sections="0,16.67,33.33,50,66.67,83.33,100",
        section_fills="white,grey,white,grey,white,grey",
    )
    run(
        "radial",
        "triangle",
        output_dir / "partitioned-radial-triangle.svg",
        partition_sections="0,33.33,66.67,100",
        section_fills="white,grey,horizontal_lines",
    )
    run(
        "radial",
        "square",
        output_dir / "partitioned-radial-square.svg",
        section_fills="white,grey,white,grey",
    )
    run(
        "radial",
        "hexagon",
        output_dir / "partitioned-radial-hexagon.svg",
        partition_sections="0,16.67,33.33,50,66.67,83.33,100",
        section_fills="white,grey,white,grey,white,grey",
    )
    run(
        "radial",
        "rectangle",
        output_dir / "partitioned-radial-rectangle.svg",
        section_fills="white,grey,grey_light,diagonal_slash",
    )

    print("Done.")


if __name__ == "__main__":
    main()
