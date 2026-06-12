#!/bin/bash
# Event Sync Service - macOS/Linux Startup Script

echo ""
echo "=========================================="
echo "  EVENT SYNC SERVICE - STARTING"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

echo "[✓] Python found"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
    echo "[✓] Virtual environment created"
else
    echo "[✓] Virtual environment found"
fi

echo ""
echo "[*] Activating virtual environment..."
source venv/bin/activate

echo "[✓] Virtual environment activated"
echo ""

# Check if dependencies are installed
pip show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[*] Installing dependencies..."
    pip install -r requirements.txt
    echo "[✓] Dependencies installed"
else
    echo "[✓] Dependencies already installed"
fi

echo ""
echo "=========================================="
echo "  STARTING EVENT SYNC SERVICE"
echo "=========================================="
echo ""
echo "Web Interface: http://localhost:8000"
echo "API Docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the service
python main.py
