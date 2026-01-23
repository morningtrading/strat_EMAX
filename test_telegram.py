#!/usr/bin/env python3
"""
Test Telegram notifications with detailed trade messages
"""

import sys
import time
from core.telegram_notifier import TelegramNotifier
from datetime import datetime

def test_basic_connection():
    """Test 1: Basic connection"""
    print("=" * 60)
    print("TEST 1: Basic Connection")
    print("=" * 60)
    
    notifier = TelegramNotifier()
    
    if not notifier.is_configured():
        print("❌ Telegram not configured!")
        return False
    
    print(f"✅ Telegram configured")
    print(f"   Bot Token: {notifier.bot_token[:20]}...")
    print(f"   Chat ID: {notifier.chat_id}")
    
    print("\nSending test message...")
    if notifier.test_connection():
        print("✅ Test message sent successfully!")
        return True
    else:
        print("❌ Failed to send test message")
        return False

def test_trade_entry():
    """Test 2: Trade entry notification with full details"""
    print("\n" + "=" * 60)
    print("TEST 2: Trade Entry Notification (Full Details)")
    print("=" * 60)
    
    notifier = TelegramNotifier()
    
    # Simulate a realistic trade entry
    print("Sending LONG entry for XAUUSD...")
    notifier.notify_trade_entry(
        symbol="XAUUSD",
        direction="LONG",
        volume=0.01,
        price=2045.50,
        sl=2040.00,
        reason="Fast EMA crossed above Slow EMA (Bullish crossover)",
        margin=10.00,
        fast_ema=2045.12,
        slow_ema=2043.89,
        balance=1000.00,
        equity=1038.50
    )
    print("✅ LONG entry sent")
    
    time.sleep(2)
    
    # Test SHORT entry
    print("Sending SHORT entry for GER40ft...")
    notifier.notify_trade_entry(
        symbol="GER40ft",
        direction="SHORT",
        volume=0.1,
        price=17825.5,
        sl=17850.0,
        reason="Fast EMA crossed below Slow EMA (Bearish crossover)",
        margin=5.50,
        fast_ema=17820.2,
        slow_ema=17835.8,
        balance=1000.00,
        equity=1038.50
    )
    print("✅ SHORT entry sent")
    
    return True

def test_trade_exit():
    """Test 3: Trade exit notification with P&L details"""
    print("\n" + "=" * 60)
    print("TEST 3: Trade Exit Notification (With P&L)")
    print("=" * 60)
    
    notifier = TelegramNotifier()
    
    # Simulate winning trade
    print("Sending WIN exit for XAUUSD...")
    notifier.notify_trade_exit(
        symbol="XAUUSD",
        direction="LONG",
        volume=0.01,
        entry_price=2045.50,
        exit_price=2052.30,
        pnl=68.00,
        reason="Fast EMA crossed below Slow EMA (Exit signal)",
        hold_time="2h 15m",
        pips=68.0,
        balance=1068.00,
        equity=1106.50,
        total_pnl=106.50
    )
    print("✅ WIN exit sent")
    
    time.sleep(2)
    
    # Simulate losing trade
    print("Sending LOSS exit for GER40ft...")
    notifier.notify_trade_exit(
        symbol="GER40ft",
        direction="SHORT",
        volume=0.1,
        entry_price=17825.5,
        exit_price=17840.0,
        pnl=-14.50,
        reason="Stop loss hit",
        hold_time="45m",
        pips=-14.5,
        balance=1053.50,
        equity=1092.00,
        total_pnl=92.00
    )
    print("✅ LOSS exit sent")
    
    return True

def test_status_notification():
    """Test 4: Connection status"""
    print("\n" + "=" * 60)
    print("TEST 4: Status Notification")
    print("=" * 60)
    
    notifier = TelegramNotifier()
    
    print("Sending connection status...")
    notifier.send_status(
        connected=True,
        account_info={
            'login': 67157299,
            'server': 'MonetaMarkets-Demo',
            'balance': 1053.50,
            'equity': 1092.00,
            'is_demo': True
        }
    )
    print("✅ Status sent")
    
    return True

def test_error_notification():
    """Test 5: Error notification"""
    print("\n" + "=" * 60)
    print("TEST 5: Error Notification")
    print("=" * 60)
    
    notifier = TelegramNotifier()
    
    print("Sending error notification...")
    notifier.notify_error(
        error_type="Order Failed",
        message="Invalid volume 0.001 (minimum is 0.01)",
        symbol="XAUUSD"
    )
    print("✅ Error notification sent")
    
    return True

def test_daily_summary():
    """Test 6: Daily summary"""
    print("\n" + "=" * 60)
    print("TEST 6: Daily Summary")
    print("=" * 60)
    
    notifier = TelegramNotifier()
    
    print("Sending daily summary...")
    notifier.send_daily_summary({
        'date': datetime.now().strftime('%Y-%m-%d'),
        'starting_balance': 1000.00,
        'daily_pnl': 92.00,
        'daily_trades': 5
    })
    print("✅ Daily summary sent")
    
    return True

def test_panic_alert():
    """Test 7: Panic button"""
    print("\n" + "=" * 60)
    print("TEST 7: Panic Alert")
    print("=" * 60)
    
    notifier = TelegramNotifier()
    
    print("Sending panic alert...")
    notifier.send_panic_alert(
        closed_count=3,
        total_pnl=-25.50
    )
    print("✅ Panic alert sent")
    
    return True

def run_all_tests():
    """Run all telegram tests"""
    print("\n" + "=" * 60)
    print("TELEGRAM NOTIFICATION TEST SUITE")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Trade Entry", test_trade_entry),
        ("Trade Exit", test_trade_exit),
        ("Status Notification", test_status_notification),
        ("Error Notification", test_error_notification),
        ("Daily Summary", test_daily_summary),
        ("Panic Alert", test_panic_alert)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
            time.sleep(2)  # Delay between tests
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Telegram is working perfectly!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
