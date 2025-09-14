#!/usr/bin/env python3
"""
MetaTrader 5 Trading Strategy
Real-time trading strategy using live MT5 data
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import datetime
import time
from typing import Optional, Dict, List

class TradingStrategy:
    """Advanced Trading Strategy Class"""
    
    def __init__(self, symbol: str = "EURUSD", timeframe: int = mt5.TIMEFRAME_H1):
        self.symbol = symbol
        self.timeframe = timeframe
        self.connected = False
        self.account_info = None
        
    def connect(self) -> bool:
        """Connect to MT5"""
        if not mt5.initialize():
            print("Failed to initialize MT5")
            return False
        
        self.account_info = mt5.account_info()
        if self.account_info:
            print(f"Connected to account: {self.account_info.login}")
            print(f"Balance: ${self.account_info.balance:.2f}")
            print(f"Equity: ${self.account_info.equity:.2f}")
        
        self.connected = True
        return True
    
    def get_rates(self, count: int = 100) -> Optional[pd.DataFrame]:
        """Get historical price data"""
        if not self.connected:
            return None
        
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, count)
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD indicator"""
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict:
        """Calculate Bollinger Bands"""
        sma = self.calculate_sma(prices, period)
        std = prices.rolling(window=period).std()
        
        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }
    
    def analyze_market(self) -> Dict:
        """Comprehensive market analysis"""
        df = self.get_rates(100)
        if df is None or len(df) < 50:
            return {"error": "Insufficient data"}
        
        close_prices = df['close']
        
        # Calculate indicators
        sma_20 = self.calculate_sma(close_prices, 20)
        sma_50 = self.calculate_sma(close_prices, 50)
        rsi = self.calculate_rsi(close_prices, 14)
        macd_data = self.calculate_macd(close_prices)
        bb_data = self.calculate_bollinger_bands(close_prices)
        
        # Current values
        current_price = close_prices.iloc[-1]
        current_sma_20 = sma_20.iloc[-1]
        current_sma_50 = sma_50.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd_data['macd'].iloc[-1]
        current_signal = macd_data['signal'].iloc[-1]
        current_bb_upper = bb_data['upper'].iloc[-1]
        current_bb_lower = bb_data['lower'].iloc[-1]
        
        # Trend analysis
        trend = "UPTREND" if current_sma_20 > current_sma_50 else "DOWNTREND"
        
        # Momentum analysis
        if current_rsi > 70:
            momentum = "OVERBOUGHT"
        elif current_rsi < 30:
            momentum = "OVERSOLD"
        else:
            momentum = "NEUTRAL"
        
        # MACD analysis
        macd_signal_type = "BULLISH" if current_macd > current_signal else "BEARISH"
        
        # Bollinger Bands analysis
        if current_price > current_bb_upper:
            bb_signal = "UPPER_BAND_TOUCH"
        elif current_price < current_bb_lower:
            bb_signal = "LOWER_BAND_TOUCH"
        else:
            bb_signal = "WITHIN_BANDS"
        
        return {
            'symbol': self.symbol,
            'current_price': current_price,
            'sma_20': current_sma_20,
            'sma_50': current_sma_50,
            'rsi': current_rsi,
            'macd': current_macd,
            'macd_signal': current_signal,
            'bb_upper': current_bb_upper,
            'bb_lower': current_bb_lower,
            'trend': trend,
            'momentum': momentum,
            'macd_signal_type': macd_signal_type,
            'bb_signal': bb_signal,
            'timestamp': datetime.datetime.now()
        }
    
    def generate_signal(self, analysis: Dict) -> str:
        """Generate trading signal based on analysis"""
        if 'error' in analysis:
            return "ERROR"
        
        # Multi-factor signal generation
        signals = []
        
        # Trend signals
        if analysis['trend'] == "UPTREND" and analysis['sma_20'] > analysis['sma_50']:
            signals.append("TREND_UP")
        elif analysis['trend'] == "DOWNTREND" and analysis['sma_20'] < analysis['sma_50']:
            signals.append("TREND_DOWN")
        
        # RSI signals
        if analysis['rsi'] < 30:
            signals.append("RSI_OVERSOLD")
        elif analysis['rsi'] > 70:
            signals.append("RSI_OVERBOUGHT")
        
        # MACD signals
        if analysis['macd'] > analysis['macd_signal']:
            signals.append("MACD_BULLISH")
        else:
            signals.append("MACD_BEARISH")
        
        # Bollinger Bands signals
        if analysis['bb_signal'] == "LOWER_BAND_TOUCH":
            signals.append("BB_OVERSOLD")
        elif analysis['bb_signal'] == "UPPER_BAND_TOUCH":
            signals.append("BB_OVERBOUGHT")
        
        # Combine signals
        buy_signals = [s for s in signals if any(x in s for x in ['UP', 'BULLISH', 'OVERSOLD'])]
        sell_signals = [s for s in signals if any(x in s for x in ['DOWN', 'BEARISH', 'OVERBOUGHT'])]
        
        if len(buy_signals) >= 2:
            return "STRONG_BUY"
        elif len(sell_signals) >= 2:
            return "STRONG_SELL"
        elif len(buy_signals) == 1:
            return "WEAK_BUY"
        elif len(sell_signals) == 1:
            return "WEAK_SELL"
        else:
            return "HOLD"
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return []
        
        return [
            {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': pos.type,
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'profit': pos.profit,
                'time': datetime.datetime.fromtimestamp(pos.time)
            }
            for pos in positions
        ]
    
    def place_order(self, order_type: str, volume: float, price: float = None, 
                   sl: float = None, tp: float = None) -> bool:
        """Place a trading order"""
        if not self.connected:
            return False
        
        # Get current price if not provided
        if price is None:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return False
            price = tick.ask if order_type == "BUY" else tick.bid
        
        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Python Trading Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp
        
        # Send order
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed: {result.retcode} - {result.comment}")
            return False
        
        print(f"Order placed successfully: {order_type} {volume} {self.symbol} @ {price}")
        return True

