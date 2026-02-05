# Picture-Based Questions – Guide

## Overview

This document describes how **picture-based questions** work in the 11+ practice platform: how they are stored in the database, where images live, and how to add both questions and pictures so the website can display them. For **NVR-style diagram questions**, it also defines a **consistent vector format (SVG)** and a **visual vocabulary** (symbols, line types, line terminations) so that diagrams look the same across questions and verbal descriptions can be used to generate pictorial assets (section 2–4).

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

The **website** will show an `<img>` when a URL is present (see section 8).

---

## 2. Diagram format and consistency

### Vector format (SVG) required for diagrams

All **diagram** assets for NVR and similar picture-based reasoning (shapes, sequences, odd-one-out, matrices, line drawings) **must** be produced in **SVG**. Raster formats (PNG, JPEG) are allowed only for **photos or complex artwork** where vector is not practical.

- **Why SVG:** Sharp at any size, small file size, editable, and compatible with the visual vocabulary below (symbols and line styles are defined in vector terms).
- **Consistency:** Using one format (SVG) ensures that the same dictionary of symbols and line styles can be applied uniformly when generating or editing diagrams.

### Consistency between diagrams

Diagrams across multiple questions must make **consistent choices** so that:

- The same concept (e.g. `circle`, `dashed`) looks the same in every question.
- Authors and AI refer to a single **visual vocabulary** (symbols, line types, line terminations) so verbal descriptions map unambiguously to pictures.

All diagram authoring and AI-assisted generation must use the **NVR visual vocabulary** (sections 3–4). Do not introduce ad hoc symbols or line styles; extend the dictionaries only when needed and then use the new terms consistently.

---

## 3. Polygon containers

**Polygon containers** are the outer shapes that may contain symbols (or other content) in a diagram. Use these names when describing "a square with two `circle`s inside" or "each answer is a regular polygon".

**Regular shape:** A **regular shape** is a **circle** or a **regular polygon** (equal sides and equal angles). When a template or description asks for a "regular polygon" or "regular shape" without specifying the number of sides, a random regular polygon should have **3–8 sides** (triangle through octagon) unless the template specifies otherwise.

**Position in answer image:** Unless the question template explicitly states otherwise (e.g. "offset to the left", "positioned at top"), **containers are centred vertically and horizontally** in the answer image. The polygon (or other outer frame) should be drawn so that its **centre coincides with the centre of the answer viewBox** (e.g. centre at (50, 50) in a 0 0 100 100 viewBox). **Triangles** (with one vertex at the top) are **centred vertically by default**: the vertical centre of the triangle's bounding box should coincide with the centre of the viewBox (e.g. at y = 50 in a 0 0 100 100 viewBox), so the triangle sits symmetrically in the vertical space.

**Size when containing symbols:** Any polygon that **contains symbols** must be **large enough** so that the required number of symbols fit inside with the specified margin (symbol centres inside the shape, symbol cell half-size clear of the boundary). In particular, **triangles** have less usable interior than squares for a given "radius"; the triangle must be drawn **large enough** (e.g. so its inscribed circle or equivalent usable area can accommodate the symbol count) and **centred** in the viewBox. Generators must use a triangle size that allows the same symbol counts as other shapes (e.g. n between 3 and 6) to be placed without overlap.

**Regularity:** Polygons are assumed **perfectly regular** (equal sides and equal angles) unless the question template specifies otherwise. For example, "triangle" means equilateral, "pentagon" means regular pentagon. If the template explicitly allows a non-regular shape (e.g. "rectangle" for a long shape), use that; otherwise draw regular polygons only. The table below lists the standard regular polygon keys (3–8 sides) and circle; for a random regular polygon, use 3–8 sides unless the template specifies otherwise.

