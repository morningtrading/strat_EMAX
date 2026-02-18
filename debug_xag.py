
import os
import sys
import json
from datetime import datetime
import pandas as pd
import logging

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.mt5_connector import MT5Connector
from core.ema_strategy import EMAStrategy

# Configure basic logging
logging.basicConfig(level=logging.INFO)

def run_debug():
    print("="*60)
    print("XAGUSD M1 DEBUGGER")
    print("="*60)
    
    # Initialize
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    # Settings from config (manually matched for verification)
    FAST_PERIOD = 18
    SLOW_PERIOD = 60
    SYMBOL = "XAGUSD"
    TIMEFRAME = "M1"
    
    print(f"Symbol: {SYMBOL}")
    print(f"Timeframe: {TIMEFRAME}")
    print(f"Config: FastEMA={FAST_PERIOD}, SlowEMA={SLOW_PERIOD}")
    
    # Fetch Data
    # Fetch extra bars to ensure EMA convergence
    print("Fetching data...")
    bars = connector.get_rates(SYMBOL, TIMEFRAME, count=200)
    
    if not bars:
        print("No data received")
        return
        
    print(f"Received {len(bars)} bars")
    
    # Manually Calculate EMAs to verify Strategy Logic
    closes = [b['close'] for b in bars]
    times = [b['time'] for b in bars]
    
    strategy = EMAStrategy()
    fast_ema = strategy.calculate_ema(closes, FAST_PERIOD)
    slow_ema = strategy.calculate_ema(closes, SLOW_PERIOD)
    
    # Print Last 10 Bars
    print("\nLast 10 Bars Analysis:")
    print("-" * 105)
    print(f"{'Time':<20} | {'Price':<10} | {'Fast(18)':<10} | {'Slow(60)':<10} | {'Diff':<10} | {'Trend':<8} | {'Signal'}")
    print("-" * 105)
    
    for i in range(-10, 0):
        t = times[i]
        p = closes[i]
        f = fast_ema[i]
        s = slow_ema[i]
        
        if f is None or s is None:
            continue
            
        diff = f - s
        trend = "BULL" if f > s else "BEAR"
        
        # Check cross
        prev_f = fast_ema[i-1]
        prev_s = slow_ema[i-1]
        signal = ""
        
        if prev_f is not None and prev_s is not None:
            if prev_f <= prev_s and f > s:
                signal = "🟢 BULL CROSS"
            elif prev_f >= prev_s and f < s:
                signal = "🔴 BEAR CROSS"
        
        print(f"{t:<20} | {p:<10.5f} | {f:<10.5f} | {s:<10.5f} | {diff:<10.5f} | {trend:<8} | {signal}")

    print("-" * 105)
    
    connector.disconnect()

if __name__ == "__main__":
    run_debug()
