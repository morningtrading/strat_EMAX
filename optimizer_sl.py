
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.mt5_connector import MT5Connector

# Configure logging
logging.basicConfig(level=logging.INFO)

def calculate_ema_numpy(prices, period):
    x = np.asarray(prices)
    return pd.Series(x).ewm(span=period, adjust=False).mean().values

def calculate_atr(high, low, close, period=14):
    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(min_periods=period, alpha=1/period, adjust=False).mean() # Wilder's RMA approx or standard EMA
    # MT5 often uses standard SMA for ATR, or smoothed. Let's use simple rolling mean for robustness or EMA.
    # standard ATR is SMMA of TR. Pandas ewm(alpha=1/period) is close to SMMA.
    return atr.values

def run_optimization():
    print("="*80)
    print("🛑 SL OPTIMIZATION: M5/M15 (Rank #1) | Last 12 Hours")
    print("   Method: ATR Multiplier (1.0 - 5.0) vs Uncapped")
    print("="*80)
    
    # Initialize connection
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    # Load Config (We need the Rank #1 settings we just saved)
    try:
        with open('config/trading_config.json', 'r') as f:
            cfg = json.load(f)
            SYMBOLS_CFG = cfg.get('symbols', {}).get('settings', {})
            SYMBOLS = cfg.get('symbols', {}).get('enabled', [])
    except Exception as e:
        print(f"Config Error: {e}")
        return

    print(f"Symbols: {SYMBOLS}")
    
    # Vars to test
    ATR_MULTS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 999.0] # 999 = effectively no SL (reversal only)
    LOOKBACK_HOURS = 12
    BARS_TO_FETCH = 500
    
    final_recs = []

    for symbol in SYMBOLS:
        print(f"\nAnalyzing {symbol}...", end=' ')
        
        # Get settings from config
        s_cfg = SYMBOLS_CFG.get(symbol, {})
        tf = s_cfg.get('timeframe', 'M5')
        fast_p = s_cfg.get('fast_ema', 9)
        slow_p = s_cfg.get('slow_ema', 41)
        
        print(f"[{tf} {fast_p}/{slow_p}]", end=' ')
        
        # 1. Fetch Data
        bars = connector.get_rates(symbol, tf, count=BARS_TO_FETCH)
        if not bars:
            continue
            
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'])
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        times = df['time'].values
        
        # Cost check
        info = connector.get_symbol_info(symbol)
        spread_cost = (info.get('spread', 10) * info.get('point', 0.00001)) if info else 0.0001
        
        # 2. Indicators
        fast_arr = calculate_ema_numpy(closes, fast_p)
        slow_arr = calculate_ema_numpy(closes, slow_p)
        atr_arr = calculate_atr(highs, lows, closes, 14)
        
        # 3. Signals (Windowed)
        start_time_limit = datetime.now() - timedelta(hours=LOOKBACK_HOURS)
        valid_indices = df[df['time'] >= start_time_limit].index
        if valid_indices.empty:
            continue
        window_start_idx = max(valid_indices[0], 50) # ensure ATR warmup
        
        # Identify Zones
        trend_zone = np.where(fast_arr > slow_arr, 1, -1)
        
        # Loop for Trades
        # We simulate trades once, then check outcome against various SLs
        # BUT SL hit changes the flow (exit early). So we must re-sim per SL?
        # Yes, because if SL hits, we might be out of market until next signal or reverse immediately?
        # EMAX logic: If SL hits, we stay flat until NEXT signal (Reverse).
        # OR does it re-enter? Usually strategy enters on transition.
        # If SL exit happens, we are flat. We wait for NEXT transition? 
        # No, if trend continues, do we re-enter?
        # Current bot logic: "entry_check... if signal and no position... open".
        # Check signal types: CROSSOVER or CONTINUOUS?
        # "if p_fast <= p_slow and c_fast > c_slow" -> Crossover only.
        # So if SL hits, we miss the rest of the trend. This is standard OCO.
        
        best_sl_mult = 0.0
        best_pnl = -999999.0
        best_trades = 0
        
        results_map = {}
        
        for mult in ATR_MULTS:
            trade_pnl_sum = 0.0
            trades_count = 0
            
            curr_pos = 0 # 0, 1, -1
            entry_price = 0.0
            entry_sl_price = 0.0
            
            # Reconstruct loop
            changes = np.where(trend_zone[1:] != trend_zone[:-1])[0] + 1
            changes = changes[changes >= window_start_idx]
            
            # We also need to check "Every Bar" for SL hit
            # This is slow in pure python loops if we don't optimize.
            # But 12h @ M5 is only 144 bars. Fast enough.
            
            # Merge signals into a timeline?
            # Iterating bar-by-bar is safest.
            
            for i in range(window_start_idx, len(closes)):
                # 1. Check SL HIT on existing position
                if curr_pos != 0:
                    hit_sl = False
                    
                    if mult < 100: # If using real SL
                        if curr_pos == 1: # Long
                            # Check Low
                             if lows[i] <= entry_sl_price:
                                 # HIT SL
                                 hit_sl = True
                                 exit_price = entry_sl_price # Slippage? Assume hit at price
                        else: # Short
                            if highs[i] >= entry_sl_price:
                                hit_sl = True
                                exit_price = entry_sl_price
                    
                    if hit_sl:
                        # Close trade
                        raw_pnl = (exit_price - entry_price) * curr_pos
                        net_pnl = raw_pnl - spread_cost
                        trade_pnl_sum += net_pnl
                        trades_count += 1
                        curr_pos = 0 # Flat
                        continue # Next bar (wait for signal)
                
                # 2. Check Signal (Cross)
                # Signal calculated at Close of PREV bar? 
                # Bot Logic: On Tick (Live) or On Bar Close?
                # Usually Bot acts on completed bar for stability.
                # Let's assess signal at `i` (Close) to execute at `i+1` (Open)?
                # Or execute Immediate Close?
                # Simplify: Signal at `i`. If Signal != CurrPos, Reverse.
                
                zone = trend_zone[i]
                prev_zone = trend_zone[i-1]
                
                is_cross = (zone != prev_zone)
                
                if is_cross:
                    # 2a. Close Existing (Reversal)
                    if curr_pos != 0:
                         # We are reversing.
                         # Exit Price = Close
                         raw_pnl = (closes[i] - entry_price) * curr_pos
                         net_pnl = raw_pnl - spread_cost
                         trade_pnl_sum += net_pnl
                         trades_count += 1
                    
                    # 2b. Open New
                    curr_pos = zone
                    entry_price = closes[i]
                    
                    # Calc SL
                    atr_val = atr_arr[i]
                    if mult < 100:
                        sl_dist = atr_val * mult
                        if curr_pos == 1:
                            entry_sl_price = entry_price - sl_dist
                        else:
                            entry_sl_price = entry_price + sl_dist
                    else:
                        entry_sl_price = 0 # No SL
            
            # End loop
            results_map[mult] = trade_pnl_sum
            
            if trade_pnl_sum > best_pnl:
                best_pnl = trade_pnl_sum
                best_sl_mult = mult
                best_trades = trades_count
        
        print(f" Best SL: ATR x {best_sl_mult} (PnL ${best_pnl:.2f})")
        
        final_recs.append({
            'Symbol': symbol,
            'BestATR': best_sl_mult,
            'PnL': best_pnl,
            'Trades': best_trades
        })
        
    print("\n" + "="*80)
    print("🎯 OPTIMAL SL RECOMMENDATIONS")
    print("="*80)
    print(f"{'Symbol':<10} | {'ATR Mult':<10} | {'PnL ($)':<10}")
    print("-" * 40)
    for res in final_recs:
        rec_str = f"{res['BestATR']}x" if res['BestATR'] < 100 else "NONE"
        print(f"{res['Symbol']:<10} | {rec_str:<10} | {res['PnL']:.2f}")

    connector.disconnect()

if __name__ == "__main__":
    run_optimization()
