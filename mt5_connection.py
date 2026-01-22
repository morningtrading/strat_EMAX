#!/usr/bin/env python3
"""
MetaTrader 5 Real Connection Script
Connects to MT5 terminal and retrieves live market data
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import datetime
import time
from typing import Optional, Dict, List, Tuple

class MT5Connection:
    """MetaTrader 5 Connection Manager"""
    
    def __init__(self):
        self.connected = False
        self.account_info = None
        self.terminal_info = None
    
    def connect(self, login: Optional[int] = None, password: Optional[str] = None, 
                server: Optional[str] = None, timeout: int = 60000) -> bool:
        """
        Connect to MetaTrader 5 terminal
        
        Args:
            login: Account login number
            password: Account password
            server: Trading server name
            timeout: Connection timeout in milliseconds
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        print("Connecting to MetaTrader 5...")
        
        # Initialize MT5
        if not mt5.initialize():
            print("Failed to initialize MT5")
            return False
        
        # Check if terminal is running
        if not mt5.terminal_info():
            print("MetaTrader 5 terminal is not running!")
            print("Please start MetaTrader 5 terminal first.")
            return False
        
        # Get terminal info
        self.terminal_info = mt5.terminal_info()
        print(f"Terminal: {self.terminal_info.name}")
        print(f"Company: {self.terminal_info.company}")
        print(f"Path: {self.terminal_info.path}")
        
        # Try to connect to account if credentials provided
        if login and password and server:
            print(f"Connecting to account {login} on server {server}...")
            
            account_info = {
                "login": login,
                "password": password,
                "server": server,
                "timeout": timeout
            }
            
            if not mt5.login(**account_info):
                print(f"Failed to login to account {login}")
                print(f"Error: {mt5.last_error()}")
                return False
        
        # Get account info
        self.account_info = mt5.account_info()
        if self.account_info:
            print(f"Account: {self.account_info.login}")
            print(f"Server: {self.account_info.server}")
            print(f"Balance: ${self.account_info.balance:.2f}")
            print(f"Equity: ${self.account_info.equity:.2f}")
            print(f"Margin: ${self.account_info.margin:.2f}")
            print(f"Currency: {self.account_info.currency}")
        
        self.connected = True
        print("✅ Successfully connected to MetaTrader 5!")
        return True
    
    def disconnect(self):
        """Disconnect from MetaTrader 5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from MetaTrader 5")
    
    def get_symbols(self) -> List[str]:
        """Get list of available trading symbols"""
        if not self.connected:
            print("Not connected to MT5")
            return []
        
        symbols = mt5.symbols_get()
        if symbols is None:
            print("Failed to get symbols")
            return []
        
        symbol_names = [symbol.name for symbol in symbols]
        print(f"Found {len(symbol_names)} trading symbols")
        return symbol_names
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed information about a symbol"""
        if not self.connected:
            print("Not connected to MT5")
            return None
        
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"Symbol {symbol} not found")
            return None
        
        return {
            'name': info.name,
            'description': info.description,
            'currency_base': info.currency_base,
            'currency_profit': info.currency_profit,
            'currency_margin': info.currency_margin,
            'point': info.point,
            'digits': info.digits,
            'spread': info.spread,
            'trade_mode': info.trade_mode,
            'trade_stops_level': info.trade_stops_level,
            'trade_freeze_level': info.trade_freeze_level,
            'volume_min': info.volume_min,
            'volume_max': info.volume_max,
            'volume_step': info.volume_step,
            'margin_initial': info.margin_initial,
            'margin_maintenance': info.margin_maintenance
        }
    
    def get_rates(self, symbol: str, timeframe: int, count: int = 100) -> Optional[pd.DataFrame]:
        """
        Get historical price data
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe (mt5.TIMEFRAME_M1, M5, M15, H1, H4, D1, etc.)
            count: Number of bars to retrieve
        
        Returns:
            DataFrame with OHLCV data
        """
        if not self.connected:
            print("Not connected to MT5")
            return None
        
        print(f"Getting {count} bars of {symbol} data...")
        
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            print(f"Failed to get rates for {symbol}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        print(f"Retrieved {len(df)} bars of data")
        return df
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current bid/ask price for a symbol"""
        if not self.connected:
            print("Not connected to MT5")
            return None
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"Failed to get tick for {symbol}")
            return None
        
        return {
            'symbol': symbol,
            'time': datetime.datetime.fromtimestamp(tick.time),
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'volume': tick.volume,
            'spread': tick.ask - tick.bid
        }
    
    def get_positions(self) -> pd.DataFrame:
        """Get current open positions"""
        if not self.connected:
            print("Not connected to MT5")
            return pd.DataFrame()
        
        positions = mt5.positions_get()
        if positions is None:
            print("No open positions")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df
    
    def get_orders(self) -> pd.DataFrame:
        """Get pending orders"""
        if not self.connected:
            print("Not connected to MT5")
            return pd.DataFrame()
        
        orders = mt5.orders_get()
        if orders is None or len(orders) == 0:
            print("No pending orders")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(orders, columns=orders[0]._asdict().keys())
        df['time_setup'] = pd.to_datetime(df['time_setup'], unit='s')
        df['time_expiration'] = pd.to_datetime(df['time_expiration'], unit='s')
        
        return df

def demo_mt5_connection():
    """Demonstrate MT5 connection and data retrieval"""
    print("MetaTrader 5 Connection Demo")
    print("=" * 50)
    
    # Create connection
    mt5_conn = MT5Connection()
    
    # Try to connect (without credentials for demo)
    if not mt5_conn.connect():
        print("\n❌ Could not connect to MT5")
        print("Make sure MetaTrader 5 terminal is running!")
        print("\nTo use with real account, call:")
        print("mt5_conn.connect(login=YOUR_LOGIN, password='YOUR_PASSWORD', server='YOUR_SERVER')")
        return
    
    try:
        # Get available symbols
        print("\n=== Available Symbols ===")
        symbols = mt5_conn.get_symbols()
        if symbols:
            print(f"Total symbols: {len(symbols)}")
            print("First 10 symbols:", symbols[:10])
        
        # Get symbol info for EURUSD
        print("\n=== EURUSD Symbol Info ===")
        eurusd_info = mt5_conn.get_symbol_info("EURUSD")
        if eurusd_info:
            for key, value in eurusd_info.items():
                print(f"{key}: {value}")
        
        # Get current price
        print("\n=== Current Price ===")
        price_info = mt5_conn.get_current_price("EURUSD")
        if price_info:
            for key, value in price_info.items():
                print(f"{key}: {value}")
        
        # Get historical data
        print("\n=== Historical Data (Last 10 bars) ===")
        rates_df = mt5_conn.get_rates("EURUSD", mt5.TIMEFRAME_H1, 10)
        if rates_df is not None:
            print(rates_df[['open', 'high', 'low', 'close', 'tick_volume']].tail())
        
        # Get positions and orders
        print("\n=== Open Positions ===")
        positions = mt5_conn.get_positions()
        if not positions.empty:
            print(positions[['symbol', 'type', 'volume', 'price_open', 'profit']])
        else:
            print("No open positions")
        
        print("\n=== Pending Orders ===")
        orders = mt5_conn.get_orders()
        if not orders.empty:
            print(orders[['symbol', 'type', 'volume', 'price_open', 'state']])
        else:
            print("No pending orders")
    
    finally:
        # Disconnect
        mt5_conn.disconnect()

def main():
    """Main function"""
    demo_mt5_connection()
    
    print("\n" + "=" * 50)
    print("Demo completed!")
    print("\nNext steps:")
    print("1. Start MetaTrader 5 terminal")
    print("2. Login to your trading account")
    print("3. Run this script again to see live data")
    print("4. Modify the script to add your trading logic")

if __name__ == "__main__":
    main()

