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

The following dictionaries define the **only** allowable motifs, line types, line terminations, and shading types for NVR-style diagram questions. Verbal descriptions of questions (and any AI that generates pictorial questions) must reference these by name. **Shape containers** (3.1) are the first dictionary; then motifs, line types, line terminations, line augmentations, and shading types. A shape may be **partitioned** (3.9) into sections with their own shading; motif layouts may be absent or confined to one partition. For arrangements of multiple shapes with depth, use **shape stacks** (3.8). Generated SVGs must use only these options so that `circle` or `dashed` is identical across questions.

**Vocabulary element** is the generic term for any single entry from these dictionaries: a **shape container** (e.g. `square`, `circle`), a **motif** (e.g. `circle`, `heart`), a **line type** (e.g. `solid`, `dashed`), a **line termination** (e.g. `arrow_single`, `chevron`), a **line augmentation** (e.g. `circle`, `arrowhead`), or a **shading type** (e.g. `solid_black`, `diagonal_slash`). In this guide, all vocabulary elements are quoted in backticks when used as formal terms, e.g. `circle`, `dashed`, `arrow_single`. When writing a verbal question template, the generator chooses random vocabulary elements and sticks with those same choices for part or all of that question (see section 4).

### 3.1 Shape containers

**Shape containers** are the outer shapes that may contain motifs (or other content) in a diagram. Use these names when describing "a `square` with two `circle`s inside" or "each answer is a regular polygon".

**Regular shape:** A **regular shape** is a **circle** or a **regular polygon** (equal sides and equal angles). When a template or description asks for a "regular polygon" or "regular shape" without specifying the number of sides, a random regular polygon should have **3–8 sides** (triangle through octagon) unless the template specifies otherwise.

**Position in answer image:** Unless the question template explicitly states otherwise (e.g. "offset to the left", "positioned at top"), **containers are centred vertically and horizontally** in the answer image. The shape (or other outer frame) should be drawn so that its **centre coincides with the centre of the answer viewBox** (e.g. centre at (50, 50) in a 0 0 100 100 viewBox). **Triangles** (with one vertex at the top) are **centred vertically by default**: the vertical centre of the triangle's bounding box should coincide with the centre of the viewBox (e.g. at y = 50 in a 0 0 100 100 viewBox), so the triangle sits symmetrically in the vertical space.

**Size when containing motifs:** Any shape that **contains motifs** must be **large enough** so that the required number of motifs fit inside with the specified margin (motif centres inside the shape, motif cell half-size clear of the boundary). In particular, **triangles** have less usable interior than squares for a given "radius"; the triangle must be drawn **large enough** (e.g. so its inscribed circle or equivalent usable area can accommodate the motif count) and **centred** in the viewBox. Generators must use a triangle size that allows the same motif counts as other shapes (e.g. n between 3 and 6) to be placed without overlap.

#### Regular shapes

**Circle** and **regular polygons** (equal sides and equal angles). Use these keys when the template asks for a "regular shape" or "regular polygon"; for a random regular polygon use 3–8 sides unless the template specifies otherwise.

