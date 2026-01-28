#!/bin/bash

echo "=========================================="
echo "      EMAX DASHBOARD RESET SCRIPT"
echo "=========================================="

# 1. Stop existing engine
echo "[1/3] Stopping EMAX Engine..."
# Kill all related processes (try multiple patterns to match wine-wrapped Python)
pkill -f "python.*main.py" 2>/dev/null
pkill -f "wine.*python.*main.py" 2>/dev/null
pkill -f "python.exe.*main.py" 2>/dev/null
sleep 2

# Force kill if still running
if pgrep -f "python.*main.py" > /dev/null 2>&1; then
    pkill -9 -f "python.*main.py" 2>/dev/null
    pkill -9 -f "wine.*python.*main.py" 2>/dev/null
    pkill -9 -f "python.exe.*main.py" 2>/dev/null
    sleep 1
fi

# 2. Clean logs (Optional, but requested for "clean slate")
echo "[2/3] Cleaning log files..."
rm -f *.log 2>/dev/null
rm -f logs/*.log 2>/dev/null
echo "      Logs cleared."

# 3. Restart Engine
echo "[3/3] Restarting Engine..."
echo "=========================================="
echo "Starting EMAX... (Press Ctrl+C to stop)"
echo "=========================================="

# Wine Python requires DISPLAY to be set
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

# Run using wine python (foreground mode)
wine python main.py
