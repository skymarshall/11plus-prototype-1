#!/usr/bin/env python3
"""
Generate 5 answer-option SVGs for Example Question Template 1 (question-gen/QUESTION-GENERATION-DESIGN.md §4).

Template 1:
  Setup: Each answer is a common shape containing a symbol layout.
  3 to 5 variators from shape, line style, fill, symbol, or number of symbols.
  With probability 1/4 add symmetry as a variator (guide §4); shape, fill, and symmetry (if present) are uncommon differentiators.
  The odd one out differs on the differentiator only (or by layout symmetry when differentiator is symmetry; horizontal or vertical only).
  Fill is restricted to solid/white only (guide §3.6: symbols cannot appear on hatched areas).

Follows question-gen/QUESTION-GENERATION-DESIGN.md §4 (terminology, frequency modifiers, allowed splits)
and §3 (vocabulary). Uses nvr_logic_frequency.py for weighted differentiator choice; nvr_logic_param_splits.py for splits;
nvr_draw_container_svg.py for SVG. Common shape = regular shape or common irregular shape (guide 3.1).

Usage:
  python gen_question_template1.py
  python gen_question_template1.py --seed 42
  python gen_question_template1.py -o output/questions/q00001   # batch: write into per-question dir
  python gen_question_template1.py --differentiator shape --variators shape fill symbol
  python gen_question_template1.py --differentiator symmetry --symmetry-line any   # some H, some V, one none
  python gen_question_template1.py --differentiator symmetry --variators shape fill symbol
  python gen_question_template1.py --variators shape fill symbol

If no --seed is given, a seed is chosen and printed so you can repeat the run.
Output: option-a.svg … option-e.svg and question_meta.json (correct_index, template_id, seed, question_text, explanation) in the same directory. Default directory: <script_dir>/output; override with -o/--output-dir.

Requires lib/nvr_logic_frequency.py, lib/nvr_logic_param_splits.py, and lib/nvr_draw_container_svg.py; nvr-symbols in parent.
"""

import argparse
import json
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR / "lib") not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR / "lib"))
from nvr_logic_frequency import weighted_choice
from nvr_logic_param_splits import ALLOWED_SPLITS, assign_split_to_indices, sample_split

GENERATOR = SCRIPT_DIR / "lib" / "nvr_draw_container_svg.py"
OPTIONS = ["option-a.svg", "option-b.svg", "option-c.svg", "option-d.svg", "option-e.svg"]
META_FILENAME = "question_meta.json"
TEMPLATE_ID = "template1"
N_OPTIONS = 5

# All parameters (guide §5). symbol_count is numeric; others use vocab pools.
PARAM_NAMES = ["shape", "line_style", "fill", "symbol", "symbol_count"]
VISUAL_PARAMS = ["shape", "line_style", "fill", "symbol"]

# Vocab from guide §3.1: common shape = regular shapes + common irregular shapes. No solid_black when shape contains symbols.
# Regular shapes (circle + polygons 3–8 sides):
SHAPES_REGULAR = ["circle", "triangle", "square", "pentagon", "hexagon", "heptagon", "octagon"]
# Common irregular shapes (guide 3.1).
SHAPES_IRREGULAR = ["right_angled_triangle", "rectangle", "semicircle", "cross", "arrow"]
SHAPES = SHAPES_REGULAR + SHAPES_IRREGULAR
# All line types from guide §3.3 (solid, dashed, dotted). When symmetry is variator we restrict to solid only.
LINE_STYLES = ["solid", "dashed", "dotted"]
LINE_STYLES_SYMMETRIC = ["solid"]  # guide §3.3: dashed/dotted break reflection symmetry
# All shading types allowed when shape contains symbols (guide §3.6: no hatched areas, no solid_black).
FILLS_WHEN_SHAPE_HAS_SYMBOLS = ["grey", "grey_light", "white"]
FILLS = FILLS_WHEN_SHAPE_HAS_SYMBOLS
SYMBOLS = ["circle", "heart", "club", "spade", "diamond", "plus", "star", "square", "triangle"]

