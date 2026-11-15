@echo off
rem Move Mar Fil parts onto their joint (notes 101), with no Claude usage: the STL itself is rewritten so its origin
rem is the joint, and the fit for that joint becomes none. Parts land exactly where they did.
rem Double-click: lists what would move, opens the report, and nothing is written until you answer Y. Y moves them;
rem every STL, sidecar and page preview is copied first (D:\Kitbash Library\_backups\origins-DATE\before).
rem   Move origins.bat restore    puts back what the last run moved (parts you saved since are left moved)
rem Run it again after Seat connectors.bat or a Save fit: only parts whose joint is off the origin move.
rem Which parts: kits\connectors\marfil.json (arms by Shoulder, legs by Waist, shoulder pads by Pad, shin pads by Shin).
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
if not exist "%BLENDER%" for /f "delims=" %%B in ('where blender 2^>nul') do set "BLENDER=%%B"
set "MOVE=kits\connectors\origins.py"
if /i "%~1"=="restore" (
  "%BLENDER%" --background --factory-startup --python %MOVE% -- restore %2
) else (
  "%BLENDER%" --background --factory-startup --python %MOVE% -- run kits\connectors\marfil.json %*
)
echo.
pause
