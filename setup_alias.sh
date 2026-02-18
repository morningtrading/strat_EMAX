#!/bin/bash

# Define the alias command
ALIAS_CMD="alias bot='cd /home/titus/projects/axibot/start_EMAXSTF && ./menu.sh'"

# File to modify (usually .bashrc or .zshrc)
RC_FILE="$HOME/.bashrc"

# Check if .bashrc exists, otherwise try .zshrc or .profile
if [ ! -f "$RC_FILE" ]; then
    if [ -f "$HOME/.zshrc" ]; then
        RC_FILE="$HOME/.zshrc"
    elif [ -f "$HOME/.profile" ]; then
        RC_FILE="$HOME/.profile"
    else
        echo "Could not find shell configuration file (.bashrc, .zshrc, or .profile)."
        exit 1
    fi
fi

# Check if alias already exists
if grep -q "alias bot=" "$RC_FILE"; then
    echo "Alias 'bot' already exists in $RC_FILE"
    # Optional: Update it? For now, just warn.
    echo "Please remove the existing alias first if you want to update it."
else
    echo "" >> "$RC_FILE"
    echo "# EMAX Trading Bot Alias" >> "$RC_FILE"
    echo "$ALIAS_CMD" >> "$RC_FILE"
    echo "Alias 'bot' added to $RC_FILE"
    echo "Please run: source $RC_FILE   OR   restart your terminal to use it."
fi
