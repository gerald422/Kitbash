@echo off
rem Gets the Kitbash Library ready for Squad Builder.html (see README.txt).
set "LIB=D:\Kitbash Library"
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
if not exist "%BLENDER%" set "BLENDER=blender"
"%BLENDER%" --background --python "%~dp0prepare_builder.py" -- "%LIB%"
echo.
pause
