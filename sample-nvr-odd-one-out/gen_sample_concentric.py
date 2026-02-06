#!/usr/bin/env python3
"""
Generate one simple concentric-partition SVG per supported shape (picture-based-questions-guide.md §3.9).

Concentric partition: three rings (centre, middle, outer). Supported for circle, polygons, semicircle, and symbol shapes (plus, times, club, heart, diamond, spade, star). Symbols use scaled path from nvr-symbols (not sampled polygon). Uses lib/nvr_draw_container_svg.py --partition concentric with --partition-sections 0,33.33,66.67,100. Requires --motifs-dir for symbol shapes.

Outputs to script_dir/output/: concentric-{shape}.svg

Usage:
  python gen_sample_concentric.py
  python gen_sample_concentric.py -o my_out

Requires lib/nvr_draw_container_svg.py.
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR = SCRIPT_DIR / "lib" / "nvr_draw_container_svg.py"
OUTPUT_DIR = SCRIPT_DIR / "output"
MOTIFS_DIR = SCRIPT_DIR.parent / "nvr-symbols"

# Shapes suitable for concentric partition (guide: plus, times, club, heart, diamond, spade not suitable)
SHAPES = [
    "circle",
    "triangle", "square", "pentagon", "hexagon", "heptagon", "octagon",
    "right_angled_triangle", "rectangle", "semicircle", "arrow", "cross",
    "star",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate one concentric-partition SVG per supported shape (output/)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory (default: output/).",
    )
    parser.add_argument(
        "--section-fills",
        type=str,
        default="white,grey,white",
        help="Comma-separated section fills for 3 sections (default: white,grey,white).",
    )
    parser.add_argument(
        "--motifs-dir",
        type=Path,
        default=MOTIFS_DIR,
        help="Directory for shape-{symbol}.svg (default: ../nvr-symbols). Required for symbol shapes.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    failed: list[str] = []

    for shape in SHAPES:
        out_path = args.output_dir / f"concentric-{shape}.svg"
        cmd = [
            sys.executable,
            str(GENERATOR),
            "--partition", "concentric",
            "--shape", shape,
            "-o", str(out_path),
            "--partition-sections", "0,33.33,66.67,100",
            "--section-fills", args.section_fills,
            "--motifs-dir", str(args.motifs_dir),
        ]
        result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            failed.append(shape)
            print(f"Failed: {out_path.name}  ({result.stderr.strip() or result.stdout.strip()})")
        else:
            print(f"Wrote {out_path.name}")

    if failed:
        print(f"\nFailed: {', '.join(failed)}")
        sys.exit(1)
    print(f"\nWrote {len(SHAPES)} files to {args.output_dir}")


if __name__ == "__main__":
    main()
