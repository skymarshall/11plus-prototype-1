@echo off
REM Run script 2: upload and insert questions.
REM Edit the variables below with your values, then double-click this file or run from cmd.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM --- Edit these (required for upload + insert) ---
set MANIFEST=output\questions\manifest.json
set BASE_URL=http://127.0.0.1:54321/storage/v1/object/public/options
set DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres

REM For upload: use EITHER (A) S3 keys [local Supabase] OR (B) service_role JWT [hosted]
set SUPABASE_URL=http://127.0.0.1:54321
REM (A) Local Supabase: from "supabase status" -> Storage -> Access Key + Secret Key
set SUPABASE_STORAGE_ACCESS_KEY=your-storage-access-key
set SUPABASE_STORAGE_SECRET_KEY=your-storage-secret-key
REM (B) Hosted: set SUPABASE_SERVICE_ROLE_KEY=eyJ... (long JWT)
REM set SUPABASE_SERVICE_ROLE_KEY=your-service-role-jwt-here

REM --- Uploads to Storage (--upload supabase) then inserts into DB ---
python upload_and_insert_questions.py --manifest "%MANIFEST%" --base-url "%BASE_URL%" --database-url "%DATABASE_URL%" --upload supabase

REM To only validate: use --dry-run and remove --base-url/--database-url if you like
REM python upload_and_insert_questions.py --manifest "%MANIFEST%" --dry-run

pause
