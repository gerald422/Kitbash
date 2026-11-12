@echo off
rem Starts only the page server (not the tunnel). Use it to restart the server after share_server.py changes while
rem the cloudflared window stays open: the https address then stays the same.
set "LIB=D:\Kitbash Library"
set "PY="
for %%P in ("C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe" "%USERPROFILE%\miniconda3\python.exe") do if not defined PY if exist %%P set "PY=%%~P"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY (echo Could not find Python: edit the Blender line at the top of this file. & pause & exit /b 1)
start "Squad Builder share - close to stop" "%PY%" "%~dp0share_server.py" --lib "%LIB%"
