# Batch question generation for database insert

This document describes the **batch workflow** in three phases: (1) generate question XML from templates, (2) generate question files (SVGs + manifest) from that XML, and (3) upload assets and insert questions into the database. This aligns with the XML schema split in **question-gen/QUESTION-GENERATION-DESIGN.md** (Phases 3, 4, and 5).

A **single script or config file** holds the "knowledge" of which questions to run the batch for (template ids, seeds, counts, output paths). The three phases use this definition to drive generation, then render, then upload/insert.

---

## 1. Batch definition (single source of truth)

There must be a **single script or config file** that defines which questions the batch will generate. It is the only place that encodes:

- **Which questions** to generate (e.g. question ids, e.g. `q00001`, `q00002`, …)
- **Which template** to use per question (e.g. `template1`, `template2`)
- **Seeds** (or other parameters) per question for reproducibility
- **Output paths** (e.g. where to write question XML in phase 1, where to write question folders in phase 2)

Phase 1 and Phase 2 runners read this definition; Phase 3 (upload/insert) reads the manifest produced by Phase 2. The batch definition ensures one place to add/remove questions or change seeds without scattering that knowledge across multiple scripts.

---

## 2. Three phases

| Phase | Purpose | Needs |
|-------|---------|--------|
| **Phase 1: Generate question XML from templates** | Run template scripts (or a single batch script) to produce **question XML** for each question. No SVGs yet. | Batch definition (script/config), template scripts that emit question XML, output directory for XML. No DB, no upload. |
| **Phase 2: Generate question files** | Run the XML→SVG renderer on each question XML; write 5 option SVGs and `question_meta.json` per question; build one `manifest.json` for the batch. | Question XML from Phase 1 (or paths from batch definition), renderer from question-gen, output directory for question folders. No DB, no upload. |
| **Phase 3: Upload and insert** | Upload option images to storage, then insert each question and its answer options into the database. | Manifest (from Phase 2), storage credentials, DB connection, subject/topic ids. |

Run Phase 1, then Phase 2, then Phase 3 when you are ready to upload and insert. Phase 1 produces question XML (e.g. one file per question under a known layout). Phase 2 produces everything under e.g. `output/questions/` (one folder per question + `manifest.json`). Phase 3 reads the manifest, uploads each folder, and performs the INSERTs.

---

## 3. Phase 1: Generate question XML from templates

1. **Read the batch definition**  
   The runner (script or tool) reads the single script or config file that lists which questions to generate: question id, template id, seed (and any other parameters).

2. **Invoke template scripts per question**  
   For each question in the batch definition, the runner runs the appropriate template script (e.g. `gen_question_template1.py`) with the chosen seed and an **output path** for that question’s XML (e.g. `output/xml/q00001.xml`). Template scripts **emit question XML only** (they do not produce SVGs or metadata). They must conform to the question XML specification (see question-gen/QUESTION-XML-SPECIFICATION.md and question-xml.xsd).

3. **Output**  
   One **question XML file per question** in a known layout (e.g. `output/xml/q00001.xml`, `output/xml/q00002.xml`). Phase 2 will consume these files.

No manifest is produced in Phase 1; the batch definition plus the written XML files are the input to Phase 2.

---

## 4. Phase 2: Generate question files

1. **Input: question XML from Phase 1**  
   The Phase 2 runner reads the batch definition (or a list of XML paths) and runs the **XML→SVG renderer** (from question-gen) on each question XML file. The renderer does not run template scripts; it only consumes question XML and produces assets.

2. **Run renderer per question**  
   For each question XML (e.g. `output/xml/q00001.xml`), the runner invokes the renderer with that file and an **output directory** per question (e.g. `-o output/questions/q00001`). The renderer writes **5 option SVGs** (e.g. `option-a.svg` … `option-e.svg`) and **question_meta.json** into that directory.

3. **Build the manifest**  
   For every generated question, the Phase 2 runner adds a **manifest entry** (from that question’s `question_meta.json`) that includes at least:
   - **Question id** (e.g. `q00001`) or a stable identifier
   - **Template id** (e.g. `template1`, `template2`)
   - **Correct option index** (0–4, i.e. which of option-a … option-e is correct)
   - **Paths (or filenames) of the 5 option image files** for that question (so the upload step knows what to upload and can map URLs back to options)
   - **Optional:** seed, question text (or template default text), **explanation** (post-answer hint shown to the user; stored in `questions.explanation`), subject/topic placeholders for INSERT

4. **Write a single manifest file**  
   Phase 2 writes one manifest (e.g. `output/questions/manifest.json`) that lists every generated question and the above metadata. Phase 3 uses this manifest after uploading images to build `INSERT` statements for `questions` and `answer_options` (see §6).

---

## 5. Output layout (recommended)

Example layout under `sample-nvr-odd-one-out/output/`:

**After Phase 1 (optional intermediate):**
```
output/
  xml/
    q00001.xml
    q00002.xml
    q00003.xml
    ...
```

**After Phase 2 (and input to Phase 3):**
```
output/
  questions/
    manifest.json          # one manifest for the whole batch
    q00001/
      option-a.svg
      option-b.svg
      option-c.svg
      option-d.svg
      option-e.svg
      question_meta.json
    q00002/
      option-a.svg
      ...
    q00003/
      ...
```

- **One subfolder per question** (`q00001`, `q00002`, …) so that upload can iterate over folders and assign one URL prefix per question (e.g. `https://cdn.example.com/options/q00001/option-a.svg`).
- **Manifest** at a fixed path (e.g. `output/questions/manifest.json`) so the insert step (Phase 3) always knows where to read metadata.

---

## 6. Manifest format (for database insert)

The manifest should contain everything needed to build INSERTs **after** images are uploaded and URLs are known. Suggested shape (JSON):

