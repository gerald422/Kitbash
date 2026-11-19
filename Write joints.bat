@echo off
rem Write a proving run's joints into the library (docs/PLAN.md, the write step; notes 116), with no Claude usage.
rem   Write joints.bat RESULTS.json [MORE.json]   drag a proving run's results.json onto this (a later file wins for a
rem                                              part both list). The report opens; nothing is written until you answer
rem                                              Y. Each sidecar and the page index are backed up first
rem                                              (D:\Kitbash Library\_backups\connectors-joints-DATE\before).
rem   Write joints.bat restore                   puts back what the last write changed (parts you saved since stay)
rem Parts in kits\connectors\marfil_write_skip.txt are not written (what the proving sheets showed wrong).
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
set "BPY=C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe"
if not exist "%BPY%" set "BPY=C:\Program Files\Blender Foundation\Blender 4.5\4.5\python\bin\python.exe"
if /i "%~1"=="restore" (
  "%BLENDER%" --background --factory-startup --python kits\connectors\seat.py -- restore %2
) else if "%~1"=="" (
  echo Drag a proving run's results.json onto this file.
) else (
  "%BPY%" kits\connectors\write_joints.py %*
)
echo.
pause
