# NVR Symbol SVG Fragments – Design

This document defines **canonical SVG fragments** for every symbol in the NVR visual vocabulary (question-gen/QUESTION-GENERATION-DESIGN.md §4, Shape containers). All diagram SVGs must use these fragments so symbols look identical across questions.

---

## 1. Coordinate system and size

### 1.1 Symbol cell size

- **Standard answer viewBox:** `0 0 100 100` (one option image).
- **Symbol size:** Each symbol occupies **1⁄8 of the answer in each direction**.
  - Symbol width = 100⁄8 = **12.5** units.  
  - Symbol height = 100⁄8 = **12.5** units.

So in a 100×100 answer, one symbol fits in a **12.5 × 12.5** region.

### 1.2 Symbol coordinate system

- Every symbol is defined in a **normalized** space: **viewBox="0 0 10 10"**.
- **Content area:** The symbol is drawn inside the region **1 ≤ x ≤ 9**, **1 ≤ y ≤ 9** (an 8×8 area centred at (5, 5)). This leaves a small margin and keeps strokes inside the cell when scaled.
- **Embedding rule:** When placing a symbol into an answer SVG (e.g. viewBox 0 0 100 100), scale the symbol so that the **10×10 box** maps to a **100⁄8 × 100⁄8** region:
  - Scale factor = (100⁄8)⁄10 = **1.25** (for a 100-unit answer).
  - Example: `<g transform="translate(50,50) scale(1.25) translate(-5,-5)"><!-- symbol content 0 0 10 10 --></g>` places the symbol centred at (50,50) at the correct size.

### 1.3 Stroke and fill

- **Stroke width** (outline symbols): **0.5** in symbol space (0 0 10 10). After scaling by 1.25 this gives a proportionally consistent line weight.
- **Stroke colour:** Use `currentColor` (or `#000`) so diagrams can be themed.
- **Fill** (filled symbols): `currentColor` or `#000`; outline-only symbols use `fill="none"`.
- **Stroke:** `stroke-linecap="round"`, `stroke-linejoin="round"` for a consistent look.

---

## 2. Symbol fragments (by key)

Each fragment is a **self-contained SVG** with `viewBox="0 0 10 10"`. You can inline the `<g>` (or the contents of the `<svg>`) into a larger diagram and wrap it in the transform above.

### 2.1 `circle`

Circle filled solid. Centre (5,5), radius 4.

```svg
<g id="symbol-circle" fill="currentColor" stroke="none">
  <circle cx="5" cy="5" r="4" />
</g>
```

### 2.2 `plus`

Plus sign: two perpendicular lines of equal length crossing at centre. Lines from (2,5)–(8,5) and (5,2)–(5,8). Stroke width 6 (thick).

```svg
<g id="symbol-plus" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
  <line x1="2" y1="5" x2="8" y2="5" />
  <line x1="5" y1="2" x2="5" y2="8" />
</g>
```

### 2.3 `heart`

Playing-card heart (♥). Symmetric filled path; scaled from 0–100 to 0–10 (÷10).

```svg
<g id="symbol-heart" fill="currentColor" stroke="none">
  <path d="M5 3.5 C5 1.5 1.5 1.5 1.5 4.5 C1.5 7.5 5 9.5 5 9.5 C5 9.5 8.5 7.5 8.5 4.5 C8.5 1.5 5 1.5 5 3.5 Z" />
</g>
```

### 2.4 `diamond`

Playing-card diamond (♦). Rhombus filled: top, right, bottom, left. Scaled from 0–100 to 0–10 (÷10).

```svg
<g id="symbol-diamond" fill="currentColor" stroke="none">
  <path d="M5 1 L8.5 5 L5 9 L1.5 5 Z" />
</g>
```

### 2.5 `club`

Three **filled** circles and a **curved stem**: point at the top (meeting the circles), curved sides, flat base at the bottom. Playing-card club (♣) centred in 1–9. (Scaled from canonical design: circles at 50,32 and 32,55 and 68,55 with r=17; stem curved path M50 45 C… 30 90 H70 C… Z in 0–100 space.)

