import MetaTrader5 as mt5
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.mt5_connector import MT5Connector

def main():
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect")
        return

    # Check a few common symbols
    test_symbols = ["EURUSD", "BTCUSD", "AAPL", "XAUUSD"]
    
    print(f"{'Symbol':<10} {'Spread (pts)':<15} {'Point':<10} {'Calc Spread':<15} {'Ask':<10} {'Bid':<10} {'Real Spread':<15} {'Spread%':<10}")
    print("-" * 100)

    for sym_name in test_symbols:
        # Select symbol in Market Watch to get fresh data
        if not mt5.symbol_select(sym_name, True):
            print(f"Failed to select {sym_name}")
            continue
            
        info = mt5.symbol_info(sym_name)
        tick = mt5.symbol_info_tick(sym_name)
        
        if info is None or tick is None:
            print(f"No info/tick for {sym_name}")
            continue
            
        spread_pts = info.spread
        point = info.point
        calc_spread = spread_pts * point
        
        real_spread = tick.ask - tick.bid
        avg_price = (tick.ask + tick.bid) / 2
        spread_percent = (real_spread / avg_price) * 100 if avg_price > 0 else 0
        
        print(f"{sym_name:<10} {spread_pts:<15} {point:<10} {calc_spread:<15.5f} {tick.ask:<10.5f} {tick.bid:<10.5f} {real_spread:<15.5f} {spread_percent:.4f}%")

    connector.disconnect()

if __name__ == "__main__":
    main()
