# Question generation – design

This document describes the design of the **question generation pipeline**: how questions (including picture-based and NVR) are produced, stored as assets, and inserted into the database for use by the practice app.

---

## 1. Purpose and scope

**Goal:** Generate batches of questions (text and/or picture-based) from templates, then make them available in the app by uploading assets and inserting rows into the database.

**In scope:**

- Running template scripts to produce question content (e.g. SVGs + metadata).
- Aggregating output into a single manifest for the batch.
- Uploading option (and optional question) images to storage.
- Inserting `questions` and `answer_options` rows with correct metadata and image URLs.

- The current scope of this document is to outline diagrammatic NVR questions only.

**Out of scope here:**

- Authoring or editing individual questions in the UI.
- The exact content of each template (see this document §4 and template repos).

**References:**

- **11plus-datamodel-design.md** — Schema for `questions`, `answer_options`, `subjects`, `topics`.
- **QUESTION-GENERATION-BATCH.md** — Concrete two-script flow and manifest shape (when using a batch runner).

---

## 2. Standard workflow (four phases)

The pipeline is split into four phases so that authoring, code generation, rendering, and database insert can be done separately and by different actors (human vs agent).

```mermaid
flowchart TD
  P1["**Phase 1: Author question templates**<br/>Define question types, structure, and variability.Likely: human. Possibly: agent."]
  P2["**Phase 2: Compile question templates into a python language script**<br/>Produces question XML satisfying the template"]
  P3["**Phase 3: Run scripts from Phase 2 to create question XML**<br/>Scripts emit question XML per question instance (seeds/config).<br/>Likely: agent."]
  P4["**Phase 4: Run Python renderer**<br/>Convert question XML → assets (JSON, text, SVG).<br/>Optional single manifest for the batch."]
  P5["**Phase 5: Insert assets into database**<br/>Upload assets to storage; build image URLs.<br/>INSERT questions + answer_options."]
  P1 --> P2 --> P3 --> P4 --> P5
```

- **Phase 1** — Templates and specs; no scripts or DB.
- **Phase 2** — Produce Python template scripts from question templates.
- **Phase 3** — Use template scripts to create multiple question XML files.
- **Phase 4** — Consumes XML; produces JSON, text, SVG (and optionally manifest).
- **Phase 5** — Consumes manifest + asset dirs; needs storage config and DB connection.

---

## 3. Question assets purpose and overview

This section describes the key assets required and produced in the workflow described in section 2.

### Question Templates

This is a human readable brief written document that uses keywords to describe a question, which are defined throughout this document.  

The template will be loosely written in English, but using strictly defined keywords and rules for default behaviour defined in this document. 

Generating the script from a question template is a highly non-deterministic process that will be best handled by an agent.

The question templates are our core assets on the contents of our product and require human time investment to produce.  They are not expendable nor easily regenerated.

### Template Scripts

This is a primarily machine-readable, agent-generated procedural language script (likely Python) which is considered an expendable asset.

The scripts should use standard reusable library functions to perform any tasks related to NVR logic or otherwise. A template script may be run any number of times to produce a novel question that adheres to the template.

Creating the template scripts will be a highly non-deterministic process and will be handled by agents.

### Question XML

A question XML document is a logically unambiguous definition of a single (usually diagrammatic) question.

It contains all of the necessary references (e.g. subject and topic identifiers) to place the question in our product. It also contains a nested XML structure describing the diagrams required for the question itself and any answers, including overall layout and formatting for each element of a diagram.

The question XML deliberately does not have sufficient detail to unambiguously define the precise visual layout of all elements described—for example the renderer will have some leeway to choose random locations; the XML may call for items to be placed randomly within a region of a diagram.

Generating question assets from XML is therefore a slightly non-deterministic process, where two outputs from runs of the same script may produce slight visual variations, but no logical variations.

### Question Assets

SVG Diagram files and JSON - these are the final product, precise question definitions with no remaining ambiguity.

---

## 4. Contracts (five-phase workflow)

Contracts between phases so that outputs of one phase are valid inputs to the next.

### Phase 1 → Phase 2: Question template

- **Output:** A question template (human-readable brief).
- **Contract:** Uses only **keywords and rules** defined in this document (and any linked specs). Written in English with strictly defined terms; default behaviour is specified so an agent can interpret the template without ambiguity for compilation. No machine-readable schema is required; the template is the source of truth for “what this question type is.”

### Phase 2 → Phase 3: Template script

- **Output:** A template script (e.g. Python) that produces question XML.
- **Contract:** The script:
  - Accepts at least: **seed** (or equivalent) for reproducibility; optionally **config** or arguments that select variants or count.
  - **Emits** one or more question XML documents (e.g. to stdout, or to files under a given output path). Each document must conform to the **question XML specification** (QUESTION-XML-SPECIFICATION.md and question-xml.xsd).
  - Does not write final assets (no SVG/JSON output); that is the role of the renderer (Phase 4).

### Phase 3 → Phase 4: Question XML

- **Output:** Question XML (per question or batch).
- **Contract:** Each XML document is a **logically unambiguous** definition of one question. It includes:
  - References needed for the product (e.g. subject and topic identifiers).
  - A nested structure describing the diagrams for the question and each answer option (layout and formatting intent, not pixel-perfect layout).
  - Intent that allows the renderer limited non-determinism (e.g. “place randomly in region”) so two runs may differ visually but not logically. The **question XML specification** (QUESTION-XML-SPECIFICATION.md and question-xml.xsd) defines the schema and semantics.

### Phase 4 → Phase 5: Question assets and manifest

- **Output:** Per-question directory containing option assets (e.g. 5 SVGs), a **question_meta.json** (or equivalent), plus an optional single **manifest** for the batch.
- **Contract:** The renderer:
  - Consumes question XML only (no direct DB or storage access).
  - Writes into a per-question directory: **5 option assets** in a defined order (e.g. `option-a.svg` … `option-e.svg`), and a metadata file with at least `correct_index` (0–4), and optionally `template_id`, `seed`, `question_text`, `explanation`, `option_files`.
  - May write a **manifest.json** (see §8) aggregating all questions in the run. Phase 5 reads this manifest and the directory layout to upload and insert.


 (template script) is run per question and **writes assets directly** (SVGs + `question_meta.json`). That corresponds to a combined Phase 2+3+4: the “template script” there is both XML producer and renderer. The contract for that script is as above for “Phase 4 → Phase 5” output (5 option files + metadata); 

## 6. Keywords and verbal question templates

Question templates (Phase 1 output) must use **only** the keywords and rules defined in this section. This section gives the **NVR visual vocabulary** (**element** (3.1)—generic term for any part of the structure: shapes, motifs, layouts, arrays, stacks—then layout, shape containers, motifs, line types, line terminations, line augmentations, shading types, partitions, and concepts), then the full rules for writing verbal question templates (parameters, variators, differentiator, parameter choice rules, frequency modifiers).

This section also contains several specific references to visual instructions on how specific keywords may affect the appearance of the diagrams, in particular with regard to default behavior, allowing templates to unambiguously omit details, and scaling of nested elements.  

---

### NVR visual vocabulary (dictionaries)

The following dictionaries define the **only** allowable motifs, line types, line terminations, and shading types for NVR-style diagram questions. All diagrammatic descriptions must reference these by **key** (e.g. `circle`, `dashed`). No ad hoc terms; extend the dictionaries only when this spec is updated. **Element** (3.1) is the generic term for any part of the structure (shapes and layouts—**stack**, **scatter**, and **array** are layout types). **Layout** (3.2) defines how content is arranged: the **default layout** is a **single centred element**; other layout types are **scatter** (elements placed randomly inside a bounding box; see below), **stack**, and **array**. **Shape containers** (3.3) are the first dictionary; then motifs (3.4), line types, line terminations, line augmentations, and shading types. A shape may be **partitioned** into sections with their own shading. Generated SVGs must use only these options so that `circle` or `dashed` is identical across questions.

**Element** is the generic term for any part of the diagram structure. **Shapes** and **layouts** are elements. **Stack**, **scatter**, and **array** are **layout types**—each is a type of layout, not a separate concept. A **layout** may arrange any type of element: shapes (see shape containers and motif dictionary), or **nested layouts** (e.g. "an array of two stacks"). The following subsections define layout (3.2), shape containers (3.3), motifs (3.4), and the other vocabulary used to describe elements.

**Vocabulary element** is the generic term for any single entry from these dictionaries: a **shape container**, **motif**, **line type**, **line termination**, **line augmentation**, or **shading type**. In this document, vocabulary elements are quoted in backticks when used as formal terms (e.g. `circle`, `dashed`, `arrow_single`). When writing a verbal question template, the generator chooses random vocabulary elements and sticks with those same choices for part or all of that question (see Template terminology below).

#### Element (3.1)

