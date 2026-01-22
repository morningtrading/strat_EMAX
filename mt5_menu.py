#!/usr/bin/env python3
"""
MT5 Menu Operations - Python backend for shell menu
Provides account info, position details, and trade execution
"""

import MetaTrader5 as mt5
import sys
import json
from datetime import datetime


def init_mt5():
    """Initialize MT5 connection"""
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        return False
    return True


def get_account_info():
    """Get and display account balance and info"""
    if not init_mt5():
        return
    
    account = mt5.account_info()
    if account:
        print("\n" + "=" * 50)
        print("💰 ACCOUNT INFORMATION")
        print("=" * 50)
        print(f"  Account:    {account.login}")
        print(f"  Server:     {account.server}")
        print(f"  Name:       {account.name}")
        print(f"  Currency:   {account.currency}")
        print("-" * 50)
        print(f"  Balance:    ${account.balance:,.2f}")
        print(f"  Equity:     ${account.equity:,.2f}")
        print(f"  Margin:     ${account.margin:,.2f}")
        print(f"  Free:       ${account.margin_free:,.2f}")
        print(f"  Profit:     ${account.profit:+,.2f}")
        print("=" * 50)
    else:
        print("❌ Failed to get account info")
    
    mt5.shutdown()


def get_positions():
    """Get and display all open positions with details"""
    if not init_mt5():
        return
    
    positions = mt5.positions_get()
    
    print("\n" + "=" * 70)
    print("📊 OPEN POSITIONS")
    print("=" * 70)
    
    if positions is None or len(positions) == 0:
        print("  No open positions")
        mt5.shutdown()
        return
    
    total_profit = 0
    for i, pos in enumerate(positions, 1):
        pos_type = "BUY" if pos.type == 0 else "SELL"
        profit_color = "🟢" if pos.profit >= 0 else "🔴"
        
        print(f"\n  Position #{i}")
        print(f"  {'-' * 40}")
        print(f"  Symbol:      {pos.symbol}")
        print(f"  Type:        {pos_type}")
        print(f"  Volume:      {pos.volume} lots")
        print(f"  Open Price:  {pos.price_open}")
        print(f"  Current:     {pos.price_current}")
        print(f"  SL:          {pos.sl if pos.sl > 0 else 'None'}")
        print(f"  TP:          {pos.tp if pos.tp > 0 else 'None'}")
        print(f"  Swap:        ${pos.swap:+.2f}")
        print(f"  Profit:      {profit_color} ${pos.profit:+.2f}")
        print(f"  Ticket:      {pos.ticket}")
        total_profit += pos.profit
    
    print("\n" + "=" * 70)
    profit_emoji = "🟢" if total_profit >= 0 else "🔴"
    print(f"  Total Positions: {len(positions)}")
    print(f"  Total Profit:    {profit_emoji} ${total_profit:+,.2f}")
    print("=" * 70)
    
    mt5.shutdown()


def close_all_positions():
    """Close all open positions"""
    if not init_mt5():
        return False
    
    positions = mt5.positions_get()
    
    if positions is None or len(positions) == 0:
        print("✅ No positions to close")
        mt5.shutdown()
        return True
    
    print(f"\n⚠️  Closing {len(positions)} position(s)...")
    print("-" * 50)
    
    success_count = 0
    failed_count = 0
    
    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        volume = pos.volume
        pos_type = pos.type
        
        # Prepare close request
        # For BUY position, we need to SELL to close
        # For SELL position, we need to BUY to close
        close_type = mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"  ❌ Failed to get price for {symbol}")
            failed_count += 1
            continue
        
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 0,
            "comment": "Close by menu",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"  ✅ Closed {symbol} #{ticket} ({volume} lots) @ {price}")
            success_count += 1
        else:
            print(f"  ❌ Failed to close {symbol} #{ticket}: {result.comment}")
            failed_count += 1
    
    print("-" * 50)
    print(f"  Closed: {success_count}, Failed: {failed_count}")
    
    mt5.shutdown()
    return failed_count == 0


def verify_closed():
    """Verify all positions are closed"""
    if not init_mt5():
        return
    
    positions = mt5.positions_get()
    
    print("\n" + "=" * 50)
    print("🔍 VERIFICATION")
    print("=" * 50)
    
    if positions is None or len(positions) == 0:
        print("  ✅ All positions are closed!")
        
        # Show final account state
        account = mt5.account_info()
        if account:
            print(f"\n  Final Balance: ${account.balance:,.2f}")
            print(f"  Final Equity:  ${account.equity:,.2f}")
    else:
        print(f"  ⚠️  {len(positions)} position(s) still open:")
        for pos in positions:
            print(f"     - {pos.symbol} ({pos.volume} lots)")
    
    print("=" * 50)
    mt5.shutdown()


def main():
    if len(sys.argv) < 2:
        print("Usage: python mt5_menu.py <command>")
        print("Commands: balance, positions, close_all, verify")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "balance":
        get_account_info()
    elif command == "positions":
        get_positions()
    elif command == "close_all":
        close_all_positions()
    elif command == "verify":
        verify_closed()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