| Key | Description | Notes |
|-----|-------------|-------|
| `triangle` | Regular triangle (3 sides) | Equilateral |
| `square` | Regular square (4 sides) | Same as rectangle with equal sides |
| `rectangle` | Rectangle (4 sides, two pairs equal) | Not regular unless template says "square"; use when template allows non-square quadrilateral |
| `pentagon` | Regular pentagon (5 sides) | |
| `hexagon` | Regular hexagon (6 sides) | |
| `heptagon` | Regular heptagon (7 sides) | |
| `octagon` | Regular octagon (8 sides) | |
| `circle` | Circle | Curved; use as outer frame when specified |

---

## 4. NVR visual vocabulary (dictionaries)

The following dictionaries define the **only** allowable symbols, line types, line terminations, and shading types for NVR-style diagram questions. Verbal descriptions of questions (and any AI that generates pictorial questions) must reference these by name. For **polygon containers** (outer frames), use section 3. Generated SVGs must use only these options so that `circle` or `dashed` is identical across questions.

**Vocabulary element** is the generic term for any single entry from these dictionaries: a **symbol** (e.g. `circle`, `heart`), a **line type** (e.g. `solid`, `dashed`), a **line termination** (e.g. `arrow_single`, `chevron`), or a **shading type** (e.g. `solid_black`, `diagonal_slash`). In this guide, all vocabulary elements are quoted in backticks when used as formal terms, e.g. `circle`, `dashed`, `arrow_single`. When writing a verbal question template, the generator chooses random vocabulary elements and sticks with those same choices for part or all of that question (see section 5).

### 4.1 Symbol dictionary

Symbols that can appear **inside** shapes, at line ends, or as standalone elements in a diagram. Use the **key** in verbal descriptions and when generating SVG (e.g. "use `circle` for the odd one out").

| Key | Description | Notes / SVG usage |
|-----|-------------|-------------------|
| `circle` | Circle filled solid | `<circle>` with `fill` (e.g. black or currentColor) |
| `cross` | Plus / cross (+) | Two perpendicular lines of equal length crossing at centre |
| `heart` | Playing card heart (♥) | Standard heart symbol |
| `diamond` | Playing card diamond (♦) | Rhombus filled |
| `club` | Playing card club (♣) | Three circles + stem, or simplified club shape |
| `spade` | Playing card spade (♠) | Inverted heart with stem |
| `square` | Square filled solid | `<rect>` with fill |
| `triangle` | Triangle filled solid | `<path>` or `<polygon>` with fill |
| `star` | Five-pointed star | Filled star |

The symbol dictionary applies to the **contents** of shapes (and to line terminations, see 4.3). For the **outer frame** that may contain symbols, use the polygon containers in section 3. For **canonical, consistent SVG** for each symbol (size 1⁄8 of a standard answer in each direction), use the fragments and files in **nvr-symbol-svg-design.md** and the **`nvr-symbols/`** folder.

**fill** of **symbols** should always be solid black unless the question specifies a **fill** variation should be used.

### 4.2 Polygon containers

**Polygon containers** are the outer shapes that may contain symbols (or other content) in a diagram. Use these names when describing "a `square` with two `circle`s inside" or "each answer is a regular polygon".

| Key | Description | Notes |
|-----|-------------|-------|
| `triangle` | Regular triangle (3 sides) | Equilateral |
| `square` | Regular square (4 sides) | Same as rectangle with equal sides |
| `rectangle` | Rectangle (4 sides, two pairs equal) | Not regular unless template says "square"; use when template allows non-square quadrilateral |
| `pentagon` | Regular pentagon (5 sides) | |
| `hexagon` | Regular hexagon (6 sides) | |
| `heptagon` | Regular heptagon (7 sides) | |
| `octagon` | Regular octagon (8 sides) | |
| `circle` | Circle | Curved; use as outer frame when specified |

**Regularity:** Unless the question template specifies otherwise, polygons are assumed **perfectly regular** (equal sides and equal angles). For example, "triangle" means equilateral, "pentagon" means regular pentagon. If the template explicitly allows a non-regular shape (e.g. "rectangle" for a long shape), use that; otherwise draw regular polygons only.

