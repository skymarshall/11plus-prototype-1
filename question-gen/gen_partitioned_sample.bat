@echo off
cd /d "%~dp0"
echo Generating partitioned sample SVGs...
python lib\nvr_draw_diagram.py sample\sample-partitioned-extensive.xml -o output
if errorlevel 1 (
  echo Failed.
  pause
  exit /b 1
)
echo Done. Output in output\
pause
