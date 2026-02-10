# Shape geometry: implementation notes

This document describes how shape geometry (path, vertices, bounding box) is obtained in the question-gen layout and container code, and how that affects **changes to the shape SVG files** in `nvr-symbols/`. It answers: will changing those SVGs break bounding box, loop path placement, scatter-inside-shape, etc.?

---

## Where geometry comes from

**Container** (`nvr_draw_container_svg.py`) exposes:

- `get_shape_geometry(shape, motifs_dir)` → `(vertices, path_d, path_d_stroke, stroke_lines, symbol_transform, symbol_path_element)`
- `get_shape_bbox(shape, vertices, path_d)` → `(x_min, x_max, y_min, y_max)`

**Layout** (`nvr_draw_layout.py`) uses these for loop path placement, scatter-inside-shape (inside_check, bounds, scale from distance-to-boundary), and drawing. It does not read any SVG files itself.

---

## Symbol shapes only (plus, times, club, heart, diamond, spade, star)

Geometry is **loaded from the SVG files**.

- **Source:** `get_shape_geometry()` calls `_symbol_geometry(shape, motifs_dir)`:
  - `_load_symbol_svg(motifs_dir, shape)` loads `shape-{symbol}.svg`, parses the first `<path d="...">` and optional parent `transform`.
  - Vertices are **sampled from that path** via `_sample_path_to_points(path_d)` (not stored in the file).
- **Used for:** path_d, symbol_transform, bounding box (from sampled vertices), loop path when `path_shape` is a symbol, scatter-inside-shape (inside_check and `min_distance_to_edges` for the polygon), and drawing.

**If you change the symbol SVG files:**

- **Content changes** (path `d`, viewBox, transform): The code **will cope**. Path, transform, and sampled vertices/bbox all update; bounding box, loop path placement, and scatter-inside-shape remain consistent with the new file.
- **Structural changes** (e.g. no path, multiple paths, different element structure): Can **break** `_load_symbol_svg` / `_symbol_geometry`, which assume a single path and an optional parent transform.

So for **symbol** shape SVGs, the implementation is intended to follow file changes; only loader assumptions (single path, etc.) can break.

---

## All other shapes (circle, square, triangle, pentagon, hexagon, heptagon, octagon, semicircle, cross, arrow, right_angled_triangle, rectangle)

Geometry is **fully computed in code**; the corresponding `shape-*.svg` files are **not** read for geometry.

- **Source:** Constants (e.g. `CIRCLE_RADIUS`, `POLYGON_RADIUS`, `POLYGON_CY`) and functions such as `regular_polygon_vertices()`, `regular_polygon_path()`, `_square`, `_circle`, `_semicircle_geometry()`, `_cross_geometry()`, etc. `get_shape_geometry()` and `get_shape_bbox()` use only these.
- **Used for:** path_d, vertices, bbox, loop path, scatter-inside-shape, and drawing for these shapes.

**If you change the non-symbol shape SVG files (e.g. `shape-triangle.svg`, `shape-square.svg`):**

- **Nothing in the layout or container geometry changes.** Bounding box, loop path placement, and scatter-inside-shape logic do not read those files, so changing them **won’t break** that code.
- The only downside is **design drift**: the SVGs on disk may no longer match what the renderer draws (which is driven entirely by the in-code geometry).

---

## Summary table

| Shape set | Geometry source | Effect of changing their SVGs |
|-----------|-----------------|-------------------------------|
| **Symbols** (plus, times, club, heart, diamond, spade, star) | `shape-{symbol}.svg` (path + optional transform; vertices from path sampling) | **Copes** with path/viewBox/transform changes; bbox, loop path, scatter-inside-shape follow the new file. Can break if structure violates loader (e.g. no single path). |
| **All others** (circle, triangle, square, pentagon, hexagon, etc.) | In-code only (constants + polygon/geometry helpers) | **No effect** on bbox or loop path placement; code won’t break, but SVGs may drift from what’s drawn. |

---

## References

- `question-gen/lib/nvr_draw_container_svg.py`: `get_shape_geometry`, `get_shape_bbox`, `_load_symbol_svg`, `_symbol_geometry`, `regular_polygon_vertices`, `get_shape_bbox`.
- `question-gen/lib/nvr_draw_layout.py`: uses container for loop path, scatter-inside-shape (inside_check, bounds, scale from distance-to-edge), and fragment drawing.
- `nvr-symbols/`: `shape-{key}.svg` for symbol and (optionally) other shapes; only symbol shapes are loaded for geometry.
