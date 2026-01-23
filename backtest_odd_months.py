#!/usr/bin/env python3
"""
================================================================================
BACKTEST ON ODD MONTHS 2025 - Current Configuration
================================================================================
Tests current configuration on Jan, Mar, May, Jul, Sep, Nov 2025
================================================================================
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import csv
import sys

# Current configuration (original settings)
CURRENT_CONFIG = {
    'XAUUSD': {'timeframe': 'H1', 'fast_ema': 5, 'slow_ema': 55, 'tf_mt5': mt5.TIMEFRAME_H1},
    'XAGUSD': {'timeframe': 'H1', 'fast_ema': 18, 'slow_ema': 60, 'tf_mt5': mt5.TIMEFRAME_H1, 'enabled': False},
    'US2000': {'timeframe': 'H1', 'fast_ema': 15, 'slow_ema': 40, 'tf_mt5': mt5.TIMEFRAME_H1},
    'SP500ft': {'timeframe': 'M15', 'fast_ema': 19, 'slow_ema': 55, 'tf_mt5': mt5.TIMEFRAME_M15},
    'NAS100ft': {'timeframe': 'M5', 'fast_ema': 12, 'slow_ema': 60, 'tf_mt5': mt5.TIMEFRAME_M5},
    'GER40ft': {'timeframe': 'H1', 'fast_ema': 10, 'slow_ema': 30, 'tf_mt5': mt5.TIMEFRAME_H1}
}

# Odd months of 2025
PERIODS = [
    ('January', datetime(2025, 1, 1), datetime(2025, 1, 31, 23, 59, 59)),
    ('March', datetime(2025, 3, 1), datetime(2025, 3, 31, 23, 59, 59)),
    ('May', datetime(2025, 5, 1), datetime(2025, 5, 31, 23, 59, 59)),
    ('July', datetime(2025, 7, 1), datetime(2025, 7, 31, 23, 59, 59)),
    ('September', datetime(2025, 9, 1), datetime(2025, 9, 30, 23, 59, 59)),
    ('November', datetime(2025, 11, 1), datetime(2025, 11, 30, 23, 59, 59))
]

SPREAD_COST = 2


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
        
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            if position == 'SHORT':
                pnl = entry_price - closes[i] - SPREAD_COST
                trades.append(pnl)
            position = 'LONG'
            entry_price = closes[i]
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            if position == 'LONG':
                pnl = closes[i] - entry_price - SPREAD_COST
                trades.append(pnl)
            position = 'SHORT'
            entry_price = closes[i]
    
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


def run_backtest():
    """Run backtest on odd months of 2025"""
    
    print("="*80)
    print("BACKTEST: Current Config on Odd Months 2025")
    print("="*80)
    print("Testing: January, March, May, July, September, November")
    print("="*80)
    
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        sys.exit(1)
    
    print("\nMT5 Connected\n")
    
    # Store results per period
    period_results = {month: {} for month, _, _ in PERIODS}
    all_results = []
    
    for month_name, start_date, end_date in PERIODS:
        print(f"\n{'='*80}")
        print(f"{month_name} 2025 ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
        print(f"{'='*80}")
        
        month_total = 0
        
        for symbol, config in CURRENT_CONFIG.items():
            if not config.get('enabled', True):
                continue
            
            rates = mt5.copy_rates_range(symbol, config['tf_mt5'], start_date, end_date)
            
            if rates is None or len(rates) < 100:
                print(f"  !  {symbol:<12} - Insufficient data")
                continue
            
            bars_df = pd.DataFrame(rates)
            result = simulate_ema_crossover(bars_df, config['fast_ema'], config['slow_ema'])
            
            month_total += result['total_pnl']
            period_results[month_name][symbol] = result['total_pnl']
            
            status = "+" if result['total_pnl'] > 0 else "-"
            print(f"  {status} {symbol:<12} {config['timeframe']:<4} {config['fast_ema']:>2}/{config['slow_ema']:<2} | "
                  f"{result['total_trades']:>3} trades | {result['win_rate']:>5.1f}% | "
                  f"PnL: {result['total_pnl']:>+9.2f}")
            
            all_results.append({
                'month': month_name,
                'symbol': symbol,
                'timeframe': config['timeframe'],
                'fast_ema': config['fast_ema'],
                'slow_ema': config['slow_ema'],
                'trades': result['total_trades'],
                'win_rate': result['win_rate'],
                'pnl': result['total_pnl']
            })
        
        print(f"  {'─'*76}")
        print(f"  {month_name} Total: {month_total:>+10.2f}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY BY MONTH")
    print("="*80)
    
    monthly_totals = {}
    for month_name, _, _ in PERIODS:
        month_total = sum(period_results[month_name].values())
        monthly_totals[month_name] = month_total
        status = "+" if month_total > 0 else "-"
        print(f"{status} {month_name:<12} {month_total:>+10.2f}")
    
    grand_total = sum(monthly_totals.values())
    print(f"{'─'*80}")
    print(f"   {'GRAND TOTAL':<12} {grand_total:>+10.2f}")
    
    # Save to CSV
    csv_filename = "backtest_odd_months_2025.csv"
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'month', 'symbol', 'timeframe', 'fast_ema', 'slow_ema',
            'trades', 'win_rate', 'pnl'
        ])
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\nResults saved to: {csv_filename}")
    
    # Symbol performance across all months
    print("\n" + "="*80)
    print("SYMBOL PERFORMANCE (Across All Odd Months)")
    print("="*80)
    
    symbol_totals = {}
    for symbol in CURRENT_CONFIG.keys():
        if not CURRENT_CONFIG[symbol].get('enabled', True):
            continue
        total = sum(period_results[month].get(symbol, 0) for month, _, _ in PERIODS)
        symbol_totals[symbol] = total
    
    for symbol, total in sorted(symbol_totals.items(), key=lambda x: x[1], reverse=True):
        status = "+" if total > 0 else "-"
        print(f"{status} {symbol:<12} {total:>+10.2f}")
    
    mt5.shutdown()
    print("\nBacktest Complete!")
    
    return grand_total


if __name__ == "__main__":
    run_backtest()
