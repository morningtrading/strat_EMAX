#!/bin/bash
# MT5 Trading Menu - Interactive shell menu for MetaTrader 5 operations
# Requires: Wine, Python with MetaTrader5 package, MT5 terminal running

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/mt5_menu.py"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_header() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║           MT5 TRADING MENU - Axi Account                 ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  $(date '+%Y-%m-%d %H:%M:%S')                                     ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_menu() {
    echo -e "${YELLOW}Select an option:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} 💰 Get Account Balance & Info"
    echo -e "  ${GREEN}2)${NC} 📊 View All Open Positions"
    echo -e "  ${GREEN}3)${NC} ❌ Close All Positions (with confirmation)"
    echo -e "  ${GREEN}4)${NC} 🔍 Verify All Positions Closed"
    echo ""
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
}

run_command() {
    wine python "$PYTHON_SCRIPT" "$1" 2>/dev/null
}

option_balance() {
    echo -e "\n${BLUE}Fetching account info...${NC}"
    run_command "balance"
}

option_positions() {
    echo -e "\n${BLUE}Fetching positions...${NC}"
    run_command "positions"
}

option_close_all() {
    echo -e "\n${RED}Closing all positions...${NC}"
    run_command "close_all"
    
    echo ""
    echo -e "${BLUE}Verifying...${NC}"
    sleep 1
    run_command "verify"
}

option_verify() {
    echo -e "\n${BLUE}Verifying positions...${NC}"
    run_command "verify"
}

# Main loop
while true; do
    show_header
    show_menu
    
    echo -e -n "${CYAN}Enter choice [0-4]: ${NC}"
    read -r choice
    
    case $choice in
        1)
            option_balance
            ;;
        2)
            option_positions
            ;;
        3)
            option_close_all
            ;;
        4)
            option_verify
            ;;
        0)
            echo -e "\n${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "\n${RED}Invalid option. Please try again.${NC}"
            ;;
    esac
    
    echo ""
    echo -e "${YELLOW}Press Enter to continue...${NC}"
    read -r
done
