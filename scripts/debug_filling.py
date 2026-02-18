
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mt5_connector import MT5Connector

def main():
    print("Initializing MT5 Connector...")
    connector = MT5Connector()
    
    if not connector.connect():
        print("❌ Failed to connect to MT5")
        return

    symbols = ["EURUSD", "XAUUSD", "USTEC", "USDJPY"]
    
    print("\n" + "="*50)
    print("SYMBOL FILLING MODE DEBUG")
    print("="*50)
    
    for symbol in symbols:
        info = connector.get_symbol_info(symbol)
        if not info:
             # Try to get raw info directly if simple wrapper fails
             import MetaTrader5 as mt5
             raw = mt5.symbol_info(symbol)
             if raw:
                 print(f"Symbol: {symbol}")
                 print(f"  Filling Mode Flags: {raw.filling_mode}")
                 print(f"  (1=FOK, 2=IOC, 3=FOK+IOC)")
             else:
                 print(f"Symbol {symbol} not found")
             continue
             
        # Access raw mt5 object to get filling_mode (my wrapper might not expose it)
        import MetaTrader5 as mt5
        raw = mt5.symbol_info(symbol)
        
        print(f"Symbol: {symbol}")
        print(f"  Filling Mode Flags: {raw.filling_mode}")
        
        modes = []
        # Check flags manually: 1=FOK, 2=IOC
        if raw.filling_mode & 1:
            modes.append("FOK")
        if raw.filling_mode & 2:
            modes.append("IOC")
        
        print(f"  Supported: {modes}")
        
    connector.disconnect()

if __name__ == "__main__":
    main()