An **element** is any part of the diagram structure. Elements are either **shapes** or **layouts**. **Stack**, **scatter**, and **array** are all **layout types**: each is a kind of layout. A layout arranges one or more elements; those elements may be shapes or **nested layouts** (e.g. an array of two stacks). A diagram is composed of a root element (see Layout (3.2)). For the default layout ("one element centred"), that root may be a single shape container or a layout (scatter, stack, or array) that itself contains elements. When we say “one element centred” (default layout), that element may be a single shape container. (Shapes used as motifs are defined in §3.4.)

#### Layout (3.2)

**Layout** is how the diagram (or a region) arranges its content. The **layout types** are **single centred** (default), **scatter**, **stack**, and **array**—so stack, scatter, and array are all types of layout. Templates and question XML specify a layout type; the renderer produces the corresponding arrangement.

**Content of a layout:** A layout may arrange **any type of element**: shapes or **nested layouts**. For example, a question may call for "an array of two stacks" or "a shape with multiple elements inside". **Scatter** is a layout type that randomly places elements inside a bounding box (see below); it is often used for irregular (non-grid) placement within a shape.

**Default layout: single centred element.** When the template does not specify a layout type, the **default layout** is a **single centred element**: one element (e.g. one shape container) centred in the answer image. Its centre coincides with the centre of the answer viewBox. No stack, no array—just one centred element.

**Layout types** (when the template specifies something other than the default):

| Layout type | Description | When to use |
|-------------|-------------|-------------|
| **Single centred** (default) | One element centred in the answer image. | Default when the template does not specify stack, array, or multiple elements inside a shape. |
| **Scatter** | A **1-dimensional array of elements** (its child shapes or layouts). The renderer places them **randomly** inside the bounding box of the shape that contains the scatter (or the top-level viewBox if at the top level). Because placement is random, the scatter is **unordered for question logic**—there is no meaningful first, second, or position order; only the set (count and type) matters. Elements are placed so they do not overlap (e.g. minimum centre-to-centre distance) with irregular spacing. | When the template asks for irregular (non-grid) placement within a region. |
| **Stack** | Depth-ordered overlapping shapes (bottom drawn first, above drawn over). | When the template asks for "N shapes in a stack", "a square with a circle on top", etc. |
| **Array** | Multiple elements in a regular arrangement; default **rectangular** (grid rows × columns). Subtypes: **loop** (1D, evenly on a circle), **triangular** (2D tapering formation). | When the template asks for "2×2 array of triangles", "six shapes in a loop array", "triangular array of circles", etc. |

**Layout type: single centred (default).** One element (e.g. one shape container) is centred in the answer image; its centre coincides with the centre of the answer viewBox. Used when the template does not specify stack, array, or multiple elements inside a shape.

**Layout type: scatter.** A **scatter** is a **1-dimensional array of elements**: its children (one or more shapes or layouts) are placed **randomly** inside the **bounding box** of the shape that contains it (or the top-level viewBox if the scatter is at the top level). Because placement is random, the scatter is **unordered for question logic**—position order (first, second, …) is not significant; only the set (count and type) is. Elements are placed so they do not overlap (e.g. minimum centre-to-centre distance) with irregular (non-grid) spacing within the shape.

**Layout type: stack.** A **stack** is a layout that orders elements by depth: the **bottom** element is drawn first, elements **above** are drawn over it. **In general, stack children should be shapes.** Nested layouts (stack or array) as direct children are possible but should be used only when necessary; see visibility constraints below. Use for "a square with a circle on top" or "four regular shapes in a stack".

**Stack terminology:**

| Term | Description |
|------|--------------|
| **Spacing** | How much successive elements overlap along the **stack direction**. **Tight** = large overlap (only a small band of each element visible). **Loose** = small overlap (more of each element visible). **Medium** = moderate overlap. The renderer may use a consistent offset (e.g. as proportion of element size) per spacing level. |
| **Regularity** | Whether the overlap/offset is **regular** (even, predictable offset from one element to the next—stack looks uniform) or **irregular** (deliberate variation or randomness in how much each element is offset from the one below—stack looks less uniform). Default: **regular**. |
| **Direction** | The **main axis** along which the stack is drawn, starting from the **bottom** element. **Up** (default) = each next element is drawn above the previous (vertical, bottom to top). **Down** = each next element is drawn below the previous (vertical, top to bottom; bottom of list = top of stack). **Right** = horizontal, left to right (first element leftmost). **Left** = horizontal, right to left (first element rightmost). Optionally **angle** (e.g. diagonal) if the spec is extended. |
| **Step (cross-axis offset)** | To give a **3D look** as if shapes sit on top of each other, each successive element must be **offset in the other dimension** (perpendicular to the stack direction). Drawing shapes only along the main axis (e.g. squares directly on top of each other with no horizontal shift) does not read as a stack. The **step** is this perpendicular offset: for **vertical** stacks (direction up/down), a **horizontal** step (each shape shifted **right** or **left** from the one below); for **horizontal** stacks (direction left/right), a **vertical** step (each shape shifted **up** or **down**). Step direction values: **right**, **left** (for vertical stacks), **up**, **down** (for horizontal stacks). Default: e.g. **right** when direction is up (stack “steps” toward the right going upward); **down** when direction is right. The renderer chooses step magnitude (e.g. proportion of element size) so the stack reads clearly. |

**Rules:** A shape at the **bottom** has none drawn underneath; it may be partially covered above. A shape **above** another is drawn so it **partially but not fully** conceals the one(s) below—enough remains visible so stack order and identity are clear. **Top** = no shapes drawn above it. **Equal depth** = neither overlaps the other (e.g. side by side).

**Visibility and constraints (stacks):** To avoid obscuring intended logic, apply the following. **(1) Prefer shapes as stack children** — stack elements should normally be shapes, not nested stacks or arrays. **(2) No nested layouts except at the top** — shapes that are **not** at the top of a stack (and their children) should **not** contain further layouts (no scatter, stack, or array inside). Only the **top** shape in a stack may contain a nested layout; otherwise overlapping elements above can hide the content and confuse the user. **(3) Partitions in stacks need extreme restriction** — partitions on shapes within a stack greatly reduce visibility of the partitioned regions when other elements overlap them. Use partitions in stacks only when necessary and keep them minimal. **(4) Partition and stack direction must align** — the stack should be **aligned** with any partition used on its shapes and we should ensure the stack contains only **regular** shapes. For example: **vertical** partitions are valid on a **vertical-direction** stack (up/down), because the partition bands run across the visible band of each shape; **horizontal** partitions on a vertical stack can be largely obscured by the elements above, so avoid horizontal partitions on vertical stacks (or restrict to the top shape). Conversely, **horizontal** partitions align with **horizontal-direction** stacks (left/right). In short: provided shapes are regular, partition orientation should match stack direction (vertical partition ↔ vertical stack; horizontal partition ↔ horizontal stack) so that the partitioned sections remain visible in the exposed band of each shape.

**In templates:** Refer by **depth** ("the shape at the bottom", "the top shape") or **count and role** ("4 regular shapes in a stack", "2 equal-depth shapes and 1 shape on top"). For "N shapes in a stack", assign depths 1…N and draw in that order. For "M equal-depth shapes and 1 on top", draw the M so they do not overlap, then draw the one on top so it partially overlaps each. Templates may specify stack **spacing** (tight / medium / loose), **regularity** (regular / irregular), **direction** (up / down / right / left), and **step** (right / left for vertical stacks; up / down for horizontal stacks) when the question type requires it.

**Layout type: array.** An **array** = layout that arranges **multiple elements** in a regular arrangement with **even spacing** and **no overlap**. The elements may be shapes, **nested layouts** (e.g. an array of two stacks), or **null** (nothing drawn in that position). Distinct from layout type **stack** (stacks overlap in depth; arrays do not). **Default array type: rectangular.**

| Array type | Description | When to use |
|------------|--------------|-------------|
| **Rectangular** (default) | Elements in a **grid** (rows × columns) with **horizontal alignment** and even spacing. May be 2D (e.g. 2×2) or 1D (e.g. 1×4 or 4×1). | When the template says "array" without specifying type, or "2×2 array", "1×4 array of pentagons", etc. **Right-angled triangular array** (or "right angled" array) is **not** a separate array type: it is shorthand for a **rectangular (square) array** with **null** elements so that the non-null positions form a right-angled triangle. The positions in the containing square that lie outside the triangle **must** be null. **Corner** (optional): **bottom_left** (default), **bottom_right**, **top_left**, **top_right** — where the **square corner** (the 90° vertex) of the right-angled triangle lies. In templates, specify by corner: e.g. "right angled array, corner at bottom left" or "right angled triangular array, corner at top right". When mesh is drawn with **draw_full_grid** false, mesh lines are never drawn to or from null positions (see mesh rule below). |
| **Loop** | Elements arranged along a **path** (default: **circle**). The path may be any shape (circle or polygon); use **path_shape** (shape container key). **Placement:** on **vertices** (one per vertex; default for polygons) or on **edges** (evenly spaced on each edge; use **per_edge** = number of items per edge). For circle, elements are evenly spaced on the circumference (**count** required). For polygon + vertices, count = number of vertices (implicit or explicit). For polygon + edges, total = number of edges × per_edge. Path centre coincides with the viewBox (or container) centre. | "Loop array", "N shapes on a circle", "shapes at vertices of a hexagon", "two shapes per edge of a square", etc. |
| **Triangular** | **2D array** in a **tapering triangular formation**: row 1 has 1 element, row 2 has 2, row 3 has 3, etc. (or symmetric variant). Even spacing within and between rows; formation centred in the answer image. **Direction** (optional): **up** (default), **down**, **left**, **right** — which way the triangle points (apex). | When the template asks for "triangular array", "triangle of shapes", "1, 2, 3… formation", etc. Template may specify direction: "triangular array pointing up/down/left/right". |

