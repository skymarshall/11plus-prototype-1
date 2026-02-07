# Picture-Based Questions – Guide

## Overview

This document describes how **picture-based questions** work in the 11+ practice platform: how they are stored in the database, where images live, and how to add both questions and pictures so the website can display them. For **NVR-style diagram questions**, it also defines a **consistent vector format (SVG)** and a **visual vocabulary** (motifs, line types, line terminations) so that diagrams look the same across questions and verbal descriptions can be used to generate pictorial assets (section 2–3).

The schema already supports images via **URLs** only (no binary data in the database). See **11plus-datamodel-design.md** → "Image support" for the column definitions.

### Editing this guide: question templates

**Question templates** (the example verbal templates and any listed NVR question templates in this document) **must not be changed** when making other updates to the guide. They are **edited by humans only**, unless the user explicitly asks for a template to be added, removed, or modified. When adding new sections, clarifying wording, or fixing typos elsewhere, leave all existing question templates unchanged.

---

## 1. How picture-based questions work

### Where images can appear

| Location | Table / column | Purpose |
|--------|----------------|---------|
| **Question** | `questions.question_image_url` | One image for the question (diagram, shape, graph, photo). Shown with or above the question text. |
| **Answer option** | `answer_options.option_image_url` | One image per option (e.g. multiple-choice shapes or pictures). Can be used with or instead of `option_text`. |

- Both columns are **optional** and **VARCHAR(500)** (store a single URL per question/option).
- **Question text** (`question_text`) is still required; it can describe the image, ask "What is shown?" or "Which shape…?", or stand alone if the image is self-explanatory.

### Typical patterns

- **Image-only question:** Set `question_image_url`; keep `question_text` short (e.g. "Look at the shape below. How many sides does it have?").
- **Image + text:** Same as above; use `question_text` for the actual question and LaTeX if needed.
- **Image options:** Set `option_image_url` on one or more `answer_options` (e.g. "Which diagram shows …?" with four diagram URLs). `option_text` can be empty, a label, or a fallback.
- **Mixed:** Question has `question_image_url` and some options have `option_image_url` and/or `option_text`.

The **website** will show an `<img>` when a URL is present (see section 7).

---

## 2. Diagram format and consistency

### Vector format (SVG) required for diagrams

All **diagram** assets for NVR and similar picture-based reasoning (shapes, sequences, odd-one-out, matrices, line drawings) **must** be produced in **SVG**. Raster formats (PNG, JPEG) are allowed only for **photos or complex artwork** where vector is not practical.

- **Why SVG:** Sharp at any size, small file size, editable, and compatible with the visual vocabulary below (motifs and line styles are defined in vector terms).
- **Consistency:** Using one format (SVG) ensures that the same dictionary of motifs and line styles can be applied uniformly when generating or editing diagrams.

### Consistency between diagrams

Diagrams across multiple questions must make **consistent choices** so that:

- The same concept (e.g. `circle`, `dashed`) looks the same in every question.
- Authors and AI refer to a single **visual vocabulary** (motifs, line types, line terminations) so verbal descriptions map unambiguously to pictures.

All diagram authoring and AI-assisted generation must use the **NVR visual vocabulary** (section 3). Do not introduce ad hoc motifs or line styles; extend the dictionaries only when needed and then use the new terms consistently.

---

## 3. NVR visual vocabulary (dictionaries)

The full **visual element definitions** (shape containers, motifs, line types, line terminations, line augmentations, shading types, layout of motifs, shape stacks, partitioned shapes, and concepts: diagram sequences, arrays, symmetry) are now in the question generation design document:

- **question-gen/QUESTION-GENERATION-DESIGN.md** — **Section 4: Keywords and verbal question templates** → **NVR visual vocabulary (dictionaries)** and **Concepts**

Use that section as the single source of truth for all NVR vocabulary keys, tables, and layout/symmetry rules. This guide retains sections 1–2 (how picture-based questions work, diagram format and consistency) and sections 4–7 (template pointer, adding questions to the DB, uploading images, display).

---

## 4. Writing verbal question templates

The full rules for writing verbal question templates (parameters, variators, differentiator, parameter choice rules, frequency modifiers, and example templates) are in the question generation design document:

- **question-gen/QUESTION-GENERATION-DESIGN.md** — **Section 4: Keywords and verbal question templates**

That section includes both the **NVR visual vocabulary** (visual element definitions) and the full template-writing rules. Use it when authoring or compiling question templates for the generation pipeline.

---
## 5. Adding questions to the database

### Prerequisites

- Images are already **uploaded** and you have a **stable public URL** for each (see section 6).
- You know the correct `subject_id` and `topic_id` (from `subjects` and `topics`).

### Insert a question with a question image

```sql
INSERT INTO questions (
  subject_id,
  topic_id,
  question_type,
  question_text,
  question_image_url,
  explanation,
  points,
  time_limit_seconds
) VALUES (
  (SELECT id FROM subjects WHERE code = 'MATH'),
  (SELECT id FROM topics WHERE subject_id = (SELECT id FROM subjects WHERE code = 'MATH') AND name = 'Shapes' AND parent_topic_id IS NULL),
  'multiple_choice',
  'Look at the shape below. How many sides does it have?',
  'https://your-storage.example.com/questions/shape-hexagon.png',
  'The shape has 6 sides, so it is a hexagon.',
  1,
  90
)
RETURNING id;
```

### Insert answer options with images

```sql
INSERT INTO answer_options (question_id, option_text, option_image_url, is_correct, display_order)
VALUES
  ((SELECT id FROM questions WHERE question_image_url = 'https://your-storage.example.com/questions/shape-hexagon.png' LIMIT 1), '', 'https://your-storage.example.com/options/option-a.svg', false, 1),
  ((SELECT id FROM questions WHERE question_image_url = 'https://your-storage.example.com/questions/shape-hexagon.png' LIMIT 1), '', 'https://your-storage.example.com/options/option-b.svg', false, 2),
  ((SELECT id FROM questions WHERE question_image_url = 'https://your-storage.example.com/questions/shape-hexagon.png' LIMIT 1), '', 'https://your-storage.example.com/options/option-c.svg', true, 3),
  ...
```

---

## 6. Uploading and hosting images

- **Storage:** Upload SVG (or PNG/JPEG) files to your chosen storage (e.g. Supabase Storage, S3, CDN). Obtain a **stable public URL** for each file.
- **URLs:** Store only the URL in `question_image_url` or `option_image_url`; the database does not store binary image data.
- **CORS / caching:** Ensure your storage allows the front-end origin to load images and set appropriate cache headers if needed.

---

## 7. Display on the website

For **diagrams and NVR-style graphics** (shapes, sequences, odd-one-out, line drawings):

- **SVG is required.** All such assets must be produced in SVG and must use only the **NVR visual vocabulary** (section 3: shape containers, motif dictionary, line types, line terminations, line augmentations, shading types). Browsers render SVG from a URL the same way (`<img src="option-a.svg">`). See **question-gen** sample XML and generated output for examples.
