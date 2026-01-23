#!/usr/bin/env python3
"""
================================================================================
EMA OPTIMIZATION BACKTESTER
================================================================================
Tests EMA crossover strategy with different fast/slow periods to find optimal
combinations for each symbol and timeframe.

Usage:
    wine python backtest_ema_optimizer.py

Output:
    - Console summary of best EMA combinations
    - CSV file with all results: backtest_results_YYYYMMDD_HHMMSS.csv
================================================================================
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from itertools import product
import csv
import sys

# Configuration
SYMBOLS = ['XAUUSD', 'XAGUSD', 'US2000', 'SP500ft', 'NAS100ft', 'GER40ft']
TIMEFRAMES = {
    'M1': mt5.TIMEFRAME_M1,
    'M5': mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'H1': mt5.TIMEFRAME_H1
}

# EMA search space
FAST_EMA_RANGE = range(5, 21)        # 5 to 20
SLOW_EMA_RANGE = range(20, 61, 5)    # 20, 25, 30, ... 60

# Backtest period - March to August 2025
START_DATE = datetime(2025, 3, 1)
END_DATE = datetime(2025, 8, 31, 23, 59, 59)

# Simulation settings
SPREAD_COST = 2  # Points of slippage/spread per trade
LOT_SIZE = 0.01


def calculate_ema(prices: np.ndarray, period: int) -> np.ndarray:
    """Calculate Exponential Moving Average"""
    ema = np.zeros_like(prices)
    multiplier = 2 / (period + 1)
    ema[0] = prices[0]
    
    for i in range(1, len(prices)):
        ema[i] = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
    
    return ema


def simulate_ema_crossover(bars: pd.DataFrame, fast_period: int, slow_period: int) -> dict:
    """
    Simulate EMA crossover strategy on historical bars.
    
    Returns dict with:
        - total_trades: Number of completed trades
        - winning_trades: Number of profitable trades
        - total_pnl: Total profit/loss in price points
        - win_rate: Percentage of winning trades
    """
    if len(bars) < slow_period + 10:
        return {'total_trades': 0, 'winning_trades': 0, 'total_pnl': 0, 'win_rate': 0}
    
    closes = bars['close'].values
    fast_ema = calculate_ema(closes, fast_period)
    slow_ema = calculate_ema(closes, slow_period)
    
    # Find crossovers
    trades = []
    position = None  # None, 'LONG', or 'SHORT'
    entry_price = 0
    
    for i in range(slow_period, len(bars)):
        prev_fast = fast_ema[i-1]
        prev_slow = slow_ema[i-1]
        curr_fast = fast_ema[i]
        curr_slow = slow_ema[i]
        
        # Bullish crossover
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            # Close short if open
            if position == 'SHORT':
                pnl = entry_price - closes[i] - SPREAD_COST
                trades.append(pnl)
            # Open long
            position = 'LONG'
            entry_price = closes[i]
        
        # Bearish crossover
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            # Close long if open
            if position == 'LONG':
                pnl = closes[i] - entry_price - SPREAD_COST
                trades.append(pnl)
            # Open short
            position = 'SHORT'
            entry_price = closes[i]
    
    # Close any open position at end
    if position == 'LONG':
        pnl = closes[-1] - entry_price - SPREAD_COST
        trades.append(pnl)
    elif position == 'SHORT':
        pnl = entry_price - closes[-1] - SPREAD_COST
        trades.append(pnl)
    
    if not trades:
        return {'total_trades': 0, 'winning_trades': 0, 'total_pnl': 0, 'win_rate': 0}
    
    winning = sum(1 for t in trades if t > 0)
    win_rate = (winning / len(trades)) * 100 if trades else 0
    
    return {
        'total_trades': len(trades),
        'winning_trades': winning,
        'total_pnl': sum(trades),
        'win_rate': win_rate
    }


def get_bars_for_range(symbol: str, timeframe, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Fetch historical bars for a specific date range"""
    rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
    if rates is None or len(rates) == 0:
        return None
    return pd.DataFrame(rates)


def run_optimization():
    """Main optimization loop"""
    
    print("="*70)
    print("EMA OPTIMIZATION BACKTESTER")
    print("="*70)
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print(f"Timeframes: {', '.join(TIMEFRAMES.keys())}")
    print(f"Fast EMA: {min(FAST_EMA_RANGE)}-{max(FAST_EMA_RANGE)}")
    print(f"Slow EMA: {min(SLOW_EMA_RANGE)}-{max(SLOW_EMA_RANGE)}")
    print(f"Period: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print("="*70)
    
    # Initialize MT5
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        sys.exit(1)
    
    print("\n✅ MT5 Connected")
    
    all_results = []
    best_results = []
    
    total_combos = len(SYMBOLS) * len(TIMEFRAMES) * len(FAST_EMA_RANGE) * len(SLOW_EMA_RANGE)
    print(f"\n🔄 Testing {total_combos} combinations...\n")
    
    for symbol in SYMBOLS:
        print(f"\n{'='*50}")
        print(f"📊 {symbol}")
        print(f"{'='*50}")
        
        for tf_name, tf_value in TIMEFRAMES.items():
            # Fetch bars for date range
            bars_df = get_bars_for_range(symbol, tf_value, START_DATE, END_DATE)
            if bars_df is None or len(bars_df) < 100:
                print(f"  ⚠️  {tf_name}: Insufficient data ({len(bars_df) if bars_df is not None else 0} bars)")
                continue
            
            print(f"  📈 {tf_name}: {len(bars_df)} bars loaded")
            
            tf_results = []
            
            # Test all EMA combinations
            for fast, slow in product(FAST_EMA_RANGE, SLOW_EMA_RANGE):
                if fast >= slow:
                    continue  # Fast must be less than slow
                
                result = simulate_ema_crossover(bars_df, fast, slow)
                
                record = {
                    'symbol': symbol,
                    'timeframe': tf_name,
                    'fast_ema': fast,
                    'slow_ema': slow,
                    **result
                }
                all_results.append(record)
                tf_results.append(record)
            
            # Find best for this symbol/timeframe
            if tf_results:
                # Sort by profit, then by win rate
                tf_results.sort(key=lambda x: (x['total_pnl'], x['win_rate']), reverse=True)
                best = tf_results[0]
                best_results.append(best)
                
                print(f"      ✅ Best: EMA {best['fast_ema']}/{best['slow_ema']} | "
                      f"Trades: {best['total_trades']} | "
                      f"Win: {best['win_rate']:.1f}% | "
                      f"PnL: {best['total_pnl']:.2f}")
    
    # Save all results to CSV
    csv_filename = f"backtest_results_Mar_Aug_2025.csv"
    
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'symbol', 'timeframe', 'fast_ema', 'slow_ema',
            'total_trades', 'winning_trades', 'win_rate', 'total_pnl'
        ])
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\n\n{'='*70}")
    print("🏆 OPTIMIZATION RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"\n{'Symbol':<12} {'TF':<5} {'Fast':<6} {'Slow':<6} {'Trades':<8} {'Win%':<8} {'PnL':<10}")
    print("-"*70)
    
    for r in best_results:
        print(f"{r['symbol']:<12} {r['timeframe']:<5} {r['fast_ema']:<6} {r['slow_ema']:<6} "
              f"{r['total_trades']:<8} {r['win_rate']:<8.1f} {r['total_pnl']:<10.2f}")
    
    print(f"\n💾 Full results saved to: {csv_filename}")
    print(f"📊 Total combinations tested: {len(all_results)}")
    
    mt5.shutdown()
    print("\n✅ Complete!")
    
    return best_results


if __name__ == "__main__":
    run_optimization()