Elements in any array (whether shapes or nested layouts) must be **scaled uniformly** so the array fits the bounding box (e.g. viewBox), except where an element is a motif (see §3.4 for standardized motif sizing).

**Drawing mesh (rectangular and triangular):** The question XML may request that the **mesh** (centre-to-centre lines between cells) be drawn. Use **draw_mesh** (true/false), **mesh_line_type** (vocabulary key: solid, dashed, dotted, bold; default solid), **draw_full_grid** (true = draw all mesh segments; false = draw only segments between adjacent **non-null** cells—never draw a mesh line that touches a null position), and **mesh_omit** (list of segments to omit, by cell-pair or line identifier). When **draw_full_grid** is false, the renderer must not draw any segment that connects to or borders a null cell; this allows e.g. a right-angled triangular layout (rectangular array with nulls) to show mesh only for the triangle, not for the missing part of the square. **mesh_omit** can still be used to omit specific segments in addition (e.g. 2×2 grid with one vertical line omitted).

**Drawing path (loop):** The question XML may request that the **path** (container shape—circle or polygon outline) be drawn. Use **draw_path** (true/false), **path_line_type** (vocabulary key; default solid), and **path_omit_edges** (polygon only: space-separated 0-based edge indices to omit).

**Loop path and placement:** The loop path defaults to a **circle**; specify **path_shape** to use another shape (e.g. square, hexagon). For polygon paths, **positions** may be **vertices** (one element per vertex) or **edges** (elements on each edge, evenly spaced; **per_edge** gives the number per edge). Total loop size: circle → count; polygon vertices → number of vertices; polygon edges → (number of edges) × per_edge.

**Null elements:** Any array position may be **null**; nothing is drawn in that location (the slot remains empty). Used for partial fills, **right-angled triangular formations** (rectangular array with nulls forming a triangle; template shorthand: "right angled triangular array" or "right angled" array—missing positions in the containing square must be null; specify **corner** = bottom_left | bottom_right | top_left | top_right, default bottom_left), or sparse layouts.

**Array size in templates:** When a template requests an **array size** or **total size** (e.g. "size 3–5", "total size 3–5"), it means the **total number of non-null elements** in the array. **Null positions do not count** towards this size. So "array of total size 4" may be a 2×2 grid with four shapes, or a 3×3 grid with four shapes and five nulls, etc.

**Examples:** 2×2 rectangular array of triangles; 6 pentagons in a loop array (circle); 4 shapes at vertices of a square (loop, path_shape=square, positions=vertices); 8 shapes (2 per edge of a square) (loop, path_shape=square, positions=edges, per_edge=2); triangular array of 10 circles (rows 1, 2, 3, 4), triangular array pointing down; **array of two stacks** (e.g. 1×2 array whose elements are two stacks); 2×2 with two null slots (e.g. circle top-left, square bottom-right, nulls elsewhere); **right-angled triangular array** (template: "right angled triangular array of circles", default corner bottom left; "right angled array, corner at top right") → rectangular array (e.g. 3×3) with nulls so non-null cells form a right-angled triangle, mesh with draw_full_grid false shows only the triangle.

**Nested perpendicular layouts (single row/column arrays and stacks):** This rule applies **only to rectangular arrays and stacks** (horizontal/vertical orientation). **Loop and triangular arrays do not use this rule**—nested content in a loop or triangular array is scaled by the outer array’s scale as usual. When a **single-row or single-column rectangular** array (e.g. 1×N or N×1) or a **stack** is nested inside a layout that is oriented the **other way** (e.g. a vertical stack inside a horizontal 1×3 array, or a horizontal stack inside a vertical 3×1 array), a **special scaling rule** applies so that severe scaling is avoided. **(1)** Only the **numerical minimum** (i.e. the **greatest scaling reduction**) of the two directions is applied, and only at the **lower** (nested) level. **(2)** **No reduction** is applied at the **top** level along its main axis. **(3)** As a result, bounding boxes at the top level **overlap** (e.g. the slots for each top-level element are not shrunk to fit the nested content). This is not a visibility problem when e.g. "tall" shapes (vertical stacks or single-column arrays) are arranged in a horizontal formation: they extend in the vertical direction and can overlap horizontally at the top level without obscuring each other. The rule avoids unnecessarily severe scaling when layouts are nested perpendicularly.

**Once per layout:** Each layout in the nesting chain may participate in this special rule **at most once** (either as the outer level, with no reduction, or as the inner level, with the minimum scale). So the rule is applied at only one perpendicular boundary per layout. Example: a chain **1 horizontal → 2 vertical → 3 horizontal** applies the rule at **2** (skip scaling at 1, apply minimum at 2); the rule does **not** apply between 2 and 3, so 3 is scaled normally relative to 2. Example: **1 vertical → 2 horizontal → 3 vertical → 4 horizontal** applies the rule at **2** (1–2 boundary) and at **4** (3–4 boundary); the rule is not applied between 2 and 3.

#### Shape containers (3.3)

**Shape containers** are the outer shapes that may contain **the same content options as the diagram root**: a **single centred shape** (one nested shape), **scatter**, **stack**, or **array**—or no layout (partition and shading only). Use these names when describing "a `square` with two `circle`s inside", "a circle containing a stack of three shapes", or "each answer is a regular polygon".

**Regular shape:** A **regular shape** is a **circle** or a **regular polygon** (equal sides and equal angles). When a template asks for a "regular polygon" or "regular shape" without specifying the number of sides, a random regular polygon should have **3–8 sides** (triangle through octagon) unless the template specifies otherwise.

**Position in answer image:** Unless the template specifies a different **layout** (see Layout (3.2)), the diagram uses the **default layout: single centred element**. One element (e.g. one shape container) is **centred vertically and horizontally** in the answer image; its centre coincides with the centre of the answer viewBox (e.g. (50, 50) in a 0 0 100 100 viewBox). **Triangles** (vertex at top) are centred so the vertical centre of the triangle’s bounding box coincides with the centre of the viewBox.

**Size when containing content:** Any shape that **contains content** (a nested shape, scatter, stack, or array) must be **large enough** so that the content fits inside with the specified margins (e.g. element centres inside the shape, element cell half-size clear of the boundary when the layout is scatter). **Triangles** must be drawn large enough to accommodate the same content as other shapes and **centred** in the viewBox.

**Scaling concern:** Content inside a shape (nested shape, scatter, stack, or array) is **scaled to fit** the shape's bounding box. Contained shapes and layouts therefore scale with the container. **Motifs** are the exception: they use **standardized sizing** (small/medium/large per §3.4) and do not scale with the container. Deep nesting or many elements inside a small shape can make layout and readability difficult; templates and renderers should keep nesting and counts reasonable for the container size.

**Regular shapes:**

