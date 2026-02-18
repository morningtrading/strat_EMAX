
import sys
import os
from datetime import datetime
import time

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

    print("-" * 60)
    server_now = datetime.now().timestamp() - connector.server_time_offset
    print(f"Estimated Server Time: {datetime.fromtimestamp(server_now)}")
    
    symbol = "BE"
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}")
        # Try finding it in all symbols
        found = False
        all_sym = mt5.symbols_get()
        for s in all_symbols:
           if s.name == symbol:
               print(f"Found {symbol} but failed to select?")
               found = True
               break
        if not found: 
             print(f"{symbol} not found on broker.")
    else:
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        print(f"\nSymbol: {symbol}")
        print(f"  Path: {info.path}")
        print(f"  Description: {info.description}")
        print(f"  Trade Mode: {info.trade_mode}")
        
        if tick:
            staleness = server_now - tick.time
            print(f"  Last Tick Time: {datetime.fromtimestamp(tick.time)} (Server Time)")
            print(f"  Staleness:      {staleness:.2f} seconds ({staleness/60:.2f} minutes)")
        else:
            print("  Last Tick: None")
            staleness = 999999
            
        print(f"  Is Open (Current Logic):  {connector.is_market_open(symbol)}")
        print(f"  Is Open (Proposed 5min):  {info.trade_mode == 4 and staleness < 300}")

    connector.disconnect()

if __name__ == "__main__":
    main()
