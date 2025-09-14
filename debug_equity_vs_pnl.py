#!/usr/bin/env python3
"""
Debug Equity vs P&L Discrepancy
Investigate why equity curve shows different values than cumulative P&L
"""

import pandas as pd
import numpy as np
from backtesting_engine_optimized import OptimizedBacktestingEngine
from datetime import datetime

def debug_equity_vs_pnl():
    """Debug the discrepancy between equity curve and cumulative P&L"""
    print("🔍 DEBUGGING EQUITY vs P&L DISCREPANCY")
    print("=" * 60)
    
    # Initialize backtesting engine
    engine = OptimizedBacktestingEngine()
    
    # Run a quick backtest
    print("Running backtest...")
    results = engine.run_backtest_optimized(
        symbol="15",
        start_date=datetime(2025, 9, 7),
        end_date=datetime(2025, 9, 14),
        initial_balance=10000
    )
    
    print(f"\n📊 TRADE ANALYSIS:")
    print(f"Total trades: {len(results.trades)}")
    
    # Analyze cumulative P&L from trades
    cumulative_pnl = 0
    min_cumulative_pnl = 0
    max_cumulative_pnl = 0
    
    print(f"\n📋 CUMULATIVE P&L TRACKING:")
    print(f"{'Trade':<5} {'P&L':<10} {'Cumulative':<12} {'Min':<10} {'Max':<10}")
    print("-" * 60)
    
    for i, trade in enumerate(results.trades):
        cumulative_pnl += trade.pnl
        min_cumulative_pnl = min(min_cumulative_pnl, cumulative_pnl)
        max_cumulative_pnl = max(max_cumulative_pnl, cumulative_pnl)
        
        if i < 10 or i >= len(results.trades) - 5:  # Show first 10 and last 5
            print(f"{i+1:<5} ${trade.pnl:<9.1f} ${cumulative_pnl:<11.1f} ${min_cumulative_pnl:<9.1f} ${max_cumulative_pnl:<9.1f}")
        elif i == 10:
            print("... (middle trades omitted)")
    
    print(f"\n📊 CUMULATIVE P&L SUMMARY:")
    print(f"Final cumulative P&L: ${cumulative_pnl:.2f}")
    print(f"Minimum cumulative P&L: ${min_cumulative_pnl:.2f}")
    print(f"Maximum cumulative P&L: ${max_cumulative_pnl:.2f}")
    
    # Analyze equity curve
    print(f"\n📊 EQUITY CURVE ANALYSIS:")
    equity_df = pd.DataFrame(engine.equity_curve)
    
    if not equity_df.empty:
        equity_min = equity_df['equity'].min()
        equity_max = equity_df['equity'].max()
        balance_min = equity_df['balance'].min()
        balance_max = equity_df['balance'].max()
        
        print(f"Equity min: ${equity_min:.2f}")
        print(f"Equity max: ${equity_max:.2f}")
        print(f"Balance min: ${balance_min:.2f}")
        print(f"Balance max: ${balance_max:.2f}")
        
        # Find when equity was at minimum
        min_equity_idx = equity_df['equity'].idxmin()
        min_equity_row = equity_df.iloc[min_equity_idx]
        
        print(f"\n🔍 MINIMUM EQUITY DETAILS:")
        print(f"Timestamp: {min_equity_row['timestamp']}")
        print(f"Equity: ${min_equity_row['equity']:.2f}")
        print(f"Balance: ${min_equity_row['balance']:.2f}")
        print(f"Drawdown: {min_equity_row['drawdown']:.4f}")
        
        # Check for unrealized P&L during minimum equity
        print(f"\n🔍 UNREALIZED P&L ANALYSIS:")
        unrealized_pnl = min_equity_row['equity'] - min_equity_row['balance']
        print(f"Unrealized P&L at minimum: ${unrealized_pnl:.2f}")
        
        # Show equity curve around minimum
        print(f"\n📋 EQUITY CURVE AROUND MINIMUM:")
        start_idx = max(0, min_equity_idx - 5)
        end_idx = min(len(equity_df), min_equity_idx + 6)
        
        for i in range(start_idx, end_idx):
            row = equity_df.iloc[i]
            marker = " <-- MIN" if i == min_equity_idx else ""
            print(f"  {row['timestamp']}: Equity=${row['equity']:.2f}, Balance=${row['balance']:.2f}{marker}")
    
    # Compare with trade results
    print(f"\n🔍 COMPARISON ANALYSIS:")
    print(f"Trade table shows minimum cumulative P&L: ${min_cumulative_pnl:.2f}")
    print(f"Equity curve shows minimum equity: ${equity_min:.2f}")
    print(f"Initial balance: ${results.initial_balance:.2f}")
    
    # Calculate expected minimum equity
    expected_min_equity = results.initial_balance + min_cumulative_pnl
    print(f"Expected minimum equity (balance + min P&L): ${expected_min_equity:.2f}")
    
    difference = equity_min - expected_min_equity
    print(f"Difference: ${difference:.2f}")
    
    if abs(difference) > 100:  # Significant difference
        print(f"⚠️  SIGNIFICANT DISCREPANCY FOUND!")
        print(f"This suggests unrealized P&L is affecting equity calculation")
    else:
        print(f"✅ Equity and P&L are consistent")

if __name__ == "__main__":
    debug_equity_vs_pnl()
