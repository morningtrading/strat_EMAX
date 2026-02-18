import MetaTrader5 as mt5
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.mt5_connector import MT5Connector

def main():
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect")
        return

    # Check FILUSD (was 0 in scan), BTCUSD (known good), AAPL (closed)
    debug_symbols = ["FILUSD", "BTCUSD", "AAPL", "EURUSD"]
    
    print(f"{'Symbol':<10} {'Selected':<10} {'Ask':<10} {'Bid':<10} {'Spread%':<10}")
    print("-" * 60)

    for sym in debug_symbols:
        res = mt5.symbol_select(sym, True)
        # small sleep to ensure data propagation if needed (though usually synchronous for tick?)
        # time.sleep(0.1) 
        tick = mt5.symbol_info_tick(sym)
        
        ask = tick.ask if tick else 0
        bid = tick.bid if tick else 0
        
        spread_pct = 0
        if bid > 0:
            spread_pct = ((ask - bid) / bid) * 100
            
        print(f"{sym:<10} {res:<10} {ask:<10.5f} {bid:<10.5f} {spread_pct:.4f}%")

    connector.disconnect()

if __name__ == "__main__":
    main()
