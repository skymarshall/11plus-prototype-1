#!/usr/bin/env python3
"""
Template 2 question generator: Odd One Out.
Type: Partitioned Shape.
Structure: Common shape container partitioned into sections.
Variators: Partition Type, Number of Sections, Fill of Sections.
Differentiator: One of the variators.
Constraints:
  - Shape is always common (never differentiator).
  - Fill variation requires constant Number of Sections.
  - Some partition types only work with specific shapes.
"""

import argparse
import json
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional

# Add lib to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

# Import library modules
try:
    import nvr_draw_container_svg as draw_lib
    from nvr_logic_param_splits import assign_split_to_indices, sample_split
    from nvr_logic_frequency import weighted_choice
except ImportError:
    # Fallback for direct execution if paths are messy
    sys.path.append(str(SCRIPT_DIR.parent / "lib"))
    import nvr_draw_container_svg as draw_lib
    from nvr_logic_param_splits import assign_split_to_indices, sample_split
    from nvr_logic_frequency import weighted_choice

N_OPTIONS = 5

# -- Definitions --

COMMON_SHAPES = ["circle", "triangle", "square", "pentagon", "hexagon", "octagon"]

# Valid partitions per shape (approximate)
# All shapes support linear partitions (horizontal, vertical, diagonal)
# Only circle supports concentric (cleanly) and radial
# Square supports nested/concentric too but nvr_draw_container_svg mostly optimized for circle/convex
PARTITIONS_ALL = ["horizontal", "vertical", "diagonal_slash", "diagonal_backslash"]
PARTITIONS_RADIAL = ["radial"]
PARTITIONS_CONCENTRIC = ["concentric"]

def get_valid_partitions(shape: str) -> list[str]:
    p = list(PARTITIONS_ALL)
    if shape == "circle":
        p.extend(PARTITIONS_RADIAL)
        p.extend(PARTITIONS_CONCENTRIC)
    elif shape == "square":
        # Square supports concentric/radial technically but let's stick to linear for cleaner T2 for now
        # Actually nvr_draw_container_svg supports concentric for polygon/square
        p.extend(PARTITIONS_CONCENTRIC)
        pass
    elif shape == "semicircle":
         p.extend(PARTITIONS_RADIAL)
    return p

FILLS = [
    "solid_black", "grey", "grey_light", "white", "white_fill",
    "diagonal_slash", "diagonal_backslash", "horizontal_lines", "vertical_lines"
]

NUM_SECTIONS_RANGE = [2, 3, 4]

# Variators
VARIATORS = ["partition_type", "num_sections", "fill"]

# Differentiator weights
DIFF_WEIGHTS = [
    ("partition_type", "common"),
    ("num_sections", "common"),
    ("fill", "uncommon"),
]

def _generate_value_indices(
    n_options: int,
    is_differentiator: bool,
    correct_index: int,
    rng: random.Random,
    max_values: Optional[int] = None
) -> list[int]:
    """Generate indices for a parameter (0=common, 1=diff/unique)."""
    if is_differentiator:
        if max_values is not None and max_values < 2:
            return [0] * n_options # Fallback if not enough values
        indices = [0] * n_options
        indices[correct_index] = 1
        return indices
    else:
        split = sample_split(n_options, rng, max_values=max_values)
        return assign_split_to_indices(split, n_options, rng)

def _get_values_from_pool(indices: list[int], pool: list[Any], rng: random.Random) -> list[Any]:
    unique_indices = sorted(list(set(indices)))
    if len(unique_indices) > len(pool):
        # Fallback: allow duplicates if pool is small
        vals = rng.sample(pool, len(pool))
        # Repeat roughly
        while len(vals) < len(unique_indices):
            vals.append(rng.choice(pool))
        mapping = {idx: v for idx, v in zip(unique_indices, vals)}
    else:
        vals = rng.sample(pool, len(unique_indices))
        mapping = {idx: v for idx, v in zip(unique_indices, vals)}
    return [mapping[i] for i in indices]

