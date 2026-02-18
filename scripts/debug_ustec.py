
import sys
import os
import MetaTrader5 as mt5

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mt5_connector import MT5Connector

def main():
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect")
        return

    symbol = "USTEC"
    # Check if we need to resolve it (wrapper does this but good to verify)
    info = connector.get_symbol_info(symbol)
    
    if not info:
        # Try alternate names if USTEC isn't found directly
        alternates = ["NAS100", "NAS100ft", "US100", "NDX"]
        for alt in alternates:
            info = connector.get_symbol_info(alt)
            if info:
                symbol = alt
                break
    
    if info:
        print(f"Symbol: {symbol}")
        print(f"  Volume Min: {info['volume_min']}")
        print(f"  Volume Max: {info['volume_max']}")
        print(f"  Volume Step: {info['volume_step']}")
        print(f"  Contract Size: {info['trade_contract_size']}")
        print(f"  Margin Initial: {info['margin_initial']}")
        print(f"  Digits: {info['digits']}")
    else:
        print(f"Symbol {symbol} not found")

    connector.disconnect()

if __name__ == "__main__":
    main()
