#!/usr/bin/env python3
"""
Generate one plain container SVG per possible shape (picture-based-questions-guide.md §3.1).

Each output is the shape outline only (no motifs). Uses lib/nvr_draw_container_svg.py --empty.
Outputs to script_dir/output/: {shape}.svg (e.g. square.svg).

Usage:
  python gen_sample_containers.py
  python gen_sample_containers.py -o my_out

Requires lib/nvr_draw_container_svg.py and nvr-symbols (for symbol shapes).
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR = SCRIPT_DIR / "lib" / "nvr_draw_container_svg.py"
OUTPUT_DIR = SCRIPT_DIR / "output"
MOTIFS_DIR = SCRIPT_DIR.parent / "nvr-symbols"

# All shape containers (guide §3.1: regular + irregular + symbols)
SHAPES = [
    "circle", "triangle", "square", "pentagon", "hexagon", "heptagon", "octagon",
    "right_angled_triangle", "rectangle", "semicircle", "cross", "arrow",
    "plus", "times", "club", "heart", "diamond", "spade", "star",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate one {shape}.svg per container, outline only (output/)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory (default: output/).",
    )
    parser.add_argument(
        "--motifs-dir",
        type=Path,
        default=MOTIFS_DIR,
        help="Directory containing shape-{symbol}.svg for symbol containers (default: ../nvr-symbols).",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    failed: list[str] = []

    for shape in SHAPES:
        out_path = args.output_dir / f"{shape}.svg"
        cmd = [
            sys.executable,
            str(GENERATOR),
            "--empty",
            "--shape", shape,
            "-o", str(out_path),
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
