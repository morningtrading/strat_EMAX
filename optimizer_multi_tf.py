
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.mt5_connector import MT5Connector

# Configure logging
logging.basicConfig(level=logging.INFO)

def calculate_ema_numpy(prices, period):
    x = np.asarray(prices)
    return pd.Series(x).ewm(span=period, adjust=False).mean().values

def run_optimization():
    print("="*80)
    print("🔥 MULTI-TIMEFRAME OPTIMIZATION: M5, M15, H1, H4 | Last 12 Hours")
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
    # Base count needed for EMA warmup + window
    # 75 (max slow) + buffer. We need bars covering the last 12h.
    # M5: 12 * 12 = 144 bars. + 100 warmup = 250.
    # H4: 12 / 4 = 3 bars. This is tiny. We fetch 300 to be safe for EMA, but PnL window is small.
    BARS_TO_FETCH = 400 
    
    # Ranges
    FAST_RANGE = range(5, 26, 2)   
    SLOW_RANGE = range(25, 76, 5) 
    
    # Load Symbols
    try:
        with open('config/trading_config.json', 'r') as f:
            cfg = json.load(f)
            SYMBOLS = cfg.get('symbols', {}).get('enabled', [])
    except:
        SYMBOLS = ['XAUUSD']
        
    print(f"Symbols: {SYMBOLS}")
    
    # Global Results: {Symbol: [List of Results]}
    final_results = {} # Symbol -> List of {TF, Fast, Slow, PnL, Trades}

    for symbol in SYMBOLS:
        print(f"\nScanning {symbol}...", end=' ')
        final_results[symbol] = []
        
        info = connector.get_symbol_info(symbol)
        spread_cost = (info.get('spread', 10) * info.get('point', 0.00001)) if info else 0.0001

        for tf in TIMEFRAMES:
            print(f"[{tf}]", end=' ')
            
            # 1. Fetch Data
            bars = connector.get_rates(symbol, tf, count=BARS_TO_FETCH)
            if not bars:
                continue
                
            df = pd.DataFrame(bars)
            df['time'] = pd.to_datetime(df['time'])
            closes = df['close'].values
            times = df['time'].values
            
            # Define Time Window (Last 12h)
            start_time_limit = datetime.now() - timedelta(hours=LOOKBACK_HOURS)
            # Find index where time >= start_time_limit
            # We must simulate whole array for correct EMA, but only count PnL after this index
            
            # Simple binary filter later inside loop? No, pre-calc index.
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
                    
                    # Logic: Identify changes inside the window
                    # Start checking for crosses FROM window_start_idx
                    # But we need "Previous Zone" to detect cross at index 'window_start_idx'.
                    
                    start_idx = window_start_idx
                    
                    # Detect changes in the slice [start_idx:]
                    # A change at index 'i' means zone[i] != zone[i-1]
                    
                    full_slice_zone = trend_zone
                    
                    # Find changes where index >= start_idx
                    # Changes indices array
                    changes = np.where(full_slice_zone[1:] != full_slice_zone[:-1])[0] + 1
                    changes = changes[changes >= start_idx]
                    
                    curr_pos_dir = 0
                    entry_price = 0.0
                    
                    # First entry: We assume we enter on the first signal found within our window 
                    # OR if we carry over? 
                    # Simulating "What if I turned on bot 12h ago?" -> enter on first cross.
                    
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
                        
                    # Close at end (Mark to Market)
                    if curr_pos_dir != 0:
                        raw_pnl = (closes[-1] - entry_price) * curr_pos_dir
                        net_pnl = raw_pnl - spread_cost
                        trade_pnl_sum += net_pnl
                        trade_count += 1 # Optional: Count open trade as trade? Yes for stats.
                        
                    if trade_count > 0: # Only record active strategies
                         final_results[symbol].append({
                            'TF': tf,
                            'Fast': fast_p,
                            'Slow': slow_p,
                            'PnL': trade_pnl_sum,
                            'Trades': trade_count
                        })

    # --- REPORTING ---
    print("\n\n" + "="*80)
    print("🏆 FINAL RECOMMENDATIONS (Top 2 Configs per Symbol)")
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
        
        # Take Top 2
        top_2 = results[:2]
        
        rank = 1
        for res in top_2:
            print(f"{symbol:<10} | #{rank:<3} | {res['TF']:<4} | {res['Fast']:<4} | {res['Slow']:<4} | {res['PnL']:<10.2f} | {res['Trades']}")
            rank += 1
            
        # Optional: Print User Warning if best is negative
        if top_2[0]['PnL'] < 0:
             print(f"   ⚠️ WARNING: Best strategy for {symbol} is losing money.")
             
        print("-" * 80)

    connector.disconnect()

if __name__ == "__main__":
    run_optimization()
