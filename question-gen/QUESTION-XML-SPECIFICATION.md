# Question XML specification

This document defines the **concrete syntax and structure** of question XML: element names, attributes, nesting, placement vocabulary, and validation rules. Semantics and allowed vocabulary keys are defined in **QUESTION-GENERATION-DESIGN.md** (§4 NVR visual vocabulary). The renderer (Phase 4) consumes question XML and produces option SVGs and metadata.

**Scope:** A single XML file may define **one question**, **multiple questions**, or **multiple standalone diagrams** (for testing). **Option count** per question is variable (default for NVR multiple-choice is **5**; the design doc also defines allowed splits for 4 and 6 options). Diagram descriptions are intent-based (layout and vocabulary keys); the renderer resolves placement and non-determinism within the rules in the design doc.

---

## 1. Document structure

### 1.1 Root element (one of three)

A valid question XML document has **exactly one root element**, which must be one of:

| Root element | Use | Content |
|--------------|-----|---------|
| **`question`** | Single question (production or one-off). | One full question (product, question_text, options, correct). |
| **`questions`** | Multiple questions in one file. | One or more **`question`** elements (same structure as above). Each `question` must have a unique `id` within the document. |
| **`diagrams`** | Standalone diagrams for testing. | One or more **`diagram`** elements. Each `diagram` has the same content model as the diagram inside an option (exactly one of: `shape`, `stack`, or `array`). No question metadata (no product, question_text, options, correct). Use for renderer tests or batch diagram authoring. |

**Backward compatibility:** Files that use root **`question`** (single question) are unchanged. Tools that accept "question XML" should accept any of the three roots and process each `question` or each `diagram` as appropriate.

### 1.2 Single-question root: `question`

- **Element:** `question` (when used as document root)
- **Attributes:**
  - `id` (required) — Stable identifier for the question (e.g. for manifest and folder naming). No spaces; typically alphanumeric and hyphen.
  - `template_id` (optional) — Identifier of the template or template script that produced this question.
  - `seed` (optional) — Integer or string used for reproducible non-deterministic choices (e.g. placement within regions).

### 1.3 Multi-question root: `questions`

- **Element:** `questions`
- **Children:** One or more **`question`** elements. Each has the same attributes and content model as in §1.2 and §1.4. **Ids:** Every `question` in the document must have a unique `id` (required for validation when multiple questions share one file).

### 1.4 Standalone diagrams root: `diagrams`

- **Element:** `diagrams`
- **Children:** One or more **`diagram`** elements. Each **`diagram`** contains exactly one of: **`shape`**, **`stack`**, or **`array`** (same content model as the `diagram` element inside an option; see §5.3). No attributes are required on `diagrams` or on each `diagram`; optional `id` on each `diagram` may be used for labelling or test naming. Use this root when the goal is to define or render a list of diagrams without question text, options, or correct answer (e.g. renderer tests, visual regression, batch diagram authoring).

### 1.5 Top-level children of `question` (in order)

| Element       | Count   | Description |
|---------------|---------|-------------|
| `product`     | 1       | Product placement (subject and topic). |
| `question_text` | 1     | The text shown to the user (e.g. “Which shape is the odd one out?”). |
| `explanation` | 0 or 1  | Post-answer hint for the user. |
| `options`     | 1       | Container for **2 or more** `option` elements (typically 4, 5, or 6 for NVR; default 5). |
| `correct`     | 1       | Zero-based index of the correct option; must be in range **[0, number of options − 1]**. |

**Root usage examples:**

- **Single question (unchanged):** `<question id="q1">...</question>` as the only root.
- **Multiple questions:** `<questions><question id="q1">...</question><question id="q2">...</question></questions>`. Each `question` has the full structure (product, question_text, options, correct); ids must be unique within the file.
- **Standalone diagrams (testing):** `<diagrams><diagram id="d1"><shape key="square"/></diagram><diagram id="d2"><stack>...</stack></diagram></diagrams>`. No question metadata; each `diagram` is one of shape | stack | array. Optional `id` on each `diagram` for labelling.

---

## 2. Product placement

- **Element:** `product`
- **Attributes:**
  - `subject_id` (optional) — Subject identifier for insertion. Use when the product uses numeric or UUID subject ids.
  - `subject_code` (optional) — Subject code or name when the product uses codes.
  - `topic_id` (optional) — Topic identifier.
  - `topic_code` (optional) — Topic code or name.

At least one of `subject_id` or `subject_code` must be present. At least one of `topic_id` or `topic_code` must be present. The renderer does not interpret these; they are for Phase 5 (database insert).

---

## 3. Question text and explanation

