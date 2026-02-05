#!/usr/bin/env python3
"""
Generate 5 answer-option SVGs for Example Question Template 1 (picture-based-questions-guide.md).

Template 1 (updated):
  Setup: Choose a differentiator and 3 to 5 variators from shape, line style, fill, symbol,
  or number of symbols. Parameters that are not variators are global (fixed for the whole question).
  Answers: Each answer is a regular polygon (3–8 sides) or circle with line style and fill,
  containing a number of similar symbols. The odd one out differs on the differentiator only.

Follows picture-based-questions-guide.md §5 (terminology, parameter choice rules, allowed splits)
and §3–4 (vocabulary). Uses param_splits.py for allowed splits; generate_nvr_option_svg.py for SVG.

Usage:
  python generate_template1_options.py
  python generate_template1_options.py --seed 42
  python generate_template1_options.py --differentiator shape --variators shape fill symbol
  python generate_template1_options.py --variators shape fill symbol
  python generate_template1_options.py --differentiator symbol_count --variators shape symbol_count

If no --seed is given, a seed is chosen and printed so you can repeat the run.

Requires generate_nvr_option_svg.py and param_splits.py in this directory; nvr-symbols in parent.
"""

import argparse
import random
import subprocess
import sys
from pathlib import Path

from param_splits import assign_split_to_indices, sample_split

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR = SCRIPT_DIR / "generate_nvr_option_svg.py"
OPTIONS = ["option-a.svg", "option-b.svg", "option-c.svg", "option-d.svg", "option-e.svg"]
N_OPTIONS = 5

# All parameters (guide §5). symbol_count is numeric; others use vocab pools.
PARAM_NAMES = ["shape", "line_style", "fill", "symbol", "symbol_count"]
VISUAL_PARAMS = ["shape", "line_style", "fill", "symbol"]

# Vocab from guide §3–4 (regular shape = circle or regular polygon 3–8 sides). No solid_black when shape contains symbols.
SHAPES = ["triangle", "square", "pentagon", "hexagon", "heptagon", "octagon", "circle"]
LINE_STYLES = ["solid", "dashed", "dotted"]
FILLS = ["grey", "white", "diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines"]
SYMBOLS = ["circle", "heart", "club", "spade", "diamond", "cross", "star", "square", "triangle"]

POOLS: dict[str, list] = {
    "shape": SHAPES,
    "line_style": LINE_STYLES,
    "fill": FILLS,
    "symbol": SYMBOLS,
}

# CLI "symbol_type" -> param "symbol"
DIFF_TO_PARAM: dict[str, str] = {"symbol_type": "symbol"}

# Symbol count pool when variator but not differentiator (guide: n typically 3–6; allow 3–7 for 5 distinct).
SYMBOL_COUNT_POOL = [3, 4, 5, 6, 7]

MAX_DISTINCT_ATTEMPTS = 500


def _values_for_split(rng: random.Random, pool: list, split: tuple[int, ...]) -> list:
    """Return len(split) distinct values from pool (for assign_split_to_indices)."""
    n_vals = len(split)
    if n_vals > len(pool):
        raise ValueError(f"Pool size {len(pool)} < {n_vals} for split {split}")
    return rng.sample(pool, n_vals)


