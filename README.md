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
- **`question-gen/QUESTION-GENERATION-DESIGN.md`** – Question generation pipeline and NVR: workflow, vocab (shape containers, motifs, line types, shading), verbal templates, parameter/variator/differentiator rules, storage/DB/insert (§4, §9).
- **`nvr-symbol-svg-design.md`** – NVR symbol SVG design and layout rules.
- **`math-formulae-markup-plan.md`** – Plan for LaTeX/KaTeX in the DB and website.

### NVR symbols and question generation

- **`nvr-symbols/`** – SVG symbol set (circle, club, spade, heart, diamond, plus, square, triangle, star) used by the NVR renderer.
- **`question-gen/`** – Question XML design, XSD, and XML→SVG renderer; sample XML and batch script. See **question-gen/QUESTION-GENERATION-DESIGN.md** and **QUESTION-XML-SPECIFICATION.md**.

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

### For question-gen (XML→SVG)

- **Python 3** (e.g. 3.10+). No extra packages required beyond the standard library.

From the repo root:

```bash
cd question-gen
python lib/nvr_draw_diagram.py sample/sample-partitioned-extensive.xml -o output
```

---

## Summary of dependencies

| Dependency   | Used for |
|-------------|----------|
| **Node.js + npm** (or Bun) | 11-practise-hub build and dev server |
| **Supabase CLI** | Local Supabase (auth + DB) for the web app |
| **Docker** | Usually required by Supabase CLI for `supabase start` |
| **Python 3** | question-gen XML→SVG renderer |

---

## Licence and usage

See the individual folders and files for any stated licences. The app and scripts are for 11+ exam practise and content generation in line with the design docs in this repo.
