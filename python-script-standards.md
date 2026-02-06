# Standards for Generated Python Scripts

This document defines naming conventions, prefixes, and output expectations for Python scripts used in NVR/picture-based question generation and shape asset production.

---

## 1. Script categories and prefixes

Scripts are grouped into five categories. Each category has a **required filename prefix** so that role and reusability are clear.

**Expendable vs non-expendable generators:** You may freely delete and regenerate **`gen_question_*`**, **`gen_sample_*`**, and **`gen_temp_*`** scripts; they should stay thin (orchestrate only; reusable logic in `nvr_logic_*`). **`nvr_draw_*`** scripts are **not** expendable: they contain (or are the sole entry point for) the shape geometry, motif placement, and partition logic that other generators depend on. Do not delete them without first moving that logic into `nvr_logic_*` and making the script a thin wrapper.

**Generator scripts** (scripts that produce outputs) are split into four kinds:

- **Draw / shape scripts** (`nvr_draw_`) — produce shape-related building blocks (single shape containers, batches, arrays). **Not expendable:** they hold the core logic other scripts rely on.
- **Question generators** (`gen_question_`) — produce the full set of answer-option images for a question (e.g. odd-one-out). Expendable; use `nvr_logic_*` and call `nvr_draw_*`.
- **Sample generators** (`gen_sample_`) — produce sample or showcase outputs for demos, docs, or development. Expendable; may call `nvr_logic_*` and `nvr_draw_*`.
- **Temporary generators** (`gen_temp_`) — one-off or exploratory work done by the agent (Cursor); may be deleted or rewritten.

### 1.1 Reusable logic modules (`nvr_logic_`)

**Prefix:** `nvr_logic_`

**Purpose:** All **reusable logic** (weighted choice, parameter splits, etc.) lives here. Code that is **imported** by `gen_*` and `nvr_draw_*` scripts. Use for:

- Weighted choice, sampling, parameter splits
- (Future) shape geometry, paths, point-in-polygon, motif placement, partition/hatch building—if extracted from `nvr_draw_*`

**Naming:** `nvr_logic_<name>.py` where `<name>` is a short, lowercase, underscore-separated identifier.

**Location:** All `nvr_logic_*` scripts live in a **`lib/`** directory (e.g. `sample-nvr-odd-one-out/lib/`).

**Current:** `lib/nvr_logic_frequency.py`, `lib/nvr_logic_param_splits.py`.

**Rules:**

- No `if __name__ == "__main__":` required; if present, it should only run minimal tests or demos.
- `gen_*` scripts that import them must add `lib/` to `sys.path` (e.g. `sys.path.insert(0, str(SCRIPT_DIR / "lib"))`) before importing.
- Dependencies should be other `nvr_logic_*.py` modules or the standard library where possible.

---

### 1.2 Draw / shape and asset generation (`nvr_draw_`)

**Prefix:** `nvr_draw_`

**Purpose:** Scripts that produce **shape-related building blocks**: single shape SVGs, batches of shape containers, arrays of shapes, or other diagram primitives. Outputs are used by `gen_question_*` and `gen_sample_*` (subprocess or import). They contain the core draw logic (geometry, motif placement, partitions).

**Naming:** `nvr_draw_<description>.py` where `<description>` describes the output.

**Location:** All `nvr_draw_*` scripts live in a **`lib/`** directory (e.g. `sample-nvr-odd-one-out/lib/`). `gen_*` scripts invoke them via `SCRIPT_DIR / "lib" / "nvr_draw_<name>.py"` or import from `lib/` after adding it to `sys.path`.

**Current scripts in this project:**

| Script | Purpose |
|--------|---------|
| `lib/nvr_draw_container_svg.py` | Single shape-container SVG (optionally with motifs, or partitioned). Default output `output/` or `-o path`. Used by all question and sample scripts that need one shape. |
| `lib/nvr_draw_containers_to_nvr_symbols.py` | Batch: one empty shape container per shape type; writes to `../nvr-symbols/shape-*.svg`. Run once to populate the repo’s shape outline assets. |
| `lib/nvr_draw_array_svg.py` | One SVG of a regular grid of shapes (rows × cols). Output via `-o`; used by `gen_sample_array.py`. |
| `lib/nvr_draw_array_partitioned.py` | 2×2 and 3×2 arrays of partitioned shapes; writes cell SVGs and combined inlined SVGs to `output/`. |

**Rules:**

- **Not expendable:** These scripts contain the shape/motif/partition logic that `gen_question_*` and `gen_sample_*` depend on. Do not delete them without first extracting that logic into `nvr_logic_*` and reducing the script to a thin wrapper.
- May be invoked as **subprocess** (path `lib/nvr_draw_<name>.py`) or **imported** (with `lib/` on `sys.path`).
- Output locations: either a path passed in (e.g. `-o path`) or a default under the project `output/` or repo `nvr-symbols/` as appropriate. When run from `lib/`, scripts resolve repo root and `output/` relative to the project root (parent of `lib/`).
- Docstring must state what is generated and where (paths and filenames).

---

### 1.3 Template question generation (`gen_question_`)

**Prefix:** `gen_question_`

**Purpose:** Scripts that implement a **question template** from the guide (e.g. picture-based-questions-guide.md §4) and produce the **full set of answer-option images** for one question (e.g. 5 options for odd-one-out).

**Naming:** `gen_question_<template_id>.py` where `<template_id>` identifies the template (e.g. `template1`, `template2`, `odd_one_out_shape`).

**Examples (target names):**