# Template 1 uses all possible line styles and all allowed fills (see above).
POOLS: dict[str, list] = {
    "shape": SHAPES,
    "line_style": LINE_STYLES,
    "fill": FILLS,
    "symbol": SYMBOLS,
}

# CLI "symbol_type" -> param "symbol"
DIFF_TO_PARAM: dict[str, str] = {"symbol_type": "symbol"}

# Template 1 (guide §4): differentiator is chosen from the selected variators with these frequencies
VARIATOR_DIFFERENTIATOR_FREQUENCY: dict[str, str] = {
    "shape": "uncommon",
    "line_style": "common",
    "fill": "uncommon",
    "symbol": "common",
    "symbol_count": "common",
    "symmetry": "uncommon",
}
# P(add symmetry as variator) = (1/3)/(1 + 1/3) = 1/4 (guide §4 "add [item] as a variator and a [frequency] differentiator")
ADD_SYMMETRY_WEIGHT = 1.0 / 3.0
DONT_ADD_SYMMETRY_WEIGHT = 1.0
P_ADD_SYMMETRY = ADD_SYMMETRY_WEIGHT / (ADD_SYMMETRY_WEIGHT + DONT_ADD_SYMMETRY_WEIGHT)  # 1/4
# When symmetry is variator/differentiator: choose line option then resolve to vertical or horizontal for forcing (guide §3.9)
SYMMETRY_LINE_OPTIONS = ["horizontal", "vertical", "any"]  # "any" → pick horizontal or vertical when forcing; diagonal not used
SYMMETRY_DIFF_LINE_TYPES = ["vertical", "horizontal"]      # resolved line types used when forcing layout

# Symmetry lines per vocabulary (guide §3.1, §3.2, §3.6, §3.9). When forcing layout symmetry, use only
# shapes/symbols/fills that have that line so the graphic does not conflict with the layout.
# Keys: vertical, horizontal, diagonal_slash, diagonal_backslash (generator names).
SHAPE_LINES: dict[str, list[str]] = {
    "circle": ["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"],
    "triangle": ["vertical"],
    "square": ["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"],
    "pentagon": ["vertical"],
    "hexagon": ["vertical", "horizontal"],
    "heptagon": ["vertical"],
    "octagon": ["vertical", "horizontal"],
    "right_angled_triangle": ["diagonal_slash"],
    "rectangle": ["vertical", "horizontal"],
    "semicircle": ["vertical"],
    "cross": ["vertical", "horizontal"],
    "arrow": ["horizontal"],
}
SYMBOL_LINES: dict[str, list[str]] = {
    "circle": ["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"],
    "plus": ["vertical", "horizontal"],
    "heart": ["vertical"],
    "diamond": ["vertical", "horizontal"],
    "club": ["vertical"],
    "spade": ["vertical"],
    "square": ["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"],
    "triangle": ["vertical"],
    "star": ["vertical"],
}
FILL_LINES: dict[str, list[str]] = {
    "grey": ["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"],
    "grey_light": ["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"],
    "white": ["vertical", "horizontal", "diagonal_slash", "diagonal_backslash"],
    "diagonal_slash": ["diagonal_backslash"],   # / hatch has \ symmetry only
    "diagonal_backslash": ["diagonal_slash"],   # \ hatch has / symmetry only
    "horizontal_lines": ["vertical"],   # horizontal hatch has vertical symmetry only (mirror left–right)
    "vertical_lines": ["horizontal"],   # vertical hatch has horizontal symmetry only (mirror top–bottom)
}


