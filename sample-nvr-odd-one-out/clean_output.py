#!/usr/bin/env python3
"""
Remove all files in the output directory so you can run sample scripts from a clean state.

Usage:
  python clean_output.py
  python clean_output.py -o my_out
"""

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "output"


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove all files in output/ (or -o dir).")
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory to clean (default: output/).",
    )
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if not out.exists():
        print(f"Nothing to clean: {out} does not exist.")
        return
    if not out.is_dir():
        print(f"Not a directory: {out}")
        return
    removed = 0
    for f in out.iterdir():
        if f.is_file():
            f.unlink()
            removed += 1
            print(f"Removed {f.name}")
    if removed == 0:
        print(f"Already empty: {out}")
    else:
        print(f"Cleaned {removed} file(s) from {out}")


if __name__ == "__main__":
    main()
