@echo off
setlocal enabledelayedexpansion

set "VENV_DIR=.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"
set "MAIN_SCRIPT=main.py"

if not exist "%VENV_DIR%\" (
    call Setup
)

echo Activating virtual environment...
call "%VENV_ACTIVATE%"

echo Installing PyInstaller...
pip install --upgrade pyinstaller

echo Building the executable...
pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --name "API Tester" "%MAIN_SCRIPT%"

echo Build completed!
exit /b 0