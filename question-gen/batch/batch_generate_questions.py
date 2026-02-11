#!/usr/bin/env python3
"""
Script 1: Create all question content (QUESTION-GENERATION-BATCH.md).

Runs template scripts many times with -o per question, reads each question_meta.json,
and writes a single manifest.json. No DB, no upload.

Usage:
  python gen_batch_questions.py --count 5
  python gen_batch_questions.py --count 5 --template gen_question_template1.py --output-dir output/questions
  python gen_batch_questions.py --seeds 42 43 44
  python gen_batch_questions.py --seeds 42 43 --template gen_question_template2.py

Requires template scripts that accept -o/--output-dir and --seed, and write
option-a.svg … option-e.svg and question_meta.json into that directory.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = SCRIPT_DIR / "gen_question_template1.py"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "output" / "questions"
META_FILENAME = "question_meta.json"
STANDARD_OPTION_FILES = [
    "option-a.svg",
    "option-b.svg",
    "option-c.svg",
    "option-d.svg",
    "option-e.svg",
]
MANIFEST_FILENAME = "manifest.json"
SUBPROCESS_TIMEOUT = 120


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate question content: run templates with -o per question, build manifest.json."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        metavar="DIR",
        help=f"Base directory for question folders and manifest. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        metavar="SCRIPT",
        help=f"Template script (must support -o and --seed, write question_meta.json). Default: {DEFAULT_TEMPLATE.name}",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--count",
        type=int,
        metavar="N",
        help="Generate N questions with auto seeds (100, 101, …).",
    )
    group.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        metavar="SEED",
        help="Use these seeds (one question per seed).",
    )
    parser.add_argument(
        "--id-prefix",
        type=str,
        default="q",
        help="Prefix for question ids (default: q → q00001, q00002, …).",
    )
    parser.add_argument(
        "--id-width",
        type=int,
        default=5,
        help="Zero-pad width for question id numbers (default: 5).",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    template_path = args.template.resolve()
    if not template_path.is_file():
        raise SystemExit(f"Template script not found: {template_path}")

    if args.count is not None:
        seeds = list(range(100, 100 + args.count))
    else:
        seeds = args.seeds

    questions: list[dict] = []
    base_dir = output_dir.name

    for i, seed in enumerate(seeds):
        qid = f"{args.id_prefix}{str(i + 1).zfill(args.id_width)}"
        question_dir = output_dir / qid
        question_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(template_path),
            "--seed",
            str(seed),
            "-o",
            str(question_dir),
        ]
        print(f"[{i + 1}/{len(seeds)}] {qid} (seed={seed}) … ", end="", flush=True)
        try:
            result = subprocess.run(
                cmd,
                cwd=SCRIPT_DIR,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            raise SystemExit(f"Template timed out for {qid}.")
        if result.returncode != 0:
            print("FAILED")
            if result.stderr:
                sys.stderr.write(result.stderr)
            raise SystemExit(f"Template failed for {qid} (exit {result.returncode}).")

        meta_path = question_dir / META_FILENAME
        if not meta_path.exists():
            raise SystemExit(f"Template did not write {META_FILENAME} in {question_dir}.")

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        entry = {
            "id": qid,
            "template_id": meta.get("template_id", args.template.stem.replace("gen_question_", "").replace("_template", "")),
            "correct_index": meta["correct_index"],
            "option_files": meta.get("option_files", STANDARD_OPTION_FILES),
            "question_text": meta.get("question_text"),
            "explanation": meta.get("explanation"),
            "seed": meta.get("seed", seed),
        }
        questions.append(entry)
        print("ok")

    manifest = {"base_dir": base_dir, "questions": questions}
    manifest_path = output_dir / MANIFEST_FILENAME
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {manifest_path} ({len(questions)} questions).")


if __name__ == "__main__":
    main()