| Key | Description | Notes | Symmetry axes | Rot. order |
|-----|-------------|-------|---------------|------------|
| `circle` | Circle | Curved; use as outer frame when specified | `-` `│` `/` `\` | ∞ |
| `triangle` | Regular triangle (3 sides) | Equilateral | `│` | 3 |
| `square` | Regular square (4 sides) | Regular quadrilateral | `-` `│` `/` `\` | 4 |
| `pentagon` | Regular pentagon (5 sides) | | `│` | 5 |
| `hexagon` | Regular hexagon (6 sides) | | `│` `-` | 6 |
| `heptagon` | Regular heptagon (7 sides) | | `│` | 7 |
| `octagon` | Regular octagon (8 sides) | | `│` `-` `/` `\`| 8 |

Unless the template specifies otherwise, polygons in this table are **perfectly regular** (e.g. "triangle" = equilateral).

The symmettry axis listed here act as a simple reference for the question template parser, to allow it to retain a rudimentary understanding of the four main lines of symmetry it should track and enforce as dictated by the template.  Tracking full symmetry for polygons (or more complex shapes) of order 5 or higher is out of scope.

**Common irregular shapes:**

| Key | Description | Notes | Symmetry axes | Rot. order |
|-----|-------------|-------|---------------|------------|
| `right_angled_triangle` | Right-angled triangle | One 90° angle; default orientation: right angle in bottom left. | `/` (if isosceles) | 1 |
| `rectangle` | Rectangle (4 sides, two pairs equal) | Not square. Default: horizontal, width = 1.6× height. | `│` `-` | 2 |
| `semicircle` | Semicircle | Default: flat edge at bottom, arc on top; vertically centred. | `│` | 1 |
| `cross` | Cross (+) | 12-sided cross from square with indented corners. Branch thickness ≈ 70% of square. | `│` `-` | 4 |
| `arrow` | Arrow outline | Full 7-sided arrow. Triangular head ≈ 50% of width. Default: point right. | `-` | 1 |

**Symbols (as shape containers):** Outline shapes that can be used as **shape containers** when the template allows. Use the same canonical SVG outlines as for motifs (see Motif dictionary and `nvr-symbols/shape-*.svg`), drawn at container size.



**Concentric partitions:** **Suitable:** circle; regular polygons (triangle through octagon); common irregular (right_angled_triangle, rectangle, semicircle, cross, arrow); and among symbols **star** only. **Not suitable for concentric:** **`plus`**, **`times`**, **`club`**, **`heart`**, **`diamond`**, **`spade`**.

| Key | Description | Notes | Symmetry axes | Rot. order |
|-----|-------------|-------|---------------|------------|
| `plus` | Plus (+) |  | `│` `-` | 4 |
| `times` | Times (×) | Diagonal cross.  | `/` `\` | 2 |
| `club` | Playing card club (♣) | Not suitable for concentric partitions (stem is confusing visually). | `│` | 1 |
| `heart` | Playing card heart (♥) |  | `│` | 1 |
| `diamond` | Playing card diamond (♦) |  | `│` `-` | 2 |
| `spade` | Playing card spade (♠) | Not suitable for concentric partitions (stem is confusing visually). | `│` | 1 |
| `star` | Five-pointed star | Radial partition: 4 or 5 sections. | `│` | 5 |

**Common shape** = a regular shape, a common irregular shape, or a symbol (when the template allows).

**"Irregular shapes" / "any shape" in templates:** When a template uses **"irregular shapes"** or **"any shape"** (or similar) in a [Choose] or variator list without further restriction, the **default** is **all common shapes**—i.e. all common regular and common irregular shapes (and symbols when the template allows). So "irregular shapes" does not mean "irregular only"; it means the full common-shape set unless the template explicitly restricts (e.g. "regular only" or "irregular only").

#### Motif dictionary 

A **motif** is a shape (any of the keys in the table below) used under **visibility restrictions**: it **cannot be partitioned**, must have **solid shading** (solid or white only—not hatched), and is drawn at a **standardized size** regardless of the scaling that would be imposed by its container. This ensures that all motifs within a question use the same standardized scaling for comparison.

**Default fill:** Motifs are **solid black** by default. The template or question XML may specify a different solid or white fill (e.g. grey, white, grey_light) when needed. If inside a black container, black motifs must not be used as they will be invisible.  If a black fill containing has been chosen by the generator for question template, it should use white motifs by default, and if the motif colour is the same across multiple diagrams, all diagrams should default to white.

**Standardized sizes:** There are three standard scalings: **small**, **medium**, and **large**. The **default** is **medium** when the motif is in the top-level bounding box or in a shape that is a direct child of the top level. The **default** is **small** for motifs at lower levels of nesting (e.g. inside a shape that is inside another layout). The renderer ignores container-based scaling for motifs and uses these sizes consistently.

Motifs may appear in **any type of layout** (single centred, scatter, stack, array): inside shapes, at line ends, as standalone elements, or as elements in a stack or array. **Restrictions:** (1) **Shading** — Motifs must not be placed on hatched (line) shaded areas; use **solid** or **white** fill for any region where motifs appear. (2) **Choice of shape container** — Some shapes have too little interior for multiple motifs (see Shape containers: not suitable for multiple elements inside); the template may impose further restrictions (currently no global restriction). When the question specifies a fill variation, motifs may use grey, white, or other solid shading; otherwise they are solid black.

| Key | Description | Notes / SVG | Symmetry axes | Rot. order |
|-----|-------------|-------------|---------------|------------|
| `circle` | Circle filled solid | `<circle>` with fill | `-` `│` `/` `\` | ∞ |
| `plus` | Plus (+) | Two perpendicular lines crossing at centre | `│` `-` | 4 |
| `times` | Times (×) | Diagonal cross | `/` `\` | 2 |
| `heart` | Playing card heart (♥) | Standard heart motif | `│` | 1 |
| `diamond` | Playing card diamond (♦) | Rhombus filled | `│` `-` | 2 |
| `club` | Playing card club (♣) | Three circles + stem or simplified | `│` | 1 |
| `spade` | Playing card spade (♠) | Inverted heart with stem | `│` | 1 |
| `square` | Square filled solid | `<rect>` with fill | `-` `│` `/` `\` | 4 |
| `triangle` | Triangle filled solid | Equilateral, vertex up | `│` | 3 |
| `star` | Five-pointed star | Filled star (upright) | `│` | 5 |

**Symmetry axes** = reflection symmetry lines in default orientation (`-` horizontal, `│` vertical, `/` `\` diagonals). **Rot. order** = rotational symmetry order (see Symmetry and rotational symmetry below). When forcing a layout to be symmetric about a line, use only elements that have that line of symmetry (for motifs see standardized sizes in this section). For **canonical SVG** per motif, use **nvr-symbol-svg-design.md** and **`nvr-symbols/`**. 

#### Scaling, spacing, and motif sizes (renderer rules)

This subsection defines how the renderer scales and spaces **children** of each layout type (so that diagrams fit the viewBox and do not overlap), and how the **three motif sizes** (small, medium, large) are defined. All values below refer to a **viewBox of 0 0 100 100**. Shapes are drawn in a local coordinate system where the shape’s bounding box has diameter 100; placement is done by translating and scaling that fragment so the shape’s centre is at `(cx, cy)` with scale `s` (i.e. the shape occupies roughly `cx ± 50s`, `cy ± 50s` in viewBox units).

**Scatter (top-level or inside a shape)**

- **Spacing:** Child centres are placed with a **minimum centre-to-centre distance** so shapes do not overlap. Positions are chosen by rejection sampling within the allowed region. For **non-motif** scatters, min distance is tied to scale (see below). For **motif** scatters, min distance = 100 × (motif scale).
- **Scale:** When shapes have **motif_scale**, size and spacing are determined by the motif size (small/medium/large). When **no motif_scale**, scale and spacing vary by **effective count** (actual count or `scale_as_count`): fewer elements → larger scale; the renderer uses the most generous scale that still avoids overlap (see proposed table below).
- **Scatter inside a shape:** The allowed region is **inside the shape boundary** with an **inset margin** from the outline (margin ≥ 50×scale so a shape centred at the boundary edge does not stick out). The renderer uses an *inside_check* (point-in-circle for circle, point-in-polygon with edge margin for polygons) and places centres only where they pass the check. No clipping: positions are chosen so every placed shape fits inside the boundary. To avoid placement failure in tight or irregular regions (e.g. triangle), the renderer applies a **scatter-inside-shape scale factor** (e.g. **0.55**): scale used for margin and min_dist is **scale(*n*) × 0.55**, so elements are smaller and placement is more likely to succeed.

**Scatter: proposed scale and spacing by count (non-motif, no overlap)**

To be **as generous as possible** with scale without allowing overlap, use the following. Shape diameter in viewBox = **100×scale**; for no overlap, **min centre-to-centre = 100×scale**. The usable region (top-level) has margin **50×scale** from each edge, so side length = **100×(1 − scale)**. Fitting *n* circles of diameter *D* = 100×scale in a square of side *L* = 100(1−scale) (grid bound) requires *L* ≥ *D*×√*n*, hence **1−scale ≥ scale×√*n***, so **scale ≤ 1/(1 + √*n*)**. A small safety factor (e.g. 0.99) accommodates random placement and floating point.

**Formula (generous, no overlap):**

- **scale(*n*) = 0.99 / (1 + √*n*)**  
- **min centre-to-centre = 100×scale(*n*)**  
- **margin (from viewBox or shape edge) = 50×scale(*n*) + ε** (e.g. ε = 1)

**Proposed scale and spacing table (viewBox 0 0 100 100):**

| *n* (effective count) | scale (proposed) | diameter (viewBox) | min centre-to-centre | margin (min from edge) |
|------------------------|------------------|--------------------|----------------------|-------------------------|
| 1 | 0.495 | 49.5 | 49.5 | 25.8 |
| 2 | 0.414 | 41.4 | 41.4 | 21.7 |
| 3 | 0.362 | 36.2 | 36.2 | 19.1 |
| 4 | 0.330 | 33.0 | 33.0 | 17.5 |
| 5 | 0.306 | 30.6 | 30.6 | 16.3 |
| 6 | 0.287 | 28.7 | 28.7 | 15.4 |
| 7 | 0.271 | 27.1 | 27.1 | 14.6 |
| 8 | 0.258 | 25.8 | 25.8 | 13.9 |
| 9 | 0.248 | 24.8 | 24.8 | 13.4 |
| 10 | 0.238 | 23.8 | 23.8 | 12.9 |
| 12 | 0.222 | 22.2 | 22.2 | 12.1 |
| 15 | 0.204 | 20.4 | 20.4 | 11.2 |
| 20 | 0.182 | 18.2 | 18.2 | 10.1 |

**Implementation note:** The renderer may use **scale(*n*) = 0.99/(1 + √*n*)** (capped at a maximum, e.g. 0.5 for *n*=1) and set **min_dist = 100×scale**, **margin = 50×scale + 1**. Use **effective count** = actual number of elements or `scale_as_count` when set (so multiple diagrams can share the same scale by setting the same `scale_as_count`). **scale_as_count** must be ≥ actual count (renderer clamps so effective_count ≥ actual_count) to avoid placement failure. For **scatter inside a shape**, multiply scale by a **scatter-inside-shape scale factor** (e.g. **0.55**) so margin and min_dist are more conservative and placement succeeds in irregular containers (e.g. triangle).

These values are suitable when placing a scatter inside an **empty bounding box**.  If the scatter is inside a shape, these values are subject to a multiplication factor of TBD.

**Stack**

- **Spacing:** Stack elements are offset along the **stack direction** by a fraction of the element size: **offset = size × (1 − stack_offset)**, with *stack_offset* (e.g. 0.52) controlling overlap (higher = tighter stack). A **cross-axis step** (e.g. 0.2 × element size) is applied so successive elements step slightly perpendicular to the stack (e.g. “step right” when stacking up).
- **Scale:** Positions are computed using a **position scale** (e.g. 0.28). The **draw scale** is the minimum of (position_scale × draw_scale_factor) and the **maximum scale that keeps all stack elements inside the viewBox** (so no shape centre is closer than 50×scale to the viewBox edge). The draw-scale factor (e.g. 1.6) allows stacks to be drawn larger than the overlap would suggest, subject to that cap.

**Array (rectangular)**

- **Spacing:** Spacing is **square**: every cell has the same width and height. The renderer uses the **minimum spacing required** in both x and y directions: **cell size = min(100/cols, 100/rows)**. The grid of `rows × cols` square cells is **centred** in the viewBox (0 0 100 100); cell centres are at `(origin_x + cell_size×(c+0.5), origin_y + cell_size×(r+0.5))` with `origin_x = 50 − (cols×cell_size)/2`, `origin_y = 50 − (rows×cell_size)/2`. No extra spacing at boundaries beyond this centring.
- **Scale:** The **array scale** is **scale = cell_size / 100**, so the shape diameter (100×scale) fits in each square cell.

**Array (loop)**

- **Spacing:** Elements are placed on a circle or polygon path. **Radius** (circle or polygon bounding radius) is **50×(1 − scale)** so the path fits inside the viewBox with the chosen scale. For a **circle**, positions are evenly spaced by angle. For a **polygon**, positions may be at **vertices** (one per vertex) or on **edges** (e.g. *per_edge* points per edge, evenly spaced along each edge).
- **Scale:** For a circle or one-per-vertex polygon: **scale_max = sin(π/n) / (1 + sin(π/n))** where *n* is the number of positions, so that the chord between adjacent positions is at least the shape diameter. For **multiple shapes per edge** (*per_edge* > 1): **scale_max = sin(π/n_sides) / ((per_edge+1) + sin(π/n_sides))** so spacing along each edge is sufficient. The **draw scale** is **scale_max × loop_scale_factor** (e.g. 0.85) so shapes are slightly smaller than the no-overlap maximum.

**Array (triangular)**

- **Spacing:** No spacing at boundaries. Row *r* has *r* cells (row 1 has 1, row 2 has 2, …). Cell size is **cell = min(100 / max_cols, 100 / num_rows)**; centres are placed in a triangular formation and centred in the viewBox.
- **Scale:** **scale = cell / 100** so each shape fits in one triangular cell.

**Nested layouts (e.g. array of stacks):** When a child of an array or stack is itself a layout (stack or array), the **perpendicular rule** (see QUESTION-XML-SPECIFICATION) may apply: only the **smaller** of the outer scale and the inner layout’s effective scale is used for the nested content, and only for **rectangular** arrays and stacks (not loop or triangular).

**Motif standardized sizes (small, medium, large)**

Motifs are drawn at a **fixed cell size** in viewBox units, independent of the container’s layout scale. The renderer uses three sizes so that templates can refer to “small”, “medium”, or “large” motifs.

| Size    | Use | ViewBox cell size (nominal) | Notes |
|---------|-----|-----------------------------|--------|
| **Small**  | Motifs at **lower nesting** (e.g. inside a shape that is inside another layout). | e.g. 7.5 units | Default when the motif is not at top level or not a direct child of the top-level layout. |
| **Medium** | Motifs at **top level** or in a shape that is a **direct child** of the top level. | e.g. 12.5 units | Default for top-level or one-level-down motifs. Reference size used in motif placement (e.g. nvr-symbol-svg-design.md “1/8 of viewBox”). |
| **Large**  | When the template explicitly requests a larger motif (e.g. “one large circle”). | e.g. 17.5 units | Used only when specified; gives a motif that reads as dominant in the cell. |

**Placement constraints for motifs inside shapes:** Motif **centres** must lie inside the shape, with a **minimum distance from the shape boundary** (e.g. half the motif cell size, or a fixed margin such as 6.25 viewBox units) so that the motif graphic does not overlap the container outline. For **circle** containers, the centre must satisfy distance from (50, 50) ≤ radius − margin. For **polygons**, the centre must pass a point-in-polygon test and the distance from the centre to the nearest edge must be ≥ margin. The **minimum centre-to-centre distance** between motifs (e.g. 12 viewBox units) avoids overlap of motif graphics.

#### Line types (3.5)

| Key | Description | SVG / usage |
|-----|-------------|-------------|
| `solid` | Continuous line | Default stroke, no dash array |
| `dashed` | Dashed line (e.g. equal dash and gap) | `stroke-dasharray` (e.g. `8 4`) |
| `dotted` | Dotted line | `stroke-dasharray` (e.g. `2 4`) |
| `bold` | Thicker solid line | Same as solid but `stroke-width` larger (e.g. 2× base) |

Use a **single base stroke-width** (e.g. 2 in a 100-unit viewBox) for `solid`, `dashed`, `dotted`; consistent multiplier for `bold`. **Symmetry:** Dashed and dotted **break reflection symmetry**; when forcing symmetry on a layout, use only **solid** or **bold** for the shape border.

#### Line terminations (3.6)

| Key | Description | Notes |
|-----|-------------|-------|
| `none` | No end cap / flat | Default line end |
| `arrow_single` | Single arrowhead (>) | One triangular arrowhead at end |
| `arrow_double` | Double arrowhead (>>) | Two arrowheads at end |
| `chevron` | Chevron at end | Single chevron, not full triangle |
| `chevron_double` | Chevrons at both ends | >——< |
| `circle` | Circle at line end | Same as motif `circle` at terminus |
| `plus` | Plus at line end | Same as motif `plus` |

Any motif from the **motif dictionary** may be used as a line termination (e.g. "line ends in a `heart`").

#### Line augmentations (3.7)

Detail drawn **on** a line (not at the ends). **Default:** augmentations are **centred on the line** and **evenly spaced around the centre** unless the template specifies otherwise.

| Key | Description | Notes |
|-----|-------------|-------|
| `arrowhead` | Arrowhead on the line | Single triangular arrowhead |
| `slash` | Slash (/) on the line | Short diagonal stroke crossing the line |
| `tick` | Vertical tick (│) on the line | Short stroke perpendicular to the line |
| `square` | Square on the line | Small square centred on the line |
| `circle` | Circle on the line | Small circle centred on the line |

Other motifs may be used as line augmentations. Use a **consistent size** (e.g. same as motif cell or line-termination size).

#### Shading types (3.8)

| Key | Description | Notes / SVG | Lines (default) |
|-----|-------------|-----------------|-----------------|
| `solid_black` | Solid black fill | `fill="#000"` or `currentColor` | `-` `│` `/` `\` |
| `grey` | Solid mid grey | e.g. `#808080`; use consistently | `-` `│` `/` `\` |
| `grey_light` | Solid light grey | e.g. `#d0d0d0`; use consistently | `-` `│` `/` `\` |
| `white` | White fill | **Default:** opaque white (`fill="#fff"`) so stacks and overlapping layouts display correctly. **Optional:** set shape attribute **`opaque="false"`** to render white as transparent (`fill="none"`) for question types that need it. | `-` `│` `/` `\` |
| `diagonal_slash` | Diagonal lines (/) | Hatched, top-left to bottom-right | `\` only |
| `diagonal_backslash` | Diagonal lines (\\) | Hatched, top-right to bottom-left | `/` only |
| `horizontal_lines` | Horizontal lines | Hatched horizontal | `│` only |
| `vertical_lines` | Vertical lines | Hatched vertical | `-` only |

**Fill and stroke opacity:** By default, white fill is **opaque** (#fff) and stroke is **opaque** (#000) so that stacks and overlapping elements display correctly (the top shape fully covers the one below). For question types that require transparency (e.g. see-through regions), the shape may set **`opaque="false"`** so that white shading is rendered as transparent (`fill="none"`). Line/stroke remains opaque unless the spec is extended.

**Lines (default)** = reflection symmetry of the shading pattern. When forcing symmetry on a layout, use only shading types that have that line of symmetry. Use **consistent line spacing and stroke width** for hatched shadings. (For motif placement and shading, see §3.4.)

#### Partitioned shapes (3.9)

A shape may be **partitioned** into **sections**, each with its own **shading** (see Shading types). Modes: **horizontal**, **vertical**, **diagonal** (slash or backslash), **concentric**, **radial**.

**Section bounds:** Proportion of the shape extent from **0** to **100**. E.g. horizontal **(0, 50)** and **(50, 100)** = two halves. Bounds inclusive at lower end, exclusive at upper for contiguous sections. Unless specified, **evenly distributed** (e.g. two sections → (0, 50), (50, 100)).

**Bands:** A thin section (e.g. **(30, 40)**); bands may be adjacent to form stripes or rings.

**Horizontal partition:** Cuts with horizontal lines. Breaks horizontal symmetry, not vertical. **Vertical:** Cuts with vertical lines. Breaks vertical symmetry, not horizontal. **Diagonal:** Cuts with diagonal lines; bounds 0–100 along diagonal axis.

**Concentric partition:** **Scaled copy of the shape inside itself**; scale 0 = centre, 100 = outer edge. E.g. **(0, 50)**, **(50, 100)** on a circle = central disc + outer ring. **(40, 50)** = thin annulus. **Suitable for concentric:** circle; regular polygons; right_angled_triangle, rectangle, semicircle, cross, arrow; and **star** only. Not: plus, times, club, heart, diamond, spade.

**Radial partition:** **Radial sections** (pie-style wedges) from the centre. For **circle**, any number of radial sections. For **regular polygon**, use when number of radial sections divides number of vertices (e.g. hexagon with 6 sections = 6 equal wedges). **Radial section numbering:** By default **clockwise from north** (12 o'clock). **Irregular shapes:** Standard is **exactly 4 radial sections** (horizontal and vertical through centre = quadrants). **Semicircle:** Radial sections from the centre of the full circle; numbering clockwise from the "start" of the semicircle. **Star:** 5 radial sections (rotational symmetry order 5).

**Elements that cannot be partitioned:** See §3.4 (motifs). When a partitioned shape contains such elements, they **may be confined to a single partition** (e.g. "three circles in the top half only"); placement rules apply **within that section** only, and that section’s fill must be solid or white where those elements appear (see §3.4). **Partition outlines:** Thin lines by default, same line type as shape border. **null sections:** A section with fill **null** is not drawn (including outer border of null partition). Where non-null meets null, draw the **normal shape outline** at that boundary.

---

### Concepts: diagram sequences, arrays, symmetry

#### Diagram sequences

A **diagram sequence** is a recognisable pattern of at least two elements within a diagram (distinct from **sequence questions**, which relate to patterns across multiple diagrams shown in order). **Examples:** A stack with shading pattern grey, black, white from the bottom; or a shape with clockwise augmentation pattern one, two, three arrowheads on sides.

**Visible domain size** = size of the visible information space (e.g. circle partitioned into 4 sections → domain size 4). **Repeating sequence** = repeats within its domain (e.g. (black, white) in 6 radial sections → black, white, black, white, black, white clockwise from north). **Terminating sequence** = does not repeat; unused positions assigned **null** (e.g. light grey). **Looping domain** = default; "first" position continues after the last (e.g. stack circle, triangle, square ≡ square, circle, triangle if domain loops). **Extended domain** = invisible element; use with care; **never use on radial partition regular shapes**. **Direction of a sequence:** Stack = up/down; radial sections = clockwise/anticlockwise; concentric = in/out; horizontal/diagonal = ascending (top to bottom); vertical = ascending/right (left to right). Two sequences are equivalent only if direction is the same. **Symmetric sequence** = reads the same start-to-end as end-to-start (e.g. (white, black, white)). Odd-one-out may have the correct answer exhibit the **mirror image** of the sequence.

For layout type **array** (rectangular, loop, triangular), see Layout (3.2).

#### Symmetry and rotational symmetry

**Lines of symmetry** (default orientation): **horizontal** (`-`), **vertical** (`│`), **diagonal** `/` and `\`. A shape is **symmetric** if it has at least one. **Rotational symmetry order** = number of distinct rotations (360°/n) that leave the shape unchanged (e.g. order 4 for a square).

**Symmetry as differentiator:** "Symmetry" as differentiator means **horizontal or vertical** only unless the template says **any symmetry** (all four) or **diagonal symmetry** (both diagonals). Split may be 4–1 or 1–4 (symmetric vs asymmetric); equal frequency unless template modifies. **Symmetry as variator:** Choice of **horizontal**, **vertical**, or **any**; if **any**, mix of lines across options (some horizontal, some vertical, one none). Diagonal lines not used when forcing layout symmetry for now.

**When forcing layout symmetry:** Use only **shape containers**, **shading types**, and **line types** that do not break symmetry (that line in default orientation). Use **solid** or **bold** for the shape border—**dashed** and **dotted** break reflection symmetry. **Layouts (e.g. of motifs, §3.4):** Such a layout has **no symmetry** by default and **destroys** the shape’s symmetry unless explicitly constructed to be symmetric. The generator **must** support **force symmetry** (e.g. mirror positions about a chosen line). **Spacing when using symmetry:** A **single element** may sit exactly on the line of symmetry. For a **pair** (canonical half + mirror), position off the line must be ≥ (min centre-to-centre distance)⁄2 from the line so the mirror is at least full min distance away. **Rotation:** If a shape is rotated, its recorded lines of symmetry change to match the new orientation.

**Shape containers (default orientation) — symmetry summary:**

| Shape | Symmetric? | Symmetry axes | Rot. order |
|-------|------------|---------------|------------|
| `circle` | Yes | `-` `│` `/` `\` | ∞ |
| `triangle` | Yes | `│` | 3 |
| `square` | Yes | `-` `│` `/` `\` | 4 |
| `pentagon` … `octagon` | Yes | per table in Shape containers | 5…8 |
| `right_angled_triangle` | Yes (if isosceles) | `/` | 1 |
| `rectangle` … `star` | Yes | per table in Shape containers | 1…5 |

---

### Template terminology

- **Parameter** — A variable that can be chosen for each answer (e.g. shape, line style, fill, motif type, number of motifs). Parameters describe how each answer looks or is defined.
- **Global parameter** — A parameter whose value is **fixed for the entire question** (one value for all answers). This is the default for parameters that appear in the template **setup** (the part before the answer definitions). E.g. “choose n between 3 and 6” makes n global; every answer uses that same n (except where the differentiator is motif count and one answer uses n+1).
- **Variator** — A parameter whose value **varies** between the items that the question type refers to (e.g. between answers for odd-one-out; between members of a set for “which belongs in the set?”). The term *variator* (rather than *variable*) is used to stress that this is a dimension along which those items **must be allowed to differ**—unlike a “variable” in the abstract sense, which might hold a single fixed value. **For odd-one-out:** variators are per-answer; their value counts across options must obey the **allowed splits** so that no single option is uniquely different on a variator that is not the differentiator.
- **[Each] (variators):** When **[Each]** prefixes a variator description (e.g. **[Each] shape at location**, **[Each] fill at location**), **every possible index or location is treated as a separate variator**. Each of these variators must be **purposely varied** according to the frequency and split rules: value counts across options must obey the allowed splits, and (for odd-one-out) only one such variator is the differentiator; all others must not make any single option uniquely different. So **[Each] shape at location** for a 2×2 array means four variators (shape at location 0, 1, 2, 3), each varied according to the rules.
- **[One] (differentiators):** When **[One]** is used in the Differentiators section (e.g. **[One] shape or fill**), the **differentiator is exactly one** of the listed kinds. The generator picks one variator from the (possibly [Each]-expanded) set that matches one of those kinds; that variator is the differentiator. So **[One] shape or fill** with **[Each] shape at location** and **[Each] fill at location** means the differentiator is either “shape at some location” or “fill at some location”.
- **Differentiator** — For **odd-one-out** questions only, the **parameter that determines the unique (correct) answer**. One of the variators is always the differentiator. The correct answer is the one that differs from the others on the differentiator only. The template need not specify which variator is the differentiator; if it does not, the generator chooses one.
- **Setup** — The part of the template that describes global parameters and question type before the answer definitions. Structured templates may use **Setup tags**: **[Choose]** = set of parameters or values to choose from; **[Never]** = must not be used (e.g. as differentiator); **[Uncommon]** = frequency modifier (lower probability); **[Allow]** = permit in this template (e.g. "nulls in array" means array cells may be null). In **Variators** and **Differentiators** sections: **[Each]** = expand to one variator per index/location, each varied by the rules; **[One]** = the differentiator is exactly one of the listed kinds (e.g. [One] shape or fill).

### Default behaviour (unless template states otherwise)

- **5 options** for multiple-choice.
- **Correct-answer position** — Uniform over options (1⁄5 each).
- **Duplication allowed** — Variator values may repeat across options (e.g. two options can both be `square`).
- **Layout** — As defined in §4 (Layout (3.2): default layout single centred element.

### Writing verbal question templates (overview)

When writing a **verbal question template** (for an author or a Phase 2 compilation agent), the **compiled script** (or the process that instantiates a question from the template) should **choose vocabulary elements at random** (motifs, line types, line terminations, line augmentations, and/or shading types from the NVR visual vocabulary in §4) and **stick with those same choices** for part or all of that question. **Increase randomness:** use a random draw or shuffle when the template calls for a free choice—e.g. “each answer is a regular polygon (3–8 sides)” → draw randomly from the allowed set per option, so question-to-question and option-to-option outcomes are unpredictable. The template may specify which vocabulary elements are fixed for the whole question and which vary per option.

#### Step 1: Verbal description

Start with a **verbal description** that: (1) states the question type (e.g. odd-one-out, sequence, matrix, code); (2) describes each figure or option using only terms from the **NVR visual vocabulary** (§4)—e.g. `circle`, `dashed`, `arrow_single`; (3) identifies the correct answer and the rule (e.g. “odd one out is B because it has two circles”). This description (or a structured form) is what Phase 2 compiles into a **template script**; when that script runs (Phase 3), it produces **question XML** that encodes concrete option diagrams using the same vocabulary keys, for the renderer (Phase 4) to turn into SVG.

#### Parameter choice rules when generating answers

When the **template script** (Phase 3) instantiates a question and writes **question XML**, it must apply the following so that answers are unambiguous and no accidental correct answers emerge. **Unless a template explicitly states otherwise**, assume: 5 options; global parameters have one value for the whole question; **for odd-one-out**, variators are chosen at random per option, **with duplication allowed**; random assignment to options (no fixed order); **layout**: default single centred element; motifs may appear in any layout (when inside a shape, with margin).

- **Number of options:** Unless stated, **5 possible answers** (not 4).
- **Correct-answer position (uniform):** Unless the template specifies which option is correct, the correct answer should be **uniformly distributed** over positions 1–5 (each 1⁄5). Do not fix to a single position.
- **Odd-one-out (general):** One of the variators is the **differentiator**. If the template does not specify which, the generator chooses one (e.g. number of motifs, line type, fill, motif type, shape). The correct answer **differs from the others on the chosen differentiator only**.
- **No duplicate parameter sets:** No two answers may use an **identical set of parameters**. Each option must differ in at least one parameter so the intended correct answer is unique.
- **Odd-one-out parameter spread (variators):** For each variator that is **not** the differentiator, **value counts** across options must obey the allowed splits below—so no single option is uniquely different on that variator. Rule: either **at least 3 different values** are used, or **if only 2 values** then **each value occurs at least twice** (e.g. never 4–1 for 5 options).
- **Allowed splits (value counts):** For variators that do not determine the correct answer, use these allowed splits (for 2 values only, each count ≥ 2). **5 options:** 2–3, 3–1–1, 2–2–1, 2–1–1–1, 1–1–1–1–1 (never 4–1). **4 options:** 2–2, 2–1–1 (never 3–1). **6 options:** 3–3, 2–2–2, 4–2, 4–1–1, 3–2–1, 3–1–1–1, 2–2–1–1, 2–1–1–1–1, 1–1–1–1–1–1 (never 5–1). Choose a split at random so questions are not always 2–3.
- **Global parameters (setup only):** Only parameters in the **template setup** (before answer definitions) are global. Do not treat shape, line style, or fill as global unless the template explicitly places them in the setup and states “same for all”.
- **Variators (odd-one-out):** For odd-one-out, any parameter that describes how each answer looks (shape, line style, fill, motif count, motif type unless “same motif for all”) is a variator. When the template uses **[Each]** (e.g. [Each] shape at location), expand to one variator per index/location and vary each according to the frequency and split rules (see **[Each] (variators)** above). When the template uses **[One]** in Differentiators (e.g. [One] shape or fill), the differentiator is exactly one of those kinds (see **[One] (differentiators)** above). The generator chooses at random from the allowed set per option, subject to no-duplicate parameter-set and odd-one-out spread rules.
- **Duplication of variator values (default):** **Duplication across options is explicitly allowed**. Two options may both be square, etc. The generator chooses at random subject only to: (1) no two options have an identical full set of parameters; (2) for odd-one-out, no single option is uniquely different on a non-differentiator variator.
- **Random assignment (no fixed order):** Variators must be **assigned randomly** to options 1–5 (e.g. random draw or shuffle). Do not use a fixed order (e.g. option 1 = triangle, option 2 = square).
- **Elements inside the containing shape:** Element centres must lie **inside** the shape with a margin so the full element cell does not cross the shape edge; for non-rectangular shapes use a point-in-polygon check and require minimum distance from element centre to boundary ≥ element cell half-size. (For motif sizing, see §3.4.)
- **No black fill when shape contains motifs:** Do **not** use `solid_black` for any shape container that contains motifs (see §3.4 for motif shading rules). Use `white`, `grey`, or `grey_light`.

**Example (avoiding accidental correct answers):** If each option is "n elements (e.g. motifs per §3.4) inside a shape" and the differentiator is element count (e.g. 3 vs 4), assign **shapes** so that no single option is the only one with a given shape—e.g. use at least three distinct shapes or ensure each shape appears at least twice (e.g. circle, circle, square, square, circle).

#### Frequency modifiers

Templates may use **common**, **uncommon**, and **rare** to affect the **probability** of outcomes (e.g. which variator value or which variator is the differentiator). Use **weighted random choice**: **common** = weight 1 (default); **uncommon** = weight 1⁄3; **rare** = weight 1⁄10. Unmodified outcomes use weight 1. Modifiers may apply to (a) choice of differentiator, (b) choice of variators, or (c) choice of values for a variator. For “**uncommon** add **symmetry** as a variator and an **uncommon** differentiator”: (1) P(add symmetry to variator set) = (1⁄3)⁄(1 + 1⁄3) = 1⁄4; (2) when choosing the differentiator among selected variators, symmetry (if present) has weight 1⁄3, others weight 1. For symmetry definition and layout rules, see **Symmetry and rotational symmetry** in the Concepts subsection above.

#### From template to question XML to pictorial assets

1. **Verbal template (Phase 1)** — Defines question type, parameters, variators, and differentiator as above.
2. **Template script (Phase 2 output, Phase 3 run)** — Compiled script instantiates questions by applying the parameter rules and writing **question XML** per question (question text, 5 options with diagram descriptions using vocabulary keys, correct index, explanation, product placement). The script does **not** produce SVG; it produces XML and a manifest. See §5 for required question XML structure. **When the template requests motifs** (e.g. "scatter of motifs", "number of motifs"), the **generator must mark those shapes as motifs in the question XML** using the convention defined in the question XML specification (e.g. set `motif_scale` on each shape that is a motif) so the renderer applies standardized motif sizing and default motif fill (solid black unless overridden).
3. **XML→SVG renderer (Phase 4)** — Reads question XML and produces 5 option SVGs and `question_meta.json` per question. The renderer uses only the NVR vocabulary and layout rules; it does not run template logic. See §6 for the renderer’s inputs, outputs, and responsibilities.
4. **Upload and insert (Phase 5)** — Manifest and asset directories are used to upload SVGs and insert DB rows. Image columns, SQL patterns, and upload steps are in §9.

#### Example Question Templates

Stored in question-gen\NVR-QUESTION-TEMPLATES.md

---

## 7. Question XML (required)

Question XML is the output of Phase 3 and the input to Phase 4 (the renderer). Each document describes **one** question in a logically unambiguous way, using the same vocabulary keys as the templates and NVR visual vocabulary (§4). The **exact schema** (element names, nesting, attributes) is defined in **QUESTION-XML-SPECIFICATION.md** and **question-xml.xsd** in this directory. The following are the **required and recommended** elements.

### Required

- **Question identity** — Stable id (e.g. for manifest and folder naming).
- **Product placement** — Subject and topic (by id or by code/name) so the question can be inserted into the correct place in the product.
- **Question text** — The text shown to the user (e.g. “Which shape is the odd one out?”).
- **Options** — Exactly **5** option elements. Each option describes the **diagram** for that answer (shape, partition, motifs, shading, layout intent) using vocabulary keys and the structural concepts in §4 (containers, partitions, stacks, sequences). No pixel-level layout; the renderer may resolve placement within the constraints given.
- **Correct answer** — Which option (0–4) is correct.
- **Explanation** (optional but recommended) — Post-answer hint for the user (`questions.explanation`). **User-facing language only:** do not use the internal term "motif" in explanation text; use user-facing terms such as "symbols" (e.g. "The odd one out contains five symbols; the others contain four").

### Recommended

- **Template id** — Which template (or template script) produced this question.
- **Seed** — For reproducibility when the renderer applies non-deterministic choices.

### Diagram structure in XML

Each option’s diagram description must be expressible in a **nested structure** whose root is a **shape** or **any layout** (scatter, stack, or array). The structure references only:

- **Shape** — Shape container (key), with optional **partition** (type, section bounds, shading per section), optional **content** (one of: shape, scatter, stack, or array — same options as the diagram root), **line type**, **shading**.
- **Layout type scatter** — **1D array of elements** (one or more child shapes or layouts) placed randomly in the bounding box. Unordered for question logic.
- **Layout type stack** — Ordered list of **elements** (bottom to top); each element may be a shape or a nested layout (scatter, stack, or array).
- **Layout type array** — Arrangement of **elements** (rectangular, loop, or triangular); each element may be a shape (repeated or explicit) or a nested layout (e.g. scatter, stack, or array).

The renderer is responsible for producing a valid, consistent SVG that obeys the NVR vocabulary and layout rules in §4.

See **QUESTION-XML-SPECIFICATION.md** for the full schema and sample documents; **question-xml.xsd** for validation.

---

## 8. XML→SVG renderer (Phase 4)

The **renderer** is a Python (or other) program that reads **question XML** and writes **question assets** (SVGs and metadata). It does not connect to the database or upload to storage.

### Inputs

- One or more **question XML** documents (files or stream), each describing a single question (§5).
- **Output directory** — Base path under which to create one subdirectory per question (e.g. `q00001/`).
- **Seed** (optional) — For reproducible non-deterministic choices (e.g. random placement within regions).

### Outputs (per question)

- **5 option SVG files** — In a defined order (e.g. `option-a.svg` … `option-e.svg`), each conforming to the NVR visual vocabulary and layout rules in §4.
- **question_meta.json** (or equivalent) — At least: `correct_index` (0–4), optional `template_id`, `seed`, `question_text`, `explanation`, `option_files` (ordered list of the 5 filenames).
- **Batch manifest** (optional) — Single `manifest.json` aggregating all questions in the run (see §8), written at a fixed path (e.g. `output/questions/manifest.json`).

### Responsibilities

- **Parse** question XML and resolve all references using only the **NVR vocabulary** (§4).
- **Resolve allowed non-determinism** — e.g. “place randomly in region”, “choose from set” — in a way that is consistent with §4 (no logical ambiguity; optional visual variation between runs).
- **Produce SVG** using consistent styling (same key ⇒ same look across questions).
- **Produce metadata** so that Phase 5 can build `questions` and `answer_options` rows and upload assets without further interpretation.

### Does not

- Connect to the database or upload to storage.
- Produce anything other than files under the given output directory (no side effects).

---

---

## 9. Output layout and manifest

**Recommended layout:**

```
output/
  questions/
    manifest.json       # one manifest for the whole batch
    q00001/
      option-a.svg
      option-b.svg
      ...
      question_meta.json
    q00002/
      ...
