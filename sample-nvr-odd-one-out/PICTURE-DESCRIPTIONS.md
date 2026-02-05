# Sample NVR Odd-One-Out Question – Picture Descriptions

**Source:** **Example Question Template 1** from **picture-based-questions-guide.md** (odd one out; n symbols vs different number). **5 options** per parameter rules. **Polygon, line style, fill, and symbol vary between answers** and are **assigned randomly** to options (no fixed order). Symbols are constrained **inside** the containing polygon with margin.

---

## How to generate

Run from this directory:

```bash
python generate_template1_options.py --seed 42
```

- **Random assignment:** Shapes, line styles, fills, and symbols are **shuffled** and assigned to option-a … option-e. There is no fixed order (e.g. option 1 ≠ always triangle).
- **Variety:** Each option gets a **different** shape, **different** fill, and **different** symbol. Line styles (3 values) are spread across 5 options.
- **Correct answer:** Option C (`option-c.svg`) has **5** symbols; all others have **4** (n = 4).
- **Symbols inside shape:** Symbol centres are placed inside the polygon with a margin so the full symbol cell stays within the boundary (point-in-polygon + distance-to-edge check).

---

## Example run (seed 42)

| File           | Polygon  | Line style | Fill       | Symbol         | Count | Odd one out? |
|----------------|----------|------------|------------|----------------|-------|--------------|
| `option-a.svg` | hexagon  | solid      | light_grey | circle  | 4     | No           |
| `option-b.svg` | square   | dotted     | white      | heart          | 4     | No           |
| `option-c.svg` | pentagon | solid      | grey       | club           | 5     | **Yes**      |
| `option-d.svg` | heptagon | dashed     | none       | spade          | 4     | No           |
| `option-e.svg` | triangle | dashed     | dark_grey  | circle  | 4     | No           |

All use `viewBox="0 0 100 100"`, symbol placement with minimum centre-to-centre 15 and symbols inside polygon with margin (nvr-symbol-svg-design.md).

---

## Question text (for database)

**Prompt:**  
“Each shape below is a regular polygon containing some symbols. Four of the shapes follow the same rule; one does not. Which shape is the odd one out?”

**Correct answer:** Option C (the only figure with 5 symbols; the others have 4).

**Explanation (for database):**  
“In shapes A, B, D and E there are 4 symbols inside the polygon. In shape C there are 5 symbols inside the pentagon, so C is the odd one out.”