| Current / example              | Standard name                    |
|--------------------------------|----------------------------------|
| `generate_template1_options.py`| `gen_question_template1.py`     |
| `generate_template2_options.py`| `gen_question_template2.py`     |

**Rules:**

- **Expendable:** No substantial library logic; use `nvr_logic_*` and call `nvr_draw_*` as needed.
- Must produce the **standard question output set** (see §2 below).
- Docstring must cite the template (e.g. “Template 1”, “picture-based-questions-guide.md §4.1”) and list variators/differentiators.

---

### 1.4 Sample and showcase generation (`gen_sample_`)

**Prefix:** `gen_sample_`

**Purpose:** Scripts that produce **sample or showcase outputs** for development, demos, or documentation: e.g. one SVG per symbol in a shape, partitioned showcases, array samples. They do **not** implement a full question template; they illustrate vocabulary or layout.

**Naming:** `gen_sample_<description>.py` where `<description>` is short and lowercase (e.g. `motif_shape_combinations`, `partitioned`, `partitioned_showcase`, `array`).

**Examples (target names):**

| Current / example               | Standard name                             |
|---------------------------------|-------------------------------------------|
| `generate_all_symbols_in_square.py` | `gen_sample_motif_shape_combinations.py` |
| `generate_partitioned_samples.py`   | `gen_sample_partitioned.py`       |
| `generate_partitioned_showcase.py`   | `gen_sample_partitioned_showcase.py` |
| `generate_array_samples.py`      | `gen_sample_array.py`             |

**Rules:**

- **Expendable:** No substantial library logic; use `nvr_logic_*` and call `nvr_draw_*` as needed.
- Outputs go to a project `output/` (or path specified by CLI). Filenames should be descriptive and consistent.
- May call `nvr_draw_*` scripts (subprocess or import) and must import `nvr_logic_*` for any reusable logic.

---

### 1.5 Temporary / agent work (`gen_temp_`)

**Prefix:** `gen_temp_`

**Purpose:** Scripts created by the **agent (Cursor)** for temporary or exploratory work: quick experiments, one-off outputs, debugging, or try-outs. These are **not** part of the long-term question or sample pipeline; they may be overwritten or removed.

**Naming:** `gen_temp_<description>.py` where `<description>` is short and lowercase (e.g. `debug_placement`, `try_heart_path`, `explore_splits`).

**Rules:**

- **Expendable:** No substantial library logic; use `nvr_logic_*` for any reusable code.
- No commitment to stable output paths or naming; may write to `output/` or a throwaway folder.
- Prefer **gen_temp_** for any new generator script the agent creates unless the output is clearly a question set (use **gen_question_**) or a documented sample/showcase (use **gen_sample_**).

---

## 2. Output files for question generation scripts

Any script in the **gen_question_** category must produce the following.

### 2.1 Required outputs

- **Option images:** One image file per answer option. For a 5-option multiple-choice question:
  - `option-a.svg`, `option-b.svg`, `option-c.svg`, `option-d.svg`, `option-e.svg`
  - Or equivalent names (e.g. `option-1.svg` … `option-5.svg`) if the project standard differs.
- **Location:** All option images for a single run must be written into the **same directory**. Default: `<script_dir>/output/`. Overridable via CLI (e.g. `--output-dir`).

### 2.2 Optional but recommended outputs

- **Metadata (optional):** A small JSON or text file in the same directory that records:
  - Which option is the correct answer (e.g. `correct_option: "b"` or `correct_index: 1`).
  - Template id and seed (e.g. `template_id: "template1"`, `seed: 42`) so the run is reproducible.
  - Variators/differentiator used (e.g. for debugging or authoring).
- **Naming:** e.g. `question_meta.json` or `options_meta.json` in the same directory as the option SVGs.

### 2.3 What must not be required

- A question generation script is **not** required to produce question text, database rows, or URLs. It is only required to produce the **option image files** (and optionally the metadata file) so that other tools or the site can attach them to questions.

---

## 3. Summary table

| Category        | Prefix         | Expendable? | Purpose                          | Output (if applicable)     |
|----------------|----------------|-------------|----------------------------------|----------------------------|
| **Logic**      | `nvr_logic_`   | No          | Reusable logic (imported by gen_*, nvr_draw_*) | —                          |
| Draw/shape     | `nvr_draw_`    | **No**      | Building blocks; hold core shape/motif logic | Per-script (see docstring) |
| Question       | `gen_question_`| Yes         | Full question option set         | §2: option-a.svg … (+ optional meta) |
| Sample         | `gen_sample_`  | Yes         | Demos, samples, showcases        | Per-script (e.g. under `output/`) |
| Temporary      | `gen_temp_`    | Yes         | One-off / exploratory (Cursor)   | Ad hoc; may be throwaway   |

---

## 4. Migration note

**Migration completed:** Scripts in `sample-nvr-odd-one-out/` have been renamed to the standard prefixes. When adding new scripts, use the prefixes above. Keep references (imports, subprocess calls, batch files, docs) in sync with these names.

**Logic vs draw vs generators:** Reusable logic belongs in **nvr_logic_***. **nvr_draw_*** scripts are **not** expendable—they contain the core shape/motif/partition logic; do not delete them without moving that logic to nvr_logic_* first. **gen_question_***, **gen_sample_***, and **gen_temp_*** are expendable; keep them thin (orchestrate only; use nvr_logic_* and nvr_draw_*). When adding or rewriting an expendable gen_* script, keep any reusable logic in nvr_logic_*.
