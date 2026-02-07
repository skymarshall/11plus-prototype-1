# Batch question generation for database insert

This document describes **two scripts**: one that creates all question content (SVGs + manifest), and one that uploads the images and inserts questions into the database (see **question-gen/QUESTION-GENERATION-DESIGN.md** §9).

---

## 1. Two scripts

| Script | Purpose | Needs |
|--------|---------|--------|
| **Script 1: Create all question content** | Run template scripts many times; write option SVGs and a manifest. | Template scripts (e.g. `gen_question_template1.py`), output directory. No DB, no upload. |
| **Script 2: Do all the rest** | Upload option images to storage, then insert each question and its answer options into the database. | Manifest (from script 1), storage credentials, DB connection, subject/topic ids. |

Run script 1 first; then run script 2 when you are ready to upload and insert. Script 1 produces everything under e.g. `output/questions/` (one folder per question + `manifest.json`). Script 2 reads the manifest, uploads each folder, and performs the INSERTs.

---

## 2. Script 1: Create all question content

1. **Invokes template scripts**  
   For each question to generate, script 1 runs one of the template scripts (e.g. `gen_question_template1.py`) with a chosen seed and an **output directory** per question (e.g. `-o output/questions/q00001`). It may call the same template many times with different seeds, or mix templates.

2. **Captures output per question**  
   Each template run writes exactly **5 option SVGs** (e.g. `option-a.svg` … `option-e.svg`) and a **question_meta.json** into the per-question folder. Script 1 does not parse stdout; it reads `question_meta.json` from each folder to get the correct-answer index and any optional text/explanation.

3. **Builds the manifest**  
   For every generated question, script 1 adds a **manifest entry** (from that question's `question_meta.json`) that includes at least:
   - **Question id** (e.g. `q00001`) or a stable identifier
   - **Template id** (e.g. `template1`, `template2`)
   - **Correct option index** (0–4, i.e. which of option-a … option-e is correct)
   - **Paths (or filenames) of the 5 option image files** for that question (so the upload step knows what to upload and can map URLs back to options)
   - **Optional:** seed, question text (or template default text), **explanation** (post-answer hint shown to the user; stored in `questions.explanation`), subject/topic placeholders for INSERT

4. **Writes a single manifest file**  
   Script 1 writes one manifest (e.g. `output/questions/manifest.json`) that lists every generated question and the above metadata. Script 2 uses this manifest after uploading images to build `INSERT` statements for `questions` and `answer_options` (see guide §5).

---

## 3. Output layout (recommended)

Example layout under `sample-nvr-odd-one-out/output/`:

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
    q00002/
      option-a.svg
      ...
    q00003/
      ...
```

- **One subfolder per question** (`q00001`, `q00002`, …) so that upload can iterate over folders and assign one URL prefix per question (e.g. `https://cdn.example.com/options/q00001/option-a.svg`).
- **Manifest** at a fixed path (e.g. `output/questions/manifest.json`) so the insert step always knows where to read metadata.

---

## 4. Manifest format (for database insert)

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

- **Insert step** (after upload): for each question, build one `INSERT INTO questions (...)` (including `explanation` from the manifest when present) and one set of `INSERT INTO answer_options (question_id, option_text, option_image_url, is_correct, display_order)` using the question’s folder + `option_files` to form URLs (e.g. `{base_url}/q00001/option-a.svg`) and set `is_correct` from `correct_index`.

---

## 5. How script 1 runs templates

- **Per question:** create a folder (e.g. `output/questions/q00001/`), then run the template with that path as the output directory (e.g. `python gen_question_template1.py --seed 42 -o output/questions/q00001`). The template must support `-o` and write `option-a.svg` … `option-e.svg` and `question_meta.json` into that directory (see python-script-standards.md §2).
- **No stdout parsing:** script 1 reads `question_meta.json` from each question folder to get `correct_index`, optional `question_text` and `explanation`, and builds the single `manifest.json` from these files.

---

## 6. Script 2: Upload and insert (do all the rest)

Script 2 reads the manifest, uploads each question folder to storage, then connects to the database and inserts each question and its 5 answer options.

1. **Read manifest** — e.g. `output/questions/manifest.json`.
2. **Upload** — For each question folder, upload the 5 option SVGs to storage (e.g. Supabase Storage, S3). Record the **base URL** per question (e.g. `https://cdn.example.com/options/q00001/`).
3. **Insert** — For each question in the manifest: one row in `questions` (see guide §5: `question_text`, optional `question_image_url`, **`explanation`** from manifest, `subject_id` / `topic_id` / etc.), then 5 rows in `answer_options` (`option_image_url` = base URL + filename from `option_files`, `is_correct` from `correct_index`, `display_order` = 1..5).

**What script 2 needs:** manifest path, storage config (credentials / bucket), DB connection, subject/topic ids. Optional: dry-run mode that skips upload/insert and only validates the manifest.

### Where explanations/hints come from

The database stores one **explanation** per question (`questions.explanation`); this is the post-answer hint shown to the user (see question-gen/QUESTION-GENERATION-DESIGN.md §9 and 11plus-datamodel-design.md).

- **Template-generated:** The batch script (or the template script) can build a short explanation from the question's parameters—e.g. "The odd one out is option C: it is the only hexagon; the others are squares" when the differentiator is shape. Template scripts already know the differentiator and correct option, so they can write a one-line explanation into the metadata file the batch script reads.
- **Manual:** Leave `explanation` blank in the manifest and fill it in when editing questions, or add it in the insert step.
- **Later pass:** Generate explanations in a separate step (e.g. from manifest + template params) and merge into the manifest or into the DB after insert.

Including `explanation` in the manifest keeps everything needed for insert in one place.

---

## 7. Summary

| Script | Responsibility |
|--------|-----------------|
| **Script 1: Create all question content** | Run template scripts many times; put each run’s 5 SVGs in a per-question folder (via -o); read each question_meta.json; write manifest.json. No DB, no upload. Manifest has id, template_id, correct_index, option_files, question_text, explanation, seed  |
| **Script 2: Do all the rest** | Read manifest; upload each question folder to storage; connect to DB; insert each question and its 5 answer_options. Needs storage config, DB connection, subject/topic ids. |

Run script 1 to generate all content; run script 2 when you are ready to upload and insert into the database.
