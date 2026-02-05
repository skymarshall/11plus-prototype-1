# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/REPLACE_WITH_PROJECT_ID

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/REPLACE_WITH_PROJECT_ID) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## Local Supabase setup

This app uses Supabase for auth and data. To run against your **local** Supabase instance:

1. **Start Supabase locally** (if not already):
   ```sh
   supabase start
   ```
   Note the API URL and `anon` key from `supabase status`.

2. **Disable email confirmation** (so signup logs you in immediately):
   - In the folder where you run `supabase start`, edit `supabase/config.toml`.
   - Ensure you have an `[auth.email]` section and set:
     ```toml
     [auth.email]
     enable_confirmations = false
     ```
   - (Do **not** use `[auth.mailer]` or `autoconfirm` — those are invalid in the CLI config.)
   - Restart: `supabase stop` then `supabase start`.
   - Without this, new users must confirm their email before a session is created, so the app will show an error after signup instead of going to the dashboard.

3. **Create a `.env` file** in this directory (see `.env.example`):
   ```env
   VITE_SUPABASE_URL=http://127.0.0.1:54321
   VITE_SUPABASE_ANON_KEY=<your-anon-key-from-supabase-status>
   ```

4. **Apply the database schema** in the Supabase SQL Editor (in order):
   - Run `docs/create_11plus_database_supabase.sql` (or the main schema from your project root).
   - Run `docs/create_11plus_users_and_progress_supabase.sql`.
   - If your `practice_sessions` table was created **before** the `question_ids` column was added, run `docs/migration_add_question_ids_to_practice_sessions.sql`.

5. **Seed questions** (optional): run your insert script (e.g. `insert_sample_arithmetic_questions_supabase.sql`) so Mathematics has at least 10 questions.

6. **Install dependencies and run**:
   ```sh
   npm i
   npm run dev
   ```

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- Supabase (Auth + PostgreSQL)
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/REPLACE_WITH_PROJECT_ID) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