def _pools_for_layout_symmetry(layout_symmetry: str) -> dict[str, list]:
    """Return POOLS with shape, symbol, fill, line_style filtered for symmetry (guide: when forcing layout symmetry). Dashed/dotted break symmetry. Use layout_symmetry 'any' for items that have both horizontal and vertical (mix of lines per option)."""
    result = dict(POOLS)
    if layout_symmetry == "any":
        result["shape"] = [s for s in SHAPES if "vertical" in SHAPE_LINES.get(s, []) and "horizontal" in SHAPE_LINES.get(s, [])]
        result["symbol"] = [s for s in SYMBOLS if "vertical" in SYMBOL_LINES.get(s, []) and "horizontal" in SYMBOL_LINES.get(s, [])]
        result["fill"] = [f for f in FILLS if "vertical" in FILL_LINES.get(f, []) and "horizontal" in FILL_LINES.get(f, [])]
    else:
        result["shape"] = [s for s in SHAPES if layout_symmetry in SHAPE_LINES.get(s, [])]
        result["symbol"] = [s for s in SYMBOLS if layout_symmetry in SYMBOL_LINES.get(s, [])]
        result["fill"] = [f for f in FILLS if layout_symmetry in FILL_LINES.get(f, [])]
    result["line_style"] = list(LINE_STYLES_SYMMETRIC)
    return result


# Symbol count pool when variator but not differentiator (guide: n typically 3–6; allow 3–7 for 5 distinct).
SYMBOL_COUNT_POOL = [3, 4, 5, 6, 7]

MAX_DISTINCT_ATTEMPTS = 500
# "any" symmetry uses pools filtered to both H and V, so fill has only 2 values; need more attempts for allowed splits
MAX_DISTINCT_ATTEMPTS_SYMMETRY_ANY = 5000


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
        # No 4–1 (or other disallowed) split on any non-differentiator variator (guide: avoid unintended odd one outs)
        # Skip variators with pool size 1: all options get the same value, so no accidental odd-one-out.
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
            f"Could not assign other variators {other_variators} with allowed splits only in {MAX_DISTINCT_ATTEMPTS} attempts."
        )

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


