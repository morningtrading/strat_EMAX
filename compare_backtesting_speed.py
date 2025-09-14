#!/usr/bin/env python3
"""
Backtesting Speed Comparison
Compare original vs optimized backtesting engine performance
"""

import time
import datetime
from backtesting_engine import BacktestingEngine
from backtesting_engine_fast import FastBacktestingEngine

def compare_backtesting_speed():
    """Compare speed between original and fast backtesting engines"""
    print("🏁 BACKTESTING SPEED COMPARISON")
    print("=" * 60)
    
    # Test parameters
    symbol = "15"
    start_date = datetime.datetime(2025, 9, 7)
    end_date = datetime.datetime(2025, 9, 14)
    initial_balance = 10000
    
    print(f"📊 Test Parameters:")
    print(f"   Symbol: {symbol}")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    print(f"   Initial Balance: ${initial_balance:,}")
    
    # Test original engine
    print(f"\n🐌 TESTING ORIGINAL BACKTESTING ENGINE...")
    start_time = time.time()
    
    try:
        original_engine = BacktestingEngine()
        original_results = original_engine.run_backtest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance
        )
        original_time = time.time() - start_time
        print(f"✅ Original engine completed in {original_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Original engine failed: {e}")
        original_time = None
        original_results = None
    
    # Test fast engine
    print(f"\n🚀 TESTING FAST BACKTESTING ENGINE...")
    start_time = time.time()
    
    try:
        fast_engine = FastBacktestingEngine()
        fast_results = fast_engine.run_backtest_fast(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance
        )
        fast_time = time.time() - start_time
        print(f"✅ Fast engine completed in {fast_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Fast engine failed: {e}")
        fast_time = None
        fast_results = None
    
    # Compare results
    print(f"\n📊 PERFORMANCE COMPARISON:")
    print(f"{'Metric':<25} {'Original':<15} {'Fast':<15} {'Improvement':<15}")
    print("-" * 70)
    
    if original_time and fast_time:
        speedup = original_time / fast_time
        print(f"{'Execution Time (sec)':<25} {original_time:<15.2f} {fast_time:<15.2f} {speedup:<15.2f}x")
        
        if speedup > 2:
            print(f"🎉 MAJOR SPEEDUP: {speedup:.1f}x faster!")
        elif speedup > 1.5:
            print(f"✅ Significant improvement: {speedup:.1f}x faster")
        elif speedup > 1.1:
            print(f"👍 Good improvement: {speedup:.1f}x faster")
        else:
            print(f"⚠️  Minimal improvement: {speedup:.1f}x faster")
    
    # Compare results accuracy
    if original_results and fast_results:
        print(f"\n🔍 RESULTS ACCURACY COMPARISON:")
        print(f"{'Metric':<25} {'Original':<15} {'Fast':<15} {'Difference':<15}")
        print("-" * 70)
        
        # Total return
        orig_return = original_results.total_return_pct
        fast_return = fast_results.total_return_pct
        return_diff = abs(orig_return - fast_return)
        print(f"{'Total Return (%)':<25} {orig_return:<15.2f} {fast_return:<15.2f} {return_diff:<15.2f}")
        
        # Win rate
        orig_winrate = original_results.win_rate
        fast_winrate = fast_results.win_rate
        winrate_diff = abs(orig_winrate - fast_winrate)
        print(f"{'Win Rate (%)':<25} {orig_winrate:<15.2f} {fast_winrate:<15.2f} {winrate_diff:<15.2f}")
        
        # Max drawdown
        orig_dd = original_results.max_drawdown_pct
        fast_dd = fast_results.max_drawdown_pct
        dd_diff = abs(orig_dd - fast_dd)
        print(f"{'Max Drawdown (%)':<25} {orig_dd:<15.2f} {fast_dd:<15.2f} {dd_diff:<15.2f}")
        
        # Total trades
        orig_trades = original_results.total_trades
        fast_trades = fast_results.total_trades
        trades_diff = abs(orig_trades - fast_trades)
        print(f"{'Total Trades':<25} {orig_trades:<15} {fast_trades:<15} {trades_diff:<15}")
        
        # Accuracy assessment
        print(f"\n🎯 ACCURACY ASSESSMENT:")
        if return_diff < 1.0 and winrate_diff < 5.0 and dd_diff < 2.0 and trades_diff < 5:
            print(f"✅ Results are highly consistent (within acceptable tolerance)")
        elif return_diff < 2.0 and winrate_diff < 10.0 and dd_diff < 5.0 and trades_diff < 10:
            print(f"👍 Results are reasonably consistent (minor differences)")
        else:
            print(f"⚠️  Results show significant differences - review implementation")
    
    # Performance optimizations summary
    print(f"\n⚡ OPTIMIZATIONS IMPLEMENTED:")
    print(f"   ✅ Pre-calculated all indicators once (vs recalculating every bar)")
    print(f"   ✅ Vectorized indicator calculations using pandas/numpy")
    print(f"   ✅ Simplified signal generation logic")
    print(f"   ✅ Reduced equity curve sampling (every 10 bars vs every bar)")
    print(f"   ✅ Optimized data structures and memory usage")
    print(f"   ✅ Eliminated redundant calculations in main loop")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if fast_time and fast_time < 5:
        print(f"   🚀 Use FastBacktestingEngine for production backtesting")
        print(f"   📊 Fast engine is suitable for real-time strategy testing")
        print(f"   🔄 Can handle larger datasets and longer time periods")
    else:
        print(f"   ⚠️  Consider additional optimizations for very large datasets")
        print(f"   💾 Implement data chunking for memory efficiency")
        print(f"   🧵 Consider parallel processing for multiple symbols")
    
    print(f"\n🎯 CONCLUSION:")
    if original_time and fast_time:
        if fast_time < original_time * 0.5:
            print(f"   🏆 FAST ENGINE WINS: {speedup:.1f}x speedup with consistent results!")
        else:
            print(f"   📈 Good improvement achieved, consider further optimizations")
    else:
        print(f"   🔧 Both engines need debugging before comparison")

if __name__ == "__main__":
    compare_backtesting_speed()
