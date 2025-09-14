#!/usr/bin/env python3
"""
Main Backtesting Script
Complete backtesting workflow using stored data from Z: drive
"""

import os
import sys
import json
import datetime
from datetime import timedelta
from typing import Dict, List
from data_loader import DataLoader
from backtesting_engine_optimized import OptimizedBacktestingEngine
from backtest_analyzer import BacktestAnalyzer

def main():
    """Main backtesting workflow"""
    print("🚀 COMPREHENSIVE BACKTESTING SYSTEM")
    print("=" * 50)
    
    # Configuration
    data_directory = "Z:\\"
    config_file = "trading_config.json"
    initial_balance = 10000
    
    # Create output directory
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f"backtest_results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    print(f"💰 Initial balance: ${initial_balance:,}")
    print(f"📊 Data directory: {data_directory}")
    
    # Step 1: Analyze available data
    print(f"\n📋 STEP 1: ANALYZING AVAILABLE DATA")
    print("-" * 30)
    
    data_loader = DataLoader(data_directory)
    summary = data_loader.get_data_summary()
    
    print(f"Found {summary['total_files']} data files:")
    available_symbols = []
    
    for file_info in summary['files']:
        filename = file_info['filename']
        size_mb = file_info['size_mb']
        
        # Extract symbol from filename
        if '_' in filename:
            symbol = filename.split('_')[0].upper()
        else:
            symbol = filename.split('.')[0].upper()
        
        available_symbols.append(symbol)
        print(f"  📄 {filename} ({size_mb:.1f} MB) -> {symbol}")
    
    if not available_symbols:
        print("❌ No data files found!")
        return
    
    # Step 2: Select symbols and timeframes
    print(f"\n⚙️  STEP 2: CONFIGURATION")
    print("-" * 30)
    
    # Load or create configuration
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"✅ Loaded configuration from {config_file}")
    except FileNotFoundError:
        print(f"⚠️  Configuration file {config_file} not found. Using default settings.")
        config = {
            "symbols": {"primary": available_symbols[0]},
            "timeframe": "H1",
            "indicators": {
                "sma": {"enabled": True, "periods": [20, 50], "weight": 0.15},
                "rsi": {"enabled": True, "period": 14, "weight": 0.20}
            },
            "risk_management": {
                "position_sizing": {"risk_per_trade": 0.02}
            }
        }
    
    # Select symbols to backtest
    symbols_to_test = [available_symbols[0]]  # Start with first available
    
    # Show timeframe options
    timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
    selected_timeframe = config.get('timeframe', 'H1')
    print(f"📈 Selected timeframe: {selected_timeframe}")
    
    # Step 3: Set backtest parameters
    print(f"\n🔧 STEP 3: BACKTEST PARAMETERS")
    print("-" * 30)
    
    # Date range (last 30 days by default)
    end_date = datetime.datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"💵 Initial balance: ${initial_balance:,}")
    
    # Execution parameters
    commission = 0.0  # Commission per lot
    slippage = 0.5    # Slippage in pips
    spread = 2.0      # Spread in pips
    
    print(f"💸 Execution costs:")
    print(f"   Commission: ${commission} per lot")
    print(f"   Slippage: {slippage} pips")
    print(f"   Spread: {spread} pips")
    
    # Step 4: Run backtests
    print(f"\n🏃 STEP 4: RUNNING BACKTESTS")
    print("-" * 30)
    
    all_results = {}
    
    for symbol in symbols_to_test:
        print(f"\n🔄 Backtesting {symbol}...")
        
        try:
            # Create backtesting engine
            engine = BacktestingEngine(config_file, data_directory)
            engine.set_execution_parameters(commission, slippage, spread)
            
            # Run backtest
            results = engine.run_backtest_optimized(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_balance=initial_balance
            )
            
            all_results[symbol] = results
            
            # Save individual results
            results_file = os.path.join(output_dir, f"{symbol}_results.json")
            engine.save_results(results, results_file)
            
            print(f"✅ {symbol} backtest completed")
            print(f"   Final balance: ${results.final_balance:,.2f}")
            print(f"   Total return: {results.total_return_pct:.2f}%")
            print(f"   Total trades: {results.total_trades}")
            print(f"   Win rate: {results.win_rate:.2f}%")
            
        except Exception as e:
            print(f"❌ Error backtesting {symbol}: {e}")
            continue
    
    if not all_results:
        print("❌ No successful backtests completed!")
        return
    
    # Step 5: Analyze results
    print(f"\n📊 STEP 5: ANALYZING RESULTS")
    print("-" * 30)
    
    for symbol, results in all_results.items():
        print(f"\n🔍 Analyzing {symbol} results...")
        
        try:
            # Create analyzer
            analyzer = BacktestAnalyzer(results)
            
            # Print summary
            analyzer.print_summary()
            
            # Create visualizations
            print(f"📈 Creating visualizations for {symbol}...")
            plot_files = analyzer.create_visualizations(save_plots=True, output_dir=output_dir)
            print(f"   Saved {len(plot_files)} plot files")
            
            # Export detailed report
            report_file = os.path.join(output_dir, f"{symbol}_analysis.json")
            analyzer.export_detailed_report(report_file)
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
    
    # Step 6: Portfolio-level analysis
    print(f"\n🎯 STEP 6: PORTFOLIO ANALYSIS")
    print("-" * 30)
    
    if len(all_results) > 1:
        # Calculate portfolio metrics
        total_initial = sum(r.initial_balance for r in all_results.values())
        total_final = sum(r.final_balance for r in all_results.values())
        total_return = ((total_final - total_initial) / total_initial) * 100
        
        print(f"📊 Portfolio Summary:")
        print(f"   Total initial balance: ${total_initial:,.2f}")
        print(f"   Total final balance:   ${total_final:,.2f}")
        print(f"   Portfolio return:      {total_return:.2f}%")
        
        # Best and worst performers
        returns = {symbol: r.total_return_pct for symbol, r in all_results.items()}
        best_symbol = max(returns, key=returns.get)
        worst_symbol = min(returns, key=returns.get)
        
        print(f"   Best performer:       {best_symbol} ({returns[best_symbol]:.2f}%)")
        print(f"   Worst performer:      {worst_symbol} ({returns[worst_symbol]:.2f}%)")
    
    # Step 7: Generate final report
    print(f"\n📋 STEP 7: FINAL REPORT")
    print("-" * 30)
    
    # Create summary report
    summary_report = {
        "backtest_info": {
            "timestamp": timestamp,
            "data_directory": data_directory,
            "config_file": config_file,
            "initial_balance": initial_balance,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "execution_parameters": {
                "commission": commission,
                "slippage": slippage,
                "spread": spread
            }
        },
        "symbols_tested": list(all_results.keys()),
        "results_summary": {}
    }
    
    for symbol, results in all_results.items():
        summary_report["results_summary"][symbol] = {
            "initial_balance": results.initial_balance,
            "final_balance": results.final_balance,
            "total_return_pct": results.total_return_pct,
            "total_trades": results.total_trades,
            "win_rate": results.win_rate,
            "profit_factor": results.profit_factor,
            "max_drawdown_pct": results.max_drawdown_pct,
            "sharpe_ratio": results.sharpe_ratio
        }
    
    # Save summary report
    summary_file = os.path.join(output_dir, "backtest_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary_report, f, indent=2)
    
    print(f"✅ Summary report saved: {summary_file}")
    
    # Final summary
    print(f"\n🎉 BACKTESTING COMPLETED!")
    print("=" * 50)
    print(f"📁 All results saved to: {output_dir}")
    print(f"📊 Symbols tested: {len(all_results)}")
    
    # Show best performing strategy
    if all_results:
        best_symbol = max(all_results.keys(), key=lambda s: all_results[s].total_return_pct)
        best_return = all_results[best_symbol].total_return_pct
        print(f"🏆 Best performer: {best_symbol} ({best_return:.2f}% return)")
    
    print(f"\n📈 Generated files:")
    print(f"   📄 Individual results: {symbol}_results.json")
    print(f"   📊 Analysis reports: {symbol}_analysis.json")
    print(f"   📈 Visualization plots: *.png files")
    print(f"   📋 Summary report: backtest_summary.json")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Review the generated plots and reports")
    print(f"   2. Analyze performance metrics")
    print(f"   3. Adjust strategy parameters if needed")
    print(f"   4. Run additional backtests with different timeframes")
    print(f"   5. Consider forward testing with paper trading")

def run_quick_backtest():
    """Quick backtest for demonstration"""
    print("🚀 QUICK BACKTEST DEMO")
    print("=" * 30)
    
    # Find available data
    data_loader = DataLoader("Z:\\")
    files = data_loader.list_available_files()
    
    if not files:
        print("❌ No data files found on Z: drive!")
        return
    
    # Use first available file
    sample_file = files[0]
    symbol = os.path.basename(sample_file).split('_')[0].upper()
    
    print(f"📊 Testing symbol: {symbol}")
    print(f"📁 Data file: {os.path.basename(sample_file)}")
    
    # Create engine and run quick backtest
    engine = OptimizedBacktestingEngine()
    engine.set_execution_parameters(commission=0.0, slippage=0.5, spread=2.0)
    
    try:
        # Run backtest for last 7 days
        end_date = datetime.datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"📅 Testing period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        results = engine.run_backtest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=10000
        )
        
        # Quick analysis
        analyzer = BacktestAnalyzer(results)
        analyzer.print_summary()
        
        print(f"\n✅ Quick backtest completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running quick backtest: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_quick_backtest()
    else:
        main()
