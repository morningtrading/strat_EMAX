
import sys
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mt5_connector import MT5Connector

def calculate_ema(prices, period):
    """Vectorized EMA calculation"""
    return prices.ewm(span=period, adjust=False).mean()

def backtest_symbol(symbol, bars, fast_range, slow_range, spread_points):
    """
    Backtest a single symbol across parameter grid
    Returns: Best (fast, slow, pnl)
    """
    df = pd.DataFrame(bars)
    if df.empty:
        return None
        
    df['close'] = df['close'].astype(float)
    
    # Pre-calculate all EMAs to avoid recomputing in loops
    # This is much faster than re-calculating inside the grid loop
    emas = {}
    all_periods = set(fast_range) | set(slow_range)
    for p in all_periods:
        emas[p] = calculate_ema(df['close'], p)
        
    best_pnl = -float('inf')
    best_params = (9, 41) # Default fallback
    
    # Grid Search
    for fast in fast_range:
        for slow in slow_range:
            if fast >= slow: continue
            
            fast_ema = emas[fast]
            slow_ema = emas[slow]
            
            # Vectorized Signal Generation
            # Buy: Fast > Slow AND PrevFast <= PrevSlow
            # Sell: Fast < Slow AND PrevFast >= PrevSlow
            
            # Shift allows comparing current vs previous
            # We use numpy for speed
            f = fast_ema.values
            s = slow_ema.values
            
            # Crossovers (True/False arrays)
            # bull_cross[i] is True if Fast[i] > Slow[i] AND Fast[i-1] <= Slow[i-1]
            # specific logic: (f > s) & (shift(f) <= shift(s))
            
            # Use simple logic:
            # 1. Position = 1 (Long) if Fast > Slow, -1 (Short) if Fast < Slow
            # 2. Trades occur when Position changes
            
            pos = np.where(f > s, 1, -1)
            
            # Trades: pos[i] != pos[i-1]
            trades = np.diff(pos) # Non-zero where change happens
            # trades = 2 (Short -> Long), -2 (Long -> Short)
            
            # Count trades
            num_trades = np.count_nonzero(trades)
            
            if num_trades == 0:
                continue
                
            # Approximate PnL
            # We are always in market (Reverse positions).
            # Return = Sum(Price_change * Position)
            # Correct Approach:
            # - We enter *after* the close of the crossover bar (Open of next)
            # - Simplified: Use Close-to-Close changes multiplied by *previous* position
            
            price_changes = np.diff(df['close'].values)
            # signal is determined by Close[i], so position applies to change from Close[i] to Close[i+1]
            # So we multiply Change[i] by Pos[i]
            
            # Align lengths: price_changes is len-1. pos needs to strip last element
            strategy_returns = price_changes * pos[:-1]
            
            gross_pnl = np.sum(strategy_returns)
            
            # Spread cost: Each trade costs `spread_points * point_value`
            # Simplify: cost per trade (approx in price terms) = spread_points * point_size
            # Assuming standard points
            point = 0.01 if 'JPY' in symbol else 0.0001
            # If symbol is index, point might be 0.1 or 1.0. Hard to know without `symbol_info`.
            # We'll use a fixed conservative cost estimate per trade based on typical spread
            
            # Use raw price spread cost approximation
            # If spread is 20 points, and point is 0.01, cost is 0.20 price units
            spread_cost_per_trade = spread_points * point 
            
            net_pnl = gross_pnl - (num_trades * spread_cost_per_trade)
            
            if net_pnl > best_pnl:
                best_pnl = net_pnl
                best_params = (fast, slow)
                
    return best_params, best_pnl

def main():
    print("="*60)
    print("EMAX MASS OPTIMIZER")
    print("="*60)
    
    # connector
    mt5 = MT5Connector()
    if not mt5.connect():
        print("Failed to connect to MT5")
        return
        
    # Read candidates
    try:
        df = pd.read_csv('filtered_candidates.csv')
        candidates = df['Symbol'].tolist()
        print(f"Loaded {len(candidates)} candidates for optimization.")
    except Exception as e:
        print(f"Error reading candidates: {e}")
        return
        
    # Grid Settings
    fast_range = range(5, 21, 2) # 5, 7, 9 ... 19
    slow_range = range(20, 65, 5) # 20, 25 ... 60
    
    results = {}
    
    print(f"Starting optimization (Grid: {len(fast_range)}x{len(slow_range)} per symbol)...")
    print("-" * 60)
    print(f"{'Symbol':<10} | {'Spread':<6} | {'Best P/L':<10} | {'Mode':<10} | {'Fast':<4} / {'Slow':<4}")
    print("-" * 60)
    
    for i, symbol in enumerate(candidates):
        try:
            # Get Info for spread/point
            info = mt5.get_symbol_info(symbol)
            if not info:
                print(f"{symbol:<10} | SKIP (No Info)")
                continue
                
            spread = info.get('spread', 20)
            point = info.get('point', 0.0001)
            
            # Get Data (M5, 1000 bars)
            bars = mt5.get_rates(symbol, "M5", 1000)
            if not bars:
                print(f"{symbol:<10} | SKIP (No Data)")
                continue
                
            # Run Backtest
            best_params, best_pnl = backtest_symbol(symbol, bars, fast_range, slow_range, spread)
            
            fast, slow = best_params
            
            # Color code
            mode = "M5-Opt"
            print(f"{symbol:<10} | {spread:<6} | {best_pnl:>10.2f} | {mode:<10} | {fast:<4} / {slow:<4}")
            
            results[symbol] = {
                "fast_ema": fast,
                "slow_ema": slow,
                "pnl": round(best_pnl, 2),
                "spread": spread
            }
            
            # Slight delay to not choke MT5
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error optimizing {symbol}: {e}")
            
    print("-" * 60)
    print("Optimization Complete.")
    
    # Update Config
    update_config(results)

def update_config(results):
    config_path = Path('config/trading_config.json')
    if not config_path.exists():
        print("Config not found!")
        return
        
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    # Apply optimized settings
    settings = config.get('symbols', {}).get('settings', {})
    updated_count = 0
    
    for symbol, data in results.items():
        if symbol in settings:
            settings[symbol]['fast_ema'] = data['fast_ema']
            settings[symbol]['slow_ema'] = data['slow_ema']
            settings[symbol]['_backtest_pnl'] = data['pnl']
            settings[symbol]['_note'] = f"Auto-Optimized M5 (dSpread={data['spread']})"
            updated_count += 1
            
    config['symbols']['settings'] = settings
    
    # Save
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
        
    print(f"\nUpdated {updated_count} symbols in {config_path}")

if __name__ == "__main__":
    main()
