@echo off
rem Free checks on this PC (no Claude usage). Double-click, or:  "Run checks.bat" record   to save the current
rem placements as the reference (do that only when the builder looks right).
setlocal
cd /d "%~dp0"
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
if not exist "%BLENDER%" for /f "delims=" %%B in ('where blender 2^>nul') do set "BLENDER=%%B"
set "LIB=D:\Kitbash Library"
echo == Kitbash checks %date% %time% > checks-report.txt
where python >nul 2>nul && (
  echo -- installed files >> checks-report.txt
  python tools\kb.py verify >> checks-report.txt 2>&1
  echo -- repo >> checks-report.txt
  python tools\validate.py --all >> checks-report.txt 2>&1
)
echo -- placements >> checks-report.txt
if exist "%BLENDER%" (
  "%BLENDER%" --background --python tests\golden\run.py -- "%LIB%" %1 > "%TEMP%\kitbash-golden.log" 2>&1
  type tests\golden\report.txt >> checks-report.txt
) else (
  echo Blender not found: set BLENDER at the top of this file >> checks-report.txt
)
type checks-report.txt
echo.
echo Report saved as checks-report.txt
pause
