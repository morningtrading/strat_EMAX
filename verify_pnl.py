
import os
import sys
import json
from datetime import datetime, timedelta
import logging

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.mt5_connector import MT5Connector

# Configure logging
logging.basicConfig(level=logging.INFO)

def run_verify():
    print("="*60)
    print("DAILY PnL VERIFICATION")
    print("="*60)
    
    # Initialize
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    # Load Config for Magic Number
    MAGIC = 123456 # Default
    try:
        with open('config/trading_config.json', 'r') as f:
            cfg = json.load(f)
            MAGIC = cfg.get('magic_number', 123456)
    except:
        pass
        
    print(f"Using Magic Number: {MAGIC}")
    
    # Define Start of Day
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Fetching deals since: {today_start}")
    
    # Get Deals
    deals = connector.get_history_deals(from_date=today_start)
    print(f"Total deals returned: {len(deals)}")
    
    # Filter
    my_deals = [d for d in deals if d.get('magic') == MAGIC]
    print(f"Deals for this bot: {len(my_deals)}")
    
    # Calculate Stats
    real_pnl = 0.0
    closed_trades = 0
    total_volume = 0.0
    
    print("\nDeal Breakdown (First 10):")
    print("-" * 80)
    print(f"{'Time':<20} | {'Type':<6} | {'Entry':<4} | {'Vol':<5} | {'Price':<8} | {'Profit':<8} | {'Comm'}")
    print("-" * 80)
    
    for i, d in enumerate(my_deals):
        # Sum PnL
        pnl = d.get('profit', 0.0)
        swap = d.get('swap', 0.0)
        comm = d.get('commission', 0.0)
        fee = d.get('fee', 0.0)
        
        net_impact = pnl + swap + comm + fee
        real_pnl += net_impact
        
        # Count Trades (Entry Out)
        entry = d.get('entry') # 0=IN, 1=OUT, 3=OUT_BY
        if entry in [1, 3]:
            closed_trades += 1
            total_volume += d.get('volume', 0)
            
        if i < 10:
            entry_str = str(entry)
            print(f"{d['time']:<20} | {d['type']:<6} | {entry_str:<4} | {d['volume']:<5} | {d['price']:<8.5f} | {pnl:<8.2f} | {comm:.2f}")

    print("-" * 80)
    print(f"\nRESULTS:")
    print(f"Closed Trades: {closed_trades}")
    print(f"Total Volume:  {total_volume:.2f}")
    print(f"Real PnL:      ${real_pnl:.2f}")
    print("="*60)
    
    connector.disconnect()

if __name__ == "__main__":
    run_verify()
