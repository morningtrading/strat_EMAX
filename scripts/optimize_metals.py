
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Setup path to include project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mt5_connector import MT5Connector

# Configure logging
logging.basicConfig(level=logging.INFO)

def calculate_ema_numpy(prices, period):
    x = np.asarray(prices)
    return pd.Series(x).ewm(span=period, adjust=False).mean().values

def run_optimization():
    print("="*80)
    print("🔥 METALS OPTIMIZATION: XAUUSD, XAGUSD | M5, M15, H1, H4 | Last 12 Hours")
    print("   Fast: 5-25 (step 2) | Slow: 25-75 (step 5)")
    print("="*80)
    
    # Initialize connection
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    # Config
    TIMEFRAMES = ["M5", "M15", "H1", "H4"]
    LOOKBACK_HOURS = 12
    BARS_TO_FETCH = 400 
    
    # Ranges
    FAST_RANGE = range(5, 26, 2)   
    SLOW_RANGE = range(25, 76, 5) 
    
    # Target Symbols
    SYMBOLS = ['XAUUSD', 'XAGUSD']
        
    print(f"Symbols: {SYMBOLS}")
    
    # Global Results: {Symbol: [List of Results]}
    final_results = {} # Symbol -> List of {TF, Fast, Slow, PnL, Trades}

    for symbol in SYMBOLS:
        print(f"\nScanning {symbol}...", end=' ')
        final_results[symbol] = []
        
        info = connector.get_symbol_info(symbol)
        if not info:
             print(f"Failed to get symbol info for {symbol}")
             continue
             
        spread_cost = (info.get('spread', 10) * info.get('point', 0.00001)) if info else 0.0001
        print(f"(Spread Cost: {spread_cost:.5f})")

        for tf in TIMEFRAMES:
            print(f"[{tf}]", end=' ')
            
            # 1. Fetch Data
            bars = connector.get_rates(symbol, tf, count=BARS_TO_FETCH)
            if not bars:
                continue
                
            df = pd.DataFrame(bars)
            df['time'] = pd.to_datetime(df['time'])
            closes = df['close'].values
            
            # Define Time Window (Last 12h)
            start_time_limit = datetime.now() - timedelta(hours=LOOKBACK_HOURS)
            valid_indices = df[df['time'] >= start_time_limit].index
            if valid_indices.empty:
                continue
            
            window_start_idx = valid_indices[0]
            # Ensure window start is after EMA warmup (approx 80 bars)
            min_ema_warmup = 80
            if window_start_idx < min_ema_warmup:
                window_start_idx = min_ema_warmup
                
            if window_start_idx >= len(closes):
                continue

            # 2. Pre-calculate EMAs
            ema_cache = {}
            all_periods = set(list(FAST_RANGE) + list(SLOW_RANGE))
            for p in all_periods:
                ema_cache[p] = calculate_ema_numpy(closes, p)
            
            # 3. Grid Search
            for fast_p in FAST_RANGE:
                for slow_p in SLOW_RANGE:
                    if fast_p >= slow_p: continue
                    
                    fast_arr = ema_cache[fast_p]
                    slow_arr = ema_cache[slow_p]
                    
                    trend_zone = np.where(fast_arr > slow_arr, 1, -1)
                    
                    trade_pnl_sum = 0.0
                    trade_count = 0
                    
                    start_idx = window_start_idx
                    full_slice_zone = trend_zone
                    
                    changes = np.where(full_slice_zone[1:] != full_slice_zone[:-1])[0] + 1
                    changes = changes[changes >= start_idx]
                    
                    curr_pos_dir = 0
                    entry_price = 0.0
                    
                    # Assume we start flat
                    for idx in changes:
                        new_zone = full_slice_zone[idx]
                        price = closes[idx]
                        
                        # Close existing
                        if curr_pos_dir != 0:
                            raw_pnl = (price - entry_price) * curr_pos_dir
                            net_pnl = raw_pnl - spread_cost
                            trade_pnl_sum += net_pnl
                            trade_count += 1
                        
                        # Open new
                        curr_pos_dir = new_zone
                        entry_price = price
                        
                    # Close at end
                    if curr_pos_dir != 0:
                        raw_pnl = (closes[-1] - entry_price) * curr_pos_dir
                        net_pnl = raw_pnl - spread_cost
                        trade_pnl_sum += net_pnl
                        trade_count += 1
                        
                    if trade_count > 0:
                         final_results[symbol].append({
                            'TF': tf,
                            'Fast': fast_p,
                            'Slow': slow_p,
                            'PnL': trade_pnl_sum,
                            'Trades': trade_count
                        })

    # --- REPORTING ---
    print("\n\n" + "="*80)
    print("🏆 FINAL RECOMMENDATIONS (Top 3 Configs per Symbol)")
    print("="*80)
    print(f"{'Symbol':<10} | {'Rank':<4} | {'TF':<4} | {'Fast':<4} | {'Slow':<4} | {'PnL($)':<10} | {'Trades'}")
    print("-" * 80)
    
    for symbol in SYMBOLS:
        results = final_results.get(symbol, [])
        if not results:
            print(f"{symbol:<10} | No trades generated in window.")
            continue
            
        # Sort by PnL desc
        results.sort(key=lambda x: x['PnL'], reverse=True)
        
        # Take Top 3
        top_3 = results[:3]
        
        rank = 1
        for res in top_3:
            print(f"{symbol:<10} | #{rank:<3} | {res['TF']:<4} | {res['Fast']:<4} | {res['Slow']:<4} | {res['PnL']:<10.2f} | {res['Trades']}")
            rank += 1
            
        print("-" * 80)

    connector.disconnect()

if __name__ == "__main__":
    run_optimization()
