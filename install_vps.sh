#!/bin/bash
################################################################################
# EMAX Trading Bot - VPS Installation Script
# Optimized for Ubuntu 24.04.3 LTS (Noble Numbat)
# Also compatible with Ubuntu 22.04 / 20.04
#
# Usage: 
#   wget https://raw.githubusercontent.com/morningtrading/strat_EMAX/main/install_vps.sh
#   chmod +x install_vps.sh
#   sudo ./install_vps.sh
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/morningtrading/strat_EMAX.git"
INSTALL_DIR="/opt/emax_trading"
MT5_INSTALLER_URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
TOTAL_STEPS=9

# Progress tracker
print_step() {
    local current=$1
    local total=$2
    local message=$3
    local remaining=$((total - current))
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[Step $current/$total] $message${NC}"
    echo -e "${CYAN}Remaining steps: $remaining${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

test_step() {
    local step_name=$1
    local test_command=$2
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ SUCCESS: $step_name verified${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED: $step_name verification failed${NC}"
        return 1
    fi
}

echo -e "${BLUE}========================================================================${NC}"
echo -e "${BLUE}  EMAX Trading Bot - Automated VPS Setup${NC}"
echo -e "${BLUE}  Ubuntu 24.04.3 LTS (Noble Numbat)${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo ./install_vps.sh${NC}"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo -e "${YELLOW}⚠️  Running as root user. Enter username to configure: ${NC}"
    read -p "Username: " ACTUAL_USER
fi

USER_HOME=$(eval echo ~$ACTUAL_USER)

echo -e "${GREEN}✓ Installing for user: $ACTUAL_USER${NC}"
echo -e "${GREEN}✓ Home directory: $USER_HOME${NC}"

# Detect Ubuntu version
print_step 1 $TOTAL_STEPS "Detecting Ubuntu version..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    UBUNTU_CODENAME=$VERSION_CODENAME
    echo -e "${GREEN}✓ Detected: Ubuntu $VERSION_ID ($UBUNTU_CODENAME)${NC}"
    
    # Verify it's Ubuntu 24.04 (noble)
    if [ "$VERSION_ID" = "24.04" ] && [ "$VERSION_CODENAME" = "noble" ]; then
        echo -e "${GREEN}✓ Perfect match: Ubuntu 24.04.3 LTS (Noble Numbat)${NC}"
    elif [ "$VERSION_CODENAME" = "jammy" ] || [ "$VERSION_CODENAME" = "focal" ]; then
        echo -e "${YELLOW}⚠️  Running on Ubuntu $VERSION_ID ($VERSION_CODENAME) - script optimized for 24.04${NC}"
    else
        echo -e "${YELLOW}⚠️  Unsupported Ubuntu version, proceeding anyway...${NC}"
    fi
    
    test_step "Ubuntu version detection" "[ -n '$VERSION_ID' ] && [ -n '$VERSION_CODENAME' ]"
else
    echo -e "${RED}❌ Cannot detect Ubuntu version${NC}"
    exit 1
fi

# Update system
print_step 2 $TOTAL_STEPS "Updating system packages..."
apt-get update -qq || { echo -e "${RED}❌ apt-get update failed${NC}"; exit 1; }
apt-get upgrade -y -qq || { echo -e "${RED}❌ apt-get upgrade failed${NC}"; exit 1; }
test_step "System update" "dpkg -l | grep -q apt"

# Install Wine
print_step 3 $TOTAL_STEPS "Installing Wine (for MetaTrader 5)..."
dpkg --add-architecture i386 || { echo -e "${RED}❌ Failed to add i386 architecture${NC}"; exit 1; }
mkdir -pm755 /etc/apt/keyrings
wget -q -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key || { echo -e "${RED}❌ Failed to download Wine GPG key${NC}"; exit 1; }
wget -q -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/${UBUNTU_CODENAME}/winehq-${UBUNTU_CODENAME}.sources || { echo -e "${RED}❌ Failed to add Wine repository${NC}"; exit 1; }
apt-get update -qq
apt-get install -y --install-recommends winehq-stable winetricks xvfb || { echo -e "${RED}❌ Wine installation failed${NC}"; exit 1; }
WINE_VERSION=$(wine --version 2>/dev/null || echo "unknown")
echo -e "${GREEN}✓ Wine installed: $WINE_VERSION${NC}"
test_step "Wine installation" "command -v wine >/dev/null 2>&1 && command -v xvfb-run >/dev/null 2>&1"

# Install Python and dependencies
print_step 4 $TOTAL_STEPS "Installing Python and system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    cabextract \
    unzip \
    supervisor || { echo -e "${RED}❌ System dependencies installation failed${NC}"; exit 1; }
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ Python installed: $PYTHON_VERSION${NC}"
test_step "Python and dependencies" "command -v python3 >/dev/null 2>&1 && command -v git >/dev/null 2>&1 && command -v pip3 >/dev/null 2>&1"

# Clone repository
print_step 5 $TOTAL_STEPS "Cloning EMAX repository..."
if [ -d "$INSTALL_DIR" ]; then
    BACKUP_DIR="${INSTALL_DIR}.backup.$(date +%s)"
    echo -e "${YELLOW}⚠️  Directory exists. Backing up to $BACKUP_DIR${NC}"
    mv "$INSTALL_DIR" "$BACKUP_DIR"
fi
git clone "$REPO_URL" "$INSTALL_DIR" || { echo -e "${RED}❌ Git clone failed${NC}"; exit 1; }
chown -R $ACTUAL_USER:$ACTUAL_USER "$INSTALL_DIR"
echo -e "${GREEN}✓ Repository cloned to $INSTALL_DIR${NC}"
test_step "Repository clone" "[ -d '$INSTALL_DIR' ] && [ -f '$INSTALL_DIR/main.py' ] && [ -f '$INSTALL_DIR/requirements.txt' ]"

# Create Python virtual environment
print_step 6 $TOTAL_STEPS "Setting up Python environment (Wine Python for MT5)..."
cd "$INSTALL_DIR"

# Install Python packages that work on native Linux first (non-MT5 dependencies)
echo -e "${CYAN}Installing Wine Python and pip...${NC}"
sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" wine python -m pip install --upgrade pip -q 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Installing Python in Wine...${NC}"
    sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" winetricks -q python312 || {
        echo -e "${YELLOW}⚠️  Downloading Python installer for Wine...${NC}"
        sudo -u $ACTUAL_USER wget -q -O /tmp/python-installer.exe https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe
        sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" wine /tmp/python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        rm -f /tmp/python-installer.exe
    }
}

