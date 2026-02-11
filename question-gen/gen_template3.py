#!/usr/bin/env python3
"""
Template 3 question generator: array of shapes, odd one out by [One] shape or fill at one location.

Uses nvr_logic_param_splits so every variator ([Each] shape at location, [Each] fill at location)
is forced to vary across the 5 options with allowed splits; ensures the 4 non-answer options
are pairwise different.

Outputs question XML (one question per run, or multiple with --count). Can write to file or stdout.
"""

import argparse
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

# Add lib for param_splits
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from lib.nvr_logic_param_splits import assign_split_to_indices, sample_split

N_OPTIONS = 5

# Template 3: [Choose] any shape, any fill — use common shapes and solid shadings (design doc §4)
COMMON_SHAPES = [
    "circle",
    "triangle",
    "square",
    "pentagon",
    "hexagon",
]
SHADINGS = ["grey", "grey_light", "white"]

# Grid (rows, cols) by total size; for 5 we can use 1×5 or 2×3 with one null
def _grid_for_size(total_size: int, rng: random.Random) -> tuple[int, int, list[int]]:
    """Return (rows, cols, null_indices). null_indices = positions that are null (empty)."""
    if total_size == 3:
        return 1, 3, []
    if total_size == 4:
        return 2, 2, []
    if total_size == 5:
        if rng.choice([True, False]):
            return 1, 5, []
        # 2×3 with one null
        null_at = rng.randint(0, 5)
        return 2, 3, [null_at]
    raise ValueError(f"total_size must be 3–5, got {total_size}")


def _position_label(rows: int, cols: int, position: int, null_positions: list[int]) -> str:
    """User-facing label for position (e.g. 'top-left', 'middle')."""
    if position in null_positions:
        return "empty"
    r, c = position // cols, position % cols
    if rows == 1:
        if cols == 3:
            return ["left", "middle", "right"][c]
        return f"position {c + 1}"
    if rows == 2 and cols == 2:
        return ["top-left", "top-right", "bottom-left", "bottom-right"][position]
    if rows == 2 and cols == 3:
        names = [
            "top-left", "top-middle", "top-right",
            "bottom-left", "bottom-middle", "bottom-right",
        ]
        return names[position]
    return f"cell {position + 1}"


def _build_value_lists(
    n_positions: int,
    diff_kind: str,
    diff_loc_idx: int,
    correct_index: int,
    rng: random.Random,
) -> tuple[list[list[int]], list[list[int]]]:
    """Build shape_value_indices and fill_value_indices so differentiator is 4-1 and others use allowed splits."""
    shape_indices: list[list[int]] = []
    fill_indices: list[list[int]] = []

    diff_shape = [0] * N_OPTIONS
    diff_shape[correct_index] = 1
    diff_fill = [0] * N_OPTIONS
    diff_fill[correct_index] = 1

    for i in range(n_positions):
        if diff_kind == "shape" and i == diff_loc_idx:
            shape_indices.append(diff_shape)
        else:
            split = sample_split(N_OPTIONS, rng)
            shape_indices.append(assign_split_to_indices(split, N_OPTIONS, rng))

        if diff_kind == "fill" and i == diff_loc_idx:
            fill_indices.append(diff_fill)
        else:
            split = sample_split(N_OPTIONS, rng)
            fill_indices.append(assign_split_to_indices(split, N_OPTIONS, rng))

    return shape_indices, fill_indices


