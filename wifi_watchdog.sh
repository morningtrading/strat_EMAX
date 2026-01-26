#!/bin/bash

# Wi-Fi Watchdog Script
# Monitors internet connectivity and reconnects Wi-Fi if dropped

CONNECTION_NAME="TMNL-01FFCE"
CHECK_INTERVAL=30
LOG_FILE="/home/titus/wifi_watchdog.log"

echo "Starting Wi-Fi Watchdog for connection: $CONNECTION_NAME"
echo "Logging to: $LOG_FILE"

# Ping Google DNS to check connectivity
if ping -c 1 -W 5 8.8.8.8 >/dev/null 2>&1; then
    # Connection is good
    # echo "$(date): Online" 
    exit 0
else
    echo "$(date): 🔴 Offline! Internet unreachable." >> "$LOG_FILE"
    echo "$(date): 🔄 Attempting to reconnect to $CONNECTION_NAME..." >> "$LOG_FILE"
    
    # Try to bring the connection up
    nmcli connection up "$CONNECTION_NAME"
    
    # Wait a bit for connection to establish
    sleep 10
    
    if ping -c 1 -W 5 8.8.8.8 >/dev/null 2>&1; then
            echo "$(date): 🟢 Reconnected successfully!" >> "$LOG_FILE"
    else
            echo "$(date): ❌ Reconnection failed." >> "$LOG_FILE"
    fi
fi
