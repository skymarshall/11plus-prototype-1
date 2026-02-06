#!/usr/bin/env python3
"""
Generate 5 answer-option SVGs for Example Question Template 2 (picture-based-questions-guide.md).

Template 2:
  Setup: Each answer is a common shape partitioned into sections using different shading.
  3 to 4 variators from shape, partition direction, number of sections, shading sequence of sections.
  Shape is not a differentiator (same shape for all 5 options).
  The odd one out differs on the differentiator only.

Uses nvr_logic_param_splits.py for allowed splits; nvr_draw_container_svg.py for SVG.
Partition-only (no symbols). Guide §3.9 partitioned shapes.
"""

import argparse
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR / "lib") not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR / "lib"))
from nvr_logic_param_splits import ALLOWED_SPLITS, assign_split_to_indices, sample_split

GENERATOR = SCRIPT_DIR / "lib" / "nvr_draw_container_svg.py"
OUTPUT_DIR = SCRIPT_DIR / "output"
OPTIONS = ["option-a.svg", "option-b.svg", "option-c.svg", "option-d.svg", "option-e.svg"]
N_OPTIONS = 5

# Template 2 params: shape (global), partition_direction, num_sections, shading_sequence
PARAM_NAMES = ["shape", "partition_direction", "num_sections", "shading_sequence"]

# Shapes that support partitioning (guide §3.1 common shapes; generator supports these for partition)
SHAPES_PARTITION = ["circle", "square", "triangle", "hexagon", "octagon"]

# Partition directions allowed per shape (circle has no diagonal; polygons support all)
PARTITION_BY_SHAPE: dict[str, list[str]] = {
    "circle": ["horizontal", "vertical", "concentric"],
    "square": ["horizontal", "vertical", "diagonal_slash", "diagonal_backslash", "concentric"],
    "triangle": ["horizontal", "vertical", "diagonal_slash", "diagonal_backslash", "concentric"],
    "hexagon": ["horizontal", "vertical", "diagonal_slash", "diagonal_backslash", "concentric"],
    "octagon": ["horizontal", "vertical", "diagonal_slash", "diagonal_backslash", "concentric"],
}

NUM_SECTIONS_POOL = [2, 3, 4]

# Shading sequences: comma-separated fill keys per section (cycle if used with more sections)
# Guide §3: grey, grey_light, white, diagonal_slash, diagonal_backslash, horizontal_lines, vertical_lines (no solid_black in partitioned samples)
SHADING_SEQUENCES = [
    "white,grey",
    "grey,white",
    "white,grey_light",
    "grey_light,white",
    "grey,white,grey_light",
    "white,grey,diagonal_slash",
    "grey,white,diagonal_slash",
    "white,diagonal_slash",
    "diagonal_slash,white",
    "grey,diagonal_slash",
    "diagonal_slash,grey",
    "white,grey,white",
    "grey,white,grey",
    "white,vertical_lines",
    "vertical_lines,white",
    "grey,white,grey_light,white",
    "white,grey_light,grey",
]

# Differentiator frequencies (guide: shape is not a differentiator)
VARIATOR_DIFFERENTIATOR_FREQUENCY: dict[str, str] = {
    "partition_direction": "common",
    "num_sections": "common",
    "shading_sequence": "common",
}

MAX_DISTINCT_ATTEMPTS = 500
SUBPROCESS_TIMEOUT = 60


def _section_fills_for_option(sequence: str, num_sections: int) -> str:
    """Expand sequence to cover num_sections by cycling. E.g. 'white,grey' and 3 -> 'white,grey,white'."""
    parts = [p.strip() for p in sequence.split(",")]
    if not parts:
        parts = ["white", "grey"]
    out: list[str] = []
    for i in range(num_sections):
        out.append(parts[i % len(parts)])
    return ",".join(out)


