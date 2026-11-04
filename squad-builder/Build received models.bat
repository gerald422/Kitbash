@echo off
rem Puts the newest models someone sent for printing into the library's _builder\inbox: open Blender with TIOW Inbox
rem first and it builds them. Run it again for the next set. Each set stays in _builder\received\<name>\<time>.
set "LIB=D:\Kitbash Library"
set "PY="
for %%P in ("C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe" "%USERPROFILE%\miniconda3\python.exe") do if not defined PY if exist %%P set "PY=%%~P"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY (echo Couldn't find Python: edit the Blender line at the top of this file. & pause & exit /b 1)
"%PY%" "%~dp0share_server.py" --lib "%LIB%" --build
pause