- **Element:** `question_text` — Character content only (no child elements). The exact string to show as the question.
- **Element:** `explanation` — Character content only. Optional; used for `questions.explanation` after the user answers.

---

## 4. Correct answer

- **Element:** `correct`
- **Content:** Single integer (whitespace trimmed). Zero-based **index** of the correct option. Must be in range **0** to **number of options − 1** (e.g. 0–3 for 4 options, 0–4 for 5, 0–5 for 6). The renderer and Phase 5 use this to set `is_correct` on the corresponding answer option. The XSD allows 0–11; the application must ensure **correct &lt; number of option elements**.

---

## 5. Options and diagrams

### 5.1 Options container

- **Element:** `options`
- **Children:** **2 or more** `option` elements (typically 4, 5, or 6 for NVR multiple-choice; see design doc default and allowed splits). The number of options is the count of `option` children; no separate attribute is required.

### 5.2 Option element

- **Element:** `option`
- **Attributes:**
  - `index` (required) — Zero-based integer matching document order. Must be **0** to **n−1** where n = number of option elements, and must be unique (0, 1, 2, … in order).
- **Children:** Exactly one `diagram` element.

### 5.3 Diagram element

- **Element:** `diagram`
- **Children:** Exactly one **diagram element** (the root of the diagram structure). A diagram element is one of:
  - `shape` — Single shape (default layout: **single centred**). May contain optional partition, **chaotic** (layout type chaotic), etc.
  - `stack` — **Layout type stack**: ordered list of elements (bottom to top); each element may be a shape or a nested layout (stack or array).
  - `array` — **Layout type array**: rectangular, orbital, or triangular arrangement of elements; each element may be a shape or a nested layout (e.g. "array of two stacks").

**Layout types:** Single centred (one shape), **chaotic** (e.g. multiple motifs inside a shape with irregular spacing), **stack**, and **array** are all layout types (see design doc §4). A layout may arrange any type of element: shapes, motifs (in any layout), or **nested layouts**. The diagram describes what to draw and how it is arranged; it does not specify pixel coordinates. The renderer uses the NVR vocabulary and layout rules in the design doc to produce SVG.

---

## 6. Shape (single shape container)

- **Element:** `shape`
- **Attributes:**
  - `key` (required) — Shape container key from the design doc §4 (e.g. `circle`, `square`, `triangle`, `hexagon`, `star`). Must be a valid key from the shape containers tables.
  - `line_type` (optional) — Line type key: `solid`, `dashed`, `dotted`, `bold`. Default: `solid`.
  - `shading` (optional) — Fill/shading key for the shape: `solid_black`, `grey`, `grey_light`, `white`, `diagonal_slash`, `diagonal_backslash`, `horizontal_lines`, `vertical_lines`. Default per design (e.g. shape outline with optional fill).
- **Children (all optional):**
  - `partition` — Partition type and sections (see §7).
  - **Exactly one layout** (at most one of): **`chaotic`** (layout type chaotic: multiple motifs with irregular spacing; see §8), **`stack`** (layout type stack: ordered elements bottom to top; see §9), or **`array`** (layout type array: rectangular, orbital, or triangular; see §10). A shape container can contain any type of layout—chaotic, stack, or array—or none (partition/shading only).
  - `placement` — Placement constraint for this element (see §10).

**Semantics:** One shape container. Unless a different layout is specified at the diagram root (stack/array), the diagram has a single centred element; this shape is that element, centred in the answer viewBox. If present, the shape’s content is drawn inside the shape according to the given layout type.

---

## 7. Partition

- **Element:** `partition`
- **Attributes:**
  - `type` (required) — One of: `horizontal`, `vertical`, `diagonal`, `concentric`, `radial`. Diagonal may be implemented as slash or backslash per design; concentric/radial have shape-specific rules (see design doc §4 Partitioned shapes).
- **Children:** One or more `section` elements, in order.

### 7.1 Section

- **Element:** `section`
- **Attributes:**
  - `low` (required) — Number 0–100, proportion of shape extent (inclusive start of section).
  - `high` (required) — Number 0–100, proportion of shape extent (exclusive end of section). Must be ≥ `low`. Contiguous sections use previous section’s `high` as this section’s `low`.
  - `shading` (required) — Shading key for this section (same set as shape shading), or `null` for a null section (not drawn; design doc §4).

**Example:** Two horizontal halves: `<section low="0" high="50" shading="white"/>`, `<section low="50" high="100" shading="grey"/>`.

---

## 8. Chaotic (layout type: multiple motifs inside a shape)