```

- One subfolder per question so upload can map one URL prefix per question.
- Manifest at a fixed path so the insert step (Phase 5) always knows where to read.

**Manifest shape (JSON):**

- Top level: `base_dir` (e.g. `"questions"`), `questions` (array).
- Per question: `id`, `template_id`, `correct_index`, `option_files` (ordered list of filenames), optional `question_text`, `explanation`, `seed`.

Phase 5 uses manifest + storage base URL to build full `option_image_url` values and inserts into `questions` and `answer_options`.

---

## 10. Storage, database, and insert

### Image columns and usage

Images are stored as **URLs only** (no binary data in the database). Schema: see **11plus-datamodel-design.md** → "Image support" for column definitions.

| Location | Table / column | Purpose |
|----------|-----------------|---------|
| **Question** | `questions.question_image_url` | One image for the question (diagram, shape, graph, photo). Shown with or above the question text. |
| **Answer option** | `answer_options.option_image_url` | One image per option (e.g. multiple-choice shapes or pictures). Can be used with or instead of `option_text`. |

- Both columns are **optional** and **VARCHAR(500)** (single URL per question/option).
- **Question text** (`question_text`) is still required; it can describe the image, ask "What is shown?" or "Which shape…?", or stand alone if the image is self-explanatory.

**Typical patterns:** **Image-only question** — set `question_image_url`; keep `question_text` short. **Image options** — set `option_image_url` on one or more `answer_options` (e.g. "Which diagram shows …?"); `option_text` can be empty, a label, or a fallback. **Mixed** — question has `question_image_url` and some options have `option_image_url` and/or `option_text`.

### Diagram format (SVG)

All **diagram** assets for NVR and similar picture-based reasoning (shapes, sequences, odd-one-out, matrices, line drawings) **must** be produced in **SVG**. Raster formats (PNG, JPEG) are allowed only for **photos or complex artwork** where vector is not practical. SVG is sharp at any size, small, editable, and compatible with the NVR visual vocabulary (§4).

### Storage and upload

- Option (and optional question) images are uploaded to object storage (e.g. Supabase Storage, S3, CDN). Obtain a **stable public URL** for each file.
- Store only the URL in `question_image_url` or `option_image_url`; the database does not store binary image data.
- Phase 5 supports both REST (JWT) and S3-compatible (access/secret key) upload for flexibility (e.g. local Supabase S3).
- **CORS / caching:** Ensure storage allows the front-end origin to load images and set appropriate cache headers if needed.

### Database tables

- **questions:** `subject_id`, `topic_id`, `question_type`, `question_text`, `question_image_url` (optional), `explanation` (optional), `points`, `time_limit_seconds`, etc.
- **answer_options:** `question_id`, `option_text`, `option_image_url`, `is_correct`, `display_order`.
- Subject/topic can be provided by ID or looked up by code/name (e.g. NVR, Shapes).

### Insert patterns (SQL)

**Prerequisites:** Images are already uploaded and you have a stable public URL for each; you know the correct `subject_id` and `topic_id` (from `subjects` and `topics`).

**Insert a question (with optional question image):**

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

**Insert answer options with images:**

```sql
INSERT INTO answer_options (question_id, option_text, option_image_url, is_correct, display_order)
VALUES
  ((SELECT id FROM questions WHERE ... LIMIT 1), '', 'https://your-storage.example.com/options/option-a.svg', false, 1),
  ((SELECT id FROM questions WHERE ... LIMIT 1), '', 'https://your-storage.example.com/options/option-b.svg', false, 2),
  ((SELECT id FROM questions WHERE ... LIMIT 1), '', 'https://your-storage.example.com/options/option-c.svg', true, 3),
  ...
