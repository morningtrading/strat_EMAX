#!/bin/bash

# Configuration
LOG_FILE="/tmp/wifi_watchdog.log"
STATUS_FILE="/tmp/wifi_status"
TARGET="8.8.8.8"

# Check connection
if ping -c 1 -W 2 "$TARGET" > /dev/null 2>&1; then
    # WiFi is UP
    echo "$(date): Online" > "$STATUS_FILE"
else
    # WiFi is DOWN
    echo "$(date): WiFi DOWN! Restarting..." >> "$LOG_FILE"
    
    # Turn WiFi OFF
    nmcli radio wifi off
    sleep 5
    
    # Turn WiFi ON
    nmcli radio wifi on
    
    # Wait for association
    sleep 15
    
    echo "$(date): WiFi Restart Triggered." >> "$LOG_FILE"
fi
