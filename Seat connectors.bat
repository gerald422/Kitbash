@echo off
rem Seat Mar Fil parts by Josh's connectors (notes 100), with no Claude usage.
rem Double-click: every Mar Fil arm, legs, shoulder pad and shin pad is searched (about 30 min), the report opens,
rem and nothing is written until you answer Y. Y writes the new fits; each sidecar and the page index are backed up
rem first (D:\Kitbash Library\_backups\connectors-DATE\before). N writes nothing.
rem   Seat connectors.bat restore   puts back what the last run wrote (parts you saved since are left alone)
rem   Seat connectors.bat write     writes the last run you answered N to, without searching again
rem Connectors are read from ~\Desktop\mar fil connectors (kits\connectors\marfil.json says which object is which).
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
if not exist "%BLENDER%" for /f "delims=" %%B in ('where blender 2^>nul') do set "BLENDER=%%B"
set "SEAT=kits\connectors\seat.py"
if /i "%~1"=="restore" (
  "%BLENDER%" --background --factory-startup --python %SEAT% -- restore %2
) else if /i "%~1"=="write" (
  "%BLENDER%" --background --factory-startup --python %SEAT% -- write %2
) else (
  "%BLENDER%" --background --factory-startup --python %SEAT% -- run kits\connectors\marfil.json %*
)
echo.
pause