def generate_question(seed: int) -> dict:
    rng = random.Random(seed)
    
    # 1. Setup
    shape = rng.choice(COMMON_SHAPES)
    valid_partitions = get_valid_partitions(shape)
    
    # 2. Choose Differentiator
    # Filter available differentiators based on constraints?
    # e.g. if num_sections is 2, maybe we don't have enough partition types?
    # Usually fine.
    diff_attr = weighted_choice(rng, DIFF_WEIGHTS)
    
    # 3. Determine Values
    correct_idx = rng.randint(0, N_OPTIONS - 1)
    
    # Initialize basic arrays
    option_partitions = [""] * N_OPTIONS
    option_num_sections = [0] * N_OPTIONS
    option_fills = [[]] * N_OPTIONS # list of lists
    
    # -- Partition Type --
    if diff_attr == "partition_type":
        # 4 commmon, 1 diff
        indices = _generate_value_indices(N_OPTIONS, True, correct_idx, rng, max_values=len(valid_partitions))
        vals = _get_values_from_pool(indices, valid_partitions, rng)
        option_partitions = vals
    else:
        # Variator (random distribution)
        # Note: If fill is diff, we might want partition constant? No, mostly num_sections constraint.
        # But if partition varies, num_sections might need to be compatible?
        # Let's keep partition constant if it's not the differentiator, to avoid chaos. 
        # T2 spec says "Choose common shape". Doesn't say "Choose common partition".
        # But varying partition type AND num_sections AND fill might be too much.
        # Let's try to make it a variator but maybe limit it.
        # Actually, let's keep it constant (Common) if not differentiator.
        # "Variators: partition type...". So it CAN vary.
        # Let's allow it to vary.
        
        # FIX: If fill is differentiator, num_sections is constant. 
        # If partition is ALSO constant, we get 4 identical options (clones).
        # We must ensure partition varies if fill is differentiator (and we have enough partition types).
        force_variance = (diff_attr == "fill" and len(valid_partitions) > 1)
        
        for _ in range(10):
            indices = _generate_value_indices(N_OPTIONS, False, correct_idx, rng, max_values=len(valid_partitions))
            if force_variance and len(set(indices)) == 1:
                continue # Retry to get some variance
            break
            
        vals = _get_values_from_pool(indices, valid_partitions, rng)
        option_partitions = vals

    # -- Num Sections --
    # Constraint: If fill is differentiator, num_sections must be constant (so we can compare fills 1:1).
    if diff_attr == "fill":
        # Constant num sections
        n = rng.choice(NUM_SECTIONS_RANGE)
        option_num_sections = [n] * N_OPTIONS
    elif diff_attr == "num_sections":
        # Differentiator
        indices = _generate_value_indices(N_OPTIONS, True, correct_idx, rng, max_values=len(NUM_SECTIONS_RANGE))
        vals = _get_values_from_pool(indices, NUM_SECTIONS_RANGE, rng)
        option_num_sections = vals
    else:
        # Variator
        indices = _generate_value_indices(N_OPTIONS, False, correct_idx, rng, max_values=len(NUM_SECTIONS_RANGE))
        vals = _get_values_from_pool(indices, NUM_SECTIONS_RANGE, rng)
        option_num_sections = vals

    # -- Fills --
    # Handle fills based on num_sections
    # Each option has 'n' sections. We need 'n' fills.
    # If num_sections varies, we can't easily have a "common fill pattern" across options unless we define it smartly (e.g. top is always black).
    # Simplification:
    # If num_sections varies, Fills are random/varied per option (but consistent logic? No, just random looks fine).
    # If fill is Differentiator, num_sections is constant.
    
    if diff_attr == "fill":
        # Num sections is constant (N).
        # We need N fill values for each option.
        # We treat "Fill Pattern" as the value.
        # e.g. Pattern A = [Black, White], Pattern B = [White, Black]
        # 4 options get Pattern A, 1 gets Pattern B.
        
        n = option_num_sections[0]
        # Generate pool of patterns
        # A pattern is a list of N fills.
        # We need at least 2 distinct patterns.
        pool_patterns = []
        for _ in range(10): # try 10 times to get unique patterns
            pat = [rng.choice(FILLS) for _ in range(n)]
            if pat not in pool_patterns:
                pool_patterns.append(pat)
        
        indices = _generate_value_indices(N_OPTIONS, True, correct_idx, rng, max_values=len(pool_patterns))
        vals = _get_values_from_pool(indices, pool_patterns, rng)
        option_fills = vals
        
    else:
        # Fill is NOT differentiator.
        # It is a variator.
        # We generate a fill set for each option.
        # If num_sections varies, each option gets `num` fills.
        # We can just pick random fills for each option. 
        # Or should we enforce "Common Fill" logic? e.g. "All options have a black section".
        # Let's Stick to "random selection from pool" which naturally creates overlaps (variator style).
        
        for i in range(N_OPTIONS):
            n = option_num_sections[i]
            # Just pick n random fills
            option_fills[i] = [rng.choice(FILLS) for _ in range(n)]

    # 4. Construct Options
    options = []
    for i in range(N_OPTIONS):
        opt = {
            "shape": shape,
            "partition": option_partitions[i],
            "num_sections": option_num_sections[i],
            "fills": option_fills[i],
            "is_correct": (i == correct_idx)
        }
        options.append(opt)
        
    question_data = {
        "seed": seed,
        "type": "Odd One Out",
        "template": "template2",
        "options": options,
        "differentiator": diff_attr,
        "common_shape": shape
    }
    return question_data

