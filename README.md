# 11+ Practise

Repository for the 11+ practise web app, database schema, design docs, and NVR (Non-Verbal Reasoning) question-generation tools.

---

## Quick start (web app)

To run the website locally:

1. **Clone the repository** using the project's Git URL:
   ```bash
   git clone <YOUR_GIT_URL>
   ```

2. **Go into the web app directory** (the app lives in `11-practise-hub/`):
   ```bash
   cd <YOUR_REPO_NAME>/11-practise-hub
   ```

3. **Install dependencies**:
   ```bash
   npm i
   ```

4. **Start the development server** (auto-reload and preview):
   ```bash
   npm run dev
   ```

The app will need a Supabase backend (and a `.env` with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`) for auth and questions. See **11-practise-hub/README.md** and the **Dependencies** section below for local Supabase setup.

---

## What's in this repo

### Web app: `11-practise-hub/`

React + TypeScript + Vite front end for UK 11+ exam practise (Mathematics, English, Verbal and Non-Verbal Reasoning). Uses Supabase for auth and data. See **11-practise-hub/README.md** for run instructions and local Supabase setup.

- **Tech:** React, TypeScript, Vite, Tailwind CSS, Radix UI, KaTeX (math formulae), Supabase JS client.
- **Key files:** `src/` (pages, components, services, lib), `package.json`, `.env.example`.

### Database and SQL scripts (root)

- **`create_11plus_supabase.sql`** – Full schema: subjects, topics (hierarchy), questions, answer_options, practice_sessions, user_question_attempts, RLS, triggers, progress view. Run once in Supabase SQL Editor.
- **`insert_sample_arithmetic_questions_supabase.sql`** – Sample maths questions (with LaTeX) and answer options.
- **`insert_sample_vr_vocabulary_questions_supabase.sql`** – Sample VR vocabulary questions.
- **`delete_all_questions_supabase.sql`** – Clears questions and dependent data (and practice_sessions) so you can re-run insert scripts.

Run insert scripts **after** `create_11plus_supabase.sql`.

### Design and planning (root)

- **`11plus-datamodel-design.md`** – Data model: tables, relationships, image support, option ordering, session/attempt recording.
- **`picture-based-questions-guide.md`** – How picture-based (e.g. NVR) questions work: vocab (symbols, line types, shading), polygon containers, verbal templates, parameter/variator/differentiator rules.
- **`nvr-symbol-svg-design.md`** – NVR symbol SVG design and layout rules.
- **`math-formulae-markup-plan.md`** – Plan for LaTeX/KaTeX in the DB and website.

### NVR symbols and sample generator

- **`nvr-symbols/`** – SVG symbol set (circle, club, spade, heart, diamond, cross, square, triangle, star) used by the NVR option generator.
- **`sample-nvr-odd-one-out/`** – Python scripts to generate NVR odd-one-out answer-option SVGs from the picture-based-questions guide:
  - **`generate_shape_container_svg.py`** – Shape container (optionally with symbols inside). Supports all common shapes (regular + irregular); use `--empty` for container only. Uses `../nvr-symbols/`.
  - **`generate_template1_options.py`** – Five options for Example Template 1 (differentiator + 3–5 variators; see guide §5).
  - **`param_splits.py`** – Allowed parameter splits for odd-one-out (e.g. 2–3, 3–1–1 for 5 options).
  - **`generate_all_symbols_in_square.py`** – One square per symbol type (for asset check).
  - **`run_generate_all_symbols.bat`** – Windows batch to run the "all symbols" script.
  - **`PICTURE-DESCRIPTIONS.md`** – Text descriptions for sample NVR questions.

---

## Dependencies

### For the web app (`11-practise-hub/`)

- **Node.js** (LTS) and **npm** (or **Bun** – `bun.lockb` is present).
- **Supabase**: the app talks to Supabase (auth + Postgres). For local dev you use the **Supabase CLI** (`supabase start`). The CLI runs Postgres and other services (often via **Docker**). So you typically need:
  - [Supabase CLI](https://supabase.com/docs/guides/cli) installed.
  - **Docker** (if you use `supabase start` and don't have a custom setup), so the CLI can start local Postgres, Studio, etc.

Install app deps and run:

```bash
cd 11-practise-hub
npm install
npm run dev
```

Copy `.env.example` to `.env` and set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (from `supabase status` after `supabase start`). Apply the schema and optional seed scripts as in **11-practise-hub/README.md**.

### For the database

- A **Supabase** project (cloud or local via Supabase CLI).
- Run `create_11plus_supabase.sql` in the Supabase SQL Editor, then the insert/delete scripts as needed.

### For NVR Python scripts (`sample-nvr-odd-one-out/`)

- **Python 3** (e.g. 3.10+). No extra packages required beyond the standard library.

From the repo root:

```bash
cd sample-nvr-odd-one-out
python generate_template1_options.py
python generate_template1_options.py --seed 42
python generate_shape_container_svg.py club -n 10 -o option-club.svg
```

---

## Summary of dependencies

| Dependency   | Used for |
|-------------|----------|
| **Node.js + npm** (or Bun) | 11-practise-hub build and dev server |
| **Supabase CLI** | Local Supabase (auth + DB) for the web app |
| **Docker** | Usually required by Supabase CLI for `supabase start` |
| **Python 3** | NVR SVG generation scripts in `sample-nvr-odd-one-out/` |

---

## Licence and usage

See the individual folders and files for any stated licences. The app and scripts are for 11+ exam practise and content generation in line with the design docs in this repo.
