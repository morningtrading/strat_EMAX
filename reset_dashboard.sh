#!/bin/bash

echo "=========================================="
echo "      EMAX DASHBOARD RESET SCRIPT"
echo "=========================================="

# 1. Stop existing engine
echo "[1/3] Stopping EMAX Engine..."
pkill -f "python main.py"
sleep 2

# 2. Clean logs (Optional, but requested for "clean slate")
echo "[2/3] Cleaning log files..."
rm -f *.log
echo "      Logs cleared."

# 3. Restart Engine
echo "[3/3] Restarting Engine..."
echo "=========================================="
echo "Starting EMAX... (Press combinations to stop: Ctrl+C)"
echo "=========================================="

# Run using wine python as per environment
wine python main.py
