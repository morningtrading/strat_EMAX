#!/bin/bash
################################################################################
# EMAX Trading Bot - One-Shot VPS Installation Script
# Optimized for Ubuntu 24.04.3 LTS (Noble Numbat)
#
# Usage (run as REGULAR USER, not sudo):
#   wget https://raw.githubusercontent.com/morningtrading/strat_EMAX/main/install_vps.sh
#   chmod +x install_vps.sh
#   ./install_vps.sh
#
# Installs to: ~/emax_trading
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
REPO_URL="https://github.com/morningtrading/strat_EMAX.git"
INSTALL_DIR="$HOME/emax_trading"
PYTHON_VERSION="3.12.0"
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe"
MT5_URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
TOTAL_STEPS=8

print_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[Step $1/$TOTAL_STEPS] $3${NC}"
    echo -e "${CYAN}Remaining: $((TOTAL_STEPS - $1)) steps${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

test_step() {
    if eval "$2"; then
        echo -e "${GREEN}✅ SUCCESS: $1${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED: $1${NC}"
        return 1
    fi
}

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           EMAX Trading Bot - One-Shot VPS Installation                  ║${NC}"
echo -e "${BLUE}║               Ubuntu 24.04.3 LTS (Noble Numbat)                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check NOT running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Do NOT run as root or with sudo!${NC}"
    echo -e "${YELLOW}Run as regular user: ./install_vps.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✓ User: $USER${NC}"
echo -e "${GREEN}✓ Home: $HOME${NC}"
echo -e "${GREEN}✓ Install to: $INSTALL_DIR${NC}"

# Step 1: System check
print_step 1 $TOTAL_STEPS "Verifying system..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "${GREEN}✓ OS: Ubuntu $VERSION_ID ($VERSION_CODENAME)${NC}"
    test_step "System detection" "[ '$VERSION_ID' = '24.04' ]"
else
    echo -e "${RED}❌ Cannot detect OS${NC}"
    exit 1
fi

# Step 2: Install system dependencies
print_step 2 $TOTAL_STEPS "Installing system dependencies (requires sudo)..."
echo -e "${YELLOW}You will be prompted for sudo password...${NC}"

if ! command -v wine &> /dev/null; then
    sudo dpkg --add-architecture i386
    sudo mkdir -pm755 /etc/apt/keyrings
    sudo wget -q -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
    sudo wget -q -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/${VERSION_CODENAME}/winehq-${VERSION_CODENAME}.sources
    sudo apt-get update -qq
    sudo apt-get install -y --install-recommends winehq-stable xvfb xserver-xephyr git curl wget
else
    echo -e "${GREEN}✓ Wine already installed${NC}"
    sudo apt-get install -y xvfb xserver-xephyr 2>/dev/null || true
fi

# Initialize Wine prefix if needed
if [ ! -d "$HOME/.wine" ]; then
    echo -e "${CYAN}Initializing Wine...${NC}"
    WINEDEBUG=-all wineboot -u
    sleep 3
fi

WINE_VER=$(wine --version)
echo -e "${GREEN}✓ Wine: $WINE_VER${NC}"
test_step "Wine installation" "command -v wine &> /dev/null && command -v xvfb-run &> /dev/null"

# Step 3: Clone repository
print_step 3 $TOTAL_STEPS "Cloning repository to $INSTALL_DIR..."
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠️  Backing up existing installation...${NC}"
    mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%s)"
fi

git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"
echo -e "${GREEN}✓ Repository cloned${NC}"
test_step "Repository" "[ -f '$INSTALL_DIR/main.py' ]"

# Step 4: Install Python in Wine
print_step 4 $TOTAL_STEPS "Installing Python $PYTHON_VERSION in Wine..."
WINE_PYTHON="$HOME/.wine/drive_c/Python312/python.exe"

if [ -f "$WINE_PYTHON" ]; then
    echo -e "${GREEN}✓ Python already installed${NC}"
else
    echo -e "${CYAN}Downloading Python installer...${NC}"
    wget -q --show-progress -O /tmp/python.exe "$PYTHON_URL"
    
    echo -e "${CYAN}Installing Python silently (~30 seconds)...${NC}"
    # Try xvfb-run first, fallback to direct wine if xvfb fails
    if ! xvfb-run -a wine /tmp/python.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 2>/dev/null; then
        echo -e "${YELLOW}⚠️  xvfb-run failed, trying direct wine...${NC}"
        DISPLAY=:0 wine /tmp/python.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 &
        sleep 30
    else
        sleep 15
    fi
    rm -f /tmp/python.exe
fi

WINE_PY_VER=$(wine python --version 2>/dev/null || echo "error")
if [ "$WINE_PY_VER" = "error" ]; then
    echo -e "${RED}❌ Python installation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Wine Python: $WINE_PY_VER${NC}"
test_step "Wine Python" "wine python --version &> /dev/null"

# Step 5: Install Python packages
print_step 5 $TOTAL_STEPS "Installing Python packages..."
echo -e "${CYAN}Upgrading pip...${NC}"
wine python -m pip install --upgrade pip setuptools wheel -q

echo -e "${CYAN}Installing packages...${NC}"
wine python -m pip install MetaTrader5 -q || { echo -e "${RED}❌ MetaTrader5 failed${NC}"; exit 1; }
wine python -m pip install requests python-telegram-bot -q || { echo -e "${RED}❌ Dependencies failed${NC}"; exit 1; }
wine python -m pip install pandas numpy python-dotenv -q

