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
ARRAY_SIZE = 3 # 1x3

COMMON_SHAPES = ["circle", "square", "triangle", "pentagon", "hexagon", "star", "cross", "diamond"]
FILLS = ["none", "solid_black", "grey", "grey_light", "diagonal_slash", "horizontal_lines"]

# Definition of features that can vary
# For an array of size 3, features are:
# Shape_0, Shape_1, Shape_2
# Fill_0, Fill_1, Fill_2
# (Total 6 possible variators)

def generate_question(seed: int) -> dict:
    rng = random.Random(seed)
    
    # 1. Setup
    # Differentiator: Pick one feature to be the Odd One Out rule.
    # e.g. "Shape at Pos 1"
    
    feature_keys = []
    for i in range(ARRAY_SIZE):
        feature_keys.append(f"shape_{i}")
        feature_keys.append(f"fill_{i}")
        
    # Pick target differentiator
    # Weights? Maybe equal.
    diff_key = rng.choice(feature_keys)
    
    # We need to generate N_OPTIONS
    # One is Correct (Unique value for diff_key, or Common value if 4:1 logic is inverted? 
    # Usually Odd One Out = 4 have X, 1 has Y. Y is correct.)
    
    max_attempts = 1000
    for attempt in range(max_attempts):
        options = []
        
        # Determine values for the differentiator
        # 4 options get "Common Value", 1 option gets "Unique Value"
        # Values depend on key type (shape or fill)
        is_shape_diff = diff_key.startswith("shape")
        pool = COMMON_SHAPES if is_shape_diff else FILLS
        
        common_val = rng.choice(pool)
        unique_val = rng.choice([x for x in pool if x != common_val])
        
        correct_idx = rng.randint(0, N_OPTIONS - 1)
        
        # Generate each option
        for i in range(N_OPTIONS):
            opt = {}
            # Set differentiator
            if i == correct_idx:
                opt[diff_key] = unique_val
            else:
                opt[diff_key] = common_val
            
            # Set other features (Variators)
            # Must avoid accidental 4:1 splits on THESE features
            # Simple approach: Random choice?
            # Or "Constraint-Based" from MD?
            # Let's try Random first, then Validate.
            
            for key in feature_keys:
                if key == diff_key:
                    continue
                
                is_shape = key.startswith("shape")
                local_pool = COMMON_SHAPES if is_shape else FILLS
                opt[key] = rng.choice(local_pool)
            
            opt["is_correct"] = (i == correct_idx)
            options.append(opt)
            
        # VALIDATION
        # Check derived parameters
        # We need to define extractors for relevant properties
        extractors = {}
        
        # Local properties
        for key in feature_keys:
            # Capture the value of key (e.g. shape_0)
            # Lambda must capture key!
            extractors[key] = (lambda k: lambda o: o[k])(key)
            
        # Derived properties (Counts)
        # Total Circles, Total Black, etc.
        for s in COMMON_SHAPES:
            extractors[f"total_{s}"] = lambda o, s=s: sum(1 for k in o if k.startswith("shape") and o[k] == s)
            
        for f in FILLS:
            extractors[f"total_{f}"] = lambda o, f=f: sum(1 for k in o if k.startswith("fill") and o[k] == f)
            
        # Check conflicts
        conflicts = check_derived_parameters(options, extractors)
        
        # Filter conflicts
        # A conflict is bad if it identifies a DIFFERENT option as the odd one out.
        # i.e. answer_index != correct_idx
        
        valid = True
        for c in conflicts:
            # c["answer_index"] matches i
            if c["answer_index"] != correct_idx:
                # Found an alternative solution!
                # e.g. Option 2 is unique in Shape_0, but Option 4 is unique in Total_Black.
                valid = False
                break
        
        if valid:
            # Also check for duplicate options (clones)
            # Serialize opt to json string for comparison (excluding is_correct)
            opt_strs = [json.dumps({k:v for k,v in o.items() if k != "is_correct"}, sort_keys=True) for o in options]
            if len(set(opt_strs)) < N_OPTIONS:
                valid = False # Clones exist
                
        if valid:
            return {
                "seed": seed,
                "type": "Odd One Out",
                "template": "template3",
                "options": options,
                "differentiator": diff_key,
                "array_size": ARRAY_SIZE
            }
            
    raise RuntimeError(f"Failed to generate valid question after {max_attempts} attempts")

def render_option_svg(opt: dict) -> str:
    """Render 1x3 array of shapes."""
    # Construct XML for nvr_draw_layout
    array_el = ET.Element("array", type="rectangular", rows="1", cols="3", draw_mesh="false", draw_full_grid="false")
    
    for i in range(ARRAY_SIZE):
        shape_type = opt[f"shape_{i}"]
        fill_type = opt[f"fill_{i}"]
        
        # Create shape element
        # Attributes for nvr_draw_layout: key, shading, line_type
        # mapping FILLS to shading
        # "solid_black" -> "black" (nvr_draw_layout uses "black", "solid_black")
        shading = fill_type
        if shading == "solid_black": shading = "black"
        
        shape_el = ET.SubElement(array_el, "shape", key=shape_type, shading=shading)
        
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
