@echo off
REM Event Sync Service - Windows Startup Script
REM This script will start the Event Sync Service

echo.
echo ==========================================
echo   EVENT SYNC SERVICE - STARTING
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo [✓] Python found
echo.

REM Check if venv exists
if not exist "venv" (
    echo [*] Creating virtual environment...
    python -m venv venv
    echo [✓] Virtual environment created
) else (
    echo [✓] Virtual environment found
)

echo.
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

echo [✓] Virtual environment activated
echo.

REM Check if dependencies are installed
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing dependencies...
    pip install -r requirements.txt
    echo [✓] Dependencies installed
) else (
    echo [✓] Dependencies already installed
)

echo.
echo ==========================================
echo   STARTING EVENT SYNC SERVICE
echo ==========================================
echo.
echo Web Interface: http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the service
python main.py
