# Mathematical Formulae in 11+ Practise – Markup Plan

## Overview

This document plans the changes needed to support a markup language (e.g. **LaTeX**) for mathematical formulae in the database and on the website. Formulae are needed mainly for Mathematics questions (and occasionally elsewhere), in question text, answer options, and explanations.

This is fully implemented and LaTeX fragments appearing in database text is correctly rendered on the front end.
---

## 1. Where formulae appear

| Location | Table / column | Example |
|----------|----------------|---------|
| Question text | `questions.question_text` | “What is \( \frac{3}{4} + \frac{2}{5} \)? ” |
| Answer option text | `answer_options.option_text` | “\( \frac{23}{20} \)” or “1 3/20” |
| Explanation | `questions.explanation` | “Common denominator: \( \frac{3}{4} = \frac{15}{20} \)…” |

All of these are already **TEXT** in the DB, so we can store markup inside them without schema changes, using a clear delimiter convention.

---

## 2. Markup language choice

| Option | Pros | Cons |
|--------|------|------|
| **LaTeX (math subset)** | Standard in education/maths, widely supported, compact | Syntax can be tricky for authors; need to escape backslashes in DB/JSON |
| **MathML** | XML, accessible, no delimiter needed | Verbose, harder to author by hand |
| **AsciiMath** | Simpler than LaTeX for basic maths | Less universal; extra parser dependency |

**Recommendation:** Use **LaTeX math** (the subset used in `\( ... \)` or `$ ... $`). Render with **KaTeX** on the frontend (fast, good quality). Optionally support a second delimiter for block maths if needed later.

---

## 3. Delimiter convention

Store in DB as plain text with inline delimiters so the same string can contain both normal text and maths:

- **Inline maths:** `\( ... \)`  
  Example: `What is \( \frac{1}{2} + \frac{1}{3} \)?`
- **Display/block maths (optional later):** `\[ ... \]` or `$$ ... $$`  
  Example: `\[ x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a} \]`

Rules:

- Backslashes and `{`, `}` are part of the LaTeX; store as-is in TEXT.
- No schema change: existing `question_text`, `option_text`, `explanation` columns stay as TEXT.
- Optional: add a **content type** or **format** field later (e.g. `plain` vs `with_math`) for filtering or different rendering; not required for v1.

---

## 4. Database changes

### 4.1 Schema

- **No new columns required** for v1. Formulae are stored as LaTeX fragments inside existing `question_text`, `option_text`, and `explanation` TEXT columns.
- **Optional later:**  
  - `questions.content_format` (e.g. `'plain' | 'latex'`) to mark questions that contain LaTeX.  
  - Or a check constraint / trigger that validates delimiter balance (e.g. every `\(` has a matching `\)`).

### 4.2 Escaping and storage

