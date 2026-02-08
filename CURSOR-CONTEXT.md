# Cursor context and exclusions

This doc describes what is **excluded from default AI context** in this repo (for memory efficiency). Keep it updated when you change `.cursorignore` so the AI is aware of "holes" in what it can see.

## Why this file exists

Paths listed in `.cursorignore` are not indexed or included in broad "whole project" context. The AI may therefore not see those files unless you **open them** or **@-mention them**. This file is for the AI to read: it summarizes exclusions so the AI can suggest opening or @-mentioning a file when the task touches excluded content.

## Excluded paths (summary)

- **Dependencies:** `node_modules/`
- **Python:** `__pycache__/`, `.venv/`, `venv/`, `env/`, `*.pyc`
- **Build/generated:** `dist/`, `dist-ssr/`, `question-gen/output/`, `sample-nvr-odd-one-out/output/`, `sample-nvr-odd-one-out/*.svg`, `*.local`
- **Binary lockfiles:** `*.lockb`
- **Test output:** `coverage/`
- **Secrets and logs:** `.env`, `.env.*`, `*.log`, `logs/`

Optional exclusions (if uncommented in `.cursorignore`): `package-lock.json`, `*.sql`.

## For the AI

- **Excluded content:** You will not see the above paths in default or "whole repo" context. If the user asks about something that might live there (e.g. SQL scripts, generated SVGs, `node_modules`), suggest they **open the file** or **@-mention it** (e.g. `@create_11plus_supabase.sql`) so it is included in context.
- **Editing excluded files:** You *can* edit a file that is in `.cursorignore` when the user has it open or explicitly references it (by name or @-mention). Exclusions only affect automatic indexing, not explicit inclusion.
