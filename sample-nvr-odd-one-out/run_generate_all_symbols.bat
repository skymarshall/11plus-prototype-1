@echo off
REM Generate option-square-10-{symbol}.svg for each symbol type in this directory.
REM Requires Python 3. Run from this directory: run_generate_all_symbols.bat
REM Symbol list is in generate_all_symbols_in_square.py (guide §4.1).

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

python generate_all_symbols_in_square.py
if errorlevel 1 exit /b 1
echo Done. Check option-square-10-*.svg
