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
| **`diagrams`** | Standalone diagrams for testing. | One or more **`diagram`** elements. Each `diagram` has the same content model as the diagram inside an option (exactly one of: `shape`, `scatter`, `stack`, or `array`). No question metadata (no product, question_text, options, correct). Use for renderer tests or batch diagram authoring. |

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
- **Children:** One or more **`diagram`** elements. Each **`diagram`** contains exactly one of: **`shape`**, **`scatter`**, **`stack`**, or **`array`** (same content model as the `diagram` element inside an option; see §5.3). No attributes are required on `diagrams` or on each `diagram`; optional `id` on each `diagram` may be used for labelling or test naming. Use this root when the goal is to define or render a list of diagrams without question text, options, or correct answer (e.g. renderer tests, visual regression, batch diagram authoring).

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
- **Standalone diagrams (testing):** `<diagrams><diagram id="d1"><shape key="square"/></diagram><diagram id="d2"><stack>...</stack></diagram></diagrams>`. No question metadata; each `diagram` is one of shape | scatter | stack | array. Optional `id` on each `diagram` for labelling.

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
  - `shape` — Single shape (default layout: **single centred**). May contain optional partition, **scatter** (layout type scatter), etc.
  - `scatter` — **Layout type scatter** at top level: one or more child elements (`shape`, `stack`, or `array`) placed randomly inside the answer viewBox. See §8.
  - `stack` — **Layout type stack**: ordered list of elements (bottom to top); each element may be a shape or a nested layout (stack or array).
  - `array` — **Layout type array**: rectangular, loop, or triangular arrangement of elements; each element may be a shape or a nested layout (e.g. "array of two stacks").

**Layout types:** Single centred (one shape), **scatter** (elements placed randomly inside a bounding box; may contain shapes or other layouts), **stack**, and **array** are all layout types (see design doc §4). A layout may arrange any type of element: shapes, motifs (in any layout), or **nested layouts**. The diagram describes what to draw and how it is arranged; it does not specify pixel coordinates. The renderer uses the NVR vocabulary and layout rules in the design doc to produce SVG.

---

## 6. Shape (single shape container)

