@echo off
rem Add someone, change their password, or take them off (-NAME) (asked twice, at least 10 characters, stored hashed in share_users.json).
set "PY="
for %%P in ("C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe" "%USERPROFILE%\miniconda3\python.exe") do if not defined PY if exist %%P set "PY=%%~P"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY (echo Couldn't find Python: edit the Blender line at the top of this file. & pause & exit /b 1)
"%PY%" "%~dp0share_server.py" --list-users
echo.
set /p "WHO=Name to add or change (or -NAME to take someone off): "
if not defined WHO exit /b 0
if "%WHO:~0,1%"=="-" ("%PY%" "%~dp0share_server.py" --remove-user "%WHO:~1%") else ("%PY%" "%~dp0share_server.py" --add-user "%WHO%")
echo Restart sharing if it's running, so the change takes over.
pause
