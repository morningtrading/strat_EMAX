#!/usr/bin/env python3
"""
================================================================================
VALIDATION BACKTEST - Optimized Settings on Unseen Data
================================================================================
Tests the optimized EMA settings on January 2025 data (outside optimization window)
to validate the strategy performance on unseen market conditions.
================================================================================
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import csv
import sys

# Optimized settings from backtest analysis
OPTIMIZED_CONFIG = {
    'XAUUSD': {'timeframe': 'H1', 'fast_ema': 19, 'slow_ema': 60, 'tf_mt5': mt5.TIMEFRAME_H1},
    'XAGUSD': {'timeframe': 'H1', 'fast_ema': 11, 'slow_ema': 60, 'tf_mt5': mt5.TIMEFRAME_H1, 'enabled': False},
    'US2000': {'timeframe': 'M15', 'fast_ema': 20, 'slow_ema': 60, 'tf_mt5': mt5.TIMEFRAME_M15},
    'SP500ft': {'timeframe': 'H1', 'fast_ema': 5, 'slow_ema': 40, 'tf_mt5': mt5.TIMEFRAME_H1},
    'NAS100ft': {'timeframe': 'M5', 'fast_ema': 11, 'slow_ema': 50, 'tf_mt5': mt5.TIMEFRAME_M5},
    'GER40ft': {'timeframe': 'M15', 'fast_ema': 7, 'slow_ema': 35, 'tf_mt5': mt5.TIMEFRAME_M15}
}

# Validation period - January 2025 (unseen data)
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 1, 22, 23, 59, 59)

# Simulation settings
SPREAD_COST = 2
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
    """Simulate EMA crossover strategy on historical bars."""
    if len(bars) < slow_period + 10:
        return {'total_trades': 0, 'winning_trades': 0, 'total_pnl': 0, 'win_rate': 0}
    
    closes = bars['close'].values
    fast_ema = calculate_ema(closes, fast_period)
    slow_ema = calculate_ema(closes, slow_period)
    
    trades = []
    position = None
    entry_price = 0
    
    for i in range(slow_period, len(bars)):
        prev_fast = fast_ema[i-1]
        prev_slow = slow_ema[i-1]
        curr_fast = fast_ema[i]
        curr_slow = slow_ema[i]
        
        # Bullish crossover
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            if position == 'SHORT':
                pnl = entry_price - closes[i] - SPREAD_COST
                trades.append(pnl)
            position = 'LONG'
            entry_price = closes[i]
        
        # Bearish crossover
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            if position == 'LONG':
                pnl = closes[i] - entry_price - SPREAD_COST
                trades.append(pnl)
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


def run_validation():
    """Validate optimized settings on January 2025 data"""
    
    print("="*80)
    print("VALIDATION BACKTEST - Optimized Settings on Unseen Data")
    print("="*80)
    print(f"Period: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print("Testing optimized EMA settings from Mar-Aug & Oct-Dec 2025 analysis")
    print("="*80)
    
    # Initialize MT5
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        sys.exit(1)
    
    print("\n✅ MT5 Connected\n")
    
    results = []
    total_pnl = 0
    
    for symbol, config in OPTIMIZED_CONFIG.items():
        if not config.get('enabled', True):
            print(f"⊘ {symbol:<12} - SKIPPED (disabled)")
            continue
        
        # Fetch bars for validation period
        rates = mt5.copy_rates_range(symbol, config['tf_mt5'], START_DATE, END_DATE)
        
        if rates is None or len(rates) < 100:
            print(f"⚠️  {symbol:<12} - Insufficient data ({len(rates) if rates else 0} bars)")
            continue
        
        bars_df = pd.DataFrame(rates)
        
        # Run simulation with optimized settings
        result = simulate_ema_crossover(bars_df, config['fast_ema'], config['slow_ema'])
        
        total_pnl += result['total_pnl']
        
        result_record = {
            'symbol': symbol,
            'timeframe': config['timeframe'],
            'fast_ema': config['fast_ema'],
            'slow_ema': config['slow_ema'],
            'bars': len(bars_df),
            **result
        }
        results.append(result_record)
        
        status = "✓" if result['total_pnl'] > 0 else "✗"
        print(f"{status} {symbol:<12} {config['timeframe']:<4} {config['fast_ema']:>2}/{config['slow_ema']:<2} | "
              f"{len(bars_df):>4} bars | {result['total_trades']:>3} trades | "
              f"{result['win_rate']:>5.1f}% win | PnL: {result['total_pnl']:>+9.2f}")
    
    # Save results
    csv_filename = "backtest_validation_Jan_2025.csv"
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'symbol', 'timeframe', 'fast_ema', 'slow_ema', 'bars',
            'total_trades', 'winning_trades', 'win_rate', 'total_pnl'
        ])
        writer.writeheader()
        writer.writerows(results)
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION RESULTS SUMMARY")
    print("="*80)
    print(f"Total PnL (Optimized Settings): {total_pnl:>+10.2f}")
    print(f"Results saved to: {csv_filename}")
    
    profitable_count = sum(1 for r in results if r['total_pnl'] > 0)
    print(f"Profitable symbols: {profitable_count}/{len(results)}")
    
    print("\n📊 Performance by Symbol:")
    sorted_results = sorted(results, key=lambda x: x['total_pnl'], reverse=True)
    for r in sorted_results:
        status = "🟢" if r['total_pnl'] > 0 else "🔴"
        print(f"  {status} {r['symbol']:<12} {r['total_pnl']:>+10.2f}")
    
    mt5.shutdown()
    print("\n✅ Validation Complete!")
    
    return results, total_pnl


if __name__ == "__main__":
    run_validation()
