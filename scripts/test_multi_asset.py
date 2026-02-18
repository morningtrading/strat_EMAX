
import sys
import os
import time
from typing import List, Dict

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mt5_connector import MT5Connector

def check_symbol(connector, symbol_name):
    print(f"Checking symbol {symbol_name}...")
    info = connector.get_symbol_info(symbol_name)
    if info:
        print(f"✅ Symbol {symbol_name} found and visible.")
        return symbol_name
    
    # Try alternate names common for indices
    alternates = {
        "USTEC": ["NAS100", "NAS100ft", "US100", "NDX"],
        "NAS100ft": ["USTEC", "NAS100", "US100", "NDX"],
        "GER40": ["GER40ft", "DAX40", "DE40"],
        "US500": ["SP500", "SP500ft", "ES"],
        "US2000": ["RUT", "US2000ft"]
    }
    
    if symbol_name in alternates:
        for alt in alternates[symbol_name]:
            print(f"Checking alternate {alt}...")
            info = connector.get_symbol_info(alt)
            if info:
                print(f"✅ Found alternate symbol: {alt}")
                return alt
                
    print(f"❌ Symbol {symbol_name} not found.")
    return None

def place_test_trade(connector, symbol):
    print(f"🚀 Placing test trade for {symbol}...")
    
    # Get price and leverage
    price_info = connector.get_current_price(symbol)
    if not price_info:
        print(f"❌ Failed to get price for {symbol}")
        return None
        
    account = connector.get_account_summary()
    leverage = account.get('leverage', 100)
    
    price = price_info['ask']
    sym_info = connector.get_symbol_info(symbol)
    
    # Calculate volume for ~$11 margin
    target_margin = 11.0
    contract_size = sym_info.get('trade_contract_size', 100000)
    min_vol = sym_info.get('volume_min', 0.01)
    
    # Volume = (Margin * Leverage) / (ContractSize * Price)
    # Note: Indices often have different margin calculations, but this is a rough target
    try:
        if sym_info.get('margin_initial', 0) > 0:
             # Some brokers provide precise margin requirements
             pass 
             
        raw_volume = (target_margin * leverage) / (contract_size * price)
    except ZeroDivisionError:
        raw_volume = min_vol

    # Volume normalization
    step = sym_info.get('volume_step', 0.01)
    if step > 0:
        # Round to nearest step
        steps = round(raw_volume / step)
        volume = steps * step
        # Ensure precision matching step decimals
        import math
        decimals = 0
        if step < 1:
            decimals = len(str(step).split('.')[1])
        volume = round(volume, decimals)
    else:
        volume = round(raw_volume, 2)

    # Enforce limits
    volume = max(min_vol, volume)
    if 'volume_max' in sym_info and sym_info['volume_max'] > 0:
        volume = min(volume, sym_info['volume_max'])
        
    print(f"  Price: {price}")
    print(f"  Volume: {volume}")
    
    res = connector.place_order(symbol, "BUY", volume, comment="Multi-Asset Test")
    
    if res['success']:
        print(f"✅ Order Placed: {res['ticket']}")
        return res['ticket']
    else:
        print(f"❌ Order Failed: {res.get('error')} (Retcode: {res.get('retcode')})")
        return None

def main():
    print("Initialize MT5 Connector...")
    connector = MT5Connector()
    if not connector.connect():
        print("❌ Failed to connect to MT5")
        return

    # Requested assets: Forex, Metal, Index
    # EURUSD, XAUUSD, USTEC
    target_assets = ["EURUSD", "XAUUSD", "USTEC"]
    
    active_tickets = []
    
    print("\n" + "="*50)
    print("STEP 1: PLACING ORDERS")
    print("="*50)
    
    for asset in target_assets:
        resolved_symbol = check_symbol(connector, asset)
        if resolved_symbol:
            ticket = place_test_trade(connector, resolved_symbol)
            if ticket:
                active_tickets.append(ticket)
        else:
            print(f"⚠️  Skipping {asset} (not found)")
            
    print("\n" + "="*50)
    print(f"STEP 2: WAITING 60 SECONDS... ({len(active_tickets)} trades active)")
    print("="*50)
    
    if active_tickets:
        for i in range(60, 0, -10):
            print(f"Closing in {i} seconds...")
            time.sleep(10)
    else:
        print("No active trades to wait for.")
        
    print("\n" + "="*50)
    print("STEP 3: CLOSING TRADES")
    print("="*50)
    
    closed_count = 0
    failed_count = 0
    
    for ticket in active_tickets:
        print(f"Closing ticket {ticket}...")
        res = connector.close_position(ticket)
        if res['success']:
            print(f"✅ Closed ticket {ticket}")
            closed_count += 1
        else:
            print(f"❌ Failed to close {ticket}: {res.get('error')}")
            failed_count += 1
            
    print("\n" + "="*50)
    print("STEP 4: VERIFICATION")
    print("="*50)
    
    # Verify no open positions
    open_positions = connector.get_positions()
    remaining = [p for p in open_positions if p['ticket'] in active_tickets]
    
    if not remaining:
        print("✅ SUCCESS: All test positions confirmed closed.")
    else:
        print(f"❌ WARNING: {len(remaining)} test positions still open!")
        for p in remaining:
            print(f"  - Ticket {p['ticket']} ({p['symbol']})")

    connector.disconnect()
    
    print("\nSUMMARY:")
    print(f"Attempted: {len(target_assets)}")
    print(f"Placed: {len(active_tickets)}")
    print(f"Closed: {closed_count}")
    print(f"Failed Close: {failed_count}")
    print(f"Remaining Open: {len(remaining)}")

if __name__ == "__main__":
    main()
