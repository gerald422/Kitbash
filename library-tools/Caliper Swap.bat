@echo off
rem Drop a folder on this file after a Caliper batch run: each repaired STL replaces its original once it passes
rem the checks in caliper_swap.py (same place, no faults); originals are backed up. Then every STL in the folder
rem is checked and any still not clean are listed in still_dirty.csv beside the log.
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
if not exist "%BLENDER%" set "BLENDER=blender"
if "%~1"=="" (echo Drop a folder onto this file. & pause & exit /b)
"%BLENDER%" --background --factory-startup --python "%~dp0caliper_swap.py" -- "%~1" --scan
echo.
pause
