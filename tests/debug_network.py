
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import MetaTrader5 as mt5
    print("MetaTrader5 module imported successfully")
except ImportError:
    print("ERROR: MetaTrader5 module NOT found")
    sys.exit(1)

def test_connection():
    print("Attempting to initialize MT5...")
    if not mt5.initialize():
        print(f"ERROR: initialize() failed, error code = {mt5.last_error()}")
        return False
    
    print("MT5 Initialized.")
    
    # Check terminal info
    term_info = mt5.terminal_info()
    if term_info:
        print(f"Terminal: {term_info.name} | {term_info.company}")
        print(f"Connected: {term_info.connected}")
    else:
        print("ERROR: Failed to get terminal info")
        
    # Check account info
    account_info = mt5.account_info()
    if account_info:
        print(f"Account: {account_info.login}")
        print(f"Balance: {account_info.balance}")
    else:
        print(f"ERROR: Failed to get account info, error code = {mt5.last_error()}")

    # Ping check? None available directly, but get_ticks works if connected
    print("Checking network via symbol_info_tick('EURUSD')...")
    eurusd = mt5.symbol_info_tick("EURUSD")
    if eurusd:
        print(f"EURUSD Tick: {eurusd.time} | Bid: {eurusd.bid}")
    else:
        print(f"WARNING: Failed to get EURUSD tick. Error: {mt5.last_error()}")

    mt5.shutdown()
    print("MT5 Shutdown.")

if __name__ == "__main__":
    test_connection()
