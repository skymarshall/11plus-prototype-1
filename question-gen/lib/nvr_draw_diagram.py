#!/usr/bin/env python3
"""
Render question/diagrams XML to SVG files.

Supports roots: question, questions, diagrams. For each diagram that is a
**single shape container** (optionally with partition, no nested scatter/stack/array),
produces one SVG using nvr_draw_single_shape (nvr_draw_container_svg).
Other diagrams are skipped (with a message).

Usage (from question-gen root):
  python lib/nvr_draw_diagram.py path/to/file.xml [-o output_dir] [--prefix name]
  python lib/nvr_draw_diagram.py sample/sample-partitioned-extensive.xml -o output

Output: one SVG per renderable diagram. With -o dir: diagram-0.svg, diagram-1.svg, ...
or diagram-{id}.svg when diagram has id. With single question and single output, writes
to the path given by -o if it ends with .svg. Default output: project output/ (parent of lib/).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

import nvr_draw_single_shape as renderer

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent


def _iter_diagrams(root: ET.Element):
    """Yield (diagram_element, label) for each diagram in the document."""
    tag = root.tag
    if tag == "diagrams":
        for i, diagram in enumerate(root.findall("diagram")):
            did = diagram.get("id") or f"diagram-{i}"
            yield diagram, did
    elif tag == "question":
        for opt in root.findall("options/option"):
            diagram = opt.find("diagram")
            if diagram is not None:
                idx = opt.get("index", "")
                yield diagram, f"option-{idx}"
    elif tag == "questions":
        for q in root.findall("question"):
            qid = q.get("id", "")
            for opt in q.findall("options/option"):
                diagram = opt.find("diagram")
                if diagram is not None:
                    idx = opt.get("index", "")
                    yield diagram, f"{qid}-option-{idx}"
    else:
        raise ValueError(f"Unsupported root element: {tag!r}. Use question, questions, or diagrams.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render question/diagrams XML to SVG (single-shape diagrams only)."
    )
    parser.add_argument(
        "xml_path",
        type=Path,
        help="Path to question XML or diagrams XML.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output path: .svg file (single diagram) or directory (multiple: diagram-0.svg, ...).",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="diagram",
        help="Filename prefix when writing multiple SVGs (default: diagram).",
    )
    parser.add_argument(
        "--motifs-dir",
        type=Path,
        default=None,
        help="Directory for symbol shape SVGs (default: repo nvr-symbols).",
    )
    args = parser.parse_args()

    xml_path = args.xml_path
    if not xml_path.is_file():
        xml_path = _PROJECT_ROOT / xml_path
    if not xml_path.is_file():
        print(f"Error: not a file: {xml_path}", file=sys.stderr)
        return 1

    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        return 1

    root = tree.getroot()
    diagrams = list(_iter_diagrams(root))
    if not diagrams:
        print("No diagrams found in document.", file=sys.stderr)
        return 0

    # Which diagrams are single-shape (renderable)?
    to_render = []
    for diagram_el, label in diagrams:
        shape_el = renderer.shape_element_from_diagram(diagram_el)
        if shape_el is not None:
            to_render.append((shape_el, label))
        else:
            print(f"Skipping {label}: not a single shape without nested layout.", file=sys.stderr)

    if not to_render:
        print("No single-shape (non-nested) diagrams to render.", file=sys.stderr)
        return 0

    motifs_dir = args.motifs_dir
    out = args.output
    prefix = args.prefix

    if out is None:
        out = _PROJECT_ROOT / "output"
    out = out.resolve()

    if len(to_render) == 1 and out.suffix.lower() == ".svg":
        # Single output file
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            svg = renderer.render_shape_to_svg(to_render[0][0], motifs_dir=motifs_dir)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        out.write_text(svg, encoding="utf-8")
        print(f"Wrote {out}")
        return 0

    # Multiple outputs: write to directory
    if out.suffix.lower() == ".svg":
        out = out.parent
    out.mkdir(parents=True, exist_ok=True)

    for i, (shape_el, label) in enumerate(to_render):
        safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(label))
        path = out / f"{prefix}-{safe_label}.svg"
        try:
            svg = renderer.render_shape_to_svg(shape_el, motifs_dir=motifs_dir)
        except ValueError as e:
            print(f"Error rendering {label}: {e}", file=sys.stderr)
            continue
        path.write_text(svg, encoding="utf-8")
        print(f"Wrote {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
