#!/usr/bin/env python3
"""
Debug Max Drawdown Calculation
Investigate why max drawdown is showing 2745%
"""

import pandas as pd
import numpy as np
from backtesting_engine_optimized import OptimizedBacktestingEngine
from datetime import datetime

def debug_drawdown_calculation():
    """Debug the max drawdown calculation"""
    print("🔍 DEBUGGING MAX DRAWDOWN CALCULATION")
    print("=" * 50)
    
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
    
    print(f"\n📊 BACKTEST RESULTS:")
    print(f"Initial Balance: ${results.initial_balance:,.2f}")
    print(f"Final Balance: ${results.final_balance:,.2f}")
    print(f"Max Drawdown: {results.max_drawdown_pct:.2f}%")
    
    # Debug the equity curve
    print(f"\n🔍 EQUITY CURVE DEBUG:")
    equity_df = pd.DataFrame(engine.equity_curve)
    
    if not equity_df.empty:
        print(f"Equity curve records: {len(equity_df)}")
        print(f"First 5 equity values:")
        for i, row in equity_df.head().iterrows():
            print(f"  {row['timestamp']}: Balance=${row['balance']:.2f}, Equity=${row['equity']:.2f}")
        
        print(f"\nLast 5 equity values:")
        for i, row in equity_df.tail().iterrows():
            print(f"  {row['timestamp']}: Balance=${row['balance']:.2f}, Equity=${row['equity']:.2f}")
        
        # Check for negative equity values
        negative_equity = equity_df[equity_df['equity'] < 0]
        if not negative_equity.empty:
            print(f"\n⚠️  NEGATIVE EQUITY FOUND:")
            print(f"Records with negative equity: {len(negative_equity)}")
            for i, row in negative_equity.head().iterrows():
                print(f"  {row['timestamp']}: Equity=${row['equity']:.2f}")
        else:
            print(f"\n✅ No negative equity values found")
        
        # Check for extremely large equity values
        large_equity = equity_df[equity_df['equity'] > 50000]
        if not large_equity.empty:
            print(f"\n⚠️  EXTREMELY LARGE EQUITY FOUND:")
            print(f"Records with equity > $50,000: {len(large_equity)}")
            for i, row in large_equity.head().iterrows():
                print(f"  {row['timestamp']}: Equity=${row['equity']:.2f}")
        
        # Manual drawdown calculation - using balance (realized P&L)
        print(f"\n🧮 MANUAL DRAWDOWN CALCULATION:")
        balance = equity_df['balance']
        running_max = balance.expanding().max()
        
        print(f"Balance min: ${balance.min():.2f}")
        print(f"Balance max: ${balance.max():.2f}")
        print(f"Running max min: ${running_max.min():.2f}")
        print(f"Running max max: ${running_max.max():.2f}")
        
        # Calculate drawdown manually using balance
        drawdown = (balance - running_max) / running_max
        max_drawdown = drawdown.min()
        max_drawdown_pct = abs(max_drawdown) * 100
        
        print(f"Max drawdown (manual): {max_drawdown:.6f}")
        print(f"Max drawdown % (manual): {max_drawdown_pct:.2f}%")
        
        # Check for problematic values
        print(f"\n🔍 PROBLEMATIC VALUES CHECK:")
        print(f"Drawdown min: {drawdown.min():.6f}")
        print(f"Drawdown max: {drawdown.max():.6f}")
        
        # Find the worst drawdown period
        worst_dd_idx = drawdown.idxmin()
        worst_balance = balance.iloc[worst_dd_idx]
        worst_running_max = running_max.iloc[worst_dd_idx]
        
        print(f"Worst drawdown at index {worst_dd_idx}:")
        print(f"  Balance: ${worst_balance:.2f}")
        print(f"  Running max: ${worst_running_max:.2f}")
        print(f"  Drawdown: {((worst_balance - worst_running_max) / worst_running_max * 100):.2f}%")
        
        # Check if there are any zero or near-zero running max values
        zero_running_max = running_max[running_max <= 0.01]
        if not zero_running_max.empty:
            print(f"\n⚠️  ZERO/NEAR-ZERO RUNNING MAX FOUND:")
            print(f"Records with running max <= $0.01: {len(zero_running_max)}")
            for i, row in zero_running_max.head().iterrows():
                print(f"  Index {i}: Running max=${row:.2f}")
        
    else:
        print("❌ No equity curve data found!")

if __name__ == "__main__":
    debug_drawdown_calculation()
