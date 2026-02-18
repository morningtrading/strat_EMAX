
import sys
import os
import json
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mt5_connector import MT5Connector
import MetaTrader5 as mt5

def main():
    connector = MT5Connector()
    print("Connecting to MT5...")
    if not connector.connect():
        print(f"Connection failed: {connector.last_error}")
        return

    symbol = "XAUUSD"
    print(f"\nChecking {symbol}:")
    
    # 1. Check Symbol Info
    info = connector.get_symbol_info(symbol)
    if info:
        print(f"  Selected: Yes")
        print(f"  Path: {info['path']}")
        print(f"  Visible: {info.get('visible')}")
        print(f"  Trade Mode: {info['trade_mode']}")
    else:
        print(f"  Selected: NO (get_symbol_info returned None)")
        # Try raw
        s = mt5.symbol_info(symbol)
        if s:
             print(f"  Raw mt5.symbol_info found it. Visible={s.visible}, Select={s.select}")
        else:
             print("  Raw mt5.symbol_info failed.")
             
    # 2. Check Data
    print("\nChecking Data (M15):")
    rates = connector.get_rates(symbol, "M15", 10)
    if rates:
        print(f"  Success! Retrieved {len(rates)} bars.")
        print(f"  Last bar: {rates[-1]['time']}")
    else:
        print("  FAILED to retrieve rates.")
        print(f"  Last Error: {mt5.last_error()}")

    connector.disconnect()

if __name__ == "__main__":
    main()
