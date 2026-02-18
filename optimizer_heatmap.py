
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.mt5_connector import MT5Connector

# Configure logging
logging.basicConfig(level=logging.INFO)

def calculate_ema_numpy(prices, period):
    x = np.asarray(prices)
    alpha = 2 / (period + 1)
    # Fast vectorized EMA calculation
    weights = (1 - alpha) ** np.arange(len(x))
    weights /= weights.sum()
    # This is actually full history EMA which is slow O(N^2) if naive, 
    # but pandas ewm is better. Let's use pandas for reliability and speed matching strategy.
    return pd.Series(x).ewm(span=period, adjust=False).mean().values

def run_optimization():
    print("="*80)
    print("🔥 EMA HEATMAP OPTIMIZATION: M5 | Last 12 Hours")
    print("   Fast: 5-25 (step 2) | Slow: 25-75 (step 5)")
    print("="*80)
    
    # Initialize connection
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    # Config
    TIMEFRAME = "M5"
    LOOKBACK_HOURS = 12
    BARS_NEEDED = (LOOKBACK_HOURS * 12) + 100
    
    # Ranges
    FAST_RANGE = range(5, 26, 2)   # 5, 7, ..., 25
    SLOW_RANGE = range(25, 76, 5)  # 25, 30, ..., 75
    
    # Load Symbols
    try:
        with open('config/trading_config.json', 'r') as f:
            cfg = json.load(f)
            SYMBOLS = cfg.get('symbols', {}).get('enabled', [])
    except:
        SYMBOLS = ['XAUUSD'] # Fallback
        
    print(f"Symbols: {SYMBOLS}")
    
    # Results Storage
    results = [] # {Symbol, Fast, Slow, NetPnL, Trades}

    for symbol in SYMBOLS:
        print(f"\nProcessing {symbol}...", end=' ')
        
        # 1. Fetch Data
        bars = connector.get_rates(symbol, TIMEFRAME, count=BARS_NEEDED)
        if not bars:
            print("No Data.")
            continue
            
        df = pd.DataFrame(bars)
        closes = df['close'].values
        times = df['time'].values
        
        # Get Symbol Info for Spread
        info = connector.get_symbol_info(symbol)
        spread_cost = (info.get('spread', 10) * info.get('point', 0.00001)) if info else 0.0001
        
        # 2. Pre-calculate EMAs
        ema_cache = {}
        # Calculate for all unique periods in both ranges
        all_periods = set(list(FAST_RANGE) + list(SLOW_RANGE))
        for p in all_periods:
            ema_cache[p] = calculate_ema_numpy(closes, p)
            
        print(f"Data Loaded. Running {len(FAST_RANGE)*len(SLOW_RANGE)} sims...", end=' ')
        
        # 3. Grid Search
        best_pnl = -999999
        best_cfg = (0, 0)
        
        for fast_p in FAST_RANGE:
            for slow_p in SLOW_RANGE:
                if fast_p >= slow_p: # Skip if fast >= slow (optional, but standard logic)
                    continue
                    
                # Vectorized Backtest Logic? 
                # Converting iterative logic to pure vector is hard with state (Open Position).
                # We will use a fast iterative loop with pre-calc arrays.
                
                fast_arr = ema_cache[fast_p]
                slow_arr = ema_cache[slow_p]
                
                # Signals: Fast > Slow (Buy), Fast < Slow (Sell)
                # Cross detection: (PrevFast <= PrevSlow) & (CurrFast > CurrSlow)
                
                # Create Signal Arrays
                # 1 = Bullish zone, -1 = Bearish zone
                trend_zone = np.where(fast_arr > slow_arr, 1, -1)
                
                # Crosses are where trend_zone changes
                # diff = trend_zone[i] - trend_zone[i-1]
                # 2 = Bull Cross (-1 -> 1)
                # -2 = Bear Cross (1 -> -1)
                
                # We need to loop to handle Position State (Exit on Cross)
                # But since Exit IS the Cross (Stop/Reverse), this is actually a "Always In" or "Reversal" system
                # UNLESS we have specific exit logic other than reverse.
                # The current logic has: Entry on Cross. Exit on Reverse Cross.
                # So it is effectively "Always In" Strategy (Flip LONG to SHORT).
                # This approximates the current bot behavior if no TP/SL hits (pure signal).
                
                # Fast PnL calc for Reversal Strategy:
                # Sum of (EntryPrice - ExitPrice) * Direction
                # Since it's always in:
                # Trade 1: Long at P1, Rev at P2. PnL = P2 - P1.
                # Trade 2: Short at P2, Rev at P3. PnL = P2 - P3 (or P2 - P3).
                # Wait, Short PnL = Entry - Exit.
                
                # Let's verify 'Always In' assumption.
                # Code says: "if signal and position is None: Open". "if position and signal != direction: Close".
                # Yes, it flips.
                
                # Identify Cross Indices
                # We start from max(slow_p) to be safe
                start_idx = 80 # Safe buffer
                
                crosses = [] # (index, type) 1=Buy, -1=Sell
                
                prev_zone = trend_zone[start_idx-1]
                
                trade_pnl_sum = 0.0
                trade_count = 0
                
                # Iterate through zones
                # Find changepoints
                changes = np.where(trend_zone[start_idx:] != np.roll(trend_zone[start_idx:], 1))[0]
                # Adjust indices because of slice
                changes = changes + start_idx
                
                # Filter valid changes (ignore 0 index of slice noise)
                curr_pos_dir = 0 # 0=None, 1=Long, -1=Short
                entry_price = 0.0
                
                for idx in changes:
                    if idx >= len(closes): break
                    
                    new_zone = trend_zone[idx]
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
                
                # End of loop - ignore open position pnl for standardized comparison (or mark to market?)
                # Standard practice: Close at last bar
                if curr_pos_dir != 0:
                     raw_pnl = (closes[-1] - entry_price) * curr_pos_dir
                     net_pnl = raw_pnl - spread_cost
                     trade_pnl_sum += net_pnl
                     trade_count += 1
                
                results.append({
                    'Symbol': symbol,
                    'Fast': fast_p,
                    'Slow': slow_p,
                    'PnL': trade_pnl_sum,
                    'Trades': trade_count
                })
                
                if trade_pnl_sum > best_pnl:
                    best_pnl = trade_pnl_sum
                    best_cfg = (fast_p, slow_p)
                    
        print(f"Done. Best: {best_cfg} (${best_pnl:.2f})")

    # --- REPORTING ---
    df_res = pd.DataFrame(results)
    
    if df_res.empty:
        print("No results generated.")
        return

    # Generate Pivot Tables (Heatmaps)
    unique_symbols = df_res['Symbol'].unique()
    
    for sym in unique_symbols:
        print(f"\n{'='*60}")
        print(f"HEATMAP: {sym} (Net PnL)")
        print(f"{'='*60}")
        
        sym_data = df_res[df_res['Symbol'] == sym]
        if sym_data.empty: continue
            
        # Pivot: Index=Slow, Columns=Fast, Values=PnL
        pivot = sym_data.pivot(index='Slow', columns='Fast', values='PnL')
        
        # Format for nicer printing
        # Fill NaN
        pivot = pivot.fillna(0)
        pd.options.display.float_format = '{:,.1f}'.format
        print(pivot)
        
        # Best setting
        best = sym_data.loc[sym_data['PnL'].idxmax()]
        print(f"\n🏆 BEST SETTING: Fast={best['Fast']}, Slow={best['Slow']} | PnL=${best['PnL']:.2f} ({int(best['Trades'])} trades)")
        
    connector.disconnect()

if __name__ == "__main__":
    run_optimization()