### 4.3 Line types

Permitted stroke styles for **lines** (borders of shapes, connectors, axes, etc.). Reference by key in verbal descriptions.

| Key | Description | SVG / usage |
|-----|-------------|-------------|
| `solid` | Continuous line | Default stroke, no dash array |
| `dashed` | Dashed line (e.g. equal dash and gap) | `stroke-dasharray` (e.g. `8 4`) |
| `dotted` | Dotted line | `stroke-dasharray` (e.g. `2 4`) |
| `bold` | Thicker solid line | Same as solid but `stroke-width` larger (e.g. 2× base) |

Use a **single base stroke-width** (e.g. 2 in a 100-unit viewBox) for `solid`, `dashed`, `dotted`; use a consistent multiplier (e.g. 2) for `bold` so `bold` is the same across all diagrams.

### 4.4 Line terminations

How a **line ends** (e.g. arrow, chevron, or a symbol). Use when describing "a line with an arrowhead" or "a line ending in a circle".

| Key | Description | Notes |
|-----|-------------|-------|
| `none` | No end cap / flat | Default line end |
| `arrow_single` | Single arrowhead (>) | One triangular arrowhead at end |
| `arrow_double` | Double arrowhead (>>) | Two arrowheads at end |
| `chevron` | Chevron (fat, tapered > shape) at end | Single chevron, not full triangle |
| `chevron_double` | Chevrons at both ends | >——< |
| `circle` | Circle at line end | Same as symbol `circle` at terminus |
| `cross` | Cross at line end | Same as symbol `cross` |

Any symbol from the **symbol dictionary** (4.1) may be used as a line termination if it makes sense (e.g. "line ends in a `heart`"). List only the most common above; others (`heart`, `diamond`, `club`, `spade`, etc.) are referenced by the same key as in 4.1.

### 4.5 Shading types

Permitted **fill / shading** for regions (e.g. inside a polygon, or a segment of a shape). Use when describing "the polygon is filled with grey" or "one half is `diagonal_slash`". Reference by key in verbal descriptions and when generating SVG.

| Key | Description | Notes / SVG usage |
|-----|-------------|-------------------|
| `solid_black` | Solid black fill | `fill="#000"` or `currentColor` |
| `grey` | Solid grey fill | `fill` with a mid grey (e.g. `#808080` or `#999`); use consistently across questions |
| `white` | No fill / white (unshaded) | `fill="none"` or `fill="#fff"`; region appears empty or white |
| `diagonal_slash` | Diagonal lines (/) | Hatched fill with lines running top-left to bottom-right; consistent spacing |
| `diagonal_backslash` | Diagonal lines (\\) | Hatched fill with lines running top-right to bottom-left; consistent spacing |
| `horizontal_lines` | Horizontal lines | Hatched fill with horizontal lines; consistent spacing |
| `vertical_lines` | Vertical lines | Hatched fill with vertical lines; consistent spacing |

Use a **consistent line spacing and stroke width** for hatched shadings (`diagonal_slash`, `diagonal_backslash`, `horizontal_lines`, `vertical_lines`) so the same key looks the same in every diagram. Shading can apply to the whole shape, to a segment, or to the **fill** of symbols (e.g. "symbol `circle` with `grey` fill").

### 4.6 Symbol layout inside shapes

When placing **multiple symbols inside a polygon container** (e.g. "a `square` with 10 `club`s inside"), choose a **layout** so that symbols do not overlap (see nvr-symbol-svg-design.md: centre-to-centre at least 12.5 in a 100×100 answer). Unless the question template states otherwise, use **randomly spaced** layout.

