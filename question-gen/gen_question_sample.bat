@echo off
cd /d "%~dp0"
echo Generating layout sample SVGs...

python lib\nvr_draw_layout.py sample\gen_template3_out.xml -o output --prefix 3q --seed 42
if errorlevel 1 (
  echo Failed.
  pause
  exit /b 1
)

echo Done. Output in output\
pause
