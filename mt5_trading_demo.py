#!/usr/bin/env python3
"""
MetaTrader 5 Trading Demo Script
A simple demonstration of MT5 trading functionality
"""

import numpy as np
import datetime
import time

def simulate_market_data(symbol="EURUSD", periods=100):
    """
    Simulate market data for demonstration purposes
    In real trading, this would come from MT5
    """
    print(f"Generating simulated market data for {symbol}...")
    
    # Generate random price data (simplified)
    base_price = 1.1000
    price_changes = np.random.normal(0, 0.0001, periods)
    prices = [base_price]
    
    for change in price_changes:
        new_price = prices[-1] + change
        prices.append(max(0.5, new_price))  # Prevent negative prices
    
    return {
        'symbol': symbol,
        'prices': prices,
        'timestamps': [datetime.datetime.now() - datetime.timedelta(minutes=i) for i in range(periods, 0, -1)]
    }

def calculate_sma(prices, period=20):
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return np.mean(prices[-period:])

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return None
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def simple_trading_strategy(data):
    """
    Simple trading strategy based on SMA and RSI
    """
    prices = data['prices']
    symbol = data['symbol']
    
    if len(prices) < 50:  # Need enough data
        return "Insufficient data for analysis"
    
    # Calculate indicators
    sma_20 = calculate_sma(prices, 20)
    sma_50 = calculate_sma(prices, 50)
    rsi = calculate_rsi(prices, 14)
    current_price = prices[-1]
    
    print(f"\n=== Trading Analysis for {symbol} ===")
    print(f"Current Price: {current_price:.5f}")
    print(f"SMA 20: {sma_20:.5f}" if sma_20 else "SMA 20: Not enough data")
    print(f"SMA 50: {sma_50:.5f}" if sma_50 else "SMA 50: Not enough data")
    print(f"RSI: {rsi:.2f}" if rsi else "RSI: Not enough data")
    
    # Simple strategy logic
    if sma_20 and sma_50 and rsi:
        if sma_20 > sma_50 and rsi < 70:
            return "BUY SIGNAL - Uptrend with RSI not overbought"
        elif sma_20 < sma_50 and rsi > 30:
            return "SELL SIGNAL - Downtrend with RSI not oversold"
        elif rsi > 70:
            return "HOLD - RSI overbought, wait for pullback"
        elif rsi < 30:
            return "HOLD - RSI oversold, potential reversal"
        else:
            return "HOLD - No clear signal"
    else:
        return "HOLD - Insufficient data for analysis"

def backtest_strategy(data, initial_balance=10000):
    """
    Simple backtesting of the trading strategy
    """
    print(f"\n=== Backtesting Strategy ===")
    print(f"Initial Balance: ${initial_balance:,.2f}")
    
    balance = initial_balance
    position = 0  # 0 = no position, 1 = long, -1 = short
    trades = []
    
    prices = data['prices']
    
    for i in range(50, len(prices)):  # Start after we have enough data
        current_prices = prices[:i+1]
        sma_20 = calculate_sma(current_prices, 20)
        sma_50 = calculate_sma(current_prices, 50)
        rsi = calculate_rsi(current_prices, 14)
        
        if not all([sma_20, sma_50, rsi]):
            continue
            
        current_price = prices[i]
        signal = None
        
        # Generate signals
        if sma_20 > sma_50 and rsi < 70 and position != 1:
            signal = "BUY"
        elif sma_20 < sma_50 and rsi > 30 and position != -1:
            signal = "SELL"
        elif rsi > 80 and position == 1:
            signal = "CLOSE_LONG"
        elif rsi < 20 and position == -1:
            signal = "CLOSE_SHORT"
        
        # Execute trades
        if signal == "BUY" and position == 0:
            position = 1
            trades.append(("BUY", current_price, i))
            print(f"Trade {len(trades)}: BUY at {current_price:.5f}")
            
        elif signal == "SELL" and position == 0:
            position = -1
            trades.append(("SELL", current_price, i))
            print(f"Trade {len(trades)}: SELL at {current_price:.5f}")
            
        elif signal == "CLOSE_LONG" and position == 1:
            # Calculate P&L
            entry_price = trades[-1][1] if trades else current_price
            pnl = (current_price - entry_price) / entry_price * balance
            balance += pnl
            trades.append(("CLOSE_LONG", current_price, i))
            print(f"Trade {len(trades)}: CLOSE LONG at {current_price:.5f}, P&L: ${pnl:.2f}")
            position = 0
            
        elif signal == "CLOSE_SHORT" and position == -1:
            # Calculate P&L
            entry_price = trades[-1][1] if trades else current_price
            pnl = (entry_price - current_price) / entry_price * balance
            balance += pnl
            trades.append(("CLOSE_SHORT", current_price, i))
            print(f"Trade {len(trades)}: CLOSE SHORT at {current_price:.5f}, P&L: ${pnl:.2f}")
            position = 0
    
    print(f"\nFinal Balance: ${balance:,.2f}")
    print(f"Total Return: {((balance - initial_balance) / initial_balance * 100):.2f}%")
    print(f"Total Trades: {len(trades)}")
    
    return balance, trades

def main():
    """Main function to run the trading demo"""
    print("MetaTrader 5 Trading Demo")
    print("=" * 40)
    
    # Generate simulated market data
    data = simulate_market_data("EURUSD", 200)
    
    # Run trading analysis
    signal = simple_trading_strategy(data)
    print(f"\nTrading Signal: {signal}")
    
    # Run backtest
    final_balance, trades = backtest_strategy(data)
    
    print("\n" + "=" * 40)
    print("Demo completed!")
    print("\nNote: This is a simulation using random data.")
    print("For real trading, you would need:")
    print("1. MetaTrader 5 installed and running")
    print("2. Valid trading account")
    print("3. Real market data connection")

if __name__ == "__main__":
    main()