def _generate_options_symmetry(
    rng: random.Random,
    variators: list[str],
    symmetry_type: str | None = None,
) -> tuple[list[dict], int]:
    """
    Generate 5 option dicts when differentiator is symmetry (odd one out differs by layout symmetry).
    symmetry_type: "vertical", "horizontal", or "any". If "any", some options get horizontal and some vertical (one has none). If None, picks one at random.
    When forcing layout symmetry, use only shapes/symbols/fills that have that line (or both for "any") (guide §3.9).
    Each option has shape, line_style, fill, symbol, symbol_count, and layout_symmetry (str or None).
    Returns (options, correct_index).
    """
    if symmetry_type is None:
        symmetry_type = rng.choice(SYMMETRY_DIFF_LINE_TYPES)
    use_any = symmetry_type == "any"
    if use_any:
        filtered_pools = _pools_for_layout_symmetry("any")
    else:
        assert symmetry_type in SYMMETRY_DIFF_LINE_TYPES, "symmetry_type must be vertical, horizontal, or any"
        filtered_pools = _pools_for_layout_symmetry(symmetry_type)
    if not filtered_pools["shape"] or not filtered_pools["symbol"] or not filtered_pools["fill"]:
        raise ValueError(
            f"No shape/symbol/fill for {symmetry_type} symmetry; cannot generate symmetry-differentiator options."
        )

    globals_: dict = {}
    variator_indices: dict[str, list[int]] = {}
    variator_values: dict[str, list] = {}

    for p in PARAM_NAMES:
        if p in variators:
            continue
        if p == "symbol_count":
            globals_[p] = rng.choice(SYMBOL_COUNT_POOL)
        else:
            globals_[p] = rng.choice(filtered_pools[p])

    # All five params vary: assign 5 distinct combinations (use filtered pools for shape, symbol, fill)
    other_variators = list(variators)
    pools_other: list[list] = []
    for p in other_variators:
        if p == "symbol_count":
            pools_other.append(list(SYMBOL_COUNT_POOL))
        else:
            pools_other.append(list(filtered_pools[p]))
    product = 1
    for pool in pools_other:
        product *= len(pool)
    if product < 5:
        raise ValueError(
            f"Product of pool sizes for {other_variators} is {product}; need >= 5 distinct combinations."
        )
    allowed_5 = set(ALLOWED_SPLITS[N_OPTIONS])
    max_attempts = MAX_DISTINCT_ATTEMPTS_SYMMETRY_ANY if use_any else MAX_DISTINCT_ATTEMPTS

    for _ in range(max_attempts):
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

        # No 4–1 (or other disallowed) split on any variator (guide: avoid unintended odd one outs)
        # Skip variators with pool size 1 (e.g. line_style=[solid] under symmetry): no accidental odd-one-out.
        counts_ok = True
        for vi, p in enumerate(other_variators):
            if len(pools_other[vi]) == 1:
                continue
            inds = variator_indices[p]
            counts = tuple(sorted(Counter(inds).values(), reverse=True))
            if counts not in allowed_5:
                counts_ok = False
                break
        if counts_ok:
            break
    else:
        raise ValueError(
            f"Could not assign variators {other_variators} with allowed splits only in {max_attempts} attempts."
        )

    # Layout symmetry: 4–1 or 1–4 split with equal frequency (guide §3.9 symmetry as differentiator)
    correct_index = rng.randrange(N_OPTIONS)
    four_symmetric_one_asymmetric = rng.random() < 0.5
    if use_any:
        # Some options horizontal, some vertical, one none (odd one out)
        layout_symmetries = [None] * N_OPTIONS
        if four_symmetric_one_asymmetric:
            # Four symmetric (mix of H and V), one asymmetric
            symmetric_indices = [i for i in range(N_OPTIONS) if i != correct_index]
            n_h = rng.randint(0, len(symmetric_indices))  # how many of the 4 get horizontal
            rng.shuffle(symmetric_indices)
            for j, i in enumerate(symmetric_indices):
                layout_symmetries[i] = "horizontal" if j < n_h else "vertical"
        else:
            # One symmetric (H or V), four asymmetric
            layout_symmetries[correct_index] = rng.choice(SYMMETRY_DIFF_LINE_TYPES)
    else:
        if four_symmetric_one_asymmetric:
            layout_symmetries = [symmetry_type] * N_OPTIONS
            layout_symmetries[correct_index] = None  # asymmetric = odd one out
        else:
            layout_symmetries = [None] * N_OPTIONS
            layout_symmetries[correct_index] = symmetry_type  # symmetric = odd one out

    options = []
    for i in range(N_OPTIONS):
        opt = {}
        for p in PARAM_NAMES:
            if p in globals_:
                opt[p] = globals_[p]
            else:
                vi = variator_indices[p][i]
                opt[p] = variator_values[p][vi]
        opt["layout_symmetry"] = layout_symmetries[i]
        options.append(opt)
    return options, correct_index


