@echo off
TITLE VENV: Create and Install

set "path_env=%~dp0..\.venv\Scripts"
echo Enviroment path: %path_env%

echo Create .venv
python -m venv %~dp0..\.venv

call "%path_env%\activate.bat"
python -m pip list
python -m pip install -U pip
python -m pip install -r "%~dp0../requirements.txt"
python -m pip list
call "%path_env%\deactivate.bat"

timeout 5