def render_option(opt: dict) -> str:
    """Render a single option using nvr_draw_container_svg."""
    # We need to construct arguments for build_partitioned_sections and build_svg
    
    shape = opt["shape"]
    partition_type = opt["partition"]
    n = opt["num_sections"]
    fills = opt["fills"]
    
    # Get Geometry
    # We don't have 'motifs_dir' easily here unless we pass it.
    # But draw_lib handles 'None' by assuming local repo structure.
    # Let's try to pass strict path.
    # SCRIPT_DIR is .../question-scripts
    # Repo root is .../
    # Motifs dir is .../nvr-symbols
    repo_root = SCRIPT_DIR.parent
    motifs_dir = repo_root / "nvr-symbols"
    
    vertices, path_d, path_d_stroke, stroke_lines, sym_transform, sym_path_elem = draw_lib.get_shape_geometry(shape, motifs_dir)
    bbox = draw_lib.get_shape_bbox(shape, vertices, path_d)
    
    # Calculate section bounds (percentages)
    bounds = draw_lib.even_section_bounds(n)
    
    # Generate consistent clip ID
    clip_id = f"clip-{random.randint(0, 999999)}"

    # Build partition
    # defs, fill_content, lines, paths
    defs_str, fill_content, part_lines, part_paths = draw_lib.build_partitioned_sections(
        shape=shape,
        path_d=path_d,
        vertices=vertices,
        bbox=bbox,
        partition_direction=partition_type,
        section_bounds=bounds,
        section_fills=fills,
        shape_clip_id=clip_id,
        symbol_transform=sym_transform,
        symbol_path_element=sym_path_elem
    )
    
    # Build SVG
    svg = draw_lib.build_svg(
        motif_content="", # No motifs
        positions=[],
        motif_name="",
        shape=shape,
        path_d=path_d,
        motif_scale=1.0, 
        motif_tx=0,
        motif_ty=0,
        line_style="solid", 
        polygon_fill="none",
        polygon_fill_defs=None,
        path_d_stroke=path_d_stroke,
        stroke_lines=stroke_lines,
        partition_defs=defs_str,
        partition_fill_content=fill_content,
        partition_lines=part_lines,
        partition_paths=part_paths,
        symbol_transform=sym_transform,
        shape_clip_id=clip_id
    )
    return svg

def generate_xml_output(questions: list[dict], output_file: Path | None = None) -> str:
    root = ET.Element("root")
    for q_data in questions:
        q_elem = ET.SubElement(root, "question_data")
        
        # Metadata
        ET.SubElement(q_elem, "type").text = q_data["type"]
        ET.SubElement(q_elem, "template").text = q_data["template"]
        ET.SubElement(q_elem, "seed").text = str(q_data["seed"])
        ET.SubElement(q_elem, "differentiator").text = q_data["differentiator"]
        ET.SubElement(q_elem, "common_shape").text = q_data["common_shape"]
        
        # Options
        opts_elem = ET.SubElement(q_elem, "options")
        for i, opt in enumerate(q_data["options"]):
            opt_elem = ET.SubElement(opts_elem, "option")
            opt_elem.set("correct", str(opt["is_correct"]).lower())
            
            # Render SVG
            svg_str = render_option(opt)
            
            # Store SVG in a sub-element (CDAT-ish)
            # We'll just define it as text. The loader will write it to file.
            svg_elem = ET.SubElement(opt_elem, "svg_content")
            svg_elem.text = svg_str
            
            # Also store params for debug
            params_elem = ET.SubElement(opt_elem, "params")
            params_elem.text = json.dumps({k:v for k,v in opt.items() if k != "is_correct"})

    # Pretty print hack
    from xml.dom import minidom
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    if output_file:
        output_file.write_text(xml_str, encoding="utf-8")
        
    return xml_str

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--count", type=int, default=1)
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    
    rng = random.Random(args.seed)
    
    # Batch mode check: -o is a directory and count is implicitly 1 (or we just take 1)
    # The batch runner passes --seed X -o DIR
    
    output_path = args.output
    if output_path and (output_path.is_dir() or not output_path.suffix):
        # Directory mode (Batch Runner)
        # Generate 1 question
        seed = args.seed if args.seed is not None else rng.randint(0, 2**32 - 1)
        q = generate_question(seed)
        
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
            
        # Write question_meta.json
        meta = {
            "template_id": "template2",
            "seed": seed,
            "correct_index": next(i for i, o in enumerate(q["options"]) if o["is_correct"]),
            "question_text": "Which shape is the odd one out?",
            "explanation": f"The odd one out is distinguished by {q['differentiator']}.",
            "option_files": ["option-a.svg", "option-b.svg", "option-c.svg", "option-d.svg", "option-e.svg"],
            "params": {k:v for k,v in q.items() if k != "options"}
        }
        with open(output_path / "question_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            
        # Write SVGs
        for i, opt in enumerate(q["options"]):
            svg_content = render_option(opt)
            filename = meta["option_files"][i]
            with open(output_path / filename, "w", encoding="utf-8") as f:
                f.write(svg_content)
                
        # Write XML for debug
        q_xml = generate_xml_output([q])
        with open(output_path / "question.xml", "w", encoding="utf-8") as f:
            f.write(q_xml)
            
    else:
        # File mode (XML)
        questions = []
        count = args.count if args.count else 1
        # If seed is provided in file mode, we usually want deterministic sequence
        current_seed = args.seed if args.seed is not None else rng.randint(0, 2**32 - 1)
        
        local_rng = random.Random(current_seed)
        
        for _ in range(count):
            s = local_rng.randint(0, 2**32 - 1)
            q = generate_question(s)
            questions.append(q)
            
        xml_out = generate_xml_output(questions)
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(xml_out)
        else:
            print(xml_out)

if __name__ == "__main__":
    main()
