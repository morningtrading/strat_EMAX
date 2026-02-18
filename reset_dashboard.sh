#!/bin/bash

echo "=========================================="
echo "      EMAX DASHBOARD RESET SCRIPT"
echo "=========================================="

# PID file
PID_FILE="engine.pid"

# 1. Stop existing engine
echo "[1/3] Stopping EMAX Engine..."

if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Killing PID $pid..."
        kill "$pid" 2>/dev/null
        sleep 2
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -9 "$pid" 2>/dev/null
            sleep 1
        fi
        rm -f "$PID_FILE"
        echo "Engine stopped."
    else
        echo "PID file exists but process gone. Cleaning up."
        rm -f "$PID_FILE"
    fi
else
    echo "No running engine found (no PID file)."
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
# Redirect to null if running in background, but here we run in foreground usually
# However, reset script implies "restart and leave running"? 
# No, "wine python main.py" runs in foreground and blocks this script.
# So we can't save PID easily unless we background it.
# The original script ran in foreground.
# If we want to support PID file, we should probably run in background or wrapper.
# Let's keep foreground behavior but warn user that PID file won't be created this way?
# Or switch to background?
# Given "reset_dashboard.sh" usually implies "restart service", background is better.

echo "Starting in background..."
wine python main.py > trading_engine.log 2>&1 &
echo $! > "$PID_FILE"
echo "Engine started with PID $(cat $PID_FILE). Logs: trading_engine.log"