def generate_one(
    seed: int,
    question_id: str = "template3-q01",
    rng: Optional[random.Random] = None,
) -> ET.Element:
    """
    Generate one Template 3 question. Each variator ([Each] shape/fill at location)
    is forced to vary via nvr_logic_param_splits; [One] shape or fill is the differentiator.
    Ensures all 5 options are distinct.
    """
    rng = rng or random.Random(seed)
    total_size = rng.choice([3, 4, 5])
    rows, cols, null_positions = _grid_for_size(total_size, rng)
    n_cells = rows * cols
    shape_positions = [i for i in range(n_cells) if i not in null_positions]
    n_pos = len(shape_positions)
    assert n_pos == total_size

    diff_kind = rng.choice(["shape", "fill"])
    diff_loc_idx = rng.randint(0, n_pos - 1)
    diff_position = shape_positions[diff_loc_idx]
    correct_index = rng.randint(0, N_OPTIONS - 1)

    shape_value_indices, fill_value_indices = _build_value_lists(
        n_pos, diff_kind, diff_loc_idx, correct_index, rng
    )

    # Map value indices to actual shapes/fills per variator (per position)
    # For each position we have up to 5 value indices; we need that many distinct values
    options_grid: list[list[tuple[str, str] | None]] = [[None] * n_cells for _ in range(N_OPTIONS)]
    max_attempts = 30
    for attempt in range(max_attempts):
        for pos_idx, pos in enumerate(shape_positions):
            n_shape_vals = max(shape_value_indices[pos_idx]) + 1
            n_fill_vals = max(fill_value_indices[pos_idx]) + 1
            shapes_here = rng.sample(COMMON_SHAPES, min(n_shape_vals, len(COMMON_SHAPES)))
            if len(shapes_here) < n_shape_vals:
                shapes_here.extend(rng.choices(COMMON_SHAPES, k=n_shape_vals - len(shapes_here)))
            # Fills: we only have 3 shadings, so allow repeats when n_fill_vals > 3
            fills_here = (
                rng.sample(SHADINGS, n_fill_vals)
                if n_fill_vals <= len(SHADINGS)
                else rng.choices(SHADINGS, k=n_fill_vals)
            )
            for opt in range(N_OPTIONS):
                si = shape_value_indices[pos_idx][opt]
                fi = fill_value_indices[pos_idx][opt]
                options_grid[opt][pos] = (shapes_here[si], fills_here[fi])

        signatures = [tuple(options_grid[o]) for o in range(N_OPTIONS)]
        if len(set(signatures)) == N_OPTIONS:
            break
    else:
        raise RuntimeError(f"Could not get 5 distinct options after {max_attempts} attempts (seed={seed})")

    pos_label = _position_label(rows, cols, diff_position, null_positions)
    if diff_kind == "shape":
        correct_shape = options_grid[correct_index][diff_position][0]
        other_shape = next(
            options_grid[o][diff_position][0]
            for o in range(N_OPTIONS)
            if o != correct_index
        )
        explanation = (
            f"The odd one out has a {correct_shape} in the {pos_label} cell; "
            f"the others have a {other_shape} there."
        )
    else:
        explanation = f"The odd one out has a different shading in the {pos_label} cell."

    root = ET.Element("question", id=question_id, template_id="template3", seed=str(seed))
    ET.SubElement(root, "product", subject_code="nvr", topic_code="odd_one_out")
    qtext = ET.SubElement(root, "question_text")
    qtext.text = "Which grid is the odd one out?" if n_cells > 1 else "Which row is the odd one out?"
    expl = ET.SubElement(root, "explanation")
    expl.text = explanation
    options_el = ET.SubElement(root, "options")
    draw_full_grid = len(null_positions) == 0

    for opt in range(N_OPTIONS):
        opt_el = ET.SubElement(options_el, "option", index=str(opt))
        diagram = ET.SubElement(opt_el, "diagram")
        arr = ET.SubElement(
            diagram,
            "array",
            type="rectangular",
            rows=str(rows),
            cols=str(cols),
            draw_mesh="true",
            draw_full_grid="true" if draw_full_grid else "false",
        )
        for pos in range(n_cells):
            if pos in null_positions:
                ET.SubElement(arr, "null")
            else:
                s, f = options_grid[opt][pos]
                ET.SubElement(arr, "shape", key=s, shading=f)

    correct_el = ET.SubElement(root, "correct")
    correct_el.text = str(correct_index)
    return root


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Template 3 (array odd-one-out) question XML.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (default: stdout)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of questions to generate (ids template3-q01, ...)",
    )
    parser.add_argument(
        "--id-prefix",
        type=str,
        default="template3-q",
        help="Prefix for question ids",
    )
    parser.add_argument(
        "--id-width",
        type=int,
        default=2,
        help="Zero-pad width for question id numbers",
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    questions: list[ET.Element] = []
    for i in range(args.count):
        qid = f"{args.id_prefix}{str(i + 1).zfill(args.id_width)}"
        questions.append(generate_one(args.seed + i, question_id=qid, rng=rng))

    if args.output is None:
        # Single question: emit one <question>; multiple: wrap in <questions>
        if len(questions) == 1:
            ET.dump(questions[0])
        else:
            root = ET.Element("questions")
            root.set(
                "xmlns:xsi",
                "http://www.w3.org/2001/XMLSchema-instance",
            )
            root.set(
                "xsi:noNamespaceSchemaLocation",
                "question-xml.xsd",
            )
            for q in questions:
                root.append(q)
            ET.dump(root)
    else:
        out = args.output.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        if len(questions) == 1:
            tree = ET.ElementTree(questions[0])
            ET.indent(tree, space="  ")
            tree.write(out, encoding="unicode", default_namespace="", xml_declaration=True)
        else:
            root = ET.Element("questions")
            root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
            root.set("xsi:noNamespaceSchemaLocation", "question-xml.xsd")
            for q in questions:
                root.append(q)
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(out, encoding="unicode", default_namespace="", xml_declaration=True)
        print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