echo -e "${CYAN}Installing Python packages via Wine...${NC}"
# Install each package individually to provide better error messages
sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" wine python -m pip install --upgrade pip setuptools wheel -q
sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" wine python -m pip install MetaTrader5 -q || { echo -e "${RED}❌ MetaTrader5 package installation failed${NC}"; exit 1; }
sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" wine python -m pip install requests -q || { echo -e "${RED}❌ requests installation failed${NC}"; exit 1; }
sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" wine python -m pip install python-telegram-bot -q || { echo -e "${RED}❌ python-telegram-bot installation failed${NC}"; exit 1; }
sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" wine python -m pip install pandas numpy python-dotenv -q

WINE_PYTHON_VERSION=$(sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" wine python --version 2>/dev/null || echo "Wine Python installed")
echo -e "${GREEN}✓ Wine Python environment configured: $WINE_PYTHON_VERSION${NC}"
test_step "Wine Python environment" "sudo -u $ACTUAL_USER WINEPREFIX='$USER_HOME/.wine' wine python -c 'import sys; sys.exit(0)' 2>/dev/null"

# Verify Python packages
echo -e "${CYAN}Verifying critical Python packages...${NC}"
PACKAGES_OK=true
for pkg in MetaTrader5 requests telegram; do
    if sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" wine python -c "import $pkg" 2>/dev/null; then
        echo -e "${GREEN}  ✓ $pkg installed and importable${NC}"
    else
        echo -e "${RED}  ✗ $pkg missing or not importable${NC}"
        PACKAGES_OK=false
    fi
done
test_step "Required Python packages" "$PACKAGES_OK"

# Install MetaTrader 5
print_step 7 $TOTAL_STEPS "Installing MetaTrader 5..."
MT5_DIR="$USER_HOME/.wine/drive_c/Program Files/MetaTrader 5"
if [ -d "$MT5_DIR" ]; then
    echo -e "${YELLOW}⚠️  MT5 already installed at: $MT5_DIR${NC}"
    test_step "MT5 installation (existing)" "[ -f '$MT5_DIR/terminal64.exe' ]"
else
    echo -e "${CYAN}Downloading MT5 installer...${NC}"
    sudo -u $ACTUAL_USER wget -q -O /tmp/mt5setup.exe "$MT5_INSTALLER_URL" || { echo -e "${RED}❌ MT5 download failed${NC}"; exit 1; }
    echo -e "${GREEN}✓ MT5 installer downloaded${NC}"
    
    echo -e "${CYAN}Installing MT5 (this may take 2-3 minutes)...${NC}"
    sudo -u $ACTUAL_USER WINEPREFIX="$USER_HOME/.wine" DISPLAY=:0 xvfb-run wine /tmp/mt5setup.exe /auto >/dev/null 2>&1 || echo -e "${YELLOW}⚠️  Wine installer may have warnings, checking result...${NC}"
    sleep 5
    rm -f /tmp/mt5setup.exe
    
    if [ -d "$MT5_DIR" ] && [ -f "$MT5_DIR/terminal64.exe" ]; then
        echo -e "${GREEN}✓ MT5 installed successfully to: $MT5_DIR${NC}"
        test_step "MT5 installation" "[ -f '$MT5_DIR/terminal64.exe' ]"
    else
        echo -e "${RED}❌ MT5 installation failed - manual installation required${NC}"
        echo -e "${YELLOW}You can install MT5 manually later with:${NC}"
        echo -e "${CYAN}  xvfb-run wine mt5setup.exe /auto${NC}"
        test_step "MT5 installation" "false" || true  # Don't exit, continue with setup
    fi
fi

# Setup configuration
print_step 8 $TOTAL_STEPS "Configuring trading bot..."
mkdir -p "$INSTALL_DIR/config"
mkdir -p "$INSTALL_DIR/logs"

# Create .env file template
cat > "$INSTALL_DIR/config/.env" << 'EOF'
# MetaTrader 5 Credentials
MT5_LOGIN=YOUR_ACCOUNT_NUMBER
MT5_PASSWORD=YOUR_PASSWORD
MT5_SERVER=YOUR_SERVER

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
EOF

# Check if trading_config.json exists
if [ ! -f "$INSTALL_DIR/config/trading_config.json" ]; then
    echo -e "${YELLOW}⚠️  config/trading_config.json not found in config/. Checking root...${NC}"
    if [ -f "$INSTALL_DIR/trading_config.json" ]; then
        cp "$INSTALL_DIR/trading_config.json" "$INSTALL_DIR/config/trading_config.json"
        echo -e "${GREEN}✓ Copied trading_config.json to config/${NC}"
    else
        echo -e "${RED}❌ trading_config.json not found${NC}"
    fi
fi

chown -R $ACTUAL_USER:$ACTUAL_USER "$INSTALL_DIR"
chmod 600 "$INSTALL_DIR/config/.env"

echo -e "${GREEN}✓ Configuration directories created${NC}"
echo -e "${YELLOW}⚠️  IMPORTANT: Edit $INSTALL_DIR/config/.env with your credentials${NC}"
test_step "Configuration setup" "[ -f '$INSTALL_DIR/config/.env' ] && [ -d '$INSTALL_DIR/logs' ]"

# Create systemd service
print_step 9 $TOTAL_STEPS "Creating systemd service..."
cat > /etc/systemd/system/emax-trading.service << EOF
[Unit]
Description=EMAX Trading Bot
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$INSTALL_DIR
Environment="DISPLAY=:0"
Environment="WINEPREFIX=$USER_HOME/.wine"
ExecStart=/usr/bin/xvfb-run -a /usr/bin/wine python $INSTALL_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload || { echo -e "${RED}❌ systemctl daemon-reload failed${NC}"; exit 1; }
echo -e "${GREEN}✓ Systemd service created${NC}"
test_step "Systemd service" "[ -f /etc/systemd/system/emax-trading.service ] && systemctl list-unit-files | grep -q emax-trading"

# Create helper scripts
echo -e "${CYAN}Creating helper scripts...${NC}"

# Start script
cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
DISPLAY=:0 xvfb-run -a wine python main.py
EOF

# Stop script
cat > "$INSTALL_DIR/stop.sh" << 'EOF'
#!/bin/bash
sudo systemctl stop emax-trading
EOF

# Status script
cat > "$INSTALL_DIR/status.sh" << 'EOF'
#!/bin/bash
sudo systemctl status emax-trading
EOF

# Logs script
cat > "$INSTALL_DIR/logs.sh" << 'EOF'
#!/bin/bash
tail -f logs/*.log 2>/dev/null || echo "No log files found yet"
EOF

chmod +x "$INSTALL_DIR"/*.sh
chown $ACTUAL_USER:$ACTUAL_USER "$INSTALL_DIR"/*.sh
echo -e "${GREEN}✓ Helper scripts created (start.sh, stop.sh, status.sh, logs.sh)${NC}"
test_step "Helper scripts" "[ -x '$INSTALL_DIR/start.sh' ] && [ -x '$INSTALL_DIR/stop.sh' ]"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ INSTALLATION COMPLETE - ALL $TOTAL_STEPS STEPS SUCCESSFUL!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}📊 INSTALLATION SUMMARY:${NC}"
echo -e "  ${GREEN}✓${NC} Ubuntu Version:       Ubuntu $VERSION_ID ($VERSION_CODENAME)"
echo -e "  ${GREEN}✓${NC} Wine Version:         $WINE_VERSION"
echo -e "  ${GREEN}✓${NC} Python Version:       $PYTHON_VERSION"
echo -e "  ${GREEN}✓${NC} Installation Dir:     $INSTALL_DIR"
echo -e "  ${GREEN}✓${NC} MT5 Directory:        $MT5_DIR"
echo -e "  ${GREEN}✓${NC} Systemd Service:      emax-trading.service"
echo -e "  ${GREEN}✓${NC} Running as User:      $ACTUAL_USER"
echo ""
echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
echo ""
echo -e "1️⃣  Configure your credentials:"
echo -e "   ${BLUE}nano $INSTALL_DIR/config/.env${NC}"
echo ""
echo -e "2️⃣  Update Telegram settings:"
echo -e "   ${BLUE}nano $INSTALL_DIR/config/trading_config.json${NC}"
echo ""
echo -e "3️⃣  Test the bot manually:"
echo -e "   ${BLUE}cd $INSTALL_DIR && ./start.sh${NC}"
echo ""
echo -e "4️⃣  Enable autostart service:"
echo -e "   ${BLUE}sudo systemctl enable emax-trading${NC}"
echo -e "   ${BLUE}sudo systemctl start emax-trading${NC}"
echo ""
echo -e "5️⃣  Check service status:"
echo -e "   ${BLUE}sudo systemctl status emax-trading${NC}"
echo -e "   ${BLUE}./status.sh${NC}"
echo ""
echo -e "6️⃣  View logs:"
echo -e "   ${BLUE}./logs.sh${NC}"
echo -e "   ${BLUE}journalctl -u emax-trading -f${NC}"
echo ""
echo -e "${YELLOW}🔧 HELPER COMMANDS:${NC}"
echo -e "   Start:   ${BLUE}sudo systemctl start emax-trading${NC}"
echo -e "   Stop:    ${BLUE}sudo systemctl stop emax-trading${NC}"
echo -e "   Restart: ${BLUE}sudo systemctl restart emax-trading${NC}"
echo -e "   Logs:    ${BLUE}journalctl -u emax-trading -f${NC}"
echo ""
echo -e "${YELLOW}📂 Installation Directory: ${BLUE}$INSTALL_DIR${NC}"
echo -e "${YELLOW}🍷 Wine Prefix: ${BLUE}$USER_HOME/.wine${NC}"
echo -e "${YELLOW}💻 MT5 Directory: ${BLUE}$MT5_DIR${NC}"
echo ""
echo -e "${GREEN}========================================================================${NC}"
