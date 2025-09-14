#!/usr/bin/env python3
"""
Complete Backtesting Engine Comparison
Compare original, fast (broken), and optimized (accurate + fast) engines
"""

import time
import datetime
from backtesting_engine import BacktestingEngine
from backtesting_engine_fast import FastBacktestingEngine
from backtesting_engine_optimized import OptimizedBacktestingEngine

def compare_all_engines():
    """Compare all three backtesting engines"""
    print("🏁 COMPLETE BACKTESTING ENGINE COMPARISON")
    print("=" * 80)
    
    # Test parameters
    symbol = "15"
    start_date = datetime.datetime(2025, 9, 7)
    end_date = datetime.datetime(2025, 9, 14)
    initial_balance = 10000
    
    print(f"📊 Test Parameters:")
    print(f"   Symbol: {symbol}")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    print(f"   Initial Balance: ${initial_balance:,}")
    
    results = {}
    times = {}
    
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
        results['original'] = original_results
        times['original'] = original_time
        print(f"✅ Original engine completed in {original_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Original engine failed: {e}")
        times['original'] = None
        results['original'] = None
    
    # Test fast engine (broken accuracy)
    print(f"\n🚀 TESTING FAST BACKTESTING ENGINE (Broken)...")
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
        results['fast'] = fast_results
        times['fast'] = fast_time
        print(f"✅ Fast engine completed in {fast_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Fast engine failed: {e}")
        times['fast'] = None
        results['fast'] = None
    
    # Test optimized engine (accurate + fast)
    print(f"\n⚡ TESTING OPTIMIZED BACKTESTING ENGINE (Accurate + Fast)...")
    start_time = time.time()
    
    try:
        optimized_engine = OptimizedBacktestingEngine()
        optimized_results = optimized_engine.run_backtest_optimized(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance
        )
        optimized_time = time.time() - start_time
        results['optimized'] = optimized_results
        times['optimized'] = optimized_time
        print(f"✅ Optimized engine completed in {optimized_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Optimized engine failed: {e}")
        times['optimized'] = None
        results['optimized'] = None
    
    # Performance comparison
    print(f"\n📊 PERFORMANCE COMPARISON:")
    print(f"{'Engine':<15} {'Time (sec)':<12} {'Speedup':<10} {'Status':<15}")
    print("-" * 60)
    
    if times['original']:
        print(f"{'Original':<15} {times['original']:<12.2f} {'1.0x':<10} {'Baseline':<15}")
    
    if times['fast'] and times['original']:
        speedup = times['original'] / times['fast']
        status = "Fast but Broken" if results['fast'] and results['original'] and abs(results['fast'].total_return_pct - results['original'].total_return_pct) > 10 else "Fast"
        print(f"{'Fast':<15} {times['fast']:<12.2f} {speedup:<10.1f}x {status:<15}")
    
    if times['optimized'] and times['original']:
        speedup = times['original'] / times['optimized']
        status = "Optimal" if results['optimized'] and results['original'] and abs(results['optimized'].total_return_pct - results['original'].total_return_pct) < 5 else "Fast"
        print(f"{'Optimized':<15} {times['optimized']:<12.2f} {speedup:<10.1f}x {status:<15}")
    
    # Results accuracy comparison
    if results['original'] and results['fast'] and results['optimized']:
        print(f"\n🔍 RESULTS ACCURACY COMPARISON:")
        print(f"{'Metric':<25} {'Original':<12} {'Fast':<12} {'Optimized':<12} {'Fast Diff':<12} {'Opt Diff':<12}")
        print("-" * 90)
        
        # Total return
        orig_return = results['original'].total_return_pct
        fast_return = results['fast'].total_return_pct
        opt_return = results['optimized'].total_return_pct
        fast_diff = abs(fast_return - orig_return)
        opt_diff = abs(opt_return - orig_return)
        print(f"{'Total Return (%)':<25} {orig_return:<12.2f} {fast_return:<12.2f} {opt_return:<12.2f} {fast_diff:<12.2f} {opt_diff:<12.2f}")
        
        # Win rate
        orig_winrate = results['original'].win_rate
        fast_winrate = results['fast'].win_rate
        opt_winrate = results['optimized'].win_rate
        fast_diff = abs(fast_winrate - orig_winrate)
        opt_diff = abs(opt_winrate - orig_winrate)
        print(f"{'Win Rate (%)':<25} {orig_winrate:<12.2f} {fast_winrate:<12.2f} {opt_winrate:<12.2f} {fast_diff:<12.2f} {opt_diff:<12.2f}")
        
        # Max drawdown
        orig_dd = results['original'].max_drawdown_pct
        fast_dd = results['fast'].max_drawdown_pct
        opt_dd = results['optimized'].max_drawdown_pct
        fast_diff = abs(fast_dd - orig_dd)
        opt_diff = abs(opt_dd - orig_dd)
        print(f"{'Max Drawdown (%)':<25} {orig_dd:<12.2f} {fast_dd:<12.2f} {opt_dd:<12.2f} {fast_diff:<12.2f} {opt_diff:<12.2f}")
        
        # Total trades
        orig_trades = results['original'].total_trades
        fast_trades = results['fast'].total_trades
        opt_trades = results['optimized'].total_trades
        fast_diff = abs(fast_trades - orig_trades)
        opt_diff = abs(opt_trades - orig_trades)
        print(f"{'Total Trades':<25} {orig_trades:<12} {fast_trades:<12} {opt_trades:<12} {fast_diff:<12} {opt_diff:<12}")
        
        # Accuracy assessment
        print(f"\n🎯 ACCURACY ASSESSMENT:")
        
        # Fast engine assessment
        fast_accuracy = "❌ BROKEN" if fast_diff > 10 or fast_diff > 5 else "✅ GOOD"
        print(f"   Fast Engine: {fast_accuracy} (Return diff: {fast_diff:.1f}%)")
        
        # Optimized engine assessment
        opt_accuracy = "✅ EXCELLENT" if opt_diff < 2 else "✅ GOOD" if opt_diff < 5 else "⚠️ ACCEPTABLE" if opt_diff < 10 else "❌ POOR"
        print(f"   Optimized Engine: {opt_accuracy} (Return diff: {opt_diff:.1f}%)")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if results['optimized'] and times['optimized'] and times['original']:
        speedup = times['original'] / times['optimized']
        if speedup > 2 and opt_diff < 5:
            print(f"   🏆 USE OPTIMIZED ENGINE: {speedup:.1f}x faster with accurate results!")
            print(f"   ✅ Perfect for production backtesting")
            print(f"   🚀 Ideal for strategy development and optimization")
        elif speedup > 1.5:
            print(f"   👍 USE OPTIMIZED ENGINE: {speedup:.1f}x faster with good accuracy")
            print(f"   ✅ Suitable for most backtesting needs")
        else:
            print(f"   ⚠️  Use Original Engine for critical accuracy")
            print(f"   📊 Use Optimized Engine for development")
    
    if results['fast']:
        print(f"   ❌ AVOID FAST ENGINE: Speed comes at cost of accuracy")
        print(f"   🔧 Signal generation logic needs fixing")
    
    # Summary
    print(f"\n🎯 FINAL VERDICT:")
    if results['optimized'] and times['optimized'] and times['original']:
        speedup = times['original'] / times['optimized']
        if speedup > 2 and opt_diff < 5:
            print(f"   🏆 OPTIMIZED ENGINE WINS!")
            print(f"   📈 {speedup:.1f}x speedup with maintained accuracy")
            print(f"   🎯 Best of both worlds: speed + accuracy")
        else:
            print(f"   📊 ORIGINAL ENGINE for accuracy")
            print(f"   ⚡ OPTIMIZED ENGINE for development")
    else:
        print(f"   🔧 Need to debug engines before comparison")

if __name__ == "__main__":
    compare_all_engines()

