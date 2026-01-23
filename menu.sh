#!/bin/bash

# EMAX Trading Engine Control Menu
# This script provides an interactive menu for controlling the trading engine

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# PID files
ENGINE_PID_FILE="$SCRIPT_DIR/.engine.pid"
DASHBOARD_PID_FILE="$SCRIPT_DIR/.dashboard.pid"
LOG_FILE="$SCRIPT_DIR/logs/engine.log"

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Function to show header
show_header() {
    clear
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}       ${GREEN}EMAX Trading Engine Control Panel${NC}              ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to check if engine is running
is_engine_running() {
    # Check for Wine-wrapped Python process OR direct python process
    if pgrep -f "python.*main.py" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to check if dashboard is running
is_dashboard_running() {
    if pgrep -f "python.*web_dashboard.py" > /dev/null 2>&1 || \
       lsof -i :8080 > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to show status
show_status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━ STATUS ━━━━━━━━━━━━━━━━━━${NC}"
    
    if is_engine_running; then
        echo -e "  Engine:    ${GREEN}● RUNNING${NC}"
    else
        echo -e "  Engine:    ${RED}○ STOPPED${NC}"
    fi
    
    if is_dashboard_running; then
        echo -e "  Dashboard: ${GREEN}● RUNNING${NC} (http://localhost:8080)"
    else
        echo -e "  Dashboard: ${RED}○ STOPPED${NC}"
    fi
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to start engine
start_engine() {
    echo -e "${YELLOW}Starting EMAX Trading Engine...${NC}"
    
    if is_engine_running; then
        echo -e "${YELLOW}Engine is already running!${NC}"
        return 1
    fi
    
    # Start engine in background
    nohup wine python main.py >> "$LOG_FILE" 2>&1 &
    ENGINE_PID=$!
    echo $ENGINE_PID > "$ENGINE_PID_FILE"
    
    sleep 3
    
    if is_engine_running; then
        echo -e "${GREEN}✓ Engine started successfully (PID: $ENGINE_PID)${NC}"
        echo -e "${CYAN}  Dashboard should be available at: http://localhost:8080${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to start engine. Check logs: $LOG_FILE${NC}"
        return 1
    fi
}

# Function to stop engine
stop_engine() {
    echo -e "${YELLOW}Stopping EMAX Trading Engine...${NC}"
    
    if ! is_engine_running; then
        echo -e "${YELLOW}Engine is not running.${NC}"
        return 0
    fi
    
    # Kill all related processes (try multiple patterns)
    pkill -f "python.*main.py" 2>/dev/null
    pkill -f "wine.*python.*main.py" 2>/dev/null
    pkill -f "python.exe.*main.py" 2>/dev/null
    
    sleep 2
    
    # Force kill if still running
    if is_engine_running; then
        pkill -9 -f "python.*main.py" 2>/dev/null
        pkill -9 -f "wine.*python.*main.py" 2>/dev/null
        pkill -9 -f "python.exe.*main.py" 2>/dev/null
        sleep 1
    fi
    
    if ! is_engine_running; then
        echo -e "${GREEN}✓ Engine stopped successfully${NC}"
        rm -f "$ENGINE_PID_FILE"
        return 0
    else
        echo -e "${RED}✗ Failed to stop engine${NC}"
        return 1
    fi
}

# Function to start dashboard only (if engine has separate dashboard)
start_dashboard() {
    echo -e "${YELLOW}Starting Dashboard...${NC}"
    
    # Note: In EMAX, the dashboard is integrated with main.py
    # This function is for cases where dashboard might be separate
    
    if is_engine_running; then
        echo -e "${CYAN}Dashboard is integrated with the engine.${NC}"
        echo -e "${GREEN}✓ Dashboard available at: http://localhost:8080${NC}"
        return 0
    else
        echo -e "${YELLOW}Engine is not running. Starting engine (which includes dashboard)...${NC}"
        start_engine
        return $?
    fi
}

# Function to stop dashboard
stop_dashboard() {
    echo -e "${YELLOW}Stopping Dashboard...${NC}"
    
    # Note: In EMAX, stopping dashboard means stopping the engine
    echo -e "${CYAN}Dashboard is integrated with the engine.${NC}"
    echo -e "${YELLOW}To stop the dashboard, you need to stop the engine.${NC}"
    
    read -p "Stop the engine? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        stop_engine
    else
        echo -e "${YELLOW}Dashboard not stopped.${NC}"
    fi
}

# Function to reset (stop, clean logs, start)
reset_engine() {
    echo -e "${YELLOW}Resetting EMAX Trading Engine...${NC}"
    
    # Stop engine
    stop_engine
    
    # Clean logs
    echo -e "${YELLOW}Cleaning log files...${NC}"
    rm -f "$SCRIPT_DIR"/*.log 2>/dev/null
    rm -f "$SCRIPT_DIR"/logs/*.log 2>/dev/null
    echo -e "${GREEN}✓ Logs cleaned${NC}"
    
    # Start engine
    start_engine
}

# Function to view logs
view_logs() {
    echo -e "${YELLOW}Viewing logs (Ctrl+C to exit)...${NC}"
    echo ""
    
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}No log file found at: $LOG_FILE${NC}"
    fi
}

# Function to clean logs
clean_logs() {
    echo -e "${YELLOW}Cleaning log files...${NC}"
    
    rm -f "$SCRIPT_DIR"/*.log 2>/dev/null
    rm -f "$SCRIPT_DIR"/logs/*.log 2>/dev/null
    
    echo -e "${GREEN}✓ All log files cleaned${NC}"
}

# Main menu
show_menu() {
    echo -e "${YELLOW}COMMANDS:${NC}"
    echo ""
    echo -e "  ${GREEN}1${NC}) Start Engine"
    echo -e "  ${RED}2${NC}) Stop Engine"
    echo -e "  ${CYAN}3${NC}) Reset Engine (Stop + Clean Logs + Start)"
    echo ""
    echo -e "  ${GREEN}4${NC}) Start Dashboard"
    echo -e "  ${RED}5${NC}) Stop Dashboard"
    echo ""
    echo -e "  ${BLUE}6${NC}) View Logs (live)"
    echo -e "  ${YELLOW}7${NC}) Clean Logs"
    echo ""
    echo -e "  ${NC}0${NC}) Exit"
    echo ""
}

# Command line argument handling
if [ $# -gt 0 ]; then
    case "$1" in
        start)
            start_engine
            ;;
        stop)
            stop_engine
            ;;
        reset)
            reset_engine
            ;;
        start-dashboard)
            start_dashboard
            ;;
        stop-dashboard)
            stop_dashboard
            ;;
        status)
            show_header
            show_status
            ;;
        logs)
            view_logs
            ;;
        clean-logs)
            clean_logs
            ;;
        *)
            echo "Usage: $0 {start|stop|reset|start-dashboard|stop-dashboard|status|logs|clean-logs}"
            exit 1
            ;;
    esac
    exit 0
fi

# Interactive menu loop
while true; do
    show_header
    show_status
    show_menu
    
    read -p "Enter choice [0-7]: " choice
    echo ""
    
    case $choice in
        1)
            start_engine
            ;;
        2)
            stop_engine
            ;;
        3)
            reset_engine
            ;;
        4)
            start_dashboard
            ;;
        5)
            stop_dashboard
            ;;
        6)
            view_logs
            ;;
        7)
            clean_logs
            ;;
        0)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
