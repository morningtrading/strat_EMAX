
import os
import sys
import json
import csv
import logging
from datetime import datetime, timedelta
import pandas as pd

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.mt5_connector import MT5Connector
from core.ema_strategy import EMAStrategy, SignalType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backtest")

def run_backtest():
    print("="*80)
    print("🧪 CUSTOM BACKTEST: M1 Timeframe | EMA 9/35 | Last 12 Hours")
    print("="*80)
    
    # Initialize
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    # Configuration
    TEST_TIMEFRAME = "M5" # Updated to M5
    FAST_EMA = 9
    SLOW_EMA = 35
    LOOKBACK_HOURS = 12
    
    # Load Symbols
    try:
        with open('config/trading_config.json', 'r') as f:
            cfg = json.load(f)
            SYMBOLS = cfg.get('symbols', {}).get('enabled', [])
    except Exception as e:
        print(f"Config Error: {e}")
        return

    print(f"Symbols: {SYMBOLS}")
    print(f"Strategy: EMA {FAST_EMA}/{SLOW_EMA} on {TEST_TIMEFRAME}")
    
    overall_results = []
    
    for symbol in SYMBOLS:
        print(f"\nProcessing {symbol}...")
        
        # Calculate bars needed (12 hours * 12 bars/hr + buffer)
        count = (LOOKBACK_HOURS * 12) + 100 
        
        # Fetch Data
        bars = connector.get_rates(symbol, TEST_TIMEFRAME, count=count)
        if not bars:
            print(f"Skipping {symbol}: No data")
            continue
            
        # Prepare Dataframe
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'])
        closes = df['close'].tolist()
        
        # Calculate EMAs manually to ensure match
        strategy = EMAStrategy()
        # Hack strategy params via internal method or just use helper
        fast_ema = strategy.calculate_ema(closes, FAST_EMA)
        slow_ema = strategy.calculate_ema(closes, SLOW_EMA)
        
        df['fast_ema'] = fast_ema
        df['slow_ema'] = slow_ema
        
        # Simulation State
        position = None # {direction, price, time, sl}
        trades = []
        equity_curve = []
        
        # Spread cost estimation (need symbol info)
        info = connector.get_symbol_info(symbol)
        spread_cost = (info.get('spread', 10) * info.get('point', 0.00001)) if info else 0.0001
        
        # Iterate bar by bar (starting after sufficient history)
        start_idx = SLOW_EMA + 2
        
        for i in range(start_idx, len(df)):
            curr_bar = df.iloc[i]
            prev_bar = df.iloc[i-1]
            
            # --- SIGNALS ---
            c_fast, c_slow = curr_bar['fast_ema'], curr_bar['slow_ema']
            p_fast, p_slow = prev_bar['fast_ema'], prev_bar['slow_ema']
            price = curr_bar['close']
            time = curr_bar['time']
            
            signal = None
            
            # Entry Logic (Crossover)
            if p_fast <= p_slow and c_fast > c_slow:
                signal = "BUY"
            elif p_fast >= p_slow and c_fast < c_slow:
                signal = "SELL"
                
            # Exit Logic (Crossover + Price Deviation)
            exit_signal = False
            exit_reason = ""
            
            if position:
                if position['direction'] == "LONG":
                     # Exit Cross
                     if p_fast >= p_slow and c_fast < c_slow:
                         exit_signal = True; exit_reason = "Cross"
                elif position['direction'] == "SHORT":
                     # Exit Cross
                     if p_fast <= p_slow and c_fast > c_slow:
                         exit_signal = True; exit_reason = "Cross"
            
            # --- EXECUTION ---
            
            # 1. Close Existing
            if position and (exit_signal or (signal and signal != position['direction'])): # Reversal closes
                 # Calculate PnL
                 if position['direction'] == "LONG":
                     diff = price - position['price']
                 else:
                     diff = position['price'] - price
                 
                 pnl_raw = diff
                 
                 # Cost of spread on entry + exit
                 # We paid spread on entry ( Ask > Bid). We pay spread on exit (Bid < Ask).
                 # Simulating spread impact explicitly:
                 # Long Entry: Buy at Ask (Mid + Spread/2). Exit at Bid (Mid - Spread/2). total cost = Spread.
                 # Short Entry: Sell at Bid. Exit at Ask. total cost = Spread.
                 
                 pnl_net = pnl_raw - spread_cost
                 
                 trades.append({
                     'Symbol': symbol,
                     'EntryTime': position['time'],
                     'ExitTime': time,
                     'Direction': position['direction'],
                     'EntryPrice': position['price'],
                     'ExitPrice': price,
                     'PnL_Raw': pnl_raw,
                     'SpreadCost': spread_cost,
                     'PnL_Net': pnl_net,
                     'Reason': exit_reason or "Reversal"
                 })
                 position = None
            
            # 2. Open New
            if signal and position is None:
                # Open
                # Price is Close. But assumed execution at Ask/Bid.
                # Long: Buy at Close + Spread/2
                # Short: Sell at Close - Spread/2
                entry_price = price 
                
                position = {
                    'direction': "LONG" if signal == "BUY" else "SHORT",
                    'price': entry_price,
                    'time': time
                }

        # Save symbol CSV
        if trades:
            trades_df = pd.DataFrame(trades)
            filename = f"test_5m9-35_{symbol}.csv" # Updated Filename
            trades_df.to_csv(filename, index=False)
            print(f"Saved {filename} ({len(trades)} trades)")
            
            net_points = trades_df['PnL_Net'].sum()
            win_rate = (len(trades_df[trades_df['PnL_Net']>0]) / len(trades_df)) * 100
            
            overall_results.append({
                'Symbol': symbol,
                'Trades': len(trades),
                'WinRate': win_rate,
                'NetPoints': net_points,
                'SpreadCostTotal': trades_df['SpreadCost'].sum()
            })
        else:
            print(f"No trades generated for {symbol}")

    # Summary
    print("\n" + "="*80)
    print("BACKTEST SUMMARY (Last 12h)")
    if overall_results:
        summary_df = pd.DataFrame(overall_results)
        print(summary_df.to_string(index=False))
        # Total
        print("-" * 80)
        print(f"Total Trades: {summary_df['Trades'].sum()}")
        print(f"Avg Win Rate: {summary_df['WinRate'].mean():.1f}%")
    else:
        print("No trades executed across all symbols.")
    print("="*80)
    
    connector.disconnect()

if __name__ == "__main__":
    run_backtest()