- **Per question:**
  - `id` — e.g. `q00001` (matches folder name)
  - `template_id` — e.g. `template1`, `template2`
  - `correct_index` — 0–4 (0 = option-a, 1 = option-b, …)
  - `option_files` — list of 5 filenames in display order, e.g. `["option-a.svg", "option-b.svg", "option-c.svg", "option-d.svg", "option-e.svg"]`
  - `question_text` (optional) — e.g. “Which shape is the odd one out?” (or leave for insert step to set)
  - `explanation` (optional) — post-answer hint/explanation shown to the user (stored in `questions.explanation`). e.g. “The odd one out is option C because it is the only hexagon; the others are squares.” Can be generated from template params or left blank for manual fill.
  - `seed` (optional) — for reproducibility

Example `manifest.json`:

```json
{
  "base_dir": "questions",
  "questions": [
    {
      "id": "q00001",
      "template_id": "template1",
      "correct_index": 2,
      "option_files": ["option-a.svg", "option-b.svg", "option-c.svg", "option-d.svg", "option-e.svg"],
      "question_text": "Which shape is the odd one out?",
      "explanation": "The odd one out is option C: it is the only hexagon; the others are squares.",
      "seed": 42
    },
    {
      "id": "q00002",
      "template_id": "template2",
      "correct_index": 0,
      "option_files": ["option-a.svg", "option-b.svg", "option-c.svg", "option-d.svg", "option-e.svg"],
      "question_text": "Which shape is the odd one out?",
      "explanation": "The odd one out is option A: it is the only one with horizontal partition; the others use vertical.",
      "seed": 123
    }
  ]
}
```

- **Insert step** (Phase 3, after upload): for each question, build one `INSERT INTO questions (...)` (including `explanation` from the manifest when present) and one set of `INSERT INTO answer_options (question_id, option_text, option_image_url, is_correct, display_order)` using the question’s folder + `option_files` to form URLs (e.g. `{base_url}/q00001/option-a.svg`) and set `is_correct` from `correct_index`.

---

## 7. How Phase 1 and Phase 2 run

- **Phase 1 (per question):** From the batch definition, create the output path for this question's XML (e.g. `output/xml/q00001.xml`), then run the template script with the chosen seed and that output path (e.g. `python gen_question_template1.py --seed 42 -o output/xml/q00001.xml` or equivalent). The template script must emit **question XML only** (conforming to the question XML spec); it does not write SVGs or `question_meta.json`.
- **Phase 2 (per question):** Create a folder (e.g. `output/questions/q00001/`), then run the renderer with the question XML file and that folder as the output directory (e.g. renderer reads `output/xml/q00001.xml`, writes to `output/questions/q00001/`). The renderer writes `option-a.svg` … `option-e.svg` and `question_meta.json` into that directory. The Phase 2 runner reads `question_meta.json` from each question folder to get `correct_index`, optional `question_text` and `explanation`, and builds the single `manifest.json` from these files.

---

## 8. Phase 3: Upload and insert (do all the rest)

Phase 3 reads the manifest, uploads each question folder to storage, then connects to the database and inserts each question and its 5 answer options.

1. **Read manifest** — e.g. `output/questions/manifest.json`.
2. **Upload** — For each question folder, upload the 5 option SVGs to storage (e.g. Supabase Storage, S3). Record the **base URL** per question (e.g. `https://cdn.example.com/options/q00001/`).
3. **Insert** — For each question in the manifest: one row in `questions` (see guide §5: `question_text`, optional `question_image_url`, **`explanation`** from manifest, `subject_id` / `topic_id` / etc.), then 5 rows in `answer_options` (`option_image_url` = base URL + filename from `option_files`, `is_correct` from `correct_index`, `display_order` = 1..5).

**What Phase 3 needs:** manifest path, storage config (credentials / bucket), DB connection, subject/topic ids. Optional: dry-run mode that skips upload/insert and only validates the manifest.

### Where explanations/hints come from

The database stores one **explanation** per question (`questions.explanation`); this is the post-answer hint shown to the user (see question-gen/QUESTION-GENERATION-DESIGN.md §9 and 11plus-datamodel-design.md).

- **Template-generated:** The template script (Phase 1) can include a short explanation in the question XML; the renderer (Phase 2) passes it into `question_meta.json` and the manifest. E.g. "The odd one out is option C: it is the only hexagon; the others are squares" when the differentiator is shape. Template scripts already know the differentiator and correct option, so they can write a one-line explanation into the XML that the renderer preserves.
- **Manual:** Leave `explanation` blank in the manifest and fill it in when editing questions, or add it in the insert step.
- **Later pass:** Generate explanations in a separate step (e.g. from manifest + template params) and merge into the manifest or into the DB after insert.

Including `explanation` in the manifest keeps everything needed for insert in one place.

---

## 9. Summary

| Phase | Responsibility |
|-------|-----------------|
| **Batch definition** | Single script or config file lists which questions to generate (id, template id, seed, paths). Read by Phase 1 and Phase 2. |
| **Phase 1: Generate question XML** | Run template scripts per question from batch definition; each run emits one question XML file. No SVGs, no manifest. |
| **Phase 2: Generate question files** | Run renderer on each question XML; put each run's 5 SVGs and question_meta.json in a per-question folder; build manifest.json. No DB, no upload. Manifest has id, template_id, correct_index, option_files, question_text, explanation, seed. |
| **Phase 3: Upload and insert** | Read manifest; upload each question folder to storage; connect to DB; insert each question and its 5 answer_options. Needs storage config, DB connection, subject/topic ids. |

Run Phase 1 to generate all question XML; run Phase 2 to produce SVGs and manifest; run Phase 3 when you are ready to upload and insert into the database.
