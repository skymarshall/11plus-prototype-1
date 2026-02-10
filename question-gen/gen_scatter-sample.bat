@echo off
cd /d "%~dp0"
echo Generating layout sample SVGs...

python lib\nvr_draw_layout.py sample\sample-scatter.xml -o output --prefix layout --seed 42
if errorlevel 1 (
  echo Failed.
  pause
  exit /b 1
)
python lib\nvr_draw_layout.py sample\sample-scatter-motifs.xml -o output --prefix layout --seed 42
if errorlevel 1 (
  echo Failed.
  pause
  exit /b 1
)
echo Done. Output in output\
pause
