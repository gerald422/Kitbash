@echo off
rem Copies the Kitbash Library's sidecars into this repository's library folder, ready to commit.
set "LIB=D:\Kitbash Library"
cd /d "%~dp0.."
python "library-tools\sync_sidecars.py" export "%LIB%" library
if errorlevel 1 "C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe" "library-tools\sync_sidecars.py" export "%LIB%" library
echo.
pause
