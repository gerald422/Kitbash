@echo off
rem Shares Squad Builder with the people you've added (see README.txt, "Sharing").
rem Two windows: the page server, and cloudflared, which prints the https address to send them.
rem Close both windows (or Ctrl+C) to stop sharing.
set "LIB=D:\Kitbash Library"
set "PY="
for %%P in ("C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe" "%USERPROFILE%\miniconda3\python.exe") do if not defined PY if exist %%P set "PY=%%~P"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY (echo Couldn't find Python: edit the Blender line at the top of this file. & pause & exit /b 1)
start "Squad Builder share - close to stop" "%PY%" "%~dp0share_server.py" --lib "%LIB%"
where cloudflared >nul 2>nul || (echo cloudflared isn't installed. In a Command Prompt run:  winget install --id Cloudflare.cloudflared & echo then run this file again. & pause & exit /b 1)
echo.
echo Send people the https://....trycloudflare.com address printed below. It changes each time you start sharing.
echo.
cloudflared tunnel --url http://localhost:8765
pause
