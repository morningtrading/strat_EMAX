
import sys
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mt5_connector import MT5Connector

def calculate_ema(prices, period):
    """Vectorized EMA calculation"""
    return prices.ewm(span=period, adjust=False).mean()

def run_backtest(df, fast_ema, slow_ema, spread_cost):
    """
    Run backtest on a dataframe with pre-calculated EMAs
    Returns: Net PnL
    """
    if df.empty: return 0.0
    
    f = df[f'ema_{fast_ema}'].values
    s = df[f'ema_{slow_ema}'].values
    
    # Position: 1 (Long) if Fast > Slow, -1 (Short) if Fast < Slow
    pos = np.where(f > s, 1, -1)
    
    # Trades: pos[i] != pos[i-1]
    trades = np.diff(pos) # Non-zero where change happens
    num_trades = np.count_nonzero(trades)
    
    if num_trades == 0: return 0.0
        
    # PnL Calculation
    price_changes = np.diff(df['close'].values)
    # Strategy Returns = Price Change * Previous Position
    strategy_returns = price_changes * pos[:-1]
    gross_pnl = np.sum(strategy_returns)
    
    net_pnl = gross_pnl - (num_trades * spread_cost)
    return net_pnl

def optimize_symbol(mt5, symbol, fast_range, slow_range):
    """
    Optimize a single symbol:
    1. Fetch 2025 Data (M5, M15, H1)
    2. Split Even/Odd Months
    3. Train Even (Grid Search)
    4. Test Odd (Validation)
    5. Return Best Params & Timeframe
    """
    
    # Get Symbol Info
    info = mt5.get_symbol_info(symbol)
    if not info:
        print(f"{symbol:<10} | SKIP (No Info)")
        return None

    spread = info.get('spread', 20)
    # Estimate point value cost
    point = info.get('point', 0.0001)
    spread_cost = spread * point
    
    timeframes = ['M5', 'M15', 'H1']
    best_overall = None
    best_test_pnl = -float('inf')
    
    print(f"\nProcessing {symbol} (Spread: {spread})...")
    
    # Date Range: 2025 Full Year
    date_from = datetime(2025, 1, 1)
    date_to = datetime(2025, 12, 31)
    
    for tf in timeframes:
        # Fetch Data
        rates = mt5.get_rates_range(symbol, tf, date_from, date_to)
        if not rates or len(rates) < 100:
            print(f"  {tf:<4}: No data for 2025")
            continue
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'])
        df['month'] = df['time'].dt.month
        df['close'] = df['close'].astype(float)
        
        # Pre-calc EMAs
        all_periods = set(fast_range) | set(slow_range)
        for p in all_periods:
            df[f'ema_{p}'] = calculate_ema(df['close'], p)
            
        # Split Train/Test
        # Train: Even Months (2, 4, 6, 8, 10, 12)
        # Test: Odd Months (1, 3, 5, 7, 9, 11)
        train_df = df[df['month'] % 2 == 0].copy()
        test_df = df[df['month'] % 2 != 0].copy()
        
        if train_df.empty or test_df.empty:
            print(f"  {tf:<4}: Insufficient data split")
            continue
            
        # Optimization on Train (Even Months)
        best_train_pnl = -float('inf')
        best_params = (9, 21)
        
        for f in fast_range:
            for s in slow_range:
                if f >= s: continue
                
                pnl = run_backtest(train_df, f, s, spread_cost)
                if pnl > best_train_pnl:
                    best_train_pnl = pnl
                    best_params = (f, s)
        
        # Validation on Test (Odd Months)
        test_pnl = run_backtest(test_df, best_params[0], best_params[1], spread_cost)
        
        print(f"  {tf:<4}: Best Params {best_params} | Train PnL: {best_train_pnl:>8.2f} | Test PnL: {test_pnl:>8.2f}")
        
        # Selection Logic: Maximize Test PnL
        if test_pnl > best_test_pnl:
            best_test_pnl = test_pnl
            best_overall = {
                'timeframe': tf,
                'fast_ema': best_params[0],
                'slow_ema': best_params[1],
                'test_pnl': test_pnl,
                'train_pnl': best_train_pnl,
                'spread': spread
            }

    if best_overall:
        print(f"Winner {symbol}: {best_overall['timeframe']} ({best_overall['fast_ema']}/{best_overall['slow_ema']}) PnL: {best_overall['test_pnl']:.2f}")
    return best_overall

def update_config(results):
    config_path = Path('config/trading_config.json')
    if not config_path.exists():
        print("Config not found!")
        return
        
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    settings = config.get('symbols', {}).get('settings', {})
    updated_count = 0
    
    for symbol, data in results.items():
        if symbol not in settings:
            settings[symbol] = {}
            
        settings[symbol]['fast_ema'] = data['fast_ema']
        settings[symbol]['slow_ema'] = data['slow_ema']
        settings[symbol]['timeframe'] = data['timeframe']
        
        # Store metadata
        settings[symbol]['_opt_pnl_test'] = round(data['test_pnl'], 2)
        settings[symbol]['_opt_pnl_train'] = round(data['train_pnl'], 2)
        settings[symbol]['_note'] = f"Opt 2025-Split ({data['timeframe']} {data['fast_ema']}/{data['slow_ema']})"
        
        updated_count += 1
            
    config['symbols']['settings'] = settings
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
        
    print(f"\nUpdated config for {updated_count} symbols.")

def main():
    print("="*60)
    print("TIMEFRAME & SPLIT OPTIMIZER (2025 Even/Odd)")
    print("="*60)
    
    mt5 = MT5Connector()
    if not mt5.connect():
        print("Failed to connect to MT5")
        return
        
    # Read candidates
    try:
        df = pd.read_csv('filtered_candidates.csv')
        candidates = df['Symbol'].tolist()
        print(f"Loaded {len(candidates)} candidates.")
    except Exception as e:
        print(f"Error reading candidates: {e}")
        return
        
    # Grid Settings
    fast_range = range(5, 21, 2)
    slow_range = range(20, 65, 5)
    
    results = {}
    
    for symbol in candidates:
        try:
            res = optimize_symbol(mt5, symbol, fast_range, slow_range)
            if res:
                results[symbol] = res
            time.sleep(0.1)
        except Exception as e:
            print(f"Error optimizing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            
    if results:
        update_config(results)
    
    mt5.disconnect()
    print("Optimization Complete.")

if __name__ == "__main__":
    main()