**Chaotic**, **array**, and **stack** are all layout types; the XML uses elements named to match: `chaotic`, `array`, `stack`. A **shape container** may contain **any** of these layout types (one of `chaotic`, `stack`, or `array` as a child of `shape`), or none (partition/shading only). Motifs may appear in any type of layout. This section describes the **chaotic** element: layout type chaotic — multiple motifs inside a shape with irregular (non-grid) spacing. Use the `chaotic` element when a shape contains **multiple motifs** arranged chaotically. (A single motif in a shape does not require a chaotic element; motifs as elements in an array or stack are encoded as shape/stack/array children.)

- **Element:** `chaotic`
- **Attributes:**
  - `motif_key` (required) — Motif key from the design doc motif dictionary (e.g. `circle`, `square`, `heart`).
  - `count` (required) — Positive integer, number of motifs.
  - `symmetry` (optional) — When forcing symmetry of the motif arrangement: `horizontal`, `vertical`, `diagonal_slash`, or `diagonal_backslash`. Only motifs with that line of symmetry should be used (design doc §4).

**Semantics:** The shape contains `count` motifs of type `motif_key`, placed so they do not overlap (e.g. minimum centre-to-centre distance per design), with irregular (non-grid) spacing. Symmetry forces mirror positions about the given line. **Motif rules (any layout):** Motifs cannot be partitioned; shading where motifs appear must be solid or white (no hatched/line shading).

---

## 9. Stack

- **Element:** `stack`
- **Attributes** (all optional; defaults as below):
  - `spacing` — Overlap between successive elements along the stack direction. One of: `tight` (large overlap), `medium` (moderate), `loose` (small overlap). Default: `medium`.
  - `regularity` — Whether offset is even or variable. One of: `regular` (even offset between elements), `irregular` (variable/random offset). Default: `regular`.
  - `direction` — Main axis of the stack from the bottom element. One of: `up` (next element above—vertical bottom-to-top), `down` (next below—vertical top-to-bottom), `right` (horizontal left-to-right), `left` (horizontal right-to-left). Default: `up`.
  - `step` — Cross-axis offset so the stack reads as 3D (shapes “on top of” each other). Perpendicular to `direction`: for vertical stacks (up/down) use `right` or `left`; for horizontal stacks (left/right) use `up` or `down`. Default: `right` when direction is up; `down` when direction is right; renderer may derive from direction if omitted.
- **Children:** Two or more **elements**. Each element is one of: `shape`, `stack`, or `array`. Order = draw order: **first** is bottom, **last** is top. **Prefer shapes as direct children**; use nested `stack` or `array` only when the question type requires it. Shapes may have `key`, `line_type`, `shading`, optional `partition`; nested stacks/arrays are defined by their own children.

**Visibility constraints (see design doc):** (1) Stack children should in general be shapes. (2) Shapes that are **not** at the top of the stack should not contain a nested layout (no `chaotic`, `stack`, or `array` inside)—only the **last** (top) child may have a layout, so overlapping elements do not hide intended logic. (3) Partitions on shapes in stacks need extreme restriction; use only when necessary. (4) Partition type must align with stack `direction`: e.g. vertical partition with vertical stack (up/down), horizontal partition with horizontal stack (left/right); otherwise partitioned sections may be obscured by elements above.

**Semantics:** Layout type **stack**. Depth-ordered overlapping elements; each element partially overlaps the one(s) below. Spacing, regularity, direction, and **step** (cross-axis offset for 3D look) control how the stack is rendered (see design doc Layout (3.2) layout type: stack and stack terminology).

---

## 10. Array

- **Element:** `array`
- **Attributes:**
  - `type` (required) — One of: `rectangular`, `orbital`, `triangular`.
  - For `rectangular`: `rows` (required), `cols` (required) — Positive integers. Total elements = rows × cols.
  - For `orbital`: `count` (required) — Positive integer; number of elements evenly placed on a circle.
  - For `triangular`: `count` (required) — Total number of elements; formation is row 1 has 1, row 2 has 2, etc. (e.g. count=10 → rows 1,2,3,4).
- **Children:** Either:
  - **One** `repeated` element containing a single `shape` (with `key`, optional `line_type`, `shading` only) — That shape is repeated for every position in the array (uniform array of shapes), or
  - **N** elements (N = array size: rows×cols, or count for orbital/triangular), each being a `shape`, `stack`, or `array` — One element per position (e.g. "array of two stacks" = 2 elements, each a `stack`). Order = row-major for rectangular; by angle for orbital; by row for triangular.

**Semantics:** Layout type **array**. A layout that arranges multiple elements in a regular arrangement; no overlap. Elements may be shapes or nested layouts. See design doc Layout (3.2) layout type: array.

