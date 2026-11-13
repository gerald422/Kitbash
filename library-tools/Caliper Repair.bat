@echo off
rem Drop a folder on this file: every STL under it with mesh faults goes through Caliper's own batch repair (no
rem window, no clicking) and the repaired copies are exported beside the originals in Caliper-repaired-... folders.
rem Then it asks whether to run Caliper Swap: each repaired file replaces its original once it passes the checks in
rem caliper_swap.py (same place, no faults); originals are backed up. Nothing is replaced before you say yes.
rem   "Caliper Repair.bat" <folder> all     sends every STL to Caliper, not only the ones with faults
rem   "Caliper Repair.bat" <folder> --dry   only lists the files with faults
setlocal
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
set "PY=C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe"
if not exist "%PY%" set "PY=python"
if "%~1"=="" (echo Drop a folder onto this file. & pause & exit /b)
"%PY%" "%~dp0caliper_repair.py" "%~1" %2 %3 %4
if errorlevel 1 (echo. & pause & exit /b)
echo.
choice /c YN /m "Check the repaired files and put them in place of the originals now (originals are backed up)"
if errorlevel 2 (echo Left as they are: drop the folder on Caliper Swap.bat when you want them swapped in. & pause & exit /b)
if not exist "%BLENDER%" set "BLENDER=blender"
"%BLENDER%" --background --factory-startup --python "%~dp0caliper_swap.py" -- "%~1" --scan
echo.
pause
