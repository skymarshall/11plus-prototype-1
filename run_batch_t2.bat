@echo off
setlocal

cd /d "%~dp0"

echo --- Step 1: Generating Questions (Template 2) ---
if not exist question-gen\output\batch_t2 mkdir question-gen\output\batch_t2

python question-gen/batch/batch_generate_questions.py ^
  --count 10 ^
  --template question-gen/question-scripts/gen_template2.py ^
  --output-dir question-gen/output/batch_t2 ^
  --id-prefix t2-q ^
  --id-width 3

if %errorlevel% neq 0 (
    echo Generation failed!
    exit /b %errorlevel%
)

echo.
echo --- Step 2: Uploading and Inserting ---

python -c "import dotenv, os, sys; dotenv.load_dotenv('question-gen/.env'); import subprocess; sys.exit(subprocess.call([sys.executable, 'question-gen/batch/batch_upload_and_insert_questions.py'] + sys.argv[1:]))" ^
  --manifest question-gen/output/batch_t2/manifest.json ^
  --upload supabase ^
  --bucket options ^
  --base-url http://127.0.0.1:54321/storage/v1/object/public/options ^
  --database-url postgresql://postgres:postgres@127.0.0.1:54322/postgres ^
  --subject-id 1 ^
  --topic-id 2

if %errorlevel% neq 0 (
    echo Upload/Insert failed!
    exit /b %errorlevel%
)

echo.
echo Batch complete!
