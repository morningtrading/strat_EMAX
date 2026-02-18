
import sys
import csv
import time
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mt5_connector import MT5Connector
import MetaTrader5 as mt5

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
    trades = np.diff(pos)
    num_trades = np.count_nonzero(trades)
    
    if num_trades == 0: return 0.0
        
    # PnL Calculation
    price_changes = np.diff(df['close'].values)
    strategy_returns = price_changes * pos[:-1]
    gross_pnl = np.sum(strategy_returns)
    
    net_pnl = gross_pnl - (num_trades * spread_cost)
    return net_pnl

def optimize_symbol(connector, symbol, fast_range, slow_range):
    """
    Optimize a single symbol:
    1. Fetch 2025 Data (M5, M15, H1)
    2. Split Even/Odd Months
    3. Train Even (Grid Search)
    4. Test Odd (Validation)
    5. Return Best Params & Timeframe & PnL%
    """
    info = connector.get_symbol_info(symbol)
    if not info:
        print(f"  [WARN] Could not get info for {symbol}")
        return None

    spread = info.get('spread', 0)
    point = info.get('point', 0.00001)
    spread_cost = spread * point
    
    timeframes = ['M5', 'M15', 'H1']
    best_overall = None
    best_test_pnl = -float('inf')
    
    # Date Range: 2025 Full Year (or recent if 2025 not available, but user V3 used 2025)
    # Let's use last 30 days for speed/recent relevance if 2025 implies strictly historical?
    # User's previous optimizations used 2025 split. I will stick to that for consistency/robustness.
    date_from = datetime(2025, 1, 1)
    date_to = datetime(2025, 12, 31)
    
    for tf in timeframes:
        # Fetch Data
        # Strategy 1: Try requested 2025 range
        rates = connector.get_rates_range(symbol, tf, date_from, date_to)
        
        # Strategy 2: Fallback to recent 10,000 bars (approx 1-3 months depending on TF)
        if not rates or len(rates) < 500:
            # print(f"  [INFO] {symbol} {tf}: 2025 range failed, trying recent data...")
            rates = connector.get_rates(symbol, tf, count=10000)
            
        if not rates or len(rates) < 500: 
            # print(f"  [WARN] {symbol} {tf}: Insufficient data ({len(rates) if rates else 0})")
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
        # If we have less than 2 months of data, just use 70/30 split
        unique_months = df['month'].unique()
        if len(unique_months) < 2:
            split_idx = int(len(df) * 0.7)
            train_df = df.iloc[:split_idx].copy()
            test_df = df.iloc[split_idx:].copy()
        else:
            train_df = df[df['month'] % 2 == 0].copy()
            test_df = df[df['month'] % 2 != 0].copy()
        
        if train_df.empty or test_df.empty:
            continue
            
        # Optimization on Train
        best_train_pnl = -float('inf')
        best_params = (9, 21)
        
        for f in fast_range:
            for s in slow_range:
                if f >= s: continue
                
                pnl = run_backtest(train_df, f, s, spread_cost)
                if pnl > best_train_pnl:
                    best_train_pnl = pnl
                    best_params = (f, s)
        
        # Validation on Test
        test_pnl = run_backtest(test_df, best_params[0], best_params[1], spread_cost)
        
        # Calculate PnL % approx
        initial_price = test_df['close'].iloc[0] if not test_df.empty else df['close'].iloc[0]
        if initial_price == 0: initial_price = 1.0
        
        pnl_percent = (test_pnl / initial_price) * 100.0
        
        if test_pnl > best_test_pnl:
            best_test_pnl = test_pnl
            best_overall = {
                'Symbol': symbol,
                'Timeframe': tf,
                'Fast': best_params[0],
                'Slow': best_params[1],
                'Test PnL': test_pnl,
                'Test PnL %': pnl_percent,
                'Initial Price': initial_price
            }

    return best_overall

def main():
    print("="*60)
    print("SELECTED SYMBOLS OPTIMIZATION (2025 Split)")
    print("="*60)
    
    # Load Config
    config_path = Path(__file__).parent.parent / 'config' / 'trading_config.json'
    try:
        with open(config_path, 'r') as f:
            cfg = json.load(f)
            enabled_symbols = cfg.get('symbols', {}).get('enabled', [])
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    if not enabled_symbols:
        print("No enabled symbols found in config.")
        return
        
    print(f"Found {len(enabled_symbols)} enabled symbols.")
    
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    # Grid Settings
    fast_range = range(5, 21, 2)
    slow_range = range(20, 65, 5)
    
    results = []
    
    print(f"{'Symbol':<10} | {'TF':<3} | {'Fast':<4} | {'Slow':<4} | {'PnL %':<8} | {'PnL $':<10}")
    print("-" * 60)
    
    for i, symbol in enumerate(enabled_symbols):
        try:
            # Ensure symbol is selected
            if not mt5.symbol_select(symbol, True):
                print(f"{symbol:<10} | Failed to select")
                continue
                
            res = optimize_symbol(connector, symbol, fast_range, slow_range)
            if res:
                results.append(res)
                print(f"{res['Symbol']:<10} | {res['Timeframe']:<3} | {res['Fast']:<4} | {res['Slow']:<4} | {res['Test PnL %']:>7.2f}% | ${res['Test PnL']:>9.2f}")
            else:
                print(f"{symbol:<10} | No Data / Opt Failed")
                
        except Exception as e:
            print(f"Error optimizing {symbol}: {e}")
            
    print("-" * 60)
    print("Optimization Complete.")
    
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values(by='Test PnL %', ascending=False)
        print("\nSUMMARY TABLE (Sorted by PnL %):")
        print(df[['Symbol', 'Timeframe', 'Fast', 'Slow', 'Test PnL %', 'Test PnL']].to_markdown(index=False, floatfmt=".2f"))
        
        filename = 'optimization_results_selected.csv'
        df.to_csv(filename, index=False)
        print(f"\nResults saved to {filename}")

    connector.disconnect()

if __name__ == "__main__":
    main()