```

Phase 5 typically builds these from the manifest + storage base URL (see §8).

### Display on the website

For **diagrams and NVR-style graphics**, SVG is required; assets must use only the NVR visual vocabulary (§4). The front end shows images via `<img src="...">` when a URL is present. See **question-gen** sample XML and generated output for examples.

---

## 11. Script responsibilities (summary)

| Phase | Role | Inputs | Outputs |
|-------|------|--------|--------|
| **1** | Author question templates (human / agent) | Domain and format requirements | Template specs, structure |
| **2** | Compile templates into Python script that produces question XML | Template specs | Template script (Python) |
| **3** | Run template script to create question XML | Template script, seeds/config | Question XML (per question or batch) |
| **4** | Run renderer: XML → assets (JSON, text, SVG) | Question XML | Per-question dirs + optional manifest |
| **5** | Upload assets; INSERT questions + answer_options | Manifest, storage config, DB config, subject/topic | Rows in DB; files in storage |

Optional for Phase 5: dry-run (validate manifest only), subject/topic lookup by code and name (e.g. NVR, Shapes).

---

## 12. Extensibility

- **Multiple templates:** Phases 2–4 can support different template types; manifest carries `template_id` per question.
- **Multiple subjects/topics:** Phase 5 can take subject/topic from manifest or config so one manifest can target different subjects/topics in future.
- **Question images:** If templates and manifest support `question_image_url` (or a question-level asset), Phase 5 can upload it and set `questions.question_image_url` the same way as option images.

---

## 13. Where implementations live

- **question-gen:** This design doc; XML spec, XSD, and XML→SVG renderer; sample XML and batch script. Further shared config, schemas, or runner scripts can be added here to support multiple question types or repos.
