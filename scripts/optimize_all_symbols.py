
import sys
import csv
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

def optimize_symbol(mt5, symbol_info, fast_range, slow_range):
    """
    Optimize a single symbol:
    1. Fetch 2025 Data (M5, M15, H1)
    2. Split Even/Odd Months
    3. Train Even (Grid Search)
    4. Test Odd (Validation)
    5. Return Best Params & Timeframe & PnL%
    """
    symbol = symbol_info.name
    spread = symbol_info.spread
    point = symbol_info.point
    spread_cost = spread * point
    
    # Quick filter: If spread is crazy high, skip? User said 900+ symbols.
    # We'll validat spread cost relative to price if possible, but let's just process everything that has data.
    
    timeframes = ['M5', 'M15', 'H1']
    best_overall = None
    best_test_pnl = -float('inf')
    
    # Date Range: 2025 Full Year
    date_from = datetime(2025, 1, 1)
    date_to = datetime(2025, 12, 31)
    
    for tf in timeframes:
        # Fetch Data
        rates = mt5.get_rates_range(symbol, tf, date_from, date_to)
        if not rates or len(rates) < 500: # Min bars
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
        train_df = df[df['month'] % 2 == 0].copy()
        test_df = df[df['month'] % 2 != 0].copy()
        
        if train_df.empty or test_df.empty:
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
        
        # Calculate PnL %
        # Base it on the first close price of the Test set (or fallback to first close of df)
        initial_price = test_df['close'].iloc[0] if not test_df.empty else df['close'].iloc[0]
        if initial_price == 0: initial_price = 1.0 # Avoid div by zero
        
        pnl_percent = (test_pnl / initial_price) * 100.0
        
        # Selection Logic: Maximize Test PnL
        if test_pnl > best_test_pnl:
            best_test_pnl = test_pnl
            best_overall = {
                'Symbol': symbol,
                'Timeframe': tf,
                'Fast': best_params[0],
                'Slow': best_params[1],
                'Test PnL': test_pnl,
                'Test PnL %': pnl_percent,
                'Train PnL': best_train_pnl,
                'Spread': spread,
                'Initial Price': initial_price
            }

    return best_overall

def main():
    print("="*60)
    print("FULL SYMBOL OPTIMIZATION (2025 Even/Odd)")
    print("="*60)
    
    mt5 = MT5Connector()
    if not mt5.connect():
        print("Failed to connect to MT5")
        return
        
    print("Fetching ALL symbols...")
    import MetaTrader5 as m5
    all_symbols = m5.symbols_get()
    
    if not all_symbols:
        print("No symbols found.")
        return
        
    print(f"Found {len(all_symbols)} symbols.")
    
    # Filter visible or valid?
    # User asked for "900 plus", which implies almost everything.
    # We will just iterate all.
    
    # Grid Settings
    fast_range = range(5, 21, 2)
    slow_range = range(20, 65, 5)
    
    results = []
    
    start_time = time.time()
    
    for i, sym_info in enumerate(all_symbols):
        try:
            # Basic visibility check or select?
            # We must select it to get data usually
            if not m5.symbol_select(sym_info.name, True):
                continue
                
            res = optimize_symbol(mt5, sym_info, fast_range, slow_range)
            if res:
                results.append(res)
                print(f"[{i+1}/{len(all_symbols)}] {res['Symbol']:<10} | {res['Timeframe']:<3} | PnL%: {res['Test PnL %']:>6.2f}%")
            else:
                if (i+1) % 10 == 0:
                    print(f"[{i+1}/{len(all_symbols)}] {sym_info.name} ... No Data/Skipped")
            
            # Flush every 50 to CSV just in case
            if len(results) > 0 and len(results) % 50 == 0:
                save_results(results, partial=True)
                
        except Exception as e:
            print(f"Error optimizing {sym_info.name}: {e}")
            
    print("-" * 60)
    print("Optimization Complete.")
    
    save_results(results)
    mt5.disconnect()

def save_results(results, partial=False):
    if not results: return
    
    df = pd.DataFrame(results)
    
    # Sort by PnL % Descending
    df = df.sort_values(by='Test PnL %', ascending=False)
    
    if not partial:
        print("\nTOP 20 PERFORMERS:")
        print(df[['Symbol', 'Timeframe', 'Fast', 'Slow', 'Test PnL %', 'Spread']].head(20).to_string(index=False))
    
    filename = 'optimization_results_full.csv'
    df.to_csv(filename, index=False)
    if not partial:
        print(f"\nSaved all results to {filename}")

if __name__ == "__main__":
    main()
