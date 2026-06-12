@echo off
REM Event Sync Service - Windows Test Runner
REM This script runs all tests with proper environment setup

echo.
echo ==========================================
echo   EVENT SYNC SERVICE - TEST RUNNER
echo ==========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo ERROR: Virtual environment not found
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

echo [*] Running comprehensive test suite...
echo.

REM Run the test runner
python run_tests.py

echo.
pause
