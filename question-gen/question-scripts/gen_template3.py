#!/usr/bin/env python3
"""
Template 3 question generator: Odd One Out.
Type: Array of Shapes (Sequence/Grid).
Structure: 3 positions (1x3).
Variators: Shape at each position, Fill at each position.
Differentiator: One of the variators.
Constraints:
  - Must validate against derived rule conflicts using nvr_logic_validation.
"""

import argparse
import json
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

# Add lib to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

# Import library modules
try:
    import nvr_draw_container_svg as draw_lib # needed? maybe for shapes
    import nvr_draw_layout as layout_lib
    from nvr_logic_validation import check_derived_parameters
    from nvr_logic_frequency import weighted_choice
except ImportError:
    # Fallback
    sys.path.append(str(SCRIPT_DIR.parent / "lib"))
    import nvr_draw_container_svg as draw_lib
    import nvr_draw_layout as layout_lib
    from nvr_logic_validation import check_derived_parameters
    from nvr_logic_frequency import weighted_choice

N_OPTIONS = 5
MAX_ARRAY_SIZE = 5
TARGET_NON_NULL = 3

COMMON_SHAPES = ["circle", "square", "triangle", "pentagon", "hexagon", "star", "cross", "diamond"]
FILLS = ["none", "solid_black", "grey", "grey_light", "diagonal_slash", "horizontal_lines"]
ARRAY_TYPES = ["rectangular", "loop", "triangular"]

def generate_question(seed: int) -> dict:
    rng = random.Random(seed)
    
    # 1. Setup
    # Layout Selection
    # Determine total slots: Target 3 non-null => 0, 1, or 2 nulls.
    # We want valid layouts for the total size.
    # Weights for nulls? Uniform? Or per spec "Uncommon" for masking? 
    # Let's pick Total Size first from [3, 4, 5]
    total_slots = rng.choice([3, 4, 5])
    num_nulls = total_slots - TARGET_NON_NULL
    
    # Select Array Type
    # Filter valid types for total_slots
    valid_types = []
    
    # Rectangular: Is there a grid for this size?
    # 3: 1x3
    # 4: 2x2, 1x4
    # 5: 1x5
    valid_types.append("rectangular")
    
    # Loop: Polygon sides = total_slots
    # 3: Triangle (valid)
    # 4: Square (valid)
    # 5: Pentagon (valid)
    valid_types.append("loop")
    
    # Triangular: Tapering 1, 2, 3...
    # Size 3 (1+2) is valid.
    # Size 6 (1+2+3) is > 5.
    # So only valid if total_slots == 3
    if total_slots == 3:
        valid_types.append("triangular")
        
    array_type = rng.choice(valid_types)
    
    # Configure Layout Params
    layout_params = {"type": array_type, "total_slots": total_slots}
    
    if array_type == "rectangular":
        if total_slots == 4:
            # 2x2 or 1x4 (more likely 2x2 for "array"-ness)
            if rng.random() < 0.8:
                layout_params.update({"rows": 2, "cols": 2})
            else:
                layout_params.update({"rows": 1, "cols": 4})
        else:
            layout_params.update({"rows": 1, "cols": total_slots})
    elif array_type == "loop":
        # Shape matches sides
        shape_map = {3: "triangle", 4: "square", 5: "pentagon"}
        layout_params.update({"path_shape": shape_map[total_slots]})
    elif array_type == "triangular":
        # Size 3 is fixed structure
        pass
        
    # Mesh Probability (Uncommon = 25%)
    draw_mesh = (rng.random() < 0.25)
    layout_params["draw_mesh"] = str(draw_mesh).lower()
    
    # Assign Nulls
    # Randomly pick indices to be null
    indices = list(range(total_slots))
    null_indices = set(rng.sample(indices, num_nulls))
    
    # Differentiator Setup
    # Features per NON-NULL position
    # We need to map logical "Item 0..2" to physical slots?
    # Or just have feature keys for all slots, and nulls obscure them?
    # Easier to have feature keys for all slots.
    
    feature_keys = []
    for i in range(total_slots):
        if i in null_indices:
            continue
        feature_keys.append(f"shape_{i}")
        feature_keys.append(f"fill_{i}")
        
    # Pick target differentiator
    diff_key = rng.choice(feature_keys)
    
    max_attempts = 1000
    for attempt in range(max_attempts):
        options = []
        
        is_shape_diff = diff_key.startswith("shape")
        pool = COMMON_SHAPES if is_shape_diff else FILLS
        
        common_val = rng.choice(pool)
        unique_val = rng.choice([x for x in pool if x != common_val])
        
        correct_idx = rng.randint(0, N_OPTIONS - 1)
        
        for i in range(N_OPTIONS):
            opt = {}
            # Copy layout params
            opt.update(layout_params)
            opt["null_indices"] = list(null_indices) # Store for renderer
            
            # Set differentiator
            if i == correct_idx:
                opt[diff_key] = unique_val
            else:
                opt[diff_key] = common_val
            
            # Set other features
            for key in feature_keys:
                if key == diff_key:
                    continue
                
                is_shape = key.startswith("shape")
                local_pool = COMMON_SHAPES if is_shape else FILLS
                opt[key] = rng.choice(local_pool)
            
            opt["is_correct"] = (i == correct_idx)
            options.append(opt)
            
        # VALIDATION
        extractors = {}
        
        # Local properties
        for key in feature_keys:
            extractors[key] = (lambda k: lambda o: o[k])(key)
            
        # Derived properties (Counts)
        for s in COMMON_SHAPES:
            extractors[f"total_{s}"] = lambda o, s=s: sum(1 for k in o if k.startswith("shape") and o[k] == s)
            
        for f in FILLS:
            extractors[f"total_{f}"] = lambda o, f=f: sum(1 for k in o if k.startswith("fill") and o[k] == f)
            
        conflicts = check_derived_parameters(options, extractors)
        
        valid = True
        for c in conflicts:
            if c["answer_index"] != correct_idx:
                valid = False
                break
        
        if valid:
            opt_strs = [json.dumps({k:v for k,v in o.items() if k != "is_correct"}, sort_keys=True) for o in options]
            if len(set(opt_strs)) < N_OPTIONS:
                valid = False
                
        if valid:
            return {
                "seed": seed,
                "type": "Odd One Out",
                "template": "template3",
                "options": options,
                "differentiator": diff_key,
                "array_size": total_slots
            }
            
    raise RuntimeError(f"Failed to generate valid question after {max_attempts} attempts")

