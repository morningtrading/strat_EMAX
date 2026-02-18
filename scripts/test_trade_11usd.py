
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mt5_connector import MT5Connector

def main():
    print("Initializing MT5 Connector...")
    connector = MT5Connector()
    
    if not connector.connect():
        print("❌ Failed to connect to MT5")
        return

    symbol = "EURUSD"
    print(f"Checking symbol {symbol}...")
    
    # Ensure symbol is enabled
    sym_info = connector.get_symbol_info(symbol)
    if not sym_info:
        print(f"❌ Failed to get symbol info for {symbol}")
        connector.disconnect()
        return

    # Get account info for leverage
    account = connector.get_account_summary()
    leverage = account.get('leverage', 100)
    balance = account.get('balance', 0)
    print(f"Account Balance: ${balance:.2f}")
    print(f"Account Leverage: 1:{leverage}")

    # Get current price
    price_info = connector.get_current_price(symbol)
    if not price_info:
        print("❌ Failed to get price")
        connector.disconnect()
        return
        
    price = price_info['ask']
    print(f"Current {symbol} Price: {price}")
    
    # Calculate volume for ~$11 margin
    # Margin = (Volume * ContractSize * Price) / Leverage
    # Volume = (Margin * Leverage) / (ContractSize * Price)
    target_margin = 11.0
    contract_size = sym_info.get('trade_contract_size', 100000)
    
    raw_volume = (target_margin * leverage) / (contract_size * price)
    
    # Round to nearest 0.01 (min step)
    volume = round(raw_volume, 2)
    
    # Ensure min volume
    min_vol = sym_info.get('volume_min', 0.01)
    if volume < min_vol:
        print(f"calculated volume {volume} < min volume {min_vol}, using min volume")
        volume = min_vol
        
    print(f"Target Margin: ${target_margin}")
    print(f"Calculated Volume: {volume} lots")
    
    if len(sys.argv) > 1 and sys.argv[1] == '-y':
        print("Auto-confirming trade due to -y flag.")
    else:
        confirm = input(f"❓ Place BUY order for {volume} lots of {symbol}? (y/n): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            connector.disconnect()
            return
    
    print(f"🚀 Placing BUY order...")
    res = connector.place_order(symbol, "BUY", volume, comment="Test $11 Trade")
    
    if res['success']:
        print(f"✅ Order Placed Successfully!")
        print(f"Ticket: {res['ticket']}")
        print(f"Volume: {res['volume']}")
        print(f"Price: {res['price']}")
    else:
        print(f"❌ Order Failed: {res.get('error')}")
        print(f"Retcode: {res.get('retcode')}")
    
    time.sleep(1)
    connector.disconnect()

if __name__ == "__main__":
    main()