```svg
<g id="symbol-club" fill="currentColor" stroke="none">
  <circle cx="5" cy="3.2" r="1.8" />
  <circle cx="3.2" cy="5.5" r="1.8" />
  <circle cx="6.8" cy="5.5" r="1.8" />
  <path d="M 5 4.5 C 5 4.5 4.5 7.5 3 9 H 7 C 5.5 7.5 5 4.5 5 4.5 Z" />
</g>
```

### 2.6 `spade`

Playing-card spade (♠). Symmetric filled path; scaled from 0–100 to 0–10 (÷10).

```svg
<g id="symbol-spade" fill="currentColor" stroke="none">
  <path d="M5 1 C3 3.5 1.2 5 1.2 7 C1.2 8.5 3 9 4.5 8 C4.5 8 4.8 8.5 4 9.5 H6 C5.2 8.5 5.5 8 5.5 8 C7 9 8.8 8.5 8.8 7 C8.8 5 7 3.5 5 1 Z" />
</g>
```

### 2.7 `square`

Square filled solid. Side 8, centred: x=1, y=1, width=8, height=8.

```svg
<g id="symbol-square" fill="currentColor" stroke="none">
  <rect x="1" y="1" width="8" height="8" />
</g>
```

### 2.8 `triangle`

Equilateral triangle filled. Apex at top, base at bottom; fits in 1–9.

```svg
<g id="symbol-triangle" fill="currentColor" stroke="none">
  <path d="M 5 1.2 L 8.8 8.8 L 1.2 8.8 Z" />
</g>
```

### 2.9 `star`

Five-pointed star, filled. Scaled from 0–100 to 0–10 (÷10).

```svg
<g id="symbol-star" fill="currentColor" stroke="none">
  <path d="M5 0.5 L6.3 3.8 L9.8 3.8 L7 5.9 L8.1 9.2 L5 7.2 L1.9 9.2 L3 5.9 L0.2 3.8 L3.7 3.8 Z" />
</g>
```

---

## 3. Using the fragments in an answer SVG

1. **Standard answer viewBox:** `0 0 100 100`.
2. **Scale:** One symbol cell = 100⁄8 = 12.5 units. So scale = **1.25** from symbol space (10 units) to answer space.
3. **Placement:** To centre a symbol at answer coordinates `(cx, cy)`:
   - `transform="translate(cx,cy) scale(1.25) translate(-5,-5)"`
   - Then include the symbol `<g>` (e.g. symbol contents with viewBox 0 0 10 10 implied by the transform).
4. **Multiple symbols:** Position each symbol at its own `(cx, cy)`; keep spacing and layout consistent (e.g. grid or symmetric positions inside the polygon).
5. **No overlap, no touching:** Symbols **must not overlap or touch each other or the inner border** of the enclosing square. Each symbol occupies a cell of size 12.5×12.5 in answer space (100×100).
   - **Minimum centre-to-centre distance:** **15** units (ensures a visible gap between symbol cells).
   - **Symbol centre bounds:** Centres must lie in **[22.25, 77.75]** so there is at least a **1 unit** gap between any symbol cell edge and the square’s inner edge (content 15–85).

---

## 4. File layout

- **Motif and shape-container SVGs:** The folder **`nvr-symbols/`** contains **`shape-{key}.svg`** for each motif and container (e.g. `shape-club.svg`, `shape-heart.svg`, `shape-square.svg`). Motif files use `viewBox="0 0 100 100"` (stroke-based outline). When **motifs** are placed inside a shape (e.g. by lib/nvr_draw_container_svg.py), the generator loads `shape-{motif}.svg`, scales to 1⁄8 of the answer (12.5 units in a 100×100 viewBox), and renders them **filled black** (guide §3.2). When a **symbol is used as a shape container**, the same outline is drawn at full container size.
- **Legacy 10×10 fragments:** The `<g>` fragments in §2 (viewBox 0 0 10 10) can still be pasted into answer SVGs and wrapped with `transform="translate(cx,cy) scale(1.25) translate(-5,-5)"` for 12.5-unit cells. The canonical on-disk assets are the `shape-*.svg` files.

Use the same scale and fill rules everywhere so motifs and shapes are **totally consistent** across all questions.
