@echo off
setlocal enabledelayedexpansion

set "VENV_DIR=.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_DIR%\" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

echo Activating virtual environment...
call "%VENV_ACTIVATE%"

echo Installing Requirements...
pip install -r requirements.txt

echo Setup complete!

exit /b 0
