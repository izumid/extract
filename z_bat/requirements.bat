@echo off
TITLE REQUIREMENTS

set "path_env=%~dp0..\.venv\Scripts"
echo Enviroment path: %path_env%

call "%path_env%\activate.bat"
pip freeze > "%~dp0..\requirements.txt"
call "%path_env%\deactivate.bat"
echo Generated file!!

timeout 5