- **Element:** `shape`
- **Attributes:**
  - `key` (required) — Shape container key from the design doc §4 (e.g. `circle`, `square`, `triangle`, `hexagon`, `star`). Must be a valid key from the shape containers tables.
  - `line_type` (optional) — Line type key: `solid`, `dashed`, `dotted`, `bold`. Default: `solid`.
  - `shading` (optional) — Fill/shading key for the shape: `solid_black`, `grey`, `grey_light`, `white`, `diagonal_slash`, `diagonal_backslash`, `horizontal_lines`, `vertical_lines`. Default per design (e.g. shape outline with optional fill).
  - `opaque` (optional) — When `true` (default), white fill is rendered as opaque (#fff) and stroke as opaque so stacks and overlapping layouts display correctly. When `false`, white shading may be rendered as transparent (`fill="none"`) for question types that need transparency. Line/stroke remains opaque.
  - `motif_scale` (optional) — When present, forces this shape to be drawn at a **standardized motif size** instead of the layout’s normal scale. Allowed values: `small`, `medium`, `large` (see design doc §3.4.1 Scaling, spacing, and motif sizes). Use when a shape in a scatter, stack, or array (or inside a shape with content) must appear at a fixed “motif” size (e.g. medium for top-level, small when nested). If omitted, the renderer uses layout scaling (or design-doc defaults for motifs when the element is treated as a motif by the template).
- **Children (all optional):**
  - `partition` — Partition type and sections (see §7).
  - **Exactly one content/layout** (at most one of): **`shape`** (single centred: one nested shape), **`scatter`** (layout type scatter: elements placed randomly inside the shape’s bounding box; see §8), **`stack`** (layout type stack: ordered elements bottom to top; see §9), or **`array`** (layout type array: rectangular, loop, or triangular; see §10). A shape container thus accepts the same options as the diagram root—nested shape, scatter, stack, or array—or none (partition/shading only).
  - `placement` — Placement constraint for this element (see §10).

**Semantics:** One shape container. Unless a different layout is specified at the diagram root (scatter/stack/array), the diagram has a single centred element; this shape is that element, centred in the answer viewBox. If present, the shape’s content is drawn inside the shape according to the given type (nested shape, scatter, stack, or array).

**Scaling:** When a shape contains content (nested shape, scatter, stack, or array), that content is laid out and **scaled to fit** within the shape's bounding box. Contained shapes and layouts scale with the container so that everything fits. **Motifs** are an exception: they use **standardized sizing** (small/medium/large) and do not scale with the container (see design doc §3.4). **Nested perpendicular layouts:** The special scaling rule applies only to **rectangular** single-row/column arrays and stacks (not loop or triangular arrays). When such arrays or stacks are nested with the opposite orientation (e.g. vertical stack inside horizontal array), the renderer applies the design doc rule: only the minimum (greatest reduction) scale applies at the nested level; no reduction at the top level, so top-level bounding boxes may overlap—this avoids severe scaling and does not harm visibility (e.g. tall shapes in a horizontal row). Each layout may participate in this rule **at most once** in the nesting chain (e.g. 1h→2v→3h applies the rule at 2 only; 1v→2h→3v→4h applies it at 2 and at 4). Authors and renderers should ensure that nested content fits within the shape; avoid deep nesting or large counts if the container is small.

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

## 8. Scatter (layout type: random placement inside a bounding box)

**Scatter**, **array**, and **stack** are all layout types; the XML uses elements named to match: `scatter`, `array`, `stack`. A **shape container** may contain **any** of these layout types (one of `scatter`, `stack`, or `array` as a child of `shape`), or none (partition/shading only). A **scatter** is a **1-dimensional array of elements**: its children (one or more `shape`, `stack`, or `array`) are placed **randomly** inside the **bounding box** of the shape that contains it (or the top-level viewBox if the scatter is at the top level). Because placement is random, the scatter is **unordered for question logic**—there is no meaningful position order; only the set (count and type) matters.

- **Element:** `scatter`
- **Content:** Either:
  - **One** `repeated` element containing a single `shape` (no nested layout) — That shape is repeated for **count** positions (uniform scatter of identical motifs). Use the **`count`** attribute on `scatter` (e.g. `count="6"`); default 5 if omitted. The shape may have `motif_scale` (small, medium, large). Or
  - One or more child elements, each a `shape`, `stack`, or `array`. The renderer places them randomly within the bounding box so they do not overlap (e.g. minimum centre-to-centre distance per design), with irregular spacing.
- **Scaling and spacing:**
  - **When shapes have `motif_scale`:** Size and spacing are determined by the motif size (small/medium/large). The author does not specify numeric scale.
  - **When no `motif_scale`:** Drawn size and spacing vary by the **effective count** (see `scale_as_count`): fewer elements → larger scale, more elements → smaller scale. The author does not specify numeric scale; the renderer derives it from count.
  - **`scale_as_count` (optional):** Override the count used for scale. The renderer treats the scatter **as if** it had this many elements when computing scale (and spacing). Use to get **uniform scaling across diagrams**: e.g. one diagram with a scatter of 2 and another with a scatter of 3 can both set `scale_as_count="3"` so both use the same element size. The author does not provide actual scaling numbers nor all diagrams to the renderer at once. This should **always** be greater or equal to the actual count (the renderer clamps to the actual count if smaller, so placement does not fail).
  - **Scatter inside a shape:** The renderer applies a **scatter-inside-shape scale factor** (e.g. 0.55) so scale (and thus margin and spacing) is reduced; this avoids placement failure in tight or irregular containers (e.g. triangle).
- **Attributes:**
  - `count` (optional) — When using `repeated`, number of instances to place. Default 5. Ignored when scatter has explicit children.
  - `scale_as_count` (optional) — Positive integer. When set, scale (and spacing) are computed as if the scatter had this many elements. Use so separate diagrams (e.g. scatter of 2 vs scatter of 3) can share the same visual scale without supplying numeric scale or rendering together.
  - `symmetry` (optional) — When forcing symmetry of the arrangement: `horizontal`, `vertical`, `diagonal_slash`, or `diagonal_backslash`. Only shapes with that line of symmetry should be used (design doc §4).

**Semantics:** The scatter's child elements are placed randomly within the bounding box. The scatter is **unordered for question logic** (no first/second/position order; only count and type matter). Symmetry forces mirror positions about the given line.
---

## 9. Stack

- **Element:** `stack`
- **Attributes** (all optional; defaults as below):
  - `spacing` — Overlap between successive elements along the stack direction. One of: `tight` (large overlap), `medium` (moderate), `loose` (small overlap). Default: `medium`.
  - `regularity` — Whether offset is even or variable. One of: `regular` (even offset between elements), `irregular` (variable/random offset). Default: `regular`.
  - `direction` — Main axis of the stack from the bottom element. One of: `up` (next element above—vertical bottom-to-top), `down` (next below—vertical top-to-bottom), `right` (horizontal left-to-right), `left` (horizontal right-to-left). Default: `up`.
  - `step` — Cross-axis offset so the stack reads as 3D (shapes “on top of” each other). Perpendicular to `direction`: for vertical stacks (up/down) use `right` or `left`; for horizontal stacks (left/right) use `up` or `down`. Default: `right` when direction is up; `down` when direction is right; renderer may derive from direction if omitted.
- **Children:** Two or more **elements**. Each element is one of: `shape`, `stack`, or `array`. Order = draw order: **first** is bottom, **last** is top. **Prefer shapes as direct children**; use nested `stack` or `array` only when the question type requires it. Shapes may have `key`, `line_type`, `shading`, optional `partition`; nested stacks/arrays are defined by their own children.

**Visibility constraints (see design doc):** (1) Stack children should in general be shapes. (2) Shapes that are **not** at the top of the stack should not contain a nested layout (no `scatter`, `stack`, or `array` inside)—only the **last** (top) child may have a layout, so overlapping elements do not hide intended logic. (3) Partitions on shapes in stacks need extreme restriction; use only when necessary. (4) Partition type must align with stack `direction`: e.g. vertical partition with vertical stack (up/down), horizontal partition with horizontal stack (left/right); otherwise partitioned sections may be obscured by elements above.

**Semantics:** Layout type **stack**. Depth-ordered overlapping elements; each element partially overlaps the one(s) below. Spacing, regularity, direction, and **step** (cross-axis offset for 3D look) control how the stack is rendered (see design doc Layout (3.2) layout type: stack and stack terminology).

---

## 10. Array

- **Element:** `array`
- **Attributes:**
  - `type` (required) — One of: `rectangular`, `loop`, `triangular`.
  - For `rectangular`: `rows` (required), `cols` (required) — Positive integers. Total elements = rows × cols. **Right-angled triangular array** is not a separate type: it is a rectangular (typically square) array with `null` in positions outside a right-angled triangle; template shorthand: "right angled triangular array" or "right angled" array. Positions outside the triangle must be null. **`right_angle_corner`** (optional) — Where the square corner (90° vertex) of the right-angled triangle is: `bottom_left` (default), `bottom_right`, `top_left`, `top_right`. Template: "right angled array, corner at bottom left" etc. When mesh is drawn with `draw_full_grid` false, mesh lines are never drawn to or from null positions (see mesh rule below).
  - For `loop`: **Path** — `path_shape` (optional) — Shape key for the path; default `circle`. Any shape container key (e.g. `circle`, `square`, `triangle`, `hexagon`). The path follows that shape’s outline (circle = circumference; polygon = vertices and edges). **Placement** — `positions` (optional): `vertices` or `edges`; only for polygon path shapes. Default for polygon: `vertices`. For `circle`, elements are placed on the circumference (ignore `positions`). **Count** — `count` (required when path is circle, or when polygon + vertices and explicit count desired): number of elements on the path. When polygon + `positions="vertices"`, count may be omitted (implicit = number of vertices). When polygon + `positions="edges"`, `per_edge` (required) — positive integer; number of items evenly spaced on **each** edge; total elements = number of edges × per_edge.
  - For `triangular`: `count` (required) — Total number of elements; formation is row 1 has 1, row 2 has 2, etc. (e.g. count=10 → rows 1,2,3,4). **`direction`** (optional) — Which way the triangle points (apex): `up` (default), `down`, `left`, `right`. Template: "triangular array pointing up/down/left/right".
- **Drawing mesh (rectangular and triangular only):** When present, the renderer may draw centre-to-centre mesh lines. **`draw_mesh`** (optional, boolean) — If true, draw the mesh (lines between cell centres). **`mesh_line_type`** (optional) — Line type key from the vocabulary (`solid`, `dashed`, `dotted`, `bold`); default `solid`. **`draw_full_grid`** (optional, boolean) — If true, draw all mesh segments. If false, draw only segments between adjacent **non-null** cells: the renderer must **not** draw any mesh line that touches a null position (so e.g. a right-angled triangular layout—rectangular array with nulls—shows mesh only for the triangle). **`mesh_omit`** (optional) — List of mesh segments to omit. For rectangular arrays: use cell-pair notation (e.g. `0-1` = segment between cell index 0 and 1 in row-major order) or line identifiers (e.g. `v0 h1` = first vertical line, second horizontal line; vertical lines run between columns, horizontal between rows). For triangular arrays: use the renderer’s segment indexing (e.g. segment indices or cell-pairs). Space- or comma-separated.
- **Drawing path (loop only):** When present, the renderer may draw the path (container) shape. **`draw_path`** (optional, boolean) — If true, draw the path outline (circle or polygon). **`path_line_type`** (optional) — Line type key; default `solid`. **`path_omit_edges`** (optional) — For polygon paths only: space-separated edge indices (0-based) to omit (e.g. `0 2` omits first and third edge). Ignored for circle.
- **Children:** Either:
  - **One** `repeated` element containing a single `shape` (with `key`, optional `line_type`, `shading` only) — That shape is repeated for every position in the array (uniform array of shapes), or
  - **N** elements (N = array size: rows×cols; for loop: count or vertices or edges×per_edge; for triangular: count), each being a `shape`, `stack`, `array`, or **`null`** — One element per position. A **`null`** element means nothing is drawn in that position (the slot is empty). Order = row-major for rectangular; for loop: by angle along path (circle) or by vertex then by edge (polygon); by row for triangular.

**Null element:** In the explicit list of N elements, use **`null`** (empty element: `<null/>`) for any position where nothing should be drawn. The slot is reserved but empty. When **`draw_full_grid`** is false, mesh lines are never drawn to or from null positions (mesh shows only the non-null region; e.g. right-angled triangular array shows a triangular mesh). Not used with **`repeated`** (repeated implies every position has the same shape).

**Semantics:** Layout type **array**. A layout that arranges multiple elements in a regular arrangement; no overlap. Elements may be shapes, nested layouts, or null (empty slot). For **loop**, the path is given by `path_shape` (default circle); use `positions` (vertices | edges) and, for edges, `per_edge` to place elements on the path. See design doc Layout (3.2) layout type: array.

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

Valid keys for attributes (`key`, `line_type`, `shading`, etc.) are those defined in **QUESTION-GENERATION-DESIGN.md** §4:

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

The following example describes one odd-one-out question: five options, each a single shape (default layout) with layout type scatter (child shapes placed randomly inside). Option 2 (index 2) is correct.

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
          <scatter>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
          </scatter>
        </shape>
      </diagram>
    </option>
    <option index="1">
      <diagram>
        <shape key="circle" line_type="dashed" shading="grey_light">
          <scatter>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
          </scatter>
        </shape>
      </diagram>
    </option>
    <option index="2">
      <diagram>
        <shape key="triangle" line_type="solid" shading="white">
          <scatter>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
          </scatter>
        </shape>
      </diagram>
    </option>
    <option index="3">
      <diagram>
        <shape key="hexagon" line_type="solid" shading="white">
          <scatter>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
          </scatter>
        </shape>
      </diagram>
    </option>
    <option index="4">
      <diagram>
        <shape key="pentagon" line_type="dotted" shading="grey_light">
          <scatter>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
            <shape key="circle"/>
          </scatter>
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
<!-- Loop array: 6 shapes on a circle (default path) -->
<option index="0">
  <diagram>
    <array type="loop" count="6">
      <repeated>
        <shape key="pentagon" line_type="solid" shading="white"/>
      </repeated>
    </array>
  </diagram>
</option>
```

```xml
<!-- Loop on square: 4 shapes at vertices -->
<array type="loop" path_shape="square" positions="vertices">
  <repeated><shape key="circle" shading="white"/></repeated>
</array>
```

```xml
<!-- Loop on square: 2 shapes per edge (8 total) -->
<array type="loop" path_shape="square" positions="edges" per_edge="2">
  <repeated><shape key="triangle" shading="grey"/></repeated>
</array>
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
