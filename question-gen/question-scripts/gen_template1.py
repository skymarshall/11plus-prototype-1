#!/usr/bin/env python3
"""
Template 1 question generator: Odd One Out.
Type: Shape containing a scatter of motifs.
Structure: Common shape container with a scatter of motifs inside.
Variators: Shape, Fill, Motif Type, Motif Count.
Differentiator: One of the variators (Shape and Fill are Uncommon differentiators).
"""

import argparse
import json
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional

# Add lib to path (script is in question-gen/question-scripts, lib is in question-gen/lib)
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))

from lib.nvr_logic_param_splits import assign_split_to_indices, sample_split
from lib.nvr_logic_frequency import weighted_choice

N_OPTIONS = 5

# -- Definitions per Template 1 Spec --

COMMON_SHAPES = ["circle", "triangle", "square", "pentagon", "hexagon"]
SHADINGS = ["grey", "grey_light", "white"]

# Motifs suitable for scatter inside shapes
MOTIFS = [
    "circle", "plus", "times", "heart", "diamond", 
    "club", "spade", "square", "triangle", "star"
]

# Motif counts (e.g. 3 to 7 is a reasonable range for scatter)
MOTIF_COUNTS = list(range(3, 8))

# Line types for container shapes
LINE_TYPES = ["solid", "dashed", "dotted"]

# All possible variators for Template 1
ALL_VARIATORS = ["shape", "fill", "motif_type", "motif_count", "line_type"]

# Frequencies for differentiator choice
# Template 1: Differentiators: [Uncommon] shape, fill.
# Implicitly: motif_type, motif_count, and line_type are Common.
DIFF_WEIGHTS = [
    ("shape", "uncommon"),
    ("fill", "uncommon"),
    ("motif_type", "common"),
    ("motif_count", "common"),
    ("line_type", "common"),
]

def _generate_value_indices(
    n_options: int,
    is_differentiator: bool,
    correct_index: int,
    rng: random.Random,
    max_values: Optional[int] = None
) -> list[int]:
    """
    Generate indices for a parameter.
    If differentiator: 4 options get one value, 1 option (correct) gets another.
    If variator: use allowed splits so no option is unique.
    """
    if is_differentiator:
        # 4-1 split. 0 for common, 1 for unique/correct.
        # Requires 2 values.
        if max_values is not None and max_values < 2:
            raise ValueError(f"Differentiator requires at least 2 distinct values, but pool has {max_values}")
        indices = [0] * n_options
        indices[correct_index] = 1
        return indices
    else:
        # Allowed split (e.g. 2-3, 2-2-1)
        # We assume max 5 distinct values are available for most things.
        split = sample_split(n_options, rng, max_values=max_values)
        return assign_split_to_indices(split, n_options, rng)

def _get_values_from_pool(
    indices: list[int],
    pool: list[Any],
    rng: random.Random
) -> list[Any]:
    """
    Map abstract indices (0, 1, ...) to concrete values from pool.
    Ensures distinct values for distinct indices.
    """
    needed = max(indices) + 1
    if needed > len(pool):
        # If we need more values than available (unlikely for strict pools, but possible for small ones),
        # we strictly need 'needed' distinct values.
        # Fallback: allow duplicates if pool is too small? 
        # For NVR logic, distinct indices MUST map to distinct values.
        # If pool is too small, we can't satisfy the split.
        raise RuntimeError(f"Pool size {len(pool)} too small for {needed} distinct values.")
    
    # Select 'needed' distinct values
    chosen_values = rng.sample(pool, needed)
    
    # Map back
    return [chosen_values[i] for i in indices]