def _generate_options(
    rng: random.Random,
    variators: list[str],
    differentiator: str,
) -> tuple[list[dict], int]:
    """
    Generate 5 option dicts: each has shape, line_style, fill, symbol, symbol_count.
    differentiator is one of variators; params not in variators are global.
    Returns (options, correct_index).
    """
    differentiator = DIFF_TO_PARAM.get(differentiator, differentiator)
    if differentiator not in variators:
        raise ValueError(f"Differentiator {differentiator} must be one of variators {variators}")

    globals_: dict = {}
    variator_indices: dict[str, list[int]] = {}  # param -> list of 5 value-indices
    variator_values: dict[str, list] = {}          # param -> list of distinct values used

    # 1. Global params: one value each
    for p in PARAM_NAMES:
        if p in variators:
            continue
        if p == "symbol_count":
            globals_[p] = rng.choice(SYMBOL_COUNT_POOL)
        else:
            globals_[p] = rng.choice(POOLS[p])

    # 2. Differentiator: two values (odd, common), split (1, 4); one random option gets odd
    correct_index = rng.randrange(N_OPTIONS)  # uniform correct position (guide §5)
    if differentiator == "symbol_count":
        diff_pool = rng.sample(SYMBOL_COUNT_POOL, 2)  # two distinct counts for odd-one-out
    else:
        diff_pool = list(POOLS[differentiator])
    odd_val = rng.choice(diff_pool)
    common_val = rng.choice([v for v in diff_pool if v != odd_val])
    variator_values[differentiator] = [odd_val, common_val]
    indices = [1] * N_OPTIONS
    indices[correct_index] = 0  # this option gets odd_val (the correct answer)
    variator_indices[differentiator] = indices

    # 3. Other variators: assign 5 distinct (v1, v2, ...) so full option tuples are distinct (guide §5).
    other_variators = [v for v in variators if v != differentiator]
    pools_other: list[list] = []
    for p in other_variators:
        if p == "symbol_count":
            pools_other.append(list(SYMBOL_COUNT_POOL))
        else:
            pools_other.append(list(POOLS[p]))
    product = 1
    for pool in pools_other:
        product *= len(pool)
    if product < 5:
        raise ValueError(
            f"Product of pool sizes for {other_variators} is {product}; need >= 5 distinct combinations."
        )
    # Sample 5 distinct linear indices; convert each to (i0, i1, ...) per variator
    linear_indices = rng.sample(range(product), 5)
    # For each variator p, variator_indices[p][option_i] = index into pool for that option
    for p in other_variators:
        variator_indices[p] = []
    for idx in linear_indices:
        t = idx
        for vi, pool in enumerate(pools_other):
            t, rem = divmod(t, len(pool))
            variator_indices[other_variators[vi]].append(rem)
    for vi, p in enumerate(other_variators):
        variator_values[p] = list(pools_other[vi])

    # 4. Build 5 option dicts
    options: list[dict] = []
    for i in range(N_OPTIONS):
        opt: dict = {}
        for p in PARAM_NAMES:
            if p in globals_:
                opt[p] = globals_[p]
            else:
                vi = variator_indices[p][i]
                opt[p] = variator_values[p][vi]
        options.append(opt)

    # 5. Correct index: the one with the differentiator's odd value
    correct_idx = next(i for i in range(N_OPTIONS) if options[i][differentiator] == odd_val)
    return options, correct_idx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate template 1 options (differentiator + 3–5 variators, guide §5)."
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed. If omitted, one is chosen and printed for reproducibility.")
    parser.add_argument(
        "--differentiator",
        type=str,
        default=None,
        choices=["symbol_count", "shape", "line_style", "fill", "symbol_type"],
        help="Parameter that defines the correct answer (default: random among variators).",
    )
    parser.add_argument(
        "--variators",
        type=str,
        nargs="+",
        default=None,
        metavar="PARAM",
        help="3–5 parameters that vary: shape, line_style, fill, symbol, symbol_count. Default: random 3–5. Use symbol_type for symbol.",
    )
    args = parser.parse_args()

    if args.seed is None:
        args.seed = random.randrange(0, 2**32)
    rng = random.Random(args.seed)

    variators_arg = args.variators
    if variators_arg is not None:
        variators_arg = [DIFF_TO_PARAM.get(v, v) for v in variators_arg]
        for v in variators_arg:
            if v not in PARAM_NAMES:
                raise SystemExit(f"Unknown variator: {v}. Use: {PARAM_NAMES}")
        if not (3 <= len(variators_arg) <= 5):
            raise SystemExit("Variators must be 3 to 5 parameters.")

    differentiator_arg = args.differentiator
    if differentiator_arg is not None:
        differentiator_arg = DIFF_TO_PARAM.get(differentiator_arg, differentiator_arg)

    options, correct_index, variators, differentiator = None, None, None, None
    for _ in range(MAX_DISTINCT_ATTEMPTS):
        variators = variators_arg
        if variators is None:
            num_v = rng.randint(3, 5)
            variators = rng.sample(PARAM_NAMES, num_v)
        differentiator = differentiator_arg
        if differentiator is None:
            differentiator = rng.choice(variators)
        elif differentiator not in variators:
            raise SystemExit("Differentiator must be one of the chosen variators.")
        try:
            options, correct_index = _generate_options(rng, variators, differentiator)
            break
        except ValueError:
            continue
    if options is None:
        raise SystemExit(f"Could not generate {N_OPTIONS} distinct options in {MAX_DISTINCT_ATTEMPTS} attempts.")

    for i, out_name in enumerate(OPTIONS):
        opt = options[i]
        count = opt["symbol_count"]
        seed_i = (args.seed + 100 + i) if args.seed is not None else None
        seed_arg = ["--seed", str(seed_i)] if seed_i is not None else []
        cmd = [
            sys.executable,
            str(GENERATOR),
            opt["symbol"],
            "-n", str(count),
            "-o", out_name,
            "--shape", opt["shape"],
            "--line-style", opt["line_style"],
            "--fill", opt["fill"],
            *seed_arg,
        ]
        result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True)
        if result.returncode != 0:
            raise SystemExit(result.returncode)

    print(f"Seed: {args.seed}")
    print(f"Question: variators={variators}, differentiator={differentiator}, correct=option-{chr(ord('a') + correct_index)} ({OPTIONS[correct_index]})")
    for i in range(N_OPTIONS):
        opt = options[i]
        mark = " *" if i == correct_index else ""
        print(f"  {OPTIONS[i]}: shape={opt['shape']}, line_style={opt['line_style']}, fill={opt['fill']}, symbol={opt['symbol']}, symbol_count={opt['symbol_count']}{mark}")


if __name__ == "__main__":
    main()