- PostgreSQL TEXT has no issue with `\`, `{`, `}`.  
- If content is ever edited via a JSON API, ensure the API layer does not strip or double-escape backslashes.
- Authoring tools (admin UI, scripts, imports) must emit valid delimiter pairs so the frontend can parse reliably.

### 4.3 Migration of existing content

- **Option A:** Leave existing rows as plain text; only new/edited content uses LaTeX.  
- **Option B:** One-off migration script that finds simple patterns (e.g. “3/4”, “x²”) and wraps them in `\( ... \)` (risky; needs manual review).  
- **Recommendation:** Option A for v1; optionally add a “contains maths” flag when authors tick “use LaTeX” in the editor, and migrate only where necessary.

---

## 5. Website (frontend) changes

### 5.1 Rendering library

- **KaTeX** (recommended): fast, small bundle, good for React.  
  - Package: `katex` + `react-katex` or use KaTeX’s `renderToString` / auto-render in a small wrapper.
- **MathJax**: more features, heavier; consider only if KaTeX is insufficient.

### 5.2 Where to render

| Place | Component / page | Change |
|-------|-------------------|--------|
| Test: question text | `Test.tsx` (question card) | Render `question_text` through a “text with math” component. |
| Test: option text | `Test.tsx` (radio options) | Same component for `option_text`. |
| Results / session detail | `Results.tsx`, `SessionDetail.tsx` | Use same component for question text, selected/correct option, explanation. |
| Dashboard / lists | Only if we show question previews with maths | Same component there too. |

### 5.3 “Text with math” component

- **Input:** string (e.g. `question_text` or `option_text`).
- **Behaviour:**  
  - Split on `\(` and `\)` (and optionally `\[` / `\]` or `$$`).  
  - Segments outside delimiters → render as plain text (escape HTML to prevent XSS).  
  - Segments inside delimiters → pass to KaTeX (e.g. `katex.renderToString(latex, { throwOnError: false })`) and inject safe HTML.
- **Output:** React fragment or div with mixed text + math spans (e.g. `dangerouslySetInnerHTML` only for the KaTeX output, with sanitisation if needed).
- **Accessibility:** KaTeX can output MathML; prefer that for screen readers where possible (KaTeX option or post-process).

### 5.4 Security

- **XSS:** Treat all non-math segments as plain text (escape HTML). For math, only allow KaTeX to generate HTML from the LaTeX string; do not allow raw HTML inside the LaTeX.  
- **Denial of service:** KaTeX can be given malicious or huge input; use `throwOnError: false` and optionally a length limit or timeout for the math segment.  
- **CSP:** If you use a Content-Security-Policy, allow KaTeX’s inline styles (it uses them for layout) or use a nonce.

### 5.5 Styling

- Include KaTeX CSS (e.g. `import 'katex/dist/katex.min.css'`) in the app so formulae are sized and aligned correctly.  
- Optionally override font size or colour to match the rest of the question/option text.

---

## 6. Authoring and content pipeline

- **Manual authoring:** Admin or author UI with a text area; authors type `\( \frac{1}{2} \)` etc. Optional: preview pane that uses the same “text with math” component.  
- **Bulk import (e.g. SQL scripts):** Insert scripts (e.g. `insert_sample_arithmetic_questions_supabase.sql`) should use the same delimiter convention; escape single quotes in SQL as usual (e.g. `''` for `'`).  
- **Paste from Word/Google:** Often produces Unicode (½, ²) or HTML; consider a small “normalise to LaTeX” helper for future, but not required for v1.

---

## 7. Implementation phases

| Phase | Scope | DB | Frontend |
|-------|--------|----|----------|
| **1** | Proof of concept | No change | Add KaTeX; one “text with math” component; use it on Test page for `question_text` and `option_text` only. |
| **2** | Full test and results | No change | Use same component in Results, SessionDetail, and for `explanation`. |
| **3** | Authoring and content | Optional `content_format` or validation | Admin/preview if applicable; migrate or tag existing maths content. |
| **4** | Polish | Optional | Accessibility (MathML), CSP, performance (lazy load KaTeX), any block-math delimiter. |

---

## 8. File and dependency checklist

- **New:** e.g. `src/components/MathText.tsx` (or `TextWithMath.tsx`) – component that parses delimiters and renders text + KaTeX.
- **New:** `src/lib/math.ts` (or similar) – helper to split string by `\( ... \)` and optionally `\[ ... \]`; call KaTeX for each math segment.
- **Package:** `katex` (and optionally `react-katex` if preferred). Add `katex/dist/katex.min.css` to the app.
- **Update:** `Test.tsx`, `Results.tsx`, `SessionDetail.tsx` – use `MathText` (or equivalent) wherever `question_text`, `option_text`, or `explanation` is rendered.
- **Docs:** Update `11plus-datamodel-design.md` “Design considerations” to mention that question/option/explanation text may contain LaTeX in `\( ... \)` (and link to this plan).

---

## 9. Summary

| Area | Change |
|------|--------|
| **DB** | No schema change; store LaTeX inside existing TEXT with `\( ... \)` (and optionally `\[ ... \]`) delimiters. |
| **Frontend** | Add KaTeX; one reusable component that parses delimiters and renders text + math; use it for question text, option text, and explanations wherever they are shown. |
| **Security** | Escape plain text; allow only KaTeX to produce HTML from LaTeX; consider length limit and CSP. |
| **Content** | Same delimiter convention in SQL inserts and any future admin/import; optional migration or “contains maths” flag later. |

This keeps the database simple, avoids breaking existing content, and confines all formula behaviour to a single convention and one frontend component.
