
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
    print(f"System Time: {datetime.now()}")
    print(f"Server Time Offset: {connector.server_time_offset:.2f} seconds")
    server_now = datetime.now().timestamp() - connector.server_time_offset
    print(f"Estimated Server Time: {datetime.fromtimestamp(server_now)}")
    print("-" * 60)
    
    # Common US Indices/Stocks on MT5 often include:
    symbols = ["US2000", "USTEC", "NAS100", "SP500", "US500", "DJ30", "US30", "Apple", "AAPL", "Tesla", "TSLA"]
    
    # Try to find valid symbols from the list
    found_symbols = []
    for s in symbols:
        if mt5.symbol_info(s):
            found_symbols.append(s)
            
    if not found_symbols:
        print("No common US symbols found. Listing first 10 symbols from MT5:")
        all_symbols = mt5.symbols_get()
        if all_symbols:
            for s in all_symbols[:10]:
                print(s.name)
        else:
            print("No symbols found at all.")
    else:
        print(f"Checking specific symbols: {found_symbols}")
        for sym in found_symbols:
            if not mt5.symbol_select(sym, True):
                print(f"Failed to select {sym}")
                continue
                
            info = mt5.symbol_info(sym)
            tick = mt5.symbol_info_tick(sym)
            
            print(f"\nSymbol: {sym}")
            
            if tick:
                staleness = server_now - tick.time
                print(f"  Last Tick Time: {datetime.fromtimestamp(tick.time)} (Server Time)")
                print(f"  Staleness:      {staleness:.2f} seconds ({staleness/60:.2f} minutes)")
            else:
                print("  Last Tick:      None")
                staleness = 999999
                
            is_open = connector.is_market_open(sym)
            print(f"  Trade Mode:     {info.trade_mode if info else 'None'}")
            print(f"  Is Open (API):  {is_open}")
            
            if is_open and staleness > 300: # 5 mins
                print("  WARNING: Reported OPEN but data is > 5 mins old!")

    connector.disconnect()

if __name__ == "__main__":
    main()