def _partition_sections_arg(num_sections: int) -> str:
    """Section bounds as comma-separated 0,...,100. E.g. 2 -> '0,50,100', 3 -> '0,33.33,66.67,100'."""
    if num_sections < 1:
        num_sections = 2
    step = 100.0 / num_sections
    bounds = [0.0]
    for k in range(1, num_sections):
        bounds.append(round(k * step, 2))
    bounds.append(100.0)
    return ",".join(f"{b:.2f}" if b != int(b) else str(int(b)) for b in bounds)


def _generate_options(
    rng: random.Random,
    shape: str,
    variators: list[str],
    differentiator: str,
) -> tuple[list[dict], int]:
    """
    Generate 5 option dicts: each has shape, partition_direction, num_sections, shading_sequence.
    shape is global; differentiator is one of variators (not shape).
    Returns (options, correct_index).
    """
    if differentiator not in variators or differentiator == "shape":
        raise ValueError("Differentiator must be one of variators and not shape.")
    partition_pool = PARTITION_BY_SHAPE.get(shape)
    if not partition_pool:
        raise ValueError(f"Shape {shape} has no partition directions.")

    pools: dict[str, list] = {
        "partition_direction": list(partition_pool),
        "num_sections": list(NUM_SECTIONS_POOL),
        "shading_sequence": list(SHADING_SEQUENCES),
    }

    globals_: dict = {"shape": shape}
    variator_indices: dict[str, list[int]] = {}
    variator_values: dict[str, list] = {}

    # Differentiator: two values (odd, common), split (1, 4)
    correct_index = rng.randrange(N_OPTIONS)
    diff_pool = list(pools[differentiator])
    if len(diff_pool) < 2:
        raise ValueError(f"Pool for {differentiator} has fewer than 2 values.")
    odd_val = rng.choice(diff_pool)
    common_val = rng.choice([v for v in diff_pool if v != odd_val])
    variator_values[differentiator] = [odd_val, common_val]
    indices = [1] * N_OPTIONS
    indices[correct_index] = 0
    variator_indices[differentiator] = indices

    # Other variators: 5 distinct combinations, allowed splits only
    other_variators = [v for v in variators if v != differentiator]
    if not other_variators:
        # Only one variator (differentiator); assign global values for the rest
        options = []
        for i in range(N_OPTIONS):
            opt = dict(globals_)
            opt[differentiator] = variator_values[differentiator][variator_indices[differentiator][i]]
            for p in ["partition_direction", "num_sections", "shading_sequence"]:
                if p not in opt:
                    opt[p] = rng.choice(pools[p])
            options.append(opt)
        return options, correct_index

    pools_other = [list(pools[p]) for p in other_variators]
    product = 1
    for pool in pools_other:
        product *= len(pool)
    if product < 5:
        raise ValueError(
            f"Product of pool sizes for {other_variators} is {product}; need >= 5 distinct."
        )
    allowed_5 = set(ALLOWED_SPLITS[N_OPTIONS])
    for _ in range(MAX_DISTINCT_ATTEMPTS):
        linear_indices = rng.sample(range(product), 5)
        for p in other_variators:
            variator_indices[p] = []
        for idx in linear_indices:
            t = idx
            for vi, pool in enumerate(pools_other):
                t, rem = divmod(t, len(pool))
                variator_indices[other_variators[vi]].append(rem)
        for vi, p in enumerate(other_variators):
            variator_values[p] = list(pools_other[vi])
        counts_ok = True
        for vi, p in enumerate(other_variators):
            if len(pools_other[vi]) == 1:
                continue
            counts = tuple(sorted(Counter(variator_indices[p]).values(), reverse=True))
            if counts not in allowed_5:
                counts_ok = False
                break
        if counts_ok:
            break
    else:
        raise ValueError(
            f"Could not assign other variators {other_variators} in {MAX_DISTINCT_ATTEMPTS} attempts."
        )

    options = []
    for i in range(N_OPTIONS):
        opt = dict(globals_)
        opt[differentiator] = variator_values[differentiator][variator_indices[differentiator][i]]
        for p in other_variators:
            vi = variator_indices[p][i]
            opt[p] = variator_values[p][vi]
        for p in PARAM_NAMES:
            if p not in opt and p != "shape":
                opt[p] = rng.choice(pools[p])
        options.append(opt)
    return options, correct_index


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate template 2 options (partitioned shapes, odd one out; guide §5)."
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed. If omitted, one is chosen and printed.")
    parser.add_argument(
        "--differentiator",
        type=str,
        default=None,
        choices=["partition_direction", "num_sections", "shading_sequence"],
        help="Parameter that defines the correct answer (default: random with equal weight).",
    )
    parser.add_argument(
        "--variators",
        type=str,
        nargs="+",
        default=None,
        metavar="PARAM",
        help="3–4 parameters that vary: partition_direction, num_sections, shading_sequence. Default: all three.",
    )
    parser.add_argument(
        "--shape",
        type=str,
        default=None,
        choices=SHAPES_PARTITION,
        help="Shape for all options (default: random). Shape is not a differentiator.",
    )
    args = parser.parse_args()

    if args.seed is None:
        args.seed = random.randrange(0, 2**32)
    rng = random.Random(args.seed)
    print(f"Seed: {args.seed}")

    variators = args.variators or ["partition_direction", "num_sections", "shading_sequence"]
    for v in variators:
        if v not in PARAM_NAMES or v == "shape":
            raise SystemExit("Variators must be partition_direction, num_sections, and/or shading_sequence (not shape).")
    if not (3 <= len(variators) <= 4):
        raise SystemExit("Variators must be 3 or 4 (shape is global, so effectively 3 varying).")
    variators = [v for v in variators if v != "shape"]

    shape = args.shape or rng.choice(SHAPES_PARTITION)
    differentiator = args.differentiator or rng.choice(variators)

    options, correct_index = None, None
    for attempt in range(MAX_DISTINCT_ATTEMPTS):
        try:
            options, correct_index = _generate_options(rng, shape, variators, differentiator)
            break
        except ValueError:
            continue
    if options is None:
        raise SystemExit(f"Could not generate {N_OPTIONS} distinct options in {MAX_DISTINCT_ATTEMPTS} attempts.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for i, out_name in enumerate(OPTIONS):
        opt = options[i]
        out_path = OUTPUT_DIR / out_name
        num_sections = opt["num_sections"]
        section_fills = _section_fills_for_option(opt["shading_sequence"], num_sections)
        partition_sections = _partition_sections_arg(num_sections)
        cmd = [
            sys.executable,
            str(GENERATOR),
            "--partition", opt["partition_direction"],
            "--shape", opt["shape"],
            "--partition-sections", partition_sections,
            "--section-fills", section_fills,
            "-o", str(out_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                cwd=SCRIPT_DIR,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            raise SystemExit(
                f"Generator timed out for {out_path} (shape={opt['shape']}, partition={opt['partition_direction']})."
            )
        if result.returncode != 0:
            print(result.stderr or result.stdout, file=sys.stderr)
            raise SystemExit(f"Generator failed for {out_path} (exit {result.returncode}).")
        print(f"  {out_path}")

    print(f"Question: shape={shape} (global), variators={variators}, differentiator={differentiator}, correct=option-{chr(ord('a') + correct_index)} ({OPTIONS[correct_index]})")
    for i in range(N_OPTIONS):
        opt = options[i]
        mark = " *" if i == correct_index else ""
        is_correct = i == correct_index
        parts = []
        for key in ["partition_direction", "num_sections", "shading_sequence"]:
            val = opt[key]
            if key == "shading_sequence":
                val = val[:30] + "..." if len(val) > 30 else val
            s = f"{key}={val}"
            if is_correct and key == differentiator:
                s = f"**{s}**"
            parts.append(s)
        print(f"  {OUTPUT_DIR / OPTIONS[i]}: {', '.join(parts)}{mark}")


if __name__ == "__main__":
    main()
