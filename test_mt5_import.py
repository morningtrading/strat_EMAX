#!/usr/bin/env python3
"""
Test MT5 Python Package Import
Run with: wine python test_mt5_import.py
"""

import sys
print(f"Python version: {sys.version}")

try:
    import MetaTrader5 as mt5
    print(f"MetaTrader5 version: {mt5.__version__}")
    print("✅ MetaTrader5 module imported successfully!")
    
    # Try to initialize (will fail if MT5 terminal is not running)
    print("\nAttempting to initialize MT5 connection...")
    if mt5.initialize():
        print("✅ MT5 initialized successfully!")
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info:
            print(f"Terminal: {terminal_info.name}")
            print(f"Company: {terminal_info.company}")
            print(f"Path: {terminal_info.path}")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            print(f"\nAccount: {account_info.login}")
            print(f"Server: {account_info.server}")
            print(f"Balance: ${account_info.balance:.2f}")
        
        mt5.shutdown()
    else:
        error = mt5.last_error()
        print(f"⚠️  MT5 initialization failed: {error}")
        print("This is expected if MT5 terminal is not running.")
        print("\nTo connect to MT5:")
        print("1. Make sure MT5 is running under Wine")
        print("2. Login to your trading account")
        print("3. Run this script again")
        
except ImportError as e:
    print(f"❌ Failed to import MetaTrader5: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n--- Test completed ---")