| Key | Description | Notes | Symmetry axes | Rot. order |
|-----|-------------|-------|---------------|------------|
| `circle` | Circle | Curved; use as outer frame when specified | `-` `│` `/` `\` | ∞ |
| `triangle` | Regular triangle (3 sides) | Equilateral | `│` | 3 |
| `square` | Regular square (4 sides) | Regular quadrilateral | `-` `│` `/` `\` | 4 |
| `pentagon` | Regular pentagon (5 sides) | | `│` | 5 |
| `hexagon` | Regular hexagon (6 sides) | | `│` `-` | 6 |
| `heptagon` | Regular heptagon (7 sides) | | `│` | 7 |
| `octagon` | Regular octagon (8 sides) | | `│` `-` | 8 |

**Regularity:** Unless the question template specifies otherwise, polygons in this table are assumed **perfectly regular**. For example, "triangle" means equilateral, "pentagon" means regular pentagon. Draw regular polygons only when using the regular-shape keys.

#### Common irregular shapes

Use these when the template explicitly allows or asks for non-regular shapes.

| Key | Description | Notes | Symmetry axes | Rot. order |
|-----|-------------|-------|---------------|------------|
| `right_angled_triangle` | Right-angled triangle | One 90° angle; orientation (which vertex is right) may be specified or random. Default orientation should have the right angle in the bottom left. Isosceles right triangle has one axis. | `/` (if isosceles) | 1 |
| `rectangle` | Rectangle (4 sides, two pairs equal) | Not square; use when template allows non-square quadrilateral. Default orientation should be horizontal with width = 1.6 times height. | `│` `-` | 2 |
| `semicircle` | Semicircle | Half of a circle. **Default orientation:** straight line at the bottom (flat edge horizontal, arc on top); vertically centred in the answer image. Flat side may be specified as horizontal or vertical if needed. | `│` | 1 |
| `cross` | Cross (+) | 12-sided cross constructed from a square with the corners indented. Default thickness of the branches of the cross should be 70% of the width/height of the containing square. | `│` `-` | 4 |
| `arrow` | Arrow outline | Arrow shape as container (full 7-sided arrow shape). Triangular head should be 50% of the width. Default orientation should be to point right. | `-` | 1 |

#### Symbols (as shape containers)

**Symbols** are outline shapes that can be used as **shape containers** when the template allows. Use the same canonical SVG outlines as for motifs (see §3.2 and `nvr-symbols/shape-*.svg`), drawn at container size (e.g. centred in the answer viewBox). When a shape container is a symbol, motifs may be placed inside it subject to the same layout rules as for other containers.

**Not suitable to contain random motif layouts:** The symbol containers **`plus`**, **`times`**, **`club`**, and **`diamond`** have too little usable interior to place multiple motifs with the required minimum centre-to-centre distance; do **not** use them as containers when the question requires a motif layout inside. Use them only as outline shapes (e.g. when the diagram shows the shape alone or with content outside it). **`heart`**, **`spade`**, and **`star`** are suitable to contain random motif layouts.

**Concentric partitions:** Shapes **suitable for concentric partition** (rings) are: **circle**; regular polygons (**triangle**, **square**, **pentagon**, **hexagon**, **heptagon**, **octagon**); common irregular shapes (**right_angled_triangle**, **rectangle**, **semicircle**, **cross**, **arrow**); and among symbols **star** only. **Not suitable for concentric:** **`plus`**, **`times`**, **`club`**, **`heart`**, **`diamond`**, and **`spade`**—do not use these for concentric partition.

| Key | Description | Notes | Symmetry axes | Rot. order |
|-----|-------------|-------|---------------|------------|
| `plus` | Plus (+) | Two perpendicular arms of equal length crossing at centre. **Not suitable to contain random motif layouts or concentric partitions.** | `│` `-` | 4 |
| `times` | Times (×) | Diagonal cross; same as plus rotated 45°. **Not suitable to contain random motif layouts or concentric partitions.** | `/` `\` | 2 |
| `club` | Playing card club (♣) | Three lobes + stem. **Not suitable to contain random motif layouts or concentric partitions.** | `│` | 1 |
| `heart` | Playing card heart (♥) | Standard heart outline. **Not suitable for concentric partitions.** | `│` | 1 |
| `diamond` | Playing card diamond (♦) | Rhombus outline (axis-aligned). **Not suitable to contain random motif layouts or concentric partitions.** | `│` `-` | 2 |
| `spade` | Playing card spade (♠) | Inverted heart with stem. **Not suitable for concentric partitions.** | `│` | 1 |
| `star` | Five-pointed star | Filled or outline star (upright). Only symbol suitable for concentric partitions. For radial partition, use **5 radial sections** (rotational symmetry order 5). | `│` | 5 |

#### Common shapes

A **common shape** is a **regular shape**, a **common irregular shape**, or a **symbol** (when the template allows symbol containers). 

### 3.2 Motif dictionary

A **motif** is a small shape on a diagram that can be any of our available standard shapes (the keys in the table below). It is small enough on our diagrams that it is considered a **fundamental unit**: it cannot be **partitioned** (too small to see) or **stacked** (overlap would be visually confusing). Motifs can be arranged into **layouts** (see §3.7); these are the arrangements of motifs inside a shape container. Motifs **can be filled** (e.g. solid black, grey, or other shading types when the question specifies a fill variation).

Motifs can appear **inside** shapes, at line ends, or as standalone elements in a diagram. Use the **key** in verbal descriptions and when generating SVG (e.g. "use `circle` for the odd one out").

| Key | Description | Notes / SVG usage | Symmetry axes | Rot. order |
|-----|-------------|-------------------|---------------|------------|
| `circle` | Circle filled solid | `<circle>` with `fill` (e.g. black or currentColor) | `-` `│` `/` `\` | ∞ |
| `plus` | Plus (+) | Two perpendicular lines of equal length crossing at centre | `│` `-` | 4 |
| `times` | Times (×) | Diagonal cross; plus rotated 45° | `/` `\` | 2 |
| `heart` | Playing card heart (♥) | Standard heart motif | `│` | 1 |
| `diamond` | Playing card diamond (♦) | Rhombus filled | `│` `-` | 2 |
| `club` | Playing card club (♣) | Three circles + stem, or simplified club shape | `│` | 1 |
| `spade` | Playing card spade (♠) | Inverted heart with stem | `│` | 1 |
| `square` | Square filled solid | `<rect>` with fill | `-` `│` `/` `\` | 4 |
| `triangle` | Triangle filled solid | `<path>` or `<polygon>` with fill (equilateral, vertex up) | `│` | 3 |
| `star` | Five-pointed star | Filled star (upright) | `│` | 5 |

**Symmetry axes** are the reflection symmetry lines in default orientation (`-` horizontal, `│` vertical, `/` diagonal slash, `\` diagonal backslash). **Rot. order** is the rotational symmetry order (see Concepts, Symmetry and rotational symmetry). When forcing a motif layout to be symmetric about a line (e.g. vertical), use only motifs that have that line of symmetry so the motif does not conflict with the layout.

The motif dictionary applies to the **contents** of shapes (and to line terminations, see 3.4). For the **outer frame** that may contain motifs, use the shape containers in 3.1. For **canonical, consistent SVG** for each motif (size 1⁄8 of a standard answer in each direction), use the fragments and files in **nvr-symbol-svg-design.md** and the **`nvr-symbols/`** folder.

**fill** of **motifs** should always be solid black unless the question specifies a **fill** variation should be used.

### 3.3 Line types

Permitted stroke styles for **lines** (borders of shapes, connectors, axes, etc.). Reference by key in verbal descriptions.

| Key | Description | SVG / usage |
|-----|-------------|-------------|
| `solid` | Continuous line | Default stroke, no dash array |
| `dashed` | Dashed line (e.g. equal dash and gap) | `stroke-dasharray` (e.g. `8 4`) |
| `dotted` | Dotted line | `stroke-dasharray` (e.g. `2 4`) |
| `bold` | Thicker solid line | Same as solid but `stroke-width` larger (e.g. 2× base) |

Use a **single base stroke-width** (e.g. 2 in a 100-unit viewBox) for `solid`, `dashed`, `dotted`; use a consistent multiplier (e.g. 2) for `bold` so `bold` is the same across all diagrams.

**Symmetry:** Dashed and dotted line types **break reflection symmetry** (the dash/dot pattern does not mirror cleanly about a line). When forcing a motif layout to be symmetric about a line, use only **solid** (or **bold**) for the shape border so the outline does not conflict with the layout.

### 3.4 Line terminations

How a **line ends** (e.g. arrow, chevron, or a motif). Use when describing "a line with an arrowhead" or "a line ending in a circle".

| Key | Description | Notes |
|-----|-------------|-------|
| `none` | No end cap / flat | Default line end |
| `arrow_single` | Single arrowhead (>) | One triangular arrowhead at end |
| `arrow_double` | Double arrowhead (>>) | Two arrowheads at end |
| `chevron` | Chevron (fat, tapered > shape) at end | Single chevron, not full triangle |
| `chevron_double` | Chevrons at both ends | >——< |
| `circle` | Circle at line end | Same as motif `circle` at terminus |
| `plus` | Plus at line end | Same as motif `plus` |

Any motif from the **motif dictionary** (3.2) may be used as a line termination if it makes sense (e.g. "line ends in a `heart`"). List only the most common above; others (`heart`, `diamond`, `club`, `spade`, etc.) are referenced by the same key as in 3.2.

### 3.5 Line augmentations

**Line augmentations** are additional detail drawn **on** a single line (as opposed to line terminations, which are at the line ends). Use when describing "a line with a circle in the middle" or "a line with arrowheads along it". Augmentations might be arrowheads, slashes (`/`), vertical ticks (`│`), squares, or circles drawn on the line.

**Default orientation:** Augmentations are **centred on the line** and **evenly spaced around the centre** unless the question template specifies otherwise (e.g. "clustered near one end", "one at centre only").

| Key | Description | Notes |
|-----|-------------|-------|
| `arrowhead` | Arrowhead on the line | Single triangular arrowhead; orientation (e.g. pointing along line) may be specified or default |
| `slash` | Slash (/) on the line | Short diagonal stroke crossing the line; angle may be specified or perpendicular to line |
| `tick` | Vertical tick (\|) on the line | Short stroke perpendicular to the line |
| `square` | Square on the line | Small square centred on the line; same as motif `square` at an on-line position |
| `circle` | Circle on the line | Small circle centred on the line; same as motif `circle` at an on-line position |

Other motifs from the **motif dictionary** (3.2) may be used as line augmentations if they make sense (e.g. "a `heart` on the line"). Reference by the same key as in 3.2. Use a **consistent size** for augmentations (e.g. same as motif cell or line-termination size) so the same key looks the same across diagrams.

### 3.6 Shading types

Permitted **fill / shading** for regions (e.g. inside a polygon, or a radial section of a shape). Use when describing "the polygon is filled with grey" or "one half is `diagonal_slash`". Reference by key in verbal descriptions and when generating SVG.

| Key | Description | Notes / SVG usage | Lines (default) |
|-----|-------------|-------------------|-----------------|
| `solid_black` | Solid black fill | `fill="#000"` or `currentColor` | `-` `│` `/` `\` |
| `grey` | Solid mid grey | `fill` with mid grey (e.g. `#808080`); use consistently across questions | `-` `│` `/` `\` |
| `grey_light` | Solid light grey | `fill` with light grey (e.g. `#d0d0d0`); use consistently across questions | `-` `│` `/` `\` |
| `white` | No fill / white (unshaded) | `fill="none"` or `fill="#fff"`; region appears empty or white | `-` `│` `/` `\` |
| `diagonal_slash` | Diagonal lines (/) | Hatched fill with lines running top-left to bottom-right; consistent spacing | `\` (backslash only) |
| `diagonal_backslash` | Diagonal lines (\\) | Hatched fill with lines running top-right to bottom-left; consistent spacing | `/` (slash only) |
| `horizontal_lines` | Horizontal lines | Hatched fill with horizontal lines; consistent spacing | `│` (vertical only) |
| `vertical_lines` | Vertical lines | Hatched fill with vertical lines; consistent spacing | `-` (horizontal only) |

**Lines (default)** are the reflection symmetry lines of the shading pattern. Solid fills are symmetric about any line through the centre. Hatched fills: **horizontal lines** have **vertical** symmetry only (mirror left–right); **vertical lines** have **horizontal** symmetry only (mirror top–bottom); **diagonal slash** (/) has **backslash** (`\`) symmetry only; **diagonal backslash** (`\`) has **slash** (/) symmetry only. When forcing a motif layout to be symmetric about a line (e.g. vertical), use only shading types that have that line of symmetry so the fill does not conflict with the layout.

Use a **consistent line spacing and stroke width** for hatched shadings (`diagonal_slash`, `diagonal_backslash`, `horizontal_lines`, `vertical_lines`) so the same key looks the same in every diagram. Shading can apply to the whole shape, to a radial section, or to the **fill** of motifs (e.g. "motif `circle` with `grey` fill").

**Motifs and hatched areas:** Motifs **must not** appear on hatched (line) shaded areas. Use **solid** or **white** fill for any region that contains a motif layout. Hatched shading is for shapes or sections that do **not** contain motifs (e.g. partitioned sections, or shape-only diagrams).

### 3.7 Layout of motifs inside shapes

When placing **multiple motifs inside a shape container** (e.g. "a `square` with 10 `club`s inside"), choose a **layout** so that motifs do not overlap (see nvr-symbol-svg-design.md: centre-to-centre at least 12.5 in a 100×100 answer). Unless the question template states otherwise, use **randomly spaced** layout. The shape **fill** (or the section fill, if partitioned) in regions where motifs are placed must be **solid** or **white**—not hatched (see §3.6: motifs cannot appear on hatched areas).

**In templates:** A template may refer to "a shape containing a **layout**" (or "a **motif layout**") to mean a shape container with one or more motifs inside, arranged according to this subsection (e.g. randomly spaced or randomly clustered).

| Layout | Description | When to use |
|--------|-------------|-------------|
| **Randomly spaced** (default) | Motifs are placed at positions that **avoid overlap** but with **deliberately irregular spacing**: avoid a regular grid; vary horizontal and vertical gaps so the arrangement looks scattered, not aligned. | **Default** when the template does not specify a layout. |
| **Randomly clustered** | Motifs are concentrated in **one region** of the shape: **top**, **bottom**, **left**, or **right**. Specify which (e.g. "motifs clustered in the top half"). Positions within that region are irregular; motifs still must not overlap. | When the template asks for clustering (e.g. "clustered in the bottom", "grouped on the left"). |

### 3.8 Shape stacks

A **shape stack** is an arrangement where shapes are drawn in a notional **depth order**: a shape at the **bottom** of the stack is drawn first, and a shape **above** it in the stack is drawn over it. Use when describing "a square with a circle on top" or "four regular shapes in a stack".

**Rules:**

- A shape at the **bottom** of the stack has no other shape drawn underneath it; it may be partially covered by shapes above.
- A shape **above** another in the stack is drawn so that it **partially but not fully** conceals the shape(s) below—enough of the lower shape(s) remains visible so that stack order and identity are clear.
- A shape with no shapes drawn **above** it is at the **top** of the stack.
- Two shapes are **equal depth** if neither overlaps the other (e.g. side by side or separated); neither is "above" the other.

**Referring to stacks in templates:** A question template can refer to shapes by **depth** (e.g. "the shape at the bottom", "the top shape") or by **count and role** (e.g. "4 regular shapes in a stack", "2 regular equal-depth shapes and 1 shape on top"). When a template requests "N shapes in a stack", assign each shape a depth (e.g. bottom = 1, next = 2, … top = N) and draw them in that order so that each higher depth partially conceals the one(s) below. When a template requests "M equal-depth shapes and 1 shape on top", draw the M shapes so they do not overlap each other, then draw the single "on top" shape so it partially overlaps each shape within the equal-depth group and does not fully conceal any single shape below.

### 3.9 Partitioned shapes

A shape may be **partitioned** to divide it into **sections**, each of which may have its own **shading** (see §3.6). Partitioning is supported in five modes: **horizontal**, **vertical**, **diagonal** (slash or backslash), **concentric**, and **radial**. Use partitioned shapes when the template describes "a shape divided into halves", "stripes", "bands", "rings", or "pie-style radial sections" (e.g. a grey annulus inside a circle, or a circle in quarters).

**Section bounds:** Each section is defined by **upper and lower bounds** along the partition dimension, given as a proportion of the shape extent from **0** (one extreme) to **100** (the other). For example, a **horizontal** partition with sections **(0, 50)** and **(50, 100)** cuts the shape into two halves (top and bottom). Bounds are **inclusive** at the lower end and **exclusive** at the upper end for contiguous sections unless the template specifies otherwise. Unless specified, partitions should be **evenly distributed** (e.g. two sections → (0, 50) and (50, 100); three sections → (0, 33⅓), (33⅓, 66⅔), (66⅔, 100)).

**Bands:** A **band** is a thin section within a partition—e.g. the second section of a partition with bounds **(0, 30)**, **(30, 40)**, **(40, 100)** is a band between 30% and 40%. Bands may be **adjacent** (e.g. **(50, 60)** and **(60, 70)**) to form multiple thin stripes or rings.

**Horizontal partition:** Cuts the shape with horizontal lines. Sections sit one above the other (e.g. top section 0–50%, bottom 50–100%). **Horizontal partitioning breaks horizontal symmetry** (a line through the centre left–right) but **does not break vertical symmetry** (top–bottom mirror).

**Vertical partition:** Cuts the shape with vertical lines. Sections sit side by side (e.g. left 0–50%, right 50–100%). **Vertical partitioning breaks vertical symmetry** but **does not break horizontal symmetry**.

**Diagonal partition:** Cuts the shape with diagonal lines (slash `/` or backslash `\`). Sections are defined along the diagonal axis in the same way as horizontal/vertical; bounds 0–100 run from one corner of the shape to the opposite corner. Diagonal partitioning breaks the corresponding diagonal symmetry but not the other diagonal.

**Concentric partition:** Divides the shape by drawing a **scaled copy of the shape inside itself**. The scale is given as a proportion: **0** = centre (or degenerate inner shape), **100** = outer edge of the shape. For example, a **(0, 50)**, **(50, 100)** concentric partition on a **circle** draws an inner circle at 50% of the radius and divides the circle into a central disc and an outer ring. A **(40, 50)** concentric **band** with grey shading inside a white circle draws a **thin grey annulus** (ring) between 40% and 50% of the radius. Bands can be adjacent (e.g. **(50, 60)** and **(60, 70)**) to form multiple concentric rings. Concentric partitioning preserves rotational symmetry of the shape but may break reflection symmetry if shading differs between rings. **Suitable for concentric partition:** **circle**; regular polygons (**triangle**, **square**, **pentagon**, **hexagon**, **heptagon**, **octagon**); common irregular shapes (**right_angled_triangle**, **rectangle**, **semicircle**, **cross**, **arrow**); and among symbols **star** only. Do **not** use concentric partition on **`plus`**, **`times`**, **`club`**, **`heart`**, **`diamond`**, or **`spade`**.

**Radial partition:** Divides the shape **radially from the centre** into **radial sections** (pie-style wedges). Section bounds 0–100 run from one radial boundary to the next; each section is one radial section.

- **Regular shapes (circle and regular polygons):** Radial partitioning divides the shape into radial wedges. For a **circle**, any number of radial sections is allowed (each wedge is identically shaped). For a **regular polygon**, use radial partitioning when the **number of radial sections divides the number of vertices** (or sides), so that each radial section is **identically shaped**—e.g. a **regular hexagon** with 6 radial sections gives 6 equal wedges; a **square** with 4 radial sections gives 4 quadrants. Other counts (e.g. 5 radial sections in a hexagon) are permitted only if the template explicitly allows non-identical radial sections. **Radial section numbering:** By default, radial sections are **numbered clockwise from north** (12 o'clock): radial section 0 is the wedge that has the top (north) direction in its span, and numbering proceeds clockwise. For a circle or polygon with a vertex at the top, the first radial section is typically the top-centre wedge.
- **Irregular shapes:** An **irregular** shape may be partitioned into **exactly 4 radial sections** by dividing **horizontally and vertically** through the centre (a central horizontal and vertical line), producing four **irregular** pieces (quadrants). This is the only standard radial partition for irregular shapes; other radial section counts are not defined unless the template specifies otherwise.
- **Semicircle:** A **semicircle** may have a radial partition. The radial sections are defined **from the centre of the original (full) circle** that the semicircle is cut from: radial lines from that centre divide the semicircle into wedges. **Radial section numbering** is **clockwise from the "start" of the semicircle**—e.g. for the default semicircle (flat at the bottom, arc on top), the start is one end of the flat edge, and radial sections are numbered clockwise along the arc. The number of radial sections is specified by the template (e.g. 2 or 3 wedges).
- **Star (symbol):** A **regular five-pointed star** has **rotational symmetry order 5**; the most natural radial partition is **5 radial sections** (wedges from the centre, numbered clockwise from north).

**Motif layouts and partitions:** Motif layouts (see §3.7) **may be absent** in a partitioned shape (the diagram shows only the divided shape and its shading). If present, motifs **may be confined to a single partition** (e.g. "three circles in the top half only"); otherwise the generator may place motifs across the shape subject to the partition boundaries. When motifs are confined to one partition, placement rules (margin, minimum centre-to-centre) apply **within that section** only.

**Partition outlines:** The lines that separate sections (or the inner boundary of a concentric band) are drawn as **thin lines by default**, using the same line type as the shape border unless the template specifies otherwise.

**null sections:** A section of a partition may be assigned a special fill of **null**. If this is the case, the shape is **not drawn** over those sections, including the outer border of any null partition. Where a non-null section meets a null section, that boundary is drawn with the **normal shape outline** (the same stroke as the shape border)—**not** the thin partition line and **not** left undrawn.  

---

## Concepts

This section defines **diagram sequences**, **arrays** of shapes, and **symmetry and rotational symmetry**, which are used when describing or comparing diagrams and when writing question templates.

### Diagram sequences

A **diagram sequence** is a recognisable pattern of at least two elements within a diagram that may be used to distinguish that diagram from others. This is **distinct** from **sequence questions** (to be fully defined later), which will relate to a pattern that changes state in a predictable way between **multiple diagrams** in a question that are presented to the user in a specific order. Within the context of describing a **particular diagram**, **sequence** should be interpreted as a **diagram sequence**.

**Examples of diagram sequences:** In a **stack** of shapes we may observe a shading pattern of grey, black, white starting from the bottom of the stack. Or, in a shape, we may observe a clockwise **augmentation** pattern of one, two, three arrowheads on sides of the shape.

**Visible domain size:** In a diagram, the **visible domain size** of a sequence is the size of the visible information space it occupies—e.g. a circle **partitioned** into 4 **sections** would have a domain size of 4. In general, for questions to be unambiguous, the sequence length should be less than or equal to the domain size; however, this will not always be the case.

**Repeating sequence:** A **repeating sequence** is one which repeats within its domain. For example, a (black, white) repeating sequence within a hexagon partitioned into 6 **radial sections** would appear as (black, white, black, white, black, white) clockwise from north.

**Terminating sequence:** A **terminating sequence** (or **non-repeating sequence**) is one which does not repeat. If the domain size is larger than the sequence length, some positions in the domain are not assigned values from the sequence and are instead assigned **null**. A parameter value for the **null** must be chosen and **assigned** to those positions. For example, in a hexagon partitioned into 6 **radial sections** with a terminating (black, white) sequence, we might choose light grey as the null; then the radial sections could appear as (light grey, light grey, black, white, light grey, light grey) or (light grey, light grey, light grey, black, white, light grey) clockwise from north. We describe this as "(black, white) with null light grey". For numeric sequences (e.g. number of arrowheads augmenting a side, or number of motifs in a shape), null should be represented as zero.

**Looping domain:** A **looping domain** is the natural default case, particularly when considering sequence patterns on radial sections, sides, or **vertices** of polygons. The "first" position in the domain is considered to continue the sequence after the last position. For example, a **stack** of shapes showing a **sequence** of circle, triangle, square and a **stack** of shapes showing a sequence of square, circle, triangle both **exhibit** the same sequence (circle, triangle, square) if we consider the domain to loop.

**Extended domain:** An **extended domain** is a possible case allowing an invisible element in the domain; it should be used with care as it may lead to ambiguous questions. For example, we could have a sequence white, light grey, grey, black with extended domain size 4. A stack of 3 circles showing white, light grey, grey, and a stack of 3 circles showing light grey, grey, black could both be considered to exhibit the sequence. **Extended domains should never be used on radial partition regular shapes** as this is highly counter-intuitive, and extended domains should only be used if the template specifically requests it.

**Direction of a sequence:** The **direction** of a sequence is the direction it follows within the domain. Some language interpretation of direction is needed:

| Domain type | Direction language (examples) |
|-------------|-------------------------------|
| **Stack** | Up, down; shapes **above** or **below** each other |
| Partitioned shape, **radial sections** | Clockwise or anticlockwise |
| Partitioned shape, **concentric** sections | **In** (toward the centre) or **out** (toward the boundary) |
| **Horizontal** and **diagonal** partitions | **Ascending** = top to bottom on the diagram |
| **Vertical** partition | **Ascending** or **right** = left to right |

Within a question, the direction of a sequence must be the same in order for two sequences to be equivalent. For example, a square with horizontal partitions (white, grey, black) top to bottom does **not** exhibit the same sequence as (black, white, grey) top to bottom.

**Symmetric sequence:** A **symmetric** sequence is one that reads the same start-to-end as end-to-start—e.g. (white, black, white), or (club, diamond, diamond, club). Any sequence of length 2 is automatically symmetric. Odd-one-out questions using sequences will frequently have all answers except one exhibiting a sequence and the correct answer exhibiting its **mirror image** (the sequence read in the opposite direction). For example, in a question where each answer is a shape with multiple concentric partitions, the sequence (grey, diagonal_slash) in one direction could be the common pattern, and the odd one out could exhibit (diagonal_slash, grey) in that same direction—the mirror image of the sequence.

### Arrays of shapes

An **array** of shapes is a layout of multiple **shape containers** within a single diagram. The shapes are arranged in a regular grid with **even spacing** between them and **horizontal alignment** (rows and columns align). The layout may be **two-dimensional** (e.g. rows × columns) or **one-dimensional** (e.g. a single row or column, such as 1×4 or 4×1).

**Scaling:** Shapes in an array must be **scaled uniformly** (same scale factor horizontally and vertically) so that the whole array, including spacing, fits inside the diagram’s **bounding box** (e.g. the viewBox of the answer image). Each shape container is drawn at the same scale as the others in the array.

**Notation and examples:** A template may specify an array by giving the grid dimensions (rows × columns) and the shape type (or a set of types, e.g. “regular shapes”). Examples:

- A **2×2 array of triangles**: four triangles in two rows and two columns.
- A **3×2 array of regular shapes**: six shapes (each chosen from the regular shape vocabulary—circle or 3–8 sided polygon) in three rows and two columns.
- A **1×4 array of pentagons**: four pentagons in a single row.

Arrays are distinct from **shape stacks** (see §3.8): in a stack, shapes overlap in depth order; in an array, shapes do not overlap and are laid out in a grid with consistent spacing.

### Symmetry and rotational symmetry

When building shapes and pictures, the generator should maintain a **rudimentary awareness** of whether the picture has **reflection symmetry** (about a line) and **rotational symmetry** (of a given order). This subsection defines how we record symmetry for shape containers only; we do not track finer detail.

**Lines of symmetry:** We record at most four **line-of-symmetry types** in default orientation: **horizontal** (`-`), **vertical** (`│`), **diagonal /** (`/`), and **diagonal \\** (`\`). A shape is **symmetric** if it has at least one line of symmetry (of any of these types). Rotational symmetry **order** is the number of distinct rotations (multiples of 360°/n) that leave the shape unchanged (e.g. order 4 for a square).

**Symmetry as differentiator:** When a template specifies **symmetry** as a differentiator (e.g. "the odd one out differs by symmetry"), it means **horizontal or vertical** line symmetry only, unless the template explicitly says **any symmetry** (all four line types) or **diagonal symmetry** (diagonal `/` and `\` only). The split of "has symmetry" vs "no symmetry" across options may be **4–1** (four symmetric, one asymmetric) or **1–4** (one symmetric, four asymmetric); treat these two outcomes with **equal frequency** unless the template explicitly modifies it. Among the **available lines of symmetry** for that template (e.g. vertical and horizontal when "symmetry" is unspecified, or all four when "any symmetry", or both diagonals when "diagonal symmetry"), select which line to use with **equal outcome frequency** for each available line unless the template explicitly modifies the frequency (e.g. with **common** / **uncommon** / **rare**).

**Symmetry as a variator (line option):** When **symmetry** is added as a variator (and may be chosen as the differentiator), the generator may offer a choice of **horizontal**, **vertical**, or **any** as the line of symmetry for that question. If **horizontal** is chosen, options where symmetry is forced use a horizontal line only; if **vertical**, a vertical line only. If **any** is chosen, the question uses a **mix** of lines across options: some answers have a horizontal line of symmetry, some have a vertical line, and one has none (the odd one out). Diagonal lines are **not** used when forcing layout symmetry for now.

**When forcing layout symmetry:** When the generator forces a motif layout to be symmetric about a line (e.g. vertical `│` or horizontal `-`), it must use only **shape containers** (see table below), **motifs** (see §3.2), **shading types** (see §3.6), and **line types** (see §3.3) that do not break symmetry. Use shapes/motifs/fills that have that line of symmetry in default orientation; use **solid** (or **bold**) for the shape border only—**dashed** and **dotted** break reflection symmetry and must be avoided.

**Default orientation:** All of the following refer to the shape in its **default orientation** (as defined in section 3.1). Rotating a shape changes which of the four line types apply; the generator must update symmetry when orientation is changed.

**Shape containers (default orientation):** See §3.1 for full shape tables. Summary:

| Shape | Symmetric? | Symmetry axes | Rot. order |
|-------|------------|---------------|------------|
| `circle` | Yes | `-` `│` `/` `\` | ∞ |
| `triangle` (regular) | Yes | `│` | 3 |
| `square` | Yes | `-` `│` `/` `\` | 4 |
| `pentagon` | Yes | `│` | 5 |
| `hexagon` | Yes | `│` `-` | 6 |
| `heptagon` | Yes | `│` | 7 |
| `octagon` | Yes | `│` `-` | 8 |
| `right_angled_triangle` | Yes (if isosceles) | `/` | 1 |
| `rectangle` | Yes | `│` `-` | 2 |
| `semicircle` | Yes | `│` | 1 |
| `cross` | Yes | `│` `-` | 4 |
| `arrow` | Yes | `-` | 1 |
| `plus` | Yes | `│` `-` | 4 |
| `times` | Yes | `/` `\` | 2 |
| `club` | Yes | `│` | 1 |
| `heart` | Yes | `│` | 1 |
| `diamond` | Yes | `│` `-` | 2 |
| `spade` | Yes | `│` | 1 |
| `star` | Yes | `│` | 5 |

**Motif layouts:** A **motif layout** (motifs placed inside a shape, see section 3.7) has **no symmetry** by default and **destroys** the symmetry of the shape when added—the combined picture (container + motifs) is not symmetric unless the layout is explicitly constructed to be symmetric. The generator **must** support a way to **force symmetry** when generating motif layouts (e.g. mirror positions about a chosen line, or rotational placement) so that a template can request "a symmetric layout" or "layout with vertical symmetry".

**Spacing when using symmetry:** When placing motifs so the layout is symmetric about a line, the generator may put a **single motif exactly on the line of symmetry** (no mirror; the motif sits on the line). For any **pair** of positions (one in the canonical half and its mirror), a position **off the line** must be at least **half the usual minimum centre-to-centre distance** from the line of symmetry; otherwise the mirror would lie within the usual minimum distance and motifs would overlap. So: on the line = allowed (one motif); off the line = distance from line ≥ (min distance)⁄2 so that the mirror is at least the full min distance away.

**Rotation:** If a shape is **rotated** from its default orientation, its **recorded lines of symmetry change** to match the new orientation (e.g. a square rotated 45° has `/` and `\` as the horizontal/vertical-looking lines in the image). The generator should update or recompute symmetry when applying rotation.

---

## 4. Writing verbal question templates

When writing a **verbal question template** (e.g. for AI or a generator), the generator should **choose vocabulary elements at random** (one or more motifs, line types, line terminations, line augmentations, and/or shading types from section 3) and **stick with those same choices** for part or all of that question. **Increase randomness:** use a random draw (or shuffle) when the template calls for a free choice—e.g. "each answer is a regular polygon (3–8 sides)" → draw randomly from the allowed set for each option, so that question-to-question and option-to-option outcomes are unpredictable. For example: "For this question, use motif `circle`, line type `dashed`, and line termination `arrow_single` for every option." That keeps the question self-consistent and avoids mixing unrelated styles within a single item. The template may specify which vocabulary elements are fixed for the whole question and which (if any) vary per option.

### Step 1: Verbal description

Start with a **verbal description** of the question that:

- States the question type (e.g. odd-one-out, sequence, matrix, code).
- Describes each figure or option using only terms from the **NVR visual vocabulary** (section 3): vocabulary elements (motifs, line types, line terminations, line augmentations, shading types) and standard shape names (`square`, `triangle`, etc.). All such terms are quoted in this guide, e.g. `circle`, `dashed`, `arrow_single`.
- Identifies the correct answer and the rule (e.g. "odd one out is B because it has two circles").

### Terminology (parameters, global parameters, variators, differentiator)

- **Parameter:** A variable that can be chosen for each answer to the question (e.g. shape, line style, fill, motif type, number of motifs). Parameters describe how each answer looks or is defined.
- **Global parameter:** A parameter whose value is **fixed for the entire question** (one value for all answers). This is the **default** for parameters that appear in the template **setup** (the part before the answer definitions). For example, "choose n between 3 and 6" makes n a global parameter; every answer uses that same n (except where the differentiator is motif count and one answer uses n+1).
- **Variator:** A **per-answer** parameter whose value is allowed to **differ between answers**, subject to the split requirements for odd-one-out (see below). For odd-one-out questions, variators are all parameters that can vary per option; their value counts across options must obey the allowed splits so that no single option is uniquely different on a variator that is not the differentiator.
- **Differentiator:** For **odd-one-out** questions, the **parameter that determines the unique (correct) answer**. One of the variators specified in the template is always the differentiator. The correct answer is the one that differs from the others on the differentiator only (e.g. if the differentiator is shape, the correct answer has a different shape; if it is motif count, it has a different number of motifs). The template need not specify which variator is the differentiator; if it does not, the generator chooses one of the specified variators.

### Parameter choice rules when generating answers

When generating NVR questions from templates that use parameters (e.g. random **motif**, **shape**, or numerical values), apply the following so that answers are unambiguous and no accidental correct answers emerge. **Unless a template explicitly states otherwise**, assume: 5 options; **global parameters** (setup) have one value for the whole question; **variators** (per-answer parameters) are chosen at random for each option, **with duplication allowed**—two or more options may share the same shape, line style, fill, or motif; random assignment to options (no fixed order); containers centred in the answer image; motifs inside the container with margin.

- **Number of options:** Unless explicitly stated in the question template, all multiple-choice questions should have **5 possible answers** (not 4).
- **Correct-answer position (uniform):** Unless the template specifies which option is correct (e.g. "option 2 is the odd one out"), the **correct answer should be uniformly distributed** over the option positions. For 5 options, the correct answer should be option 1, 2, 3, 4, or 5 with **equal probability** (e.g. each with probability 1⁄5). Do not fix the correct answer to a single position (e.g. always option 3).
- **Odd-one-out (general):** For **odd-one-out** questions, one of the variators specified in the template is the **differentiator** (the parameter that defines the correct answer). If the template does not specify which variator is the differentiator, the generator chooses one of the variators (e.g. **number of motifs**, **line type**, **fill**, **motif type**, or **shape**). The **correct answer** is the one that **differs from the others on the chosen differentiator only** (e.g. if the differentiator is shape, the correct answer has a different shape; if it is motif count, it has a different number of motifs). Unless the template states otherwise, the correct-answer position follows the defaults above (uniform over options).
- **No duplicate parameter sets:** No two possible answers may use an **identical set of parameters**. If answers are described by a combination of parameters (e.g. shape + motif count), each option must differ in at least one parameter so that the intended correct answer is unique.
- **Odd-one-out parameter spread (variators):** Where the same description is used to generate multiple answers for **odd-one-out** questions, ensure that for each **variator** (per-answer parameter that is **not** the differentiator) the **value counts** across options obey the allowed splits below—so no single option is uniquely different on that variator. Rule: either **at least 3 different values** are used, or **if only 2 values** are used then **each value occurs at least twice** (e.g. never 4–1 for 5 options, never 3–1 for 4 options).

- **Allowed splits (value counts) per number of options:** For **variators** (parameters that do not determine the correct answer), generators should **vary** the distribution of values. Use these allowed splits (for 2 values only, each count ≥ 2). **5 options:** 2–3, 3–1–1, 2–2–1, 2–1–1–1, 1–1–1–1–1 (never 4–1). **4 options:** 2–2, 2–1–1 (never 3–1). **6 options:** 3–3, 2–2–2, 4–2, 4–1–1, 3–2–1, 3–1–1–1, 2–2–1–1, 2–1–1–1–1, 1–1–1–1–1–1 (never 5–1). Choose a split at random so that questions are not always 2–3 for 5 options.

- **Global parameters vs variators (where they are defined):**
  - **Global parameters (setup only):** Only parameters that appear **in the template setup** (the top part, **before** the answer definitions) are global; one value for the whole question. Typically this is a single choice such as "choose n between 3 and 6". The generator picks **one** value and uses it for **all** answers. **Do not** treat shape, line style, or fill as global unless the template explicitly places them in the setup and states "same for all".
  - **Variators (answer definitions):** Any parameter that describes **how each answer looks**—shape (polygon type), line style, fill, motif count, and motif type unless the template says "same motif for all"—is a **variator** (per-answer). The generator **chooses at random** from the allowed set for each option, subject to the no-duplicate parameter-set and odd-one-out spread rules. **Randomness:** use a random draw or shuffle so that which option gets which value is unpredictable.

- **Duplication of variator values (default):** When the template calls for a **free choice** of a variator (e.g. "each answer is a regular polygon between 3 and 8 sides"), **duplication across options is explicitly allowed**. For example, two options may both be square, three may use `solid` line style, and two may use the same motif. This is the **default**; the template need not state "duplication allowed". The generator **chooses at random** from the allowed values for each option (so the distribution varies), subject only to: (1) no two options have an **identical full set** of parameters (so the intended correct answer is unique), and (2) for odd-one-out, no single option is uniquely different on a variator that is **not** the differentiator (odd-one-out spread above).

- **Random assignment (no fixed order):** Variators (shapes, line styles, fills, motifs) must be **assigned randomly** to options 1–5 (e.g. by random draw or shuffle). Do **not** use a fixed order (e.g. option 1 = triangle, option 2 = square, option 3 = pentagon). Use a random process so that which option gets which value is unpredictable. When there are fewer variator values than options, **spread** repeats so no single value dominates and no option is the "only one" with a given value where that would confuse the intended rule (e.g. for odd-one-out by motif count, avoid one option being the only square).

- **Motifs inside the containing shape:** Motif centres must lie **inside** the shape container, with a margin so that the full motif cell does not cross the shape edge. For non-rectangular shapes (e.g. triangle, pentagon), use a point-in-polygon check and require the minimum distance from the motif centre to the shape boundary to be at least the motif cell half-size so that motifs remain fully inside the shape.

- **No black fill when shape contains motifs:** Do **not** use solid black fill (`solid_black`) for any shape container that contains motifs. Motifs are drawn in black (or currentColor); on a black background they would not be visible. When the shape has motif content, use `white`, `grey`, `grey_light`

**Example (avoiding accidental correct answers):** Suppose each of the 5 options is "a quantity of a randomly chosen `motif` inside a randomly chosen `shape`". The intended rule is "each shape contains 3 motifs, except the odd one out (e.g. option 2) which contains 4." The **differentiator** is motif count. If the generator chose shapes as: 1. circle, 2. circle, 3. circle, 4. square, 5. circle, then option 4 (square) would be the only square and could be misinterpreted as another valid "odd one out". To avoid that, assign **variators** (here, shape) so that no single option is unique on a variator that is not the differentiator—e.g. use at least three distinct shapes (e.g. triangle, circle, circle, square, circle) or ensure each shape value appears at least twice (e.g. circle, circle, square, square, circle).

### Frequency modifiers

Question templates may use the words **common**, **uncommon**, and **rare** to affect the **probability** of particular outcomes—for example when selecting a variator value from a set, or when selecting which variator is the **differentiator**. The generator should use **weighted random choice** according to the rules below.

**Weights (default context):** When a frequency modifier applies to a per-answer or per-choice context (e.g. which value to assign for a variator, or which variator to use as differentiator when the template does not specify), the default frequency for any outcome is **common**, meaning **weight 1**. All outcomes are then chosen with probability proportional to their weight.

- **common** (default): weight **1**. If no modifier is specified, treat the outcome as common.
- **uncommon**: weight **1⁄3**. The outcome is one-third as likely as a common outcome.
- **rare**: weight **1⁄10**. The outcome is one-tenth as likely as a common outcome.

**Example (default context):** If there are 5 outcomes and one is marked **uncommon** (weight 1⁄3) and the other four are common (weight 1 each), total weight = 4×1 + 1⁄3 = 13⁄3. The uncommon outcome is selected with probability (1⁄3)⁄(13⁄3) = **1⁄13**.

**Where modifiers apply:** Templates may attach frequency modifiers to (a) the choice of **differentiator** (when the template allows the generator to choose), (b) the choice of **variators** (which parameters vary), or (c) the choice of **values** for a variator (e.g. "shape: square common, circle uncommon, triangle rare"). In all of these contexts, unmodified outcomes use **weight 1** (common); only outcomes explicitly marked uncommon or rare use 1⁄3 or 1⁄10 respectively.

**“Add [item] as a variator and a [frequency] differentiator”:** A template may say e.g. “**uncommon** add **symmetry** as a variator and an **uncommon** differentiator”. Interpret this as two separate weighted choices. (1) **Whether to add the item to the variator set:** Weights are **add** = weight for the stated frequency (e.g. uncommon → 1⁄3) and **do not add** = weight 1. So P(add) = (1⁄3)⁄(1 + 1⁄3) = **1⁄4**. The variator set is then formed from the usual list (e.g. shape, line style, fill, motif, number of motifs), plus this item if “add” was chosen. (2) **Choice of differentiator** (from whichever variators were selected): The item, if present, has the stated frequency (e.g. uncommon → weight 1⁄3); other variators have weight 1 unless the template gives them a different frequency. So “uncommon add symmetry as a variator and an uncommon differentiator” means: 1⁄4 chance symmetry is in the variator set; when choosing the differentiator among the selected variators, symmetry (if present) has weight 1⁄3 and each other variator has weight 1. For the definition of symmetry and how to apply it when generating diagrams, see **Concepts → Symmetry and rotational symmetry**.

### Step 2: Generate pictorial assets (SVG)

From the verbal description:

- **AI or author** produces one SVG per question image and per option image.
- Use **only** the vocabulary elements from section 3 (shape containers, motifs, line types, line terminations, line augmentations, shading types). Use a consistent viewBox (e.g. `0 0 100 100`) and base stroke-width across options so diagrams are comparable.
- **Containers centred:** Unless the question template explicitly states otherwise (e.g. "offset to the left", "positioned at top"), **shape containers (and other outer frames) must be centred vertically and horizontally** in the answer image. The centre of the container should coincide with the centre of the viewBox (e.g. (50, 50) for viewBox 0 0 100 100).
- Save as `.svg` files (e.g. `option-a.svg` … `option-d.svg`) and host them; store the URLs in `question_image_url` / `option_image_url` as in section 4–5.

Verbal descriptions can be stored alongside the question (e.g. in a content pipeline or as comments) so that future edits or regeneration still reference the same vocabulary.

### Placeholder for example questions

Once this guide is approved, **10 example verbal NVR questions** will be added (or kept in a separate file) that reference the above dictionaries. Each will be in the form of a short verbal description suitable for feeding into diagram generation. All section 4 defaults (5 options, random per-answer choice **with duplication allowed**, containers centred, etc.) apply unless the template states otherwise; templates need not mention duplication.

----
**Example Question Template 1**

**Odd one out**

**Setup**
- Each answer is a **common shape** containing a **layout** (motif layout)
- 3 to 5 variators from **shape**, **line style**, **fill**, **motif** or **number of motifs** 
- **shape** and **fill** are **uncommon** differentiators
- **uncommon** add **symmetry** as a variator and an **uncommon** differentiator

**Example Question Template 2**

**Odd one out**

**Setup**
- Each answer is a **common shape** **partitioned** into **sections** using different **shading**
- 3 to 4 variators from **shape**, **partition direction**, **number of sections**, **shading sequence of sections** 
- **shape** is not a differentiator


----

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

- **SVG is required.** All such assets must be produced in SVG and must use only the **NVR visual vocabulary** (section 3: shape containers, motif dictionary, line types, line terminations, line augmentations, shading types). Browsers render SVG from a URL the same way (`<img src="option-a.svg">`). See the sample assets in `sample-nvr-odd-one-out/` for examples.
