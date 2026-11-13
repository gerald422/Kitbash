@echo off
rem Add new parts from a maker who is already in the library, with no Claude usage.
rem Drop the folder with the new STLs (it must be inside D:\new cults) on this file, pick the maker's recipe by
rem number, look at the sheet and the test pictures that open, and answer Y. Heads / helmets and shoulder pads get
rem their fit; other types are filed without one and listed. Nothing is added before you answer Y, and the library's
rem lists are backed up first (D:\Kitbash Library\_backups\<task>\before). Parts the library already has are left out.
setlocal
cd /d "%~dp0"
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
if not exist "%BLENDER%" for /f "delims=" %%B in ('where blender 2^>nul') do set "BLENDER=%%B"
if "%~1"=="" (echo Drop the folder with the new parts onto this file. & pause & exit /b)
"%BLENDER%" --background --factory-startup --python kits\creator\add_creator.py -- add --src "%~1" %2 %3
echo.
pause
