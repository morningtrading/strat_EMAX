#!/bin/bash

# Script to clean stalled PID files
# This is useful when the bot crash or was killed and left a PID file behind

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Cleaning stalled PID files...${NC}"

FILES_REMOVED=0

if [ -f "engine.pid" ]; then
    echo -e "  Removing engine.pid..."
    rm -f engine.pid
    FILES_REMOVED=$((FILES_REMOVED + 1))
fi

if [ -f ".engine.pid" ]; then
    echo -e "  Removing .engine.pid..."
    rm -f .engine.pid
    FILES_REMOVED=$((FILES_REMOVED + 1))
fi

if [ $FILES_REMOVED -gt 0 ]; then
    echo -e "${GREEN}✓ Removed $FILES_REMOVED stalled PID file(s)${NC}"
else
    echo -e "${GREEN}✓ No stalled PID files found${NC}"
fi

echo -e "You can now start the engine normally."