---

## 11. Placement constraints

Placement constraints tell the renderer **how** to place content without giving coordinates. They are optional; default is “centred” for the root element.

- **Element:** `placement` (child of a `shape` or, in future, other elements where placement is configurable)
- **Content or attribute:** A single token from the **placement vocabulary** below.

**Placement vocabulary:**

| Value                    | Meaning |
|--------------------------|---------|
| `centred`                | Default. Element centre coincides with viewBox centre (or parent region centre). |
| `randomly_within_region`  | Place within the current region (whole viewBox or partition section) with no overlap; exact position is non-deterministic. |
| `clustered_in_top_half`  | Constrain to top half of region. |
| `clustered_in_bottom_half` | Constrain to bottom half. |
| `clustered_in_left_half`  | Constrain to left half. |
| `clustered_in_right_half` | Constrain to right half. |

**Encoding:** Use a `placement` element with attribute `constraint` (e.g. `constraint="randomly_within_region"`) or with text content equal to one of the values above. Schema below uses attribute `constraint`.

---

## 12. Vocabulary key reference

Valid keys for attributes (`key`, `line_type`, `shading`, `motif_key`, etc.) are those defined in **QUESTION-GENERATION-DESIGN.md** §4:

- **Shape containers:** §4 Shape containers (3.3) — regular shapes, common irregular shapes, symbols (circle, triangle, square, pentagon, hexagon, heptagon, octagon, right_angled_triangle, rectangle, semicircle, cross, arrow, plus, times, club, heart, diamond, spade, star).
- **Motifs:** §4 Motif dictionary (3.4) — circle, plus, times, heart, diamond, club, spade, square, triangle, star.
- **Line types:** §4 Line types (3.5) — solid, dashed, dotted, bold.
- **Line terminations / augmentations:** §4 (3.6, 3.7) — used when the spec is extended for lines.
- **Shading types:** §4 Shading types (3.8) — solid_black, grey, grey_light, white, diagonal_slash, diagonal_backslash, horizontal_lines, vertical_lines.

The schema may use `xs:string` for these and rely on the renderer to validate against the design doc; or the schema can reference enumerated types if keys are frozen in an appendix.

---

## 13. XML Schema (XSD)

The file **question-xml.xsd** in this directory defines the schema. It allows **2–12** `option` elements and **correct** / option `index` in range 0–11. Validation: the document root must be one of **`question`**, **`questions`**, or **`diagrams`**, and the document must conform to the XSD. **Co-constraint:** For each `question`, the value of `correct` must be less than the number of `option` elements (enforced by the renderer or producer, not by the XSD). When root is **`questions`**, every `question` must have a unique `id` within the document.

---

## 14. Sample question XML

The following example describes one odd-one-out question: five options, each a single shape (default layout) with layout type chaotic (motifs inside). Option 2 (index 2) is correct.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<question id="nvr-odd-001" template_id="odd-one-out-motif" seed="42">
  <product subject_code="nvr" topic_code="odd_one_out"/>
  <question_text>Which shape is the odd one out?</question_text>
  <explanation>The others have four motifs; this one has five.</explanation>
  <options>
    <option index="0">
      <diagram>
        <shape key="square" line_type="solid" shading="white">
          <chaotic motif_key="circle" count="4"/>
        </shape>
      </diagram>
    </option>
    <option index="1">
      <diagram>
        <shape key="circle" line_type="dashed" shading="grey_light">
          <chaotic motif_key="circle" count="4"/>
        </shape>
      </diagram>
    </option>
    <option index="2">
      <diagram>
        <shape key="triangle" line_type="solid" shading="white">
          <chaotic motif_key="circle" count="5"/>
        </shape>
      </diagram>
    </option>
    <option index="3">
      <diagram>
        <shape key="hexagon" line_type="solid" shading="white">
          <chaotic motif_key="circle" count="4"/>
        </shape>
      </diagram>
    </option>
    <option index="4">
      <diagram>
        <shape key="pentagon" line_type="dotted" shading="grey_light">
          <chaotic motif_key="circle" count="4"/>
        </shape>
      </diagram>
    </option>
  </options>
  <correct>2</correct>