| Layout | Description | When to use |
|--------|-------------|-------------|
| **Randomly spaced** (default) | Symbols are placed at positions that **avoid overlap** but with **deliberately irregular spacing**: avoid a regular grid; vary horizontal and vertical gaps so the arrangement looks scattered, not aligned. | **Default** when the template does not specify a layout. |
| **Randomly clustered** | Symbols are concentrated in **one region** of the shape: **top**, **bottom**, **left**, or **right**. Specify which (e.g. "symbols clustered in the top half"). Positions within that region are irregular; symbols still must not overlap. | When the template asks for clustering (e.g. "clustered in the bottom", "grouped on the left"). |

---

## 5. Writing verbal question templates

When writing a **verbal question template** (e.g. for AI or a generator), the generator should **choose vocabulary elements at random** (one or more symbols, line types, line terminations, and/or shading types from sections 3–4) and **stick with those same choices** for part or all of that question. **Increase randomness:** use a random draw (or shuffle) when the template calls for a free choice—e.g. "each answer is a regular polygon (3–8 sides)" → draw randomly from the allowed set for each option, so that question-to-question and option-to-option outcomes are unpredictable. For example: "For this question, use symbol `circle`, line type `dashed`, and line termination `arrow_single` for every option." That keeps the question self-consistent and avoids mixing unrelated styles within a single item. The template may specify which vocabulary elements are fixed for the whole question and which (if any) vary per option.

### Step 1: Verbal description

Start with a **verbal description** of the question that:

- States the question type (e.g. odd-one-out, sequence, matrix, code).
- Describes each figure or option using only terms from the **NVR visual vocabulary** (sections 3–4): vocabulary elements (symbols, line types, line terminations, shading types) and standard polygon names (`square`, `triangle`, etc.). All such terms are quoted in this guide, e.g. `circle`, `dashed`, `arrow_single`.
- Identifies the correct answer and the rule (e.g. "odd one out is B because it has two circles").

### Terminology (parameters, global parameters, variators, differentiator)

- **Parameter:** A variable that can be chosen for each answer to the question (e.g. shape, line style, fill, symbol type, number of symbols). Parameters describe how each answer looks or is defined.
- **Global parameter:** A parameter whose value is **fixed for the entire question** (one value for all answers). This is the **default** for parameters that appear in the template **setup** (the part before the answer definitions). For example, "choose n between 3 and 6" makes n a global parameter; every answer uses that same n (except where the differentiator is symbol count and one answer uses n+1).
- **Variator:** A **per-answer** parameter whose value is allowed to **differ between answers**, subject to the split requirements for odd-one-out (see below). For odd-one-out questions, variators are all parameters that can vary per option; their value counts across options must obey the allowed splits so that no single option is uniquely different on a variator that is not the differentiator.
- **Differentiator:** For **odd-one-out** questions, the **parameter that determines the unique (correct) answer**. One of the variators specified in the template is always the differentiator. The correct answer is the one that differs from the others on the differentiator only (e.g. if the differentiator is shape, the correct answer has a different shape; if it is symbol count, it has a different number of symbols). The template need not specify which variator is the differentiator; if it does not, the generator chooses one of the specified variators.

### Parameter choice rules when generating answers

When generating NVR questions from templates that use parameters (e.g. random **symbol**, **shape**, or numerical values), apply the following so that answers are unambiguous and no accidental correct answers emerge. **Unless a template explicitly states otherwise**, assume: 5 options; **global parameters** (setup) have one value for the whole question; **variators** (per-answer parameters) are chosen at random for each option, **with duplication allowed**—two or more options may share the same shape, line style, fill, or symbol; random assignment to options (no fixed order); containers centred in the answer image; symbols inside the container with margin.