def render_option_svg(opt: dict) -> str:
    """Render array of shapes with variable layout."""
    rows = opt.get("rows", "1")
    cols = opt.get("cols", str(opt["total_slots"]))
    draw_mesh = opt.get("draw_mesh", "false")
    
    # Construct XML for nvr_draw_layout
    array_attrs = {
        "type": opt["type"],
        "draw_mesh": draw_mesh,
        "draw_full_grid": "false" # Always false per spec for null handling
    }
    
    if opt["type"] == "rectangular":
        array_attrs["rows"] = str(rows)
        array_attrs["cols"] = str(cols)
    elif opt["type"] == "loop":
        array_attrs["path_shape"] = opt["path_shape"]
        array_attrs["positions"] = "vertices" # Default for now
        array_attrs["count"] = str(opt["total_slots"])
    elif opt["type"] == "triangular":
        # Triangular doesn't need explicit size if inferred, but library might need it?
        # Library infers from children.
        pass
        
    array_el = ET.Element("array", **array_attrs)
    
    total_slots = opt["total_slots"]
    null_indices = set(opt["null_indices"])
    
    for i in range(total_slots):
        if i in null_indices:
            # Add null element
            ET.SubElement(array_el, "null")
            continue
            
        shape_type = opt[f"shape_{i}"]
        fill_type = opt[f"fill_{i}"]
        
        shading = fill_type
        if shading == "solid_black": shading = "black"
        
        ET.SubElement(array_el, "shape", key=shape_type, shading=shading)
        
    diagram_el = ET.Element("diagram")
    diagram_el.append(array_el)
    
    return layout_lib.render_diagram_to_svg(diagram_el)

def generate_xml_output(questions: list[dict], output_file: Path | None = None) -> str:
    root = ET.Element("root")
    for q_data in questions:
        q_elem = ET.SubElement(root, "question_data")
        
        # Metadata
        ET.SubElement(q_elem, "type").text = q_data["type"]
        ET.SubElement(q_elem, "template").text = q_data["template"]
        ET.SubElement(q_elem, "seed").text = str(q_data["seed"])
        ET.SubElement(q_elem, "differentiator").text = q_data["differentiator"]
        
        # Options
        opts_elem = ET.SubElement(q_elem, "options")
        for i, opt in enumerate(q_data["options"]):
            opt_elem = ET.SubElement(opts_elem, "option")
            opt_elem.set("correct", str(opt["is_correct"]).lower())
            
            # Render SVG
            svg_str = render_option_svg(opt)
            
            svg_elem = ET.SubElement(opt_elem, "svg_content")
            svg_elem.text = svg_str
            
            # Store params
            # Filter internal keys for cleaner param storage if desired, but keeping all is good for debug
            params_elem = ET.SubElement(opt_elem, "params")
            params_elem.text = json.dumps({k:v for k,v in opt.items() if k != "is_correct"})

    # Pretty print
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
    
    output_path = args.output
    if output_path and (output_path.is_dir() or not output_path.suffix):
        # Batch Mode
        seed = args.seed if args.seed is not None else rng.randint(0, 2**32 - 1)
        try:
            q = generate_question(seed)
        except RuntimeError as e:
            print(f"Error generating question: {e}")
            sys.exit(1)

        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
            
        meta = {
            "template_id": "template3",
            "seed": seed,
            "correct_index": next(i for i, o in enumerate(q["options"]) if o["is_correct"]),
            "question_text": "Which option is the odd one out?",
            "explanation": f"The odd one out is distinguished by {q['differentiator']}.",
            "option_files": [f"option-{chr(97+i)}.svg" for i in range(N_OPTIONS)],
            "params": {k:v for k,v in q.items() if k != "options"}
        }
        with open(output_path / "question_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            
        for i, opt in enumerate(q["options"]):
            svg_content = render_option_svg(opt)
            with open(output_path / meta["option_files"][i], "w", encoding="utf-8") as f:
                f.write(svg_content)
                
        # Debug XML
        q_xml = generate_xml_output([q])
        with open(output_path / "question.xml", "w", encoding="utf-8") as f:
            f.write(q_xml)
            
    else:
        # File/Stdout Mode
        questions = []
        count = args.count if args.count else 1
        current_seed = args.seed if args.seed is not None else rng.randint(0, 2**32 - 1)
        local_rng = random.Random(current_seed)
        
        for _ in range(count):
            s = local_rng.randint(0, 2**32 - 1)
            try:
                q = generate_question(s)
                questions.append(q)
            except RuntimeError:
                continue
            
        xml_out = generate_xml_output(questions)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(xml_out)
        else:
            print(xml_out)

if __name__ == "__main__":
    main()