echo -e "${CYAN}Verifying imports...${NC}"
for pkg in MetaTrader5 requests telegram; do
    if wine python -c "import $pkg" 2>/dev/null; then
        echo -e "${GREEN}  ✓ $pkg${NC}"
    else
        echo -e "${RED}  ✗ $pkg failed${NC}"
        exit 1
    fi
done
test_step "Python packages" "wine python -c 'import MetaTrader5, requests, telegram' 2>/dev/null"

# Step 6: Install MetaTrader 5
print_step 6 $TOTAL_STEPS "Installing MetaTrader 5..."
MT5_DIR="$HOME/.wine/drive_c/Program Files/MetaTrader 5"

if [ -f "$MT5_DIR/terminal64.exe" ]; then
    echo -e "${GREEN}✓ MT5 already installed${NC}"
else
    echo -e "${CYAN}Downloading MT5...${NC}"
    wget -q --show-progress -O /tmp/mt5.exe "$MT5_URL"
    
    echo -e "${CYAN}Installing MT5 silently (~20 seconds)...${NC}"
    xvfb-run wine /tmp/mt5.exe /auto >/dev/null 2>&1 || true
    sleep 10
    rm -f /tmp/mt5.exe
fi

if [ -f "$MT5_DIR/terminal64.exe" ]; then
    echo -e "${GREEN}✓ MT5 installed${NC}"
    test_step "MT5" "[ -f '$MT5_DIR/terminal64.exe' ]"
else
    echo -e "${YELLOW}⚠️  MT5 not detected - may need manual install${NC}"
    test_step "MT5" "false" || true
fi

# Step 7: Setup configuration
print_step 7 $TOTAL_STEPS "Creating configuration..."
mkdir -p "$INSTALL_DIR/config" "$INSTALL_DIR/logs"

cat > "$INSTALL_DIR/config/.env" << 'EOF'
# MetaTrader 5 Credentials
MT5_LOGIN=YOUR_ACCOUNT_NUMBER
MT5_PASSWORD=YOUR_PASSWORD
MT5_SERVER=YOUR_MT5_SERVER

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
EOF

if [ ! -f "$INSTALL_DIR/config/trading_config.json" ] && [ -f "$INSTALL_DIR/trading_config.json" ]; then
    cp "$INSTALL_DIR/trading_config.json" "$INSTALL_DIR/config/"
fi

chmod 600 "$INSTALL_DIR/config/.env"
echo -e "${GREEN}✓ Configuration created${NC}"
test_step "Configuration" "[ -f '$INSTALL_DIR/config/.env' ]"

# Create helper scripts
cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Starting EMAX Trading Bot..."
xvfb-run wine python main.py
EOF

cat > "$INSTALL_DIR/stop.sh" << 'EOF'
#!/bin/bash
pkill -f "wine.*python.*main.py" || echo "Not running"
EOF

cat > "$INSTALL_DIR/status.sh" << 'EOF'
#!/bin/bash
if pgrep -f "wine.*python.*main.py" > /dev/null; then
    echo "✓ Bot running (PID: $(pgrep -f 'wine.*python.*main.py'))"
else
    echo "✗ Bot not running"
fi
EOF

cat > "$INSTALL_DIR/logs.sh" << 'EOF'
#!/bin/bash
tail -f logs/*.log 2>/dev/null || echo "No logs yet"
EOF

chmod +x "$INSTALL_DIR"/*.sh

# Step 8: Create systemd service
print_step 8 $TOTAL_STEPS "Creating systemd service..."
sudo tee /etc/systemd/system/emax-trading.service > /dev/null << EOF
[Unit]
Description=EMAX Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="DISPLAY=:0"
Environment="HOME=$HOME"
ExecStart=/usr/bin/xvfb-run -a /usr/bin/wine python $INSTALL_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/systemd.log
StandardError=append:$INSTALL_DIR/logs/systemd.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo -e "${GREEN}✓ Service created${NC}"
test_step "Systemd service" "systemctl list-unit-files | grep -q emax-trading"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✅ INSTALLATION COMPLETE!                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📊 SUMMARY:${NC}"
echo -e "  ${GREEN}✓${NC} Installation:    $INSTALL_DIR"
echo -e "  ${GREEN}✓${NC} Wine Python:     $WINE_PY_VER"
echo -e "  ${GREEN}✓${NC} MT5:             $MT5_DIR"
echo -e "  ${GREEN}✓${NC} Config:          $INSTALL_DIR/config/.env"
echo -e "  ${GREEN}✓${NC} Service:         emax-trading.service"
echo ""
echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
echo ""
echo -e "1️⃣  ${BLUE}Edit credentials:${NC}"
echo -e "    nano $INSTALL_DIR/config/.env"
echo ""
echo -e "2️⃣  ${BLUE}Test run:${NC}"
echo -e "    cd $INSTALL_DIR && ./start.sh"
echo ""
echo -e "3️⃣  ${BLUE}Run as service (autostart on boot):${NC}"
echo -e "    sudo systemctl enable emax-trading"
echo -e "    sudo systemctl start emax-trading"
echo ""
echo -e "${YELLOW}🔧 COMMANDS:${NC}"
echo -e "  Manual start:      ${CYAN}cd $INSTALL_DIR && ./start.sh${NC}"
echo -e "  Manual stop:       ${CYAN}./stop.sh${NC}"
echo -e "  Check status:      ${CYAN}./status.sh${NC}"
echo -e "  View logs:         ${CYAN}./logs.sh${NC}"
echo -e "  Service start:     ${CYAN}sudo systemctl start emax-trading${NC}"
echo -e "  Service stop:      ${CYAN}sudo systemctl stop emax-trading${NC}"
echo -e "  Service status:    ${CYAN}sudo systemctl status emax-trading${NC}"
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════${NC}"