- **Number of options:** Unless explicitly stated in the question template, all multiple-choice questions should have **5 possible answers** (not 4).
- **Correct-answer position (uniform):** Unless the template specifies which option is correct (e.g. "option 2 is the odd one out"), the **correct answer should be uniformly distributed** over the option positions. For 5 options, the correct answer should be option 1, 2, 3, 4, or 5 with **equal probability** (e.g. each with probability 1⁄5). Do not fix the correct answer to a single position (e.g. always option 3).
- **Odd-one-out (general):** For **odd-one-out** questions, one of the variators specified in the template is the **differentiator** (the parameter that defines the correct answer). If the template does not specify which variator is the differentiator, the generator chooses one of the variators (e.g. **number of symbols**, **line type**, **fill**, **symbol type**, or **shape**). The **correct answer** is the one that **differs from the others on the chosen differentiator only** (e.g. if the differentiator is shape, the correct answer has a different shape; if it is symbol count, it has a different number of symbols). Unless the template states otherwise, the correct-answer position follows the defaults above (uniform over options).
- **No duplicate parameter sets:** No two possible answers may use an **identical set of parameters**. If answers are described by a combination of parameters (e.g. shape + symbol count), each option must differ in at least one parameter so that the intended correct answer is unique.
- **Odd-one-out parameter spread (variators):** Where the same description is used to generate multiple answers for **odd-one-out** questions, ensure that for each **variator** (per-answer parameter that is **not** the differentiator) the **value counts** across options obey the allowed splits below—so no single option is uniquely different on that variator. Rule: either **at least 3 different values** are used, or **if only 2 values** are used then **each value occurs at least twice** (e.g. never 4–1 for 5 options, never 3–1 for 4 options).

- **Allowed splits (value counts) per number of options:** For **variators** (parameters that do not determine the correct answer), generators should **vary** the distribution of values. Use these allowed splits (for 2 values only, each count ≥ 2). **5 options:** 2–3, 3–1–1, 2–2–1, 2–1–1–1, 1–1–1–1–1 (never 4–1). **4 options:** 2–2, 2–1–1 (never 3–1). **6 options:** 3–3, 2–2–2, 4–2, 4–1–1, 3–2–1, 3–1–1–1, 2–2–1–1, 2–1–1–1–1, 1–1–1–1–1–1 (never 5–1). Choose a split at random so that questions are not always 2–3 for 5 options.

- **Global parameters vs variators (where they are defined):**
  - **Global parameters (setup only):** Only parameters that appear **in the template setup** (the top part, **before** the answer definitions) are global; one value for the whole question. Typically this is a single choice such as "choose n between 3 and 6". The generator picks **one** value and uses it for **all** answers. **Do not** treat shape, line style, or fill as global unless the template explicitly places them in the setup and states "same for all".
  - **Variators (answer definitions):** Any parameter that describes **how each answer looks**—shape (polygon type), line style, fill, symbol count, and symbol type unless the template says "same symbol for all"—is a **variator** (per-answer). The generator **chooses at random** from the allowed set for each option, subject to the no-duplicate parameter-set and odd-one-out spread rules. **Randomness:** use a random draw or shuffle so that which option gets which value is unpredictable.

- **Duplication of variator values (default):** When the template calls for a **free choice** of a variator (e.g. "each answer is a regular polygon between 3 and 8 sides"), **duplication across options is explicitly allowed**. For example, two options may both be square, three may use `solid` line style, and two may use the same symbol. This is the **default**; the template need not state "duplication allowed". The generator **chooses at random** from the allowed values for each option (so the distribution varies), subject only to: (1) no two options have an **identical full set** of parameters (so the intended correct answer is unique), and (2) for odd-one-out, no single option is uniquely different on a variator that is **not** the differentiator (odd-one-out spread above).

- **Random assignment (no fixed order):** Variators (shapes, line styles, fills, symbols) must be **assigned randomly** to options 1–5 (e.g. by random draw or shuffle). Do **not** use a fixed order (e.g. option 1 = triangle, option 2 = square, option 3 = pentagon). Use a random process so that which option gets which value is unpredictable. When there are fewer variator values than options, **spread** repeats so no single value dominates and no option is the "only one" with a given value where that would confuse the intended rule (e.g. for odd-one-out by symbol count, avoid one option being the only square).

