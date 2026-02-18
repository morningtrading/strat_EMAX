
import sys
import os
import json
import logging
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mt5_connector import MT5Connector
from core.ema_strategy import EMAStrategy
import MetaTrader5 as mt5

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugXAU")

def main():
    print("="*60)
    print("DEBUG XAUUSD STRATEGY")
    print("="*60)
    
    # 1. Connect
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect")
        return

    symbol = "XAUUSD"
    timeframe = "M15"
    
    # 2. Get Data (100 bars like main.py)
    print(f"Fetching {timeframe} data for {symbol}...")
    bars = connector.get_rates(symbol, timeframe, count=100)
    if not bars:
        print("Failed to get bars")
        return
    print(f"Got {len(bars)} bars")
    
    # 3. Initialize Strategy
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'trading_config.json')
    strategy = EMAStrategy(config_path)
    
    # Check config for XAUUSD
    xau_settings = strategy.config.get('symbols', {}).get('settings', {}).get(symbol, {})
    print(f"Settings for {symbol}: {xau_settings}")
    
    # 4. Run Analysis
    print("Running analyze()...")
    try:
        strategy.set_position(symbol, None) # Assume flat
        signal = strategy.analyze(symbol, bars, None)
        print("Analyze success!")
        print(f"Signal: {signal}")
    except Exception as e:
        print(f"Analyze FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    # 5. Check EMA Values
    print("Checking EMA values...")
    try:
        vals = strategy.get_ema_values(symbol)
        print(f"EMA Values: {vals}")
        
        # Analyze trend (used for dashboard)
        fast = vals.get('fast_ema', [])
        slow = vals.get('slow_ema', [])
        trend = strategy.analyze_trend_momentum(fast, slow)
        print(f"Trend Analysis: {trend}")
    except Exception as e:
        print(f"EMA/Trend Check FAILED: {e}")
        traceback.print_exc()

    connector.disconnect()

if __name__ == "__main__":
    main()
