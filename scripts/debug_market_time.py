
import sys
import os
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mt5_connector import MT5Connector

def main():
    connector = MT5Connector()
    print("Connecting to MT5...")
    if not connector.connect():
        print(f"Connection failed: {connector.last_error}")
        return

    print("-" * 60)
    print(f"Server Time Offset: {connector.server_time_offset:.2f} seconds")
    print("-" * 60)
    
    symbols = ["BTCUSD", "EURUSD", "XAUUSD", "STJ", "BE"]
    
    for sym in symbols:
        is_open = connector.is_market_open(sym)
        info = connector.get_symbol_info(sym)
        
        print(f"Symbol: {sym}")
        print(f"  Is Open:      {is_open}")
        if info:
            print(f"  Trade Mode:   {info.get('trade_mode')}")
            # print(f"  Path:         {info.get('path')}")
        else:
            print("  Info:         None")
        print("-" * 60)
        
    connector.disconnect()

if __name__ == "__main__":
    main()
