#!/usr/bin/env python3
"""Compare original vs optimized settings on January 2025 validation data"""

import csv
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

# Original config (before optimization)
ORIGINAL_CONFIG = {
    'XAUUSD': {'timeframe': 'H1', 'fast_ema': 5, 'slow_ema': 55, 'tf_mt5': mt5.TIMEFRAME_H1},
    'US2000': {'timeframe': 'H1', 'fast_ema': 15, 'slow_ema': 40, 'tf_mt5': mt5.TIMEFRAME_H1},
    'SP500ft': {'timeframe': 'M15', 'fast_ema': 19, 'slow_ema': 55, 'tf_mt5': mt5.TIMEFRAME_M15},
    'NAS100ft': {'timeframe': 'M5', 'fast_ema': 12, 'slow_ema': 60, 'tf_mt5': mt5.TIMEFRAME_M5},
    'GER40ft': {'timeframe': 'H1', 'fast_ema': 10, 'slow_ema': 30, 'tf_mt5': mt5.TIMEFRAME_H1}
}

# Optimized config
OPTIMIZED_CONFIG = {
    'XAUUSD': {'timeframe': 'H1', 'fast_ema': 19, 'slow_ema': 60, 'tf_mt5': mt5.TIMEFRAME_H1},
    'US2000': {'timeframe': 'M15', 'fast_ema': 20, 'slow_ema': 60, 'tf_mt5': mt5.TIMEFRAME_M15},
    'SP500ft': {'timeframe': 'H1', 'fast_ema': 5, 'slow_ema': 40, 'tf_mt5': mt5.TIMEFRAME_H1},
    'NAS100ft': {'timeframe': 'M5', 'fast_ema': 11, 'slow_ema': 50, 'tf_mt5': mt5.TIMEFRAME_M5},
    'GER40ft': {'timeframe': 'M15', 'fast_ema': 7, 'slow_ema': 35, 'tf_mt5': mt5.TIMEFRAME_M15}
}

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 1, 22, 23, 59, 59)
SPREAD_COST = 2

def calculate_ema(prices, period):
    ema = np.zeros_like(prices)
    multiplier = 2 / (period + 1)
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
    return ema

def simulate_ema_crossover(bars, fast_period, slow_period):
    if len(bars) < slow_period + 10:
        return {'total_trades': 0, 'winning_trades': 0, 'total_pnl': 0, 'win_rate': 0}
    
    closes = bars['close'].values
    fast_ema = calculate_ema(closes, fast_period)
    slow_ema = calculate_ema(closes, slow_period)
    
    trades = []
    position = None
    entry_price = 0
    
    for i in range(slow_period, len(bars)):
        prev_fast, prev_slow = fast_ema[i-1], slow_ema[i-1]
        curr_fast, curr_slow = fast_ema[i], slow_ema[i]
        
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            if position == 'SHORT':
                trades.append(entry_price - closes[i] - SPREAD_COST)
            position = 'LONG'
            entry_price = closes[i]
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            if position == 'LONG':
                trades.append(closes[i] - entry_price - SPREAD_COST)
            position = 'SHORT'
            entry_price = closes[i]
    
    if position == 'LONG':
        trades.append(closes[-1] - entry_price - SPREAD_COST)
    elif position == 'SHORT':
        trades.append(entry_price - closes[-1] - SPREAD_COST)
    
    if not trades:
        return {'total_trades': 0, 'winning_trades': 0, 'total_pnl': 0, 'win_rate': 0}
    
    winning = sum(1 for t in trades if t > 0)
    return {
        'total_trades': len(trades),
        'winning_trades': winning,
        'total_pnl': sum(trades),
        'win_rate': (winning / len(trades)) * 100
    }

print("\nRunning comparison on January 2025 validation data...")
mt5.initialize()

print("\n" + "╔" + "═"*120 + "╗")
print("║" + " "*35 + "VALIDATION: Original vs Optimized Settings (Jan 2025)" + " "*30 + "║")
print("╠" + "═"*120 + "╣")
print("║ Symbol      │ Original Config  │ Orig PnL  │ Orig Trades │ Optimized Config │ Opt PnL   │ Opt Trades │ Improvement    ║")
print("╠" + "═"*120 + "╣")

total_orig = 0
total_opt = 0

for symbol in ORIGINAL_CONFIG.keys():
    orig = ORIGINAL_CONFIG[symbol]
    opt = OPTIMIZED_CONFIG[symbol]
    
    # Get data for original config
    rates_orig = mt5.copy_rates_range(symbol, orig['tf_mt5'], START_DATE, END_DATE)
    if rates_orig is None or len(rates_orig) < 100:
        continue
    
    bars_orig = pd.DataFrame(rates_orig)
    result_orig = simulate_ema_crossover(bars_orig, orig['fast_ema'], orig['slow_ema'])
    
    # Get data for optimized config
    rates_opt = mt5.copy_rates_range(symbol, opt['tf_mt5'], START_DATE, END_DATE)
    if rates_opt is None or len(rates_opt) < 100:
        continue
    
    bars_opt = pd.DataFrame(rates_opt)
    result_opt = simulate_ema_crossover(bars_opt, opt['fast_ema'], opt['slow_ema'])
    
    total_orig += result_orig['total_pnl']
    total_opt += result_opt['total_pnl']
    
    orig_str = f"{orig['timeframe']} {orig['fast_ema']:>2}/{orig['slow_ema']:<2}"
    opt_str = f"{opt['timeframe']} {opt['fast_ema']:>2}/{opt['slow_ema']:<2}"
    
    diff = result_opt['total_pnl'] - result_orig['total_pnl']
    if diff > 0:
        imp = f"⬆ +{diff:.2f}"
    elif diff < 0:
        imp = f"⬇ {diff:.2f}"
    else:
        imp = "➡ 0.00"
    
    print(f"║ {symbol:<11} │ {orig_str:<16} │ {result_orig['total_pnl']:>8.2f} │ {result_orig['total_trades']:>11} │ {opt_str:<16} │ {result_opt['total_pnl']:>8.2f} │ {result_opt['total_trades']:>10} │ {imp:<14} ║")

print("╠" + "═"*120 + "╣")
total_diff = total_opt - total_orig
print(f"║ {'TOTAL':<11} │ {'':16} │ {total_orig:>8.2f} │ {'':11} │ {'':16} │ {total_opt:>8.2f} │ {'':10} │ {total_diff:>+8.2f}      ║")
print("╚" + "═"*120 + "╝")

print("\n📊 VALIDATION SUMMARY:")
print(f"   • Original config PnL:  {total_orig:>+10.2f}")
print(f"   • Optimized config PnL: {total_opt:>+10.2f}")
print(f"   • Change:               {total_diff:>+10.2f}")

if total_diff < 0:
    print(f"\n⚠️  WARNING: Optimized settings performed WORSE on validation data!")
    print(f"   This suggests the optimization may have overfit to the training periods.")
    print(f"   January 2025 had different market conditions than Mar-Aug & Oct-Dec 2025.")
    print(f"   Consider using more conservative settings or averaging across periods.")
else:
    print(f"\n✅ Optimized settings maintained positive performance on unseen data!")

mt5.shutdown()
