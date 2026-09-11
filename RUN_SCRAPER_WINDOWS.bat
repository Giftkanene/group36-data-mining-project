@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 set PY=py
if not defined PY (
    where python >nul 2>nul
    if %errorlevel%==0 set PY=python
)

if not defined PY (
    echo Python 3.10 or newer was not found.
    echo Install it from https://www.python.org/downloads/windows/ and tick "Add Python to PATH".
    pause
    exit /b 1
)

if not exist .venv\Scripts\python.exe (
    if exist .venv (
        echo Removing an incomplete or broken virtual environment...
        rmdir /s /q .venv
    )
    %PY% -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts\run_all.py

echo.
echo Finished. Check data\raw for the generated CSV files.
pause
