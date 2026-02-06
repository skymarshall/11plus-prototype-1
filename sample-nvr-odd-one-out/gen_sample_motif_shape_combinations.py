#!/usr/bin/env python3
"""
Generate one SVG per possible container shape, each containing 10 random motifs (picture-based-questions-guide.md §3.1, §3.2).

Each output is one shape container with N motifs of one type inside, randomly placed with no overlap.
The motif type for each container is chosen at random from the motif dictionary. Uses lib/nvr_draw_container_svg.py.

Outputs to script_dir/output/: option-{shape}-{n}.svg (e.g. option-square-10.svg).
One file per container; motif count default 10.
Uses white background fill and white motifs (black outline) to compare which shapes work as motif containers.
Runs all containers even if some fail; reports failures at the end.

Usage:
  python gen_sample_motif_shape_combinations.py
  python gen_sample_motif_shape_combinations.py --seed 0
  python gen_sample_motif_shape_combinations.py -o my_output -n 10

Requires lib/nvr_draw_container_svg.py and nvr-symbols in parent.
"""

import argparse
import random
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR = SCRIPT_DIR / "lib" / "nvr_draw_container_svg.py"
OUTPUT_DIR = SCRIPT_DIR / "output"
DEFAULT_MOTIF_COUNT = 10

# All shape containers supported by nvr_draw_container_svg (guide §3.1: regular + irregular + symbols)
SHAPES = [
    "circle", "triangle", "square", "pentagon", "hexagon", "heptagon", "octagon",
    "right_angled_triangle", "rectangle", "semicircle", "cross", "arrow",
    "plus", "times", "club", "heart", "diamond", "spade", "star",
]

# Motif dictionary (guide §3.2); must match shape-{motif}.svg in nvr-symbols/
MOTIFS = ["circle", "heart", "club", "spade", "diamond", "plus", "times", "star", "square", "triangle"]

# Max motifs per shape (cap per shape if needed; empty = use default count for all)
MAX_MOTIFS_BY_SHAPE: dict[str, int] = {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate one option-{shape}-{n}.svg per container, each with N random motifs (output/)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for motif type and placement (default: random per run).",
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=DEFAULT_MOTIF_COUNT,
        metavar="N",
        help=f"Number of motifs per container (default: {DEFAULT_MOTIF_COUNT}).",
    )
    parser.add_argument(
        "--motifs-dir",
        type=Path,
        default=SCRIPT_DIR.parent / "nvr-symbols",
        help="Directory containing motif SVGs shape-{motif}.svg (default: ../nvr-symbols).",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory (default: output/).",
    )
    parser.add_argument(
        "--motif-fill",
        type=str,
        default="white",
        choices=["black", "white"],
        help="Motif fill passed to generator (default: white for this sample script).",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    # Cap by shape when MAX_MOTIFS_BY_SHAPE is set
    def motif_count(s: str) -> int:
        cap = MAX_MOTIFS_BY_SHAPE.get(s)
        return min(args.count, cap) if cap is not None else args.count

    total = len(SHAPES)
    failures: list[tuple[str, str]] = []  # (out_path_name, stderr_snippet)
    for idx, shape in enumerate(SHAPES):
        motif = rng.choice(MOTIFS)
        n = motif_count(shape)
        out_name = f"option-{shape}-{n}.svg"
        out_path = args.output_dir / out_name
        seed = (args.seed + idx) if args.seed is not None else None
        seed_arg = ["--seed", str(seed)] if seed is not None else []
        # White background fill; white motifs (black outline) for comparing container suitability
        cmd = [
            sys.executable,
            str(GENERATOR),
            motif,
            "-n", str(n),
            "--shape", shape,
            "-o", str(out_path),
            "--motifs-dir", str(args.motifs_dir),
            "--motif-fill", args.motif_fill,
            "--fill", "white_fill",
            *seed_arg,
        ]
        result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            stderr_snippet = (result.stderr or "").strip().split("\n")[-1] if result.stderr else "unknown error"
            failures.append((out_name, stderr_snippet))
            print(f"Failed: {out_name}  ({stderr_snippet})", file=sys.stderr)
            continue

    ok = total - len(failures)
    print(f"Wrote {ok}/{total} files to {args.output_dir} (fill=white_fill, motif-fill={args.motif_fill}). Seed: {args.seed}")
    if failures:
        print(f"Failed ({len(failures)}):", file=sys.stderr)
        for out_name, err in failures:
            print(f"  {out_name}: {err}", file=sys.stderr)


if __name__ == "__main__":
    main()