- **Symbols inside the containing shape:** Symbol centres must lie **inside** the polygon container, with a margin so that the full symbol cell does not cross the polygon edge. For non-rectangular shapes (e.g. triangle, pentagon), use a point-in-polygon check and require the minimum distance from the symbol centre to the polygon boundary to be at least the symbol cell half-size so that symbols remain fully inside the shape.

- **No black fill when shape contains symbols:** Do **not** use solid black fill (`solid_black`) for any polygon or container that contains symbols. Symbols are drawn in black (or currentColor); on a black background they would not be visible. When the shape has symbol content, use `white`, `grey`, or a hatched shading instead.

**Example (avoiding accidental correct answers):** Suppose each of the 5 options is "a quantity of a randomly chosen `symbol` inside a randomly chosen `shape`". The intended rule is "each shape contains 3 symbols, except the odd one out (e.g. option 2) which contains 4." The **differentiator** is symbol count. If the generator chose shapes as: 1. circle, 2. circle, 3. circle, 4. square, 5. circle, then option 4 (square) would be the only square and could be misinterpreted as another valid "odd one out". To avoid that, assign **variators** (here, shape) so that no single option is unique on a variator that is not the differentiator—e.g. use at least three distinct shapes (e.g. triangle, circle, circle, square, circle) or ensure each shape value appears at least twice (e.g. circle, circle, square, square, circle).

### Step 2: Generate pictorial assets (SVG)

From the verbal description:

- **AI or author** produces one SVG per question image and per option image.
- Use **only** the vocabulary elements from section 3 (symbols, line types, line terminations, shading types). Use a consistent viewBox (e.g. `0 0 100 100`) and base stroke-width across options so diagrams are comparable.
- **Containers centred:** Unless the question template explicitly states otherwise (e.g. "offset to the left", "positioned at top"), **polygon containers (and other outer frames) must be centred vertically and horizontally** in the answer image. The centre of the container should coincide with the centre of the viewBox (e.g. (50, 50) for viewBox 0 0 100 100).
- Save as `.svg` files (e.g. `option-a.svg` … `option-d.svg`) and host them; store the URLs in `question_image_url` / `option_image_url` as in section 5–6.

Verbal descriptions can be stored alongside the question (e.g. in a content pipeline or as comments) so that future edits or regeneration still reference the same vocabulary.

### Placeholder for example questions

Once this guide is approved, **10 example verbal NVR questions** will be added (or kept in a separate file) that reference the above dictionaries. Each will be in the form of a short verbal description suitable for feeding into diagram generation. All section 5 defaults (5 options, random per-answer choice **with duplication allowed**, containers centred, etc.) apply unless the template states otherwise; templates need not mention duplication.

**Example Question Template 1**

**Odd one out**

- **Setup:** 3 to 5 variators from **regular shape**, **line style**, **fill**, **symbol** or **number of symbols** 

---

## 6. Adding questions to the database

### Prerequisites

- Images are already **uploaded** and you have a **stable public URL** for each (see section 7).
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

## 7. Uploading and hosting images

- **Storage:** Upload SVG (or PNG/JPEG) files to your chosen storage (e.g. Supabase Storage, S3, CDN). Obtain a **stable public URL** for each file.
- **URLs:** Store only the URL in `question_image_url` or `option_image_url`; the database does not store binary image data.
- **CORS / caching:** Ensure your storage allows the front-end origin to load images and set appropriate cache headers if needed.

---

## 8. Display on the website

For **diagrams and NVR-style graphics** (shapes, sequences, odd-one-out, line drawings):

- **SVG is required.** All such assets must be produced in SVG and must use only the **NVR visual vocabulary** (section 3: symbol dictionary, line types, line terminations, shading types). Browsers render SVG from a URL the same way (`<img src="option-a.svg">`). See the sample assets in `sample-nvr-odd-one-out/` for examples.
