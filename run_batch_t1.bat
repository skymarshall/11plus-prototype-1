@echo off
setlocal

REM Load env vars from .env if possible, or assume they are set. 
REM Actually, Python scripts read os.environ. We can use `question-gen/.env` if we run via something that loads it, 
REM or we can rely on the python scripts usage of `python-dotenv` if they have it (they don't seem to import it).
REM So we should export them here or rely on the user having them set? 
REM The user said "I created question-gen/.env". 
REM I should probably add a python one-liner to load it or just manually set key vars if I can.
REM Better: Modify `batch_upload_and_insert_questions.py` or `gen_template1.py` to load .env?
REM No, `batch_upload...` reads `os.environ`.
REM I'll use a helper to load .env into the session or just rely on the python script doing it. 
REM Wait, `question-gen/.env` exists. I'll add a line to the batch file to read it.

cd /d "%~dp0"

echo --- Step 1: Generating Questions (Template 1) ---
python question-gen/batch/batch_generate_questions.py ^
  --count 10 ^
  --template question-gen/question-scripts/gen_template1.py ^
  --output-dir question-gen/output/batch_t1 ^
  --id-prefix t1-q ^
  --id-width 3

if %errorlevel% neq 0 (
    echo Generation failed!
    exit /b %errorlevel%
)

echo.
echo --- Step 2: Uploading and Inserting ---

REM We need to ensure environment variables are loaded.
REM A simple way is to use `set -a && source .env` in bash, but in cmd it's harder.
REM I will assume the user has python-dotenv installed or I can write a small loader.
REM Or I can pass them as arguments? `batch_upload...` takes many args.
REM But it also looks for SUPABASE_... env vars.
REM I'll use a python one-liner to run the script with loaded envs.

python -c "import dotenv, os, sys; dotenv.load_dotenv('question-gen/.env'); import subprocess; sys.exit(subprocess.call([sys.executable, 'question-gen/batch/batch_upload_and_insert_questions.py'] + sys.argv[1:]))" ^
  --manifest question-gen/output/batch_t1/manifest.json ^
  --upload supabase ^
  --bucket options ^
  --base-url http://127.0.0.1:54321/storage/v1/object/public/options ^
  --database-url postgresql://postgres:postgres@127.0.0.1:54322/postgres ^
  --subject-id 1 ^
  --topic-id 2

REM detailed args: subject-id 1 (NVR? need to check DB), topic-id 1 (Shapes?)
REM The script `batch_upload...` has lookup logic if IDs are missing but requires code.
REM Let's just use the defaults or lookup.
REM Script says: "--subject-id ... Default: lookup by code 'NVR'."
REM So I can omit subject/topic IDs if the script defaults work.
REM Let's check `batch_upload...` default args again.
REM It says: `default=None, help="Subject id for questions. Default: lookup by code 'NVR'."`
REM So I will OMIT subject-id and topic-id to use the lookup logic.

if %errorlevel% neq 0 (
    echo Upload/Insert failed!
    exit /b %errorlevel%
)

echo.
echo Batch complete!
