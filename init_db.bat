@echo off
setlocal

echo Initializing database...

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

echo Running create_11plus_supabase.sql...
type sql\create_11plus_supabase.sql | docker exec -i %DB_CONTAINER% psql -U %DB_USER% -d %DB_NAME%
if %errorlevel% neq 0 exit /b %errorlevel%

echo Running insert_nvr_subject_topic_supabase.sql...
type sql\insert_nvr_subject_topic_supabase.sql | docker exec -i %DB_CONTAINER% psql -U %DB_USER% -d %DB_NAME%
if %errorlevel% neq 0 exit /b %errorlevel%

echo Running insert_sample_arithmetic_questions_supabase.sql...
type sql\insert_sample_arithmetic_questions_supabase.sql | docker exec -i %DB_CONTAINER% psql -U %DB_USER% -d %DB_NAME%
if %errorlevel% neq 0 exit /b %errorlevel%

echo Running insert_sample_vr_vocabulary_questions_supabase.sql...
type sql\insert_sample_vr_vocabulary_questions_supabase.sql | docker exec -i %DB_CONTAINER% psql -U %DB_USER% -d %DB_NAME%
if %errorlevel% neq 0 exit /b %errorlevel%

echo Database initialized successfully.
endlocal
