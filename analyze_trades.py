
import os
import sys
import json
from datetime import datetime
import pandas as pd
import logging

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.mt5_connector import MT5Connector

# Configure logging
logging.basicConfig(level=logging.INFO)

def analyze():
    print("="*80)
    print("🤖 EMAX TRADING ENGINE - PERFORMANCE ANALYSIS")
    print("="*80)
    
    # Initialize
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    # Load Config for Magic Number
    MAGIC = 123456
    try:
        with open('config/trading_config.json', 'r') as f:
            cfg = json.load(f)
            MAGIC = cfg.get('magic_number', 123456)
    except:
        pass
        
    # Fetch Data (Today)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Fetching deals since: {today_start}")
    
    deals = connector.get_history_deals(from_date=today_start)
    my_deals = [d for d in deals if d.get('magic') == MAGIC]
    
    if not my_deals:
        print("No trades found for today.")
        return

    # Create DataFrame
    data = []
    for d in my_deals:
        # We only care about exits for PnL, but need entry time for duration
        # MT5 Deals are individual events. We need to match IN and OUT.
        # Simplification: Analyze the exit deals which contain the PnL.
        
        # Entry types: 0=IN, 1=OUT, 3=OUT_BY
        if d['entry'] in [1, 3]: # Exits
            net_pnl = d['profit'] + d['swap'] + d['commission'] + d['fee']
            duration_mins = 0
            
            # Find matching entry (simplified, assumes unique positions per symbol for now)
            # A real backtest engine would match IDs, but for daily stats this is close enough
            # We can calculate duration if we find the deal with entry=0 and same position_id (ticket in pos history? no, deal.position_id)
            # MT5 Connector returns 'order' and 'ticket', need 'position_id' ideally.
            # let's assume 'order' might link them or just skip duration for now to be fast.
            
            data.append({
                'Time': d['time'],
                'Symbol': d['symbol'],
                'Type': "BUY" if d['type'] == 0 else "SELL", # Deal type at exit. 
                # Note: Exit deal type is opposite of position. 
                # If pos was BUY, exit deal is SELL (type 1).
                # Interpreting direction:
                'Direction': "LONG" if d['type'] == 1 else "SHORT", # If we sold to close, we were Long.
                'Volume': d['volume'],
                'Price': d['price'],
                'PnL': net_pnl
            })
    
    # ... (previous code above)
    
    # 2. FETCH OPEN POSITIONS
    print("Fetching open positions...")
    positions = connector.get_positions()
    my_positions = [p for p in positions if p.get('magic') == MAGIC]
    
    open_pnl = 0.0
    open_count = len(my_positions)
    
    if my_positions:
        print(f"Found {open_count} open positions.")
        for p in my_positions:
            floating_pnl = p['profit'] + p.get('swap', 0)
            open_pnl += floating_pnl
            
            # Add to data for holistic analysis
            data.append({
                'Time': p['time'], # Entry time
                'Symbol': p['symbol'],
                'Type': p['type'], # "BUY" or "SELL" string from get_positions
                'Direction': "LONG" if p['type'] == "BUY" else "SHORT",
                'Volume': p['volume'],
                'Price': p['price_current'], # Current price for open pos
                'PnL': floating_pnl,
                'Status': 'OPEN'
            })
    else:
        print("No open positions.")

    if not data:
        print("No trades (open or closed) found.")
        return
        
    df = pd.DataFrame(data)
    if 'Status' not in df.columns:
        df['Status'] = 'CLOSED'
    
    # --- GLOBAL STATS ---
    closed_df = df[df['Status'] == 'CLOSED']
    open_df = df[df['Status'] == 'OPEN']
    
    realized_pnl = closed_df['PnL'].sum() if not closed_df.empty else 0
    unrealized_pnl = open_df['PnL'].sum() if not open_df.empty else 0
    total_pnl = realized_pnl + unrealized_pnl
    
    total_trades = len(df)
    winners = df[df['PnL'] > 0]
    losers = df[df['PnL'] <= 0]
    
    win_rate = (len(winners) / total_trades) * 100
    avg_win = winners['PnL'].mean() if not winners.empty else 0
    avg_loss = losers['PnL'].mean() if not losers.empty else 0
    
    # Profit factor: (Realized Wins + Unrealized Wins) / abs(Realized Losses + Unrealized Losses)
    gross_profit = winners['PnL'].sum()
    gross_loss = abs(losers['PnL'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0
    
    print(f"\n📊 SESSION SUMMARY (Closed + Open)")
    print(f"Total Trades: {total_trades} ({len(closed_df)} Closed, {len(open_df)} Open)")
    print(f"Net PnL:      ${total_pnl:.2f}")
    print(f"  - Realized:   ${realized_pnl:.2f}")
    print(f"  - Unrealized: ${unrealized_pnl:.2f}")
    print(f"Win Rate:     {win_rate:.1f}%")
    print(f"Profit Factor: {profit_factor:.2f}")
    
    # --- BY SYMBOL ---
    print(f"\n📈 BY SYMBOL")
    print("-" * 80)
    print(f"{'Symbol':<10} | {'Tot':<4} | {'Open':<4} | {'Win%':<6} | {'Net PnL':<10} | {'Open PnL':<10}")
    print("-" * 80)
    
    by_symbol = df.groupby('Symbol')
    for sym, group in by_symbol:
        s_pnl = group['PnL'].sum()
        s_open = group[group['Status'] == 'OPEN']
        s_open_pnl = s_open['PnL'].sum() if not s_open.empty else 0
        s_trades = len(group)
        s_wins = len(group[group['PnL'] > 0])
        s_wr = (s_wins / s_trades) * 100
        
        print(f"{sym:<10} | {s_trades:<4} | {len(s_open):<4} | {s_wr:<6.1f} | ${s_pnl:<9.2f} | ${s_open_pnl:<9.2f}")
        
    # --- OPEN POSITIONS ---
    print(f"\n🚀 OPEN RUNNERS")
    print("-" * 65)
    if not open_df.empty:
      runners = open_df.sort_values('PnL', ascending=False)
      for _, row in runners.iterrows():
          print(f"{row['Symbol']} {row['Direction']} | Vol: {row['Volume']} | PnL: ${row['PnL']:.2f}")
    else:
      print("No open positions.")

    # --- RECENT LOSERS ---
    # ... (rest of logic)
        
    # --- BY HOUR ---
    df['Hour'] = pd.to_datetime(df['Time']).dt.hour
    print(f"\n🕒 BY HOUR")
    print("-" * 65)
    print(f"{'Hour':<10} | {'Trades':<6} | {'Win%':<6} | {'PnL':<10}")
    print("-" * 65)
    
    by_hour = df.groupby('Hour')
    for hour, group in by_hour:
        h_pnl = group['PnL'].sum()
        h_trades = len(group)
        h_wins = len(group[group['PnL'] > 0])
        h_wr = (h_wins / h_trades) * 100
        print(f"{hour:02d}:00      | {h_trades:<6} | {h_wr:<6.1f} | ${h_pnl:<9.2f}")

    # --- RECENT LOSERS ---
    print(f"\n⚠️ WORST LOSERS (Last 10)")
    print("-" * 65)
    worst = df.sort_values('PnL').head(10)
    for _, row in worst.iterrows():
        print(f"{row['Time']} | {row['Symbol']} | {row['Direction']} | ${row['PnL']:.2f}")

    connector.disconnect()

if __name__ == "__main__":
    analyze()
