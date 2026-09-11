@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 set "PY_CMD=py"
if not defined PY_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%~fD\python.exe" set "PY_CMD=%%~fD\python.exe"
    )
)

if not defined PY_CMD (
    for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Python\PythonCore\3.13\InstallPath" /v ExecutablePath 2^>nul ^| findstr /i "ExecutablePath"') do (
        if exist "%%B" set "PY_CMD=%%B"
    )
)

if not defined PY_CMD (
    echo Python 3.10 or newer was not found.
    echo Install it from https://www.python.org/downloads/windows/ and tick "Add Python to PATH".
    pause
    exit /b 1
)

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -c "import sys; print(sys.executable)" >nul 2>nul
    if errorlevel 1 (
        echo Removing an incomplete or broken virtual environment...
        rmdir /s /q .venv
    )
)

if not exist .venv\Scripts\python.exe (
    if exist .venv (
        echo Removing an incomplete or broken virtual environment...
        rmdir /s /q .venv
    )
    "%PY_CMD%" -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts\run_all.py

echo.
echo Finished. Check data\raw for the generated CSV files.
pause