def _explanation_for_template1(
    options: list[dict], correct_index: int, differentiator: str
) -> str:
    """Build a one-line explanation for the odd-one-out (for questions.explanation)."""
    letter = chr(ord("a") + correct_index)
    correct_opt = options[correct_index]
    # One representative wrong option (any option that is not the correct one)
    wrong_index = 0 if correct_index != 0 else 1
    wrong_opt = options[wrong_index]
    if differentiator == "shape":
        return f"The odd one out is option {letter}: it is the only {correct_opt['shape']}; the others are {wrong_opt['shape']}s."
    if differentiator == "line_style":
        return f"The odd one out is option {letter}: it is the only one with a {correct_opt['line_style']} outline; the others have {wrong_opt['line_style']}."
    if differentiator == "fill":
        return f"The odd one out is option {letter}: it is the only one with {correct_opt['fill']} fill; the others have {wrong_opt['fill']}."
    if differentiator == "symbol":
        return f"The odd one out is option {letter}: it is the only one containing {correct_opt['symbol']}s; the others contain {wrong_opt['symbol']}s."
    if differentiator == "symbol_count":
        n, m = correct_opt["symbol_count"], wrong_opt["symbol_count"]
        return f"The odd one out is option {letter}: it has {n} symbol{'s' if n != 1 else ''}; the others have {m}."
    if differentiator == "symmetry":
        ls = correct_opt.get("layout_symmetry")
        if ls:
            return f"The odd one out is option {letter}: it is the only one with {ls} symmetry; the others differ."
        return f"The odd one out is option {letter}: it is the only one without layout symmetry; the others have symmetry."
    return f"The odd one out is option {letter}."


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate template 1 options (differentiator + 3–5 variators, guide §5)."
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed. If omitted, one is chosen and printed for reproducibility.")
    parser.add_argument(
        "--differentiator",
        type=str,
        default=None,
        choices=["symbol_count", "shape", "line_style", "fill", "symbol_type", "symmetry"],
        help="Parameter that defines the correct answer (default: weighted by template frequencies).",
    )
    parser.add_argument(
        "--variators",
        type=str,
        nargs="+",
        default=None,
        metavar="PARAM",
        help="3–5 parameters that vary: shape, line_style, fill, symbol, symbol_count. Default: random 3–5. Use symbol_type for symbol.",
    )
    parser.add_argument(
        "--symmetry-line",
        type=str,
        default=None,
        choices=["horizontal", "vertical", "any"],
        help="When differentiator is symmetry: use this line option. 'any' = some options horizontal, some vertical, one none. Default: random.",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directory for option SVGs and question_meta.json. Default: <script_dir>/output.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir if args.output_dir is not None else SCRIPT_DIR / "output"

    if args.seed is None:
        args.seed = random.randrange(0, 2**32)
    rng = random.Random(args.seed)
    print(f"Seed: {args.seed}")

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

    SUBPROCESS_TIMEOUT = 60
    options, correct_index, variators, differentiator = None, None, None, None

    for attempt in range(MAX_DISTINCT_ATTEMPTS):
        options, correct_index, variators, differentiator = None, None, None, None
        for _ in range(MAX_DISTINCT_ATTEMPTS):
            # 1. Base variators: 3–5 from shape, line_style, fill, symbol, symbol_count (guide Template 1). When symmetry is involved, use all 5 so line_style and fill are always variators.
            variators_base = variators_arg
            if variators_base is None:
                if differentiator_arg == "symmetry":
                    variators_base = list(PARAM_NAMES)  # all 5 when user forces symmetry
                else:
                    num_v = rng.randint(3, 5)
                    variators_base = rng.sample(PARAM_NAMES, num_v)
            # 2. With probability 1/4 add symmetry as a variator (guide §4 "add [item] as a variator")
            add_symmetry = differentiator_arg == "symmetry" or rng.random() < P_ADD_SYMMETRY
            if add_symmetry and variators_arg is None:
                variators_base = list(PARAM_NAMES)  # use all 5 so line_style and fill are always variators
            variators = list(variators_base)
            if add_symmetry and "symmetry" not in variators:
                variators.append("symmetry")
            # When symmetry is in the variator set, choose line option: horizontal, vertical, or any (guide §3.9)
            symmetry_line_option = (args.symmetry_line if args.symmetry_line else rng.choice(SYMMETRY_LINE_OPTIONS)) if add_symmetry else None
            # 3. Differentiator from variators with weights: shape/fill/symmetry uncommon, rest common
            differentiator = differentiator_arg
            if differentiator is None:
                diff_choices = [(v, VARIATOR_DIFFERENTIATOR_FREQUENCY.get(v, "common")) for v in variators]
                differentiator = weighted_choice(rng, diff_choices)
            if differentiator not in variators:
                raise SystemExit("Differentiator must be one of the chosen variators.")
            if differentiator == "symmetry":
                # Pass line option: "horizontal", "vertical", or "any" (any = mix of H and V per option, one none)
                try:
                    options, correct_index = _generate_options_symmetry(rng, variators_base, symmetry_type=symmetry_line_option)
                    break
                except ValueError:
                    continue
            else:
                try:
                    # _generate_options only uses POOLS (no "symmetry" key); omit symmetry from variators
                    variators_for_options = [v for v in variators if v != "symmetry"]
                    options, correct_index = _generate_options(rng, variators_for_options, differentiator)
                    break
                except ValueError:
                    continue
        if options is None:
            raise SystemExit(f"Could not generate {N_OPTIONS} distinct options in {MAX_DISTINCT_ATTEMPTS} attempts.")

        # Run SVG generator for each option; retry whole generation if one fails (e.g. symmetry placement)
        svg_failed = False
        output_dir.mkdir(parents=True, exist_ok=True)
        for i, out_name in enumerate(OPTIONS):
            opt = options[i]
            count = opt["symbol_count"]
            out_path = output_dir / out_name
            seed_i = (args.seed + 100 + attempt * N_OPTIONS + i) if args.seed is not None else None
            seed_arg = ["--seed", str(seed_i)] if seed_i is not None else []
            cmd = [
                sys.executable,
                str(GENERATOR),
                opt["symbol"],
                "-n", str(count),
                "-o", str(out_path),
                "--shape", opt["shape"],
                "--line-style", opt["line_style"],
                "--fill", opt["fill"],
                *seed_arg,
            ]
            if opt.get("layout_symmetry") is not None:
                cmd.extend(["--layout-symmetry", opt["layout_symmetry"]])
            try:
                result = subprocess.run(
                    cmd,
                    cwd=SCRIPT_DIR,
                    capture_output=True,
                    text=True,
                    timeout=SUBPROCESS_TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                print(f"Error: generator timed out after {SUBPROCESS_TIMEOUT}s for {out_path} (shape={opt['shape']}, n={count}).", file=sys.stderr)
                svg_failed = True
                break
            if result.returncode != 0:
                print(f"Generator failed for {out_path} (shape={opt['shape']}, n={count}), retrying...", file=sys.stderr)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
                svg_failed = True
                break
        if not svg_failed:
            break
        # Advance RNG so next attempt gets different options (avoids repeated impossible symmetry cases)
        for _ in range(50):
            rng.random()
    else:
        raise SystemExit("SVG generator failed after multiple attempts.")

    # Required metadata for batch script and database insert (python-script-standards.md §2)
    question_text = "Which shape is the odd one out?"
    explanation = _explanation_for_template1(options, correct_index, differentiator)
    meta = {
        "correct_index": correct_index,
        "template_id": TEMPLATE_ID,
        "seed": args.seed,
        "question_text": question_text,
        "explanation": explanation,
        "variators": variators,
        "differentiator": differentiator,
    }
    meta_path = output_dir / META_FILENAME
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote {meta_path}")

    print(f"Question: variators={variators}, differentiator={differentiator}, correct=option-{chr(ord('a') + correct_index)} ({OPTIONS[correct_index]})")
    for i in range(N_OPTIONS):
        opt = options[i]
        mark = " *" if i == correct_index else ""
        is_correct = i == correct_index
        parts = []
        for key in ["shape", "line_style", "fill", "symbol", "symbol_count"]:
            s = f"{key}={opt[key]}"
            if is_correct and key == differentiator:
                s = f"**{s}**"
            parts.append(s)
        if differentiator == "symmetry":
            ls = opt.get("layout_symmetry")
            if ls:
                s = f"layout_symmetry={ls}"
            else:
                s = "layout_symmetry=None"
            if is_correct:
                s = f"**{s} (odd one out)**"
            parts.append(s)
        print(f"  {output_dir / OPTIONS[i]}: {', '.join(parts)}{mark}")


if __name__ == "__main__":
    main()