def run_trading_demo():
    """Run the trading strategy demo"""
    print("MetaTrader 5 Trading Strategy Demo")
    print("=" * 50)
    
    # Create strategy instance
    strategy = TradingStrategy("EURUSD", mt5.TIMEFRAME_H1)
    
    # Connect to MT5
    if not strategy.connect():
        print("Failed to connect to MT5")
        return
    
    print(f"\nAnalyzing {strategy.symbol}...")
    
    # Perform market analysis
    analysis = strategy.analyze_market()
    
    if 'error' in analysis:
        print(f"Analysis error: {analysis['error']}")
        return
    
    # Display analysis results
    print("\n" + "=" * 50)
    print("MARKET ANALYSIS")
    print("=" * 50)
    print(f"Symbol: {analysis['symbol']}")
    print(f"Current Price: {analysis['current_price']:.5f}")
    print(f"SMA 20: {analysis['sma_20']:.5f}")
    print(f"SMA 50: {analysis['sma_50']:.5f}")
    print(f"RSI: {analysis['rsi']:.2f}")
    print(f"MACD: {analysis['macd']:.5f}")
    print(f"MACD Signal: {analysis['macd_signal']:.5f}")
    print(f"BB Upper: {analysis['bb_upper']:.5f}")
    print(f"BB Lower: {analysis['bb_lower']:.5f}")
    print(f"Trend: {analysis['trend']}")
    print(f"Momentum: {analysis['momentum']}")
    print(f"MACD Signal Type: {analysis['macd_signal_type']}")
    print(f"BB Signal: {analysis['bb_signal']}")
    
    # Generate trading signal
    signal = strategy.generate_signal(analysis)
    print(f"\nTrading Signal: {signal}")
    
    # Check current positions
    positions = strategy.get_positions()
    print(f"\nCurrent Positions: {len(positions)}")
    for pos in positions:
        print(f"  {pos['symbol']} {pos['type']} {pos['volume']} @ {pos['price_open']} (P&L: ${pos['profit']:.2f})")
    
    print("\n" + "=" * 50)
    print("Demo completed!")
    print("\nNote: This is analysis only. No real trades were placed.")
    print("To place real trades, uncomment the trading code in the script.")

def main():
    """Main function"""
    run_trading_demo()

if __name__ == "__main__":
    main()
