@echo off
setlocal

echo Clearing NVR questions (subject_id=1) from database...

REM Container name for local Supabase DB
set DB_CONTAINER=supabase_db_supabase
set DB_USER=postgres
set DB_NAME=postgres

echo Checking if container %DB_CONTAINER% is running...
docker ps | findstr %DB_CONTAINER% >nul
if %errorlevel% neq 0 (
    echo Error: Supabase DB container '%DB_CONTAINER%' is not running.
    echo Please run 'npm run db:start' first.
    exit /b 1
)

REM We first delete answer_options for these questions (cascade should handle it if setup, but safe to be explicit or rely on cascading)
REM Assuming ON DELETE CASCADE on question_id foreign key in answer_options.

echo Clearing 'options' storage bucket...
python clear_options_bucket.py
if %errorlevel% neq 0 (
    echo Error clearing storage bucket.
    exit /b %errorlevel%
)

echo Deleting questions with subject_id = 1...
docker exec -i %DB_CONTAINER% psql -U %DB_USER% -d %DB_NAME% -c "DELETE FROM questions WHERE subject_id = 1;"

if %errorlevel% neq 0 (
    echo Error executing delete command.
    exit /b %errorlevel%
)

echo NVR questions cleared successfully.
endlocal