</question>
```

**Second example:** Partitioned shape (no motifs). Two sections, horizontal partition.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<question id="nvr-odd-002" seed="100">
  <product subject_code="nvr" topic_code="odd_one_out"/>
  <question_text>Which shape is the odd one out?</question_text>
  <options>
    <option index="0">
      <diagram>
        <shape key="square" line_type="solid">
          <partition type="horizontal">
            <section low="0" high="50" shading="white"/>
            <section low="50" high="100" shading="grey"/>
          </partition>
        </shape>
      </diagram>
    </option>
    <option index="1">
      <diagram>
        <shape key="square" line_type="solid">
          <partition type="horizontal">
            <section low="0" high="50" shading="grey"/>
            <section low="50" high="100" shading="white"/>
          </partition>
        </shape>
      </diagram>
    </option>
    <option index="2">
      <diagram>
        <shape key="circle" line_type="solid">
          <partition type="horizontal">
            <section low="0" high="50" shading="white"/>
            <section low="50" high="100" shading="grey"/>
          </partition>
        </shape>
      </diagram>
    </option>
    <option index="3">
      <diagram>
        <shape key="square" line_type="solid">
          <partition type="horizontal">
            <section low="0" high="50" shading="grey_light"/>
            <section low="50" high="100" shading="white"/>
          </partition>
        </shape>
      </diagram>
    </option>
    <option index="4">
      <diagram>
        <shape key="square" line_type="solid">
          <partition type="horizontal">
            <section low="0" high="50" shading="white"/>
            <section low="50" high="100" shading="grey"/>
          </partition>
        </shape>
      </diagram>
    </option>
  </options>
  <correct>2</correct>
</question>
```

**Third example:** Stack (three shapes) and rectangular array.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<question id="nvr-stack-001" seed="200">
  <product subject_code="nvr" topic_code="stacks"/>
  <question_text>Which stack is different?</question_text>
  <options>
    <option index="0">
      <diagram>
        <stack>
          <shape key="square" shading="grey"/>
          <shape key="circle" shading="white"/>
          <shape key="triangle" shading="grey_light"/>
        </stack>
      </diagram>
    </option>
    <option index="1">
      <diagram>
        <stack>
          <shape key="circle" shading="white"/>
          <shape key="square" shading="grey"/>
          <shape key="triangle" shading="grey_light"/>
        </stack>
      </diagram>
    </option>
    <option index="2">
      <diagram>
        <stack>
          <shape key="square" shading="grey"/>
          <shape key="triangle" shading="white"/>
          <shape key="circle" shading="grey_light"/>
        </stack>
      </diagram>
    </option>
    <option index="3">
      <diagram>
        <stack>
          <shape key="triangle" shading="grey_light"/>
          <shape key="circle" shading="white"/>
          <shape key="square" shading="grey"/>
        </stack>
      </diagram>
    </option>
    <option index="4">
      <diagram>
        <stack>
          <shape key="square" shading="grey"/>
          <shape key="circle" shading="white"/>
          <shape key="triangle" shading="grey_light"/>
        </stack>
      </diagram>
    </option>
  </options>
  <correct>1</correct>
</question>
```

```xml
<!-- Array example: 2×2 rectangular array of triangles -->
<option index="0">
  <diagram>
    <array type="rectangular" rows="2" cols="2">
      <repeated>
        <shape key="triangle" line_type="solid" shading="white"/>
      </repeated>
    </array>
  </diagram>
</option>
```

```xml
<!-- Orbital array: 6 shapes on a circle -->
<option index="0">
  <diagram>
    <array type="orbital" count="6">
      <repeated>
        <shape key="pentagon" line_type="solid" shading="white"/>
      </repeated>
    </array>
  </diagram>
</option>
```

```xml
<!-- Array of two stacks (layout type array whose elements are two layout type stacks) -->
<option index="0">
  <diagram>
    <array type="rectangular" rows="1" cols="2">
      <stack>
        <shape key="square" shading="grey"/>
        <shape key="circle" shading="white"/>
      </stack>
      <stack>
        <shape key="triangle" shading="grey_light"/>
        <shape key="hexagon" shading="white"/>
      </stack>
    </array>
  </diagram>
</option>
```

```xml
<!-- Shape containing a stack (layout type stack inside a shape container) -->
<option index="0">
  <diagram>
    <shape key="circle" line_type="solid" shading="white">
      <stack>
        <shape key="square" shading="grey"/>
        <shape key="triangle" shading="grey_light"/>
        <shape key="hexagon" shading="white"/>
      </stack>
    </shape>
  </diagram>
</option>
```

---

## 15. Changes and extensions

- **New layout types or array types** — Add attributes and elements as needed; update design doc and this spec together.
- **Line terminations / augmentations** — When the design doc is used for diagram types that include lines, add elements for line type, terminations, and augmentations under `shape` or a new `line` element.
- **Diagram sequences** — For questions that rely on sequence (e.g. shading sequence in radial sections), the partition `section` ordering and `shading` per section already encode sequence; no extra element required unless sequence metadata is needed for the renderer.
