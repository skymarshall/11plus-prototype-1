# Frontend changes for picture-based (NVR) questions

This document describes the changes needed in **11-practise-hub** so that questions with **option images** (e.g. NVR odd-one-out SVGs) and optional **question images** display correctly. The database and types already support `option_image_url` and `question_image_url`; the UI currently only shows text.

---

## 1. Already in place

- **`src/types/index.ts`**  
  - `Question.question_image_url?: string`  
  - `AnswerOption.option_image_url?: string`

- **`src/data/questions.ts`**  
  - Fetches `question_image_url` and `option_image_url` from the DB and maps them onto `QuestionWithOptions` / `AnswerOption`. No changes needed.

---

## 2. Test page (`src/pages/Test.tsx`)

**Goal:** During a test, show option images when present (e.g. NVR shapes); keep text-only behaviour for options that have no image.

### 2.1 Question image (optional)

- **Where:** Inside the question card, above or below `question_text`.
- **Change:** If `currentQuestion.question_image_url` is set, render an `<img>` above the question text (or below, depending on design).
  - Example: `<img src={currentQuestion.question_image_url} alt="" className="max-w-full max-h-48 object-contain" />`
  - Use a sensible max height so the question block doesn’t dominate the screen.

### 2.2 Option list (required for NVR)

- **Where:** The `RadioGroup` that renders `currentQuestion.options` (around lines 263–288).
- **Current behaviour:** Each option is a row with `RadioGroupItem` + `Label` showing `option.option_text` only.
- **Change:**
  - If `option.option_image_url` is present: show the image (e.g. `<img src={option.option_image_url} alt="" />`) as the main content of the option. Optionally show `option.option_text` as a caption or leave it empty when it’s only a placeholder (e.g. `""` for NVR).
  - If `option.option_image_url` is absent: keep current behaviour (text only).
- **Layout:** Keep the same click/selection behaviour (whole row selectable, `RadioGroupItem` + `Label`). Give the image a fixed max size so options don’t vary too much in height (e.g. `max-h-32` or `h-24 w-24` with `object-contain`).
- **Accessibility:** Use `alt=""` for decorative diagram options, or a short `alt` like "Option A" if you don’t have a better description.

**Example structure for one option (pseudo-JSX):**

```tsx
<div key={option.id} className="flex items-center space-x-3 rounded-lg border p-4 ...">
  <RadioGroupItem value={option.id.toString()} id={`option-${option.id}`} />
  <Label htmlFor={`option-${option.id}`} className="flex-1 cursor-pointer flex items-center gap-3">
    {option.option_image_url ? (
      <img
        src={option.option_image_url}
        alt=""
        className="max-h-28 w-auto object-contain"
      />
    ) : null}
    {option.option_text ? (
      <MathText component="span">{option.option_text}</MathText>
    ) : null}
  </Label>
</div>
```

Adjust classes to match your layout (e.g. vertical stack for image + text if preferred).

---

## 3. Results page (`src/pages/Results.tsx`)

**Goal:** In the collapsible “Question N” blocks, show option images when present for “Your answer” and “Correct answer” instead of (or in addition to) text.

- **Where:** Inside `CollapsibleContent` for each question (around lines 177–208).
- **Current behaviour:** “Your answer” and “Correct answer” show only `selectedOption.option_text` and `correctOption.option_text`.
- **Change:**
  - For “Your answer”: if `selectedOption?.option_image_url` exists, render a small image (e.g. `<img src={...} alt="" className="max-h-16 ..." />`) alongside or above the text; if only text, keep current behaviour.
  - For “Correct answer”: same for `correctOption?.option_image_url`.
  - If both image and text exist, show both (image + text); if only image (e.g. NVR with empty `option_text`), show only the image so the user can see which shape they chose and which was correct.

---

## 4. Session detail page (`src/pages/SessionDetail.tsx`)

**Goal:** Same as Results: when viewing a past session, show option images for “Your answer” and “Correct answer” when available.

- **Where:** Same structure as Results: `CollapsibleContent` per question (around lines 202–237).
- **Change:** Mirror the Results page: for “Your answer” and “Correct answer”, if the option has `option_image_url`, render the image (with a small max height); otherwise or in addition show `option_text`.

---

## 5. Optional: shared option display component

To avoid duplicating the “show image and/or text for an option” logic, you can add a small presentational component, e.g.:

- **`src/components/OptionDisplay.tsx`** (or similar)  
  - Props: `option: { option_text: string; option_image_url?: string }`, optional `size?: 'small' | 'medium'`.  
  - Renders either the image, or the text (wrapped in `MathText` if needed), or both, with consistent sizing.  
  - Use it in Test (option list), Results, and SessionDetail.

---

## 6. CORS and storage

- Option and question images are loaded from Supabase Storage (e.g. `http://127.0.0.1:54321/storage/v1/object/public/options/...` or your hosted URL).
- Ensure the Storage bucket allows your frontend origin in CORS so `<img src={url}>` works. For local dev, Supabase local usually allows this; for production, configure the bucket CORS in the Supabase dashboard.

---

## 7. Summary table

| File                     | Change |
|--------------------------|--------|
| `src/types/index.ts`     | No change (already has URLs). |
| `src/data/questions.ts`  | No change (already fetches URLs). |
| `src/pages/Test.tsx`     | Show `question_image_url` if set; show `option_image_url` in option list (with optional text). |
| `src/pages/Results.tsx`  | Show option images for “Your answer” and “Correct answer” when present. |
| `src/pages/SessionDetail.tsx` | Same as Results for option images. |
| Optional                 | Add `OptionDisplay` (or similar) component and reuse in Test, Results, SessionDetail. |

---

## 8. Reference

- **question-gen/QUESTION-GENERATION-DESIGN.md** (§9): question/option image columns, INSERT patterns, upload, display (SVG via `<img src="...">`).
- **11plus-datamodel-design.md**: `questions.question_image_url`, `answer_options.option_image_url` (VARCHAR(500)).