def generate_one(
    seed: int,
    question_id: str = "template1-q01",
    rng: Optional[random.Random] = None,
) -> ET.Element:
    rng = rng or random.Random(seed)

    # 1. Choose number of additional variators (2-4, plus fill which is mandatory)
    # Fill is mandatory to ensure visual variety in container shading
    num_additional = rng.randint(2, 4)
    
    # 2. Select random variators: fill is always included, plus 2-4 others
    other_variators = [v for v in ALL_VARIATORS if v != "fill"]
    selected_others = rng.sample(other_variators, num_additional)
    variator_keys = ["fill"] + selected_others
    
    # 3. Choose Differentiator from selected variators
    # Filter DIFF_WEIGHTS to only include selected variators
    available_diffs = [(k, w) for k, w in DIFF_WEIGHTS if k in variator_keys]
    differentiator = weighted_choice(rng, available_diffs)
    
    # 4. Choose Correct Index
    correct_index = rng.randint(0, N_OPTIONS - 1)
    
    # 5. Generate Values for each variator
    # We store the final values for each option here
    # options_data[opt_index] = { "shape": ..., "fill": ..., "line_type": ... }
    options_data = [{} for _ in range(N_OPTIONS)]
    
    # Set defaults for variators not selected (so XML generation always has values)
    for i in range(N_OPTIONS):
        options_data[i] = {
            "shape": "circle",  # default
            "fill": "white",    # default
            "motif_type": "circle",  # default
            "motif_count": 4,   # default
            "line_type": "solid",  # default
        }
    
    # Generate values for selected variators
    for key in variator_keys:
        is_diff = (key == differentiator)
        
        pool = []
        if key == "shape": pool = COMMON_SHAPES
        elif key == "fill": pool = SHADINGS
        elif key == "motif_type": pool = MOTIFS
        elif key == "motif_count": pool = MOTIF_COUNTS
        elif key == "line_type": pool = LINE_TYPES
        
        # Pass len(pool) as max_values for variators to ensure we pick a compatible split
        indices = _generate_value_indices(N_OPTIONS, is_diff, correct_index, rng, max_values=len(pool))
        values = _get_values_from_pool(indices, pool, rng)
        
        for i in range(N_OPTIONS):
            options_data[i][key] = values[i]

    # 5. Explanation
    # Simplified explanation logic
    val_correct = options_data[correct_index][differentiator]
    # Find a wrong option to get the 'common' value
    wrong_index = (correct_index + 1) % N_OPTIONS
    val_common = options_data[wrong_index][differentiator]
    
    diff_nice_name = differentiator.replace("_", " ")
    explanation = f"The odd one out has a distinct {diff_nice_name} ({val_correct}); the others have {val_common} or share a different distribution."
    # A better explanation would be specific to the split, but this suffices for now.
    if differentiator == "motif_count":
        explanation = f"The odd one out has {val_correct} motifs; the others have {val_common}."
    elif differentiator == "motif_type":
        explanation = f"The odd one out contains {val_correct}s; the others contain {val_common}s."

    # 6. Construct XML
    root = ET.Element("question", id=question_id, template_id="template1", seed=str(seed))
    ET.SubElement(root, "product", subject_code="nvr", topic_code="odd_one_out")
    
    qtext = ET.SubElement(root, "question_text")
    qtext.text = "Which shape is the odd one out?"
    
    expl = ET.SubElement(root, "explanation")
    expl.text = explanation
    
    options_el = ET.SubElement(root, "options")
    
    for opt in range(N_OPTIONS):
        data = options_data[opt]
        opt_el = ET.SubElement(options_el, "option", index=str(opt))
        diagram = ET.SubElement(opt_el, "diagram")
        
        # Shape Container
        # Note: 'fill' in parameter is usually shading. 
        # If shape contains motifs, fill should NOT be solid_black (design doc).
        # Our SHADINGS pool excludes black, so it's fine.
        shape_attrs = {
            "key": data["shape"],
            "shading": data["fill"],
            "line_type": data["line_type"],
        }
        shape_el = ET.SubElement(diagram, "shape", **shape_attrs)
        
        # Scatter of motifs
        scatter_el = ET.SubElement(shape_el, "scatter")
        
        # Add 'count' motifs of type 'motif_type'
        # Motifs default to medium in top-level, but small inside shapes?
        # Design doc: "Default is small for motifs at lower levels of nesting".
        # We'll set motif_scale="auto" or let renderer handle it, or explicit "small".
        # Design doc says: "when the template requests motifs... generator must mark those shapes as motifs... e.g. set motif_scale"
        # We will use motif_scale="small" (or just let renderer default). 
        # Actually template 3 uses no explicit scale for motifs inside array? No, template 3 is array of shapes.
        # Let's use `motif_scale="small"` to be safe as they are inside a container.
        
        count = data["motif_count"]
        m_type = data["motif_type"]
        
        for _ in range(count):
            ET.SubElement(scatter_el, "shape", key=m_type, motif_scale="medium", shading="black") 
            # Motifs usually black unless spec says otherwise.
            # Design doc: "Motifs are solid black by default."

    correct_el = ET.SubElement(root, "correct")
    correct_el.text = str(correct_index)

    return root

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Template 1 (Shape scatter) question XML.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output path (default: stdout)")
    parser.add_argument("--count", type=int, default=1, help="Number of questions to generate")
    parser.add_argument("--id-prefix", type=str, default="template1-q", help="Prefix for question ids")
    parser.add_argument("--id-width", type=int, default=2, help="Zero-pad width for question id numbers")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    questions = []
    for i in range(args.count):
        qid = f"{args.id_prefix}{str(i + 1).zfill(args.id_width)}"
        questions.append(generate_one(args.seed + i, question_id=qid, rng=rng))

    # Output logic handling directory for batch runner
    if args.output is None:
        if len(questions) == 1:
            ET.dump(questions[0])
        else:
            root = ET.Element("questions")
            root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
            root.set("xsi:noNamespaceSchemaLocation", "question-xml.xsd")
            for q in questions: root.append(q)
            ET.dump(root)
    else:
        out_path = args.output.resolve()
        
        # If output is a directory (or doesn't exist but has no socket/suffix implies dir for batch?), 
        # checking if we are in batch mode (count=1 but specific structure expected).
        # Actually batch runner passes a directory path to -o.
        # We should check if it looks like a directory or if we have 1 question.
        # Batch runner passes -o .../q00001 which is a directory.
        
        # For batch runner compatibility:
        # If we have 1 question and we are supposed to write assets:
        # Check if we should write to a directory.
        
        # Implementation: output to the directory specified by -o
        # Write option-a.svg ... option-e.svg and question_meta.json
        
        if len(questions) == 1:
            q = questions[0]
            # Ensure output dir exists
            out_path.mkdir(parents=True, exist_ok=True)
            
            # 1. Write metadata
            # Extract basic meta
            correct_idx = int(q.find("correct").text)
            q_text = q.find("question_text").text
            explanation = q.find("explanation").text
            
            meta = {
                "template_id": q.get("template_id"),
                "seed": int(q.get("seed")),
                "correct_index": correct_idx,
                "question_text": q_text,
                "explanation": explanation,
                "option_files": ["option-a.svg", "option-b.svg", "option-c.svg", "option-d.svg", "option-e.svg"]
            }
            
            with open(out_path / "question_meta.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
            
            # Write the question XML for review
            tree = ET.ElementTree(q)
            ET.indent(tree, space="  ")
            tree.write(out_path / "question.xml", encoding="unicode", default_namespace="", xml_declaration=True)
                
            # 2. Render SVGs
            # We need to import the renderer. 
            # We assume lib is in python path (it is inserted at top of script).
            from lib import nvr_draw_layout
            
            options_el = q.find("options")
            if options_el is None:
                raise ValueError("No options found in question XML")
                
            for i, opt in enumerate(options_el.findall("option")):
                if i >= 5: break
                filename = meta["option_files"][i]
                diagram = opt.find("diagram")
                if diagram is None:
                    continue
                
                # motifs_dir points to nvr-symbols in repository root
                # SCRIPT_DIR = question-gen/question-scripts
                # SCRIPT_DIR.parent = question-gen
                # SCRIPT_DIR.parent.parent = repository root (where nvr-symbols lives)
                repo_root = SCRIPT_DIR.parent.parent
                motifs_path = repo_root / "nvr-symbols"
                
                try:
                    # Use render_diagram_to_svg which properly handles scatter layouts
                    svg_content = nvr_draw_layout.render_diagram_to_svg(
                        diagram, 
                        motifs_dir=motifs_path, 
                        seed=int(q.get("seed"))
                    )
                    
                    with open(out_path / filename, "w", encoding="utf-8") as f:
                        f.write(svg_content)
                except Exception as e:
                    print(f"Error rendering option {i}: {e}", file=sys.stderr)
                    # Don't fail the whole batch, strictly?
                    # But for now let's raise
                    raise e

        else:
            # Multiple questions - batch runner shouldn't call us this way for 'content generation'.
            # It calls us once per question.
            # But if user calls manually with --count 5 -o file.xml:
            # We write a multi-question XML file.
            if out_path.suffix == ".xml":
                 root = ET.Element("questions")
                 root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
                 root.set("xsi:noNamespaceSchemaLocation", "question-xml.xsd")
                 for q in questions: root.append(q)
                 tree = ET.ElementTree(root)
                 ET.indent(tree, space="  ")
                 tree.write(out_path, encoding="unicode", default_namespace="", xml_declaration=True)
            else:
                 # Assume directory, write q01/..., q02/...
                 # Not strictly needed for the batch runner which does one by one.
                 print("Batch mode with count > 1 and output directory not fully implemented in this script override. Use batch runner.", file=sys.stderr)


if __name__ == "__main__":
    main()
