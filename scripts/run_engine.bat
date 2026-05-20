@echo off
REM DeepFind Engine — Quick start script for Windows
REM Run from the project root: scripts\run_engine.bat

echo.
echo ==========================================
echo   DeepFind Engine Setup ^& Run
echo ==========================================

cd /d "%~dp0..\engine"

REM Check if virtual environment exists
IF NOT EXIST ".venv" (
    echo [1/3] Creating Python virtual environment...
    python -m venv .venv
    echo     Done.
) ELSE (
    echo [1/3] Virtual environment already exists.
)

REM Activate
echo [2/3] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo [3/3] Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo ==========================================
echo   Starting DeepFind Engine on port 8765
echo ==========================================
echo.

python main.py

pause
