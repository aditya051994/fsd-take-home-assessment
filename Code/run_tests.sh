#!/bin/bash
# Event Sync Service - Unix/Mac Test Runner
# This script runs all tests with proper environment setup

echo ""
echo "=========================================="
echo "  EVENT SYNC SERVICE - TEST RUNNER"
echo "=========================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

echo "[*] Activating virtual environment..."
source venv/bin/activate

echo "[*] Running comprehensive test suite..."
echo ""

# Run the test runner
python run_tests.py

echo ""
