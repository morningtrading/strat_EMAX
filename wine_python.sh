#!/bin/bash
# Wine Python wrapper script for running MT5 Python scripts on Linux
# Usage: ./wine_python.sh <script.py> [args...]

# Set display for headless operation (optional)
# export DISPLAY=:0

# Run Python script with Wine
wine python "$@"
