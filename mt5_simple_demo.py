#!/usr/bin/env python3
"""
Simple MetaTrader 5 Demo
Basic MT5 connection and data retrieval
"""

import MetaTrader5 as mt5
import datetime
import time

def check_mt5_status():
    """Check if MT5 is available and running"""
    print("MetaTrader 5 Status Check")
    print("=" * 40)
    
    # Initialize MT5
    print("Initializing MetaTrader 5...")
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        print("Make sure MetaTrader 5 terminal is installed and running!")
        return False
    
    print("✅ MT5 initialized successfully")
    
    # Check terminal info
    terminal_info = mt5.terminal_info()
    if terminal_info:
        print(f"Terminal: {terminal_info.name}")
        print(f"Company: {terminal_info.company}")
        print(f"Path: {terminal_info.path}")
        print(f"Build: {terminal_info.build}")
    else:
        print("❌ Could not get terminal info")
        return False
    
    # Check account info
    account_info = mt5.account_info()
    if account_info:
        print(f"\nAccount Information:")
        print(f"Login: {account_info.login}")
        print(f"Server: {account_info.server}")
        print(f"Balance: ${account_info.balance:.2f}")
        print(f"Equity: ${account_info.equity:.2f}")
        print(f"Currency: {account_info.currency}")
        print(f"Leverage: 1:{account_info.leverage}")
    else:
        print("⚠️  No account logged in (this is normal for demo)")
    
    return True

def get_symbols_demo():
    """Get and display available trading symbols"""
    print("\n" + "=" * 40)
    print("Available Trading Symbols")
    print("=" * 40)
    
    symbols = mt5.symbols_get()
    if symbols is None:
        print("❌ Could not retrieve symbols")
        return
    
    print(f"Total symbols available: {len(symbols)}")
    print("\nFirst 20 symbols:")
    
    for i, symbol in enumerate(symbols[:20]):
        print(f"{i+1:2d}. {symbol.name} - {symbol.description}")
    
    if len(symbols) > 20:
        print(f"... and {len(symbols) - 20} more symbols")

def get_eurusd_info():
    """Get detailed information about EURUSD"""
    print("\n" + "=" * 40)
    print("EURUSD Symbol Information")
    print("=" * 40)
    
    symbol_info = mt5.symbol_info("EURUSD")
    if symbol_info is None:
        print("❌ EURUSD symbol not found")
        return
    
    print(f"Name: {symbol_info.name}")
    print(f"Description: {symbol_info.description}")
    print(f"Base Currency: {symbol_info.currency_base}")
    print(f"Quote Currency: {symbol_info.currency_profit}")
    print(f"Point: {symbol_info.point}")
    print(f"Digits: {symbol_info.digits}")
    print(f"Spread: {symbol_info.spread}")
    print(f"Trade Mode: {symbol_info.trade_mode}")
    print(f"Min Volume: {symbol_info.volume_min}")
    print(f"Max Volume: {symbol_info.volume_max}")
    print(f"Volume Step: {symbol_info.volume_step}")

def get_current_price():
    """Get current price for EURUSD"""
    print("\n" + "=" * 40)
    print("Current EURUSD Price")
    print("=" * 40)
    
    tick = mt5.symbol_info_tick("EURUSD")
    if tick is None:
        print("❌ Could not get current price")
        return
    
    print(f"Time: {datetime.datetime.fromtimestamp(tick.time)}")
    print(f"Bid: {tick.bid:.5f}")
    print(f"Ask: {tick.ask:.5f}")
    print(f"Last: {tick.last:.5f}")
    print(f"Volume: {tick.volume}")
    print(f"Spread: {(tick.ask - tick.bid):.5f}")

def get_historical_data():
    """Get historical price data"""
    print("\n" + "=" * 40)
    print("Historical Data (Last 5 bars)")
    print("=" * 40)
    
    # Get last 5 hourly bars
    rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_H1, 0, 5)
    if rates is None:
        print("❌ Could not get historical data")
        return
    
    print("Time\t\t\tOpen\tHigh\tLow\tClose\tVolume")
    print("-" * 70)
    
    for rate in rates:
        time_str = datetime.datetime.fromtimestamp(rate['time']).strftime('%Y-%m-%d %H:%M')
        print(f"{time_str}\t{rate['open']:.5f}\t{rate['high']:.5f}\t{rate['low']:.5f}\t{rate['close']:.5f}\t{rate['tick_volume']}")

def get_positions_and_orders():
    """Get current positions and orders"""
    print("\n" + "=" * 40)
    print("Positions and Orders")
    print("=" * 40)
    
    # Get positions
    positions = mt5.positions_get()
    if positions:
        print(f"Open Positions: {len(positions)}")
        for pos in positions:
            print(f"  {pos.symbol} {pos.type} {pos.volume} @ {pos.price_open}")
    else:
        print("No open positions")
    
    # Get orders
    orders = mt5.orders_get()
    if orders:
        print(f"\nPending Orders: {len(orders)}")
        for order in orders:
            print(f"  {order.symbol} {order.type} {order.volume} @ {order.price_open}")
    else:
        print("\nNo pending orders")

def main():
    """Main demo function"""
    print("MetaTrader 5 Simple Demo")
    print("=" * 50)
    
    # Check MT5 status
    if not check_mt5_status():
        print("\n❌ Cannot proceed without MT5 connection")
        print("\nTo fix this:")
        print("1. Install MetaTrader 5 terminal")
        print("2. Start the terminal")
        print("3. Run this script again")
        return
    
    # Run demos
    get_symbols_demo()
    get_eurusd_info()
    get_current_price()
    get_historical_data()
    get_positions_and_orders()
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("\nNext steps:")
    print("1. Login to your trading account in MT5")
    print("2. Use the trading functions in mt5_connection.py")
    print("3. Develop your trading strategies")

if __name__ == "__main__":
    main()

