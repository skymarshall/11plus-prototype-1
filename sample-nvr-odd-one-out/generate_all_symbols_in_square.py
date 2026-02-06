#!/usr/bin/env python3
"""
Generate option-square-10-{symbol}.svg for each symbol type (guide §4.1).

Each output is a square containing 10 instances of that symbol, randomly placed
with no overlap. Uses generate_shape_container_svg.py. See picture-based-questions-guide.md
§3.7 (symbol layout) and nvr-symbol-svg-design.md.

Usage:
  python generate_all_symbols_in_square.py
  python generate_all_symbols_in_square.py --seed 0

Requires generate_shape_container_svg.py in this directory and nvr-symbols in parent.
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR = SCRIPT_DIR / "generate_shape_container_svg.py"
SYMBOL_COUNT = 10

# Symbol dictionary (guide §4.1); must match files in nvr-symbols/
SYMBOLS = ["circle", "heart", "club", "spade", "diamond", "cross", "star", "square", "triangle"]

# Output filename: plural for club/spade to match option-square-10-clubs.svg / option-square-10-spades.svg
OUTPUT_NAMES = {"club": "clubs", "spade": "spades"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate option-square-10-{symbol}.svg for each symbol type."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for symbol placement (default: random per run).",
    )
    parser.add_argument(
        "--symbols-dir",
        type=Path,
        default=SCRIPT_DIR.parent / "nvr-symbols",
        help="Directory containing symbol SVGs (default: ../nvr-symbols).",
    )
    args = parser.parse_args()

    for i, symbol in enumerate(SYMBOLS):
        out_name = OUTPUT_NAMES.get(symbol, symbol)
        out_path = SCRIPT_DIR / f"option-square-10-{out_name}.svg"
        seed = (args.seed + i) if args.seed is not None else None
        seed_arg = ["--seed", str(seed)] if seed is not None else []
        cmd = [
            sys.executable,
            str(GENERATOR),
            symbol,
            "-n", str(SYMBOL_COUNT),
            "-o", str(out_path),
            "--symbols-dir", str(args.symbols_dir),
            *seed_arg,
        ]
        result = subprocess.run(cmd, cwd=SCRIPT_DIR)
        if result.returncode != 0:
            raise SystemExit(result.returncode)

    print(f"Wrote {len(SYMBOLS)} option-square-10-*.svg files. Seed: {args.seed}")


if __name__ == "__main__":
    main()
