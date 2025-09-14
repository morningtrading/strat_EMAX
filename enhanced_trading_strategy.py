#!/usr/bin/env python3
"""
Enhanced MetaTrader 5 Trading Strategy
Advanced trading strategy with configurable indicators and risk management
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import datetime
import time
import os
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class TradeSignal:
    """Data class for trade signals"""
    signal_type: str  # BUY, SELL, HOLD
    strength: str     # STRONG, WEAK
    confidence: float # 0.0 to 1.0
    indicators_used: List[str]
    reasoning: str

class EnhancedTradingStrategy:
    """Enhanced Trading Strategy with configurable indicators and risk management"""
    
    def __init__(self, config_file: str = "trading_config.json"):
        self.config = self.load_config(config_file)
        self.connected = False
        self.account_info = None
        self.daily_stats = {
            'trades_today': 0,
            'profit_today': 0.0,
            'loss_today': 0.0,
            'consecutive_losses': 0
        }
        self.portfolio_state_file = f"portfolio_state_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found. Using default settings.")
            return self.get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration if config file is not available"""
        return {
            "symbols": {"primary": "EURUSD"},
            "timeframe": "H1",
            "indicators": {
                "sma": {"enabled": True, "periods": [20, 50]},
                "rsi": {"enabled": True, "period": 14}
            },
            "risk_management": {
                "position_sizing": {"risk_per_trade": 0.02}
            }
        }
    
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
    
    def get_rates(self, symbol: str, count: int = 100) -> Optional[pd.DataFrame]:
        """Get historical price data"""
        if not self.connected:
            return None
        
        timeframe_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        
        timeframe = timeframe_map.get(self.config["timeframe"], mt5.TIMEFRAME_H1)
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df
    
    # Technical Indicators
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
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Dict:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return williams_r
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict:
        """Calculate Average Directional Index"""
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        dm_plus = high - high.shift(1)
        dm_minus = low.shift(1) - low
        
        dm_plus = np.where((dm_plus > dm_minus) & (dm_plus > 0), dm_plus, 0)
        dm_minus = np.where((dm_minus > dm_plus) & (dm_minus > 0), dm_minus, 0)
        
        # Smoothed values
        atr = tr.rolling(window=period).mean()
        di_plus = 100 * (pd.Series(dm_plus).rolling(window=period).mean() / atr)
        di_minus = 100 * (pd.Series(dm_minus).rolling(window=period).mean() / atr)
        
        # ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(window=period).mean()
        
        return {
            'adx': adx,
            'di_plus': di_plus,
            'di_minus': di_minus
        }
    
    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())) if len(x) > 0 else np.nan)
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all enabled indicators"""
        indicators = {}
        
        if df is None or len(df) < 50:
            return indicators
        
        close = df['close']
        high = df['high']
        low = df['low']
        
        # SMA
        if self.config['indicators']['sma']['enabled']:
            for period in self.config['indicators']['sma']['periods']:
                indicators[f'sma_{period}'] = self.calculate_sma(close, period)
        
        # EMA
        if self.config['indicators']['ema']['enabled']:
            for period in self.config['indicators']['ema']['periods']:
                indicators[f'ema_{period}'] = self.calculate_ema(close, period)
        
        # RSI
        if self.config['indicators']['rsi']['enabled']:
            indicators['rsi'] = self.calculate_rsi(close, self.config['indicators']['rsi']['period'])
        
        # MACD
        if self.config['indicators']['macd']['enabled']:
            macd_config = self.config['indicators']['macd']
            macd_data = self.calculate_macd(close, macd_config['fast'], macd_config['slow'], macd_config['signal'])
            indicators.update(macd_data)
        
        # Bollinger Bands
        if self.config['indicators']['bollinger_bands']['enabled']:
            bb_config = self.config['indicators']['bollinger_bands']
            bb_data = self.calculate_bollinger_bands(close, bb_config['period'], bb_config['std_dev'])
            indicators.update(bb_data)
        
        # Stochastic
        if self.config['indicators']['stochastic']['enabled']:
            stoch_config = self.config['indicators']['stochastic']
            stoch_data = self.calculate_stochastic(high, low, close, stoch_config['k_period'], stoch_config['d_period'])
            indicators.update(stoch_data)
        
        # Williams %R
        if self.config['indicators']['williams_r']['enabled']:
            indicators['williams_r'] = self.calculate_williams_r(high, low, close, self.config['indicators']['williams_r']['period'])
        
        # ADX
        if self.config['indicators']['adx']['enabled']:
            adx_data = self.calculate_adx(high, low, close, self.config['indicators']['adx']['period'])
            indicators.update(adx_data)
        
        # CCI
        if self.config['indicators']['cci']['enabled']:
            indicators['cci'] = self.calculate_cci(high, low, close, self.config['indicators']['cci']['period'])
        
        # ATR
        if self.config['indicators']['atr']['enabled']:
            indicators['atr'] = self.calculate_atr(high, low, close, self.config['indicators']['atr']['period'])
        
        return indicators
    
    def analyze_market(self, symbol: str = None) -> Dict:
        """Comprehensive market analysis using all enabled indicators"""
        if symbol is None:
            symbol = self.config['symbols']['primary']
        
        df = self.get_rates(symbol, 200)
        if df is None or len(df) < 50:
            return {"error": "Insufficient data"}
        
        indicators = self.calculate_all_indicators(df)
        current_price = df['close'].iloc[-1]
        
        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'timestamp': datetime.datetime.now(),
            'indicators': {},
            'signals': {}
        }
        
        # Get current indicator values
        for name, indicator in indicators.items():
            if isinstance(indicator, pd.Series) and not indicator.empty:
                analysis['indicators'][name] = indicator.iloc[-1]
            elif isinstance(indicator, dict):
                analysis['indicators'][name] = {}
                for key, value in indicator.items():
                    if isinstance(value, pd.Series) and not value.empty:
                        analysis['indicators'][name][key] = value.iloc[-1]
        
        return analysis
    
    def generate_trading_signal(self, analysis: Dict) -> TradeSignal:
        """Generate trading signal based on weighted indicator analysis"""
        if 'error' in analysis:
            return TradeSignal("HOLD", "WEAK", 0.0, [], "Error in analysis")
        
        buy_signals = []
        sell_signals = []
        indicators_used = []
        total_weight = 0
        
        indicators = analysis['indicators']
        current_price = analysis['current_price']
        
        # SMA Analysis
        if self.config['indicators']['sma']['enabled']:
            sma_config = self.config['indicators']['sma']
            weight = sma_config['weight']
            total_weight += weight
            
            sma_20 = indicators.get('sma_20')
            sma_50 = indicators.get('sma_50')
            
            if sma_20 and sma_50:
                indicators_used.append('SMA')
                if sma_20 > sma_50:
                    buy_signals.append(('SMA_UPTREND', weight))
                else:
                    sell_signals.append(('SMA_DOWNTREND', weight))
        
        # RSI Analysis
        if self.config['indicators']['rsi']['enabled']:
            rsi_config = self.config['indicators']['rsi']
            weight = rsi_config['weight']
            total_weight += weight
            
            rsi = indicators.get('rsi')
            if rsi:
                indicators_used.append('RSI')
                if rsi < rsi_config['oversold']:
                    buy_signals.append(('RSI_OVERSOLD', weight))
                elif rsi > rsi_config['overbought']:
                    sell_signals.append(('RSI_OVERBOUGHT', weight))
        
        # MACD Analysis
        if self.config['indicators']['macd']['enabled']:
            macd_config = self.config['indicators']['macd']
            weight = macd_config['weight']
            total_weight += weight
            
            macd = indicators.get('macd')
            macd_signal = indicators.get('signal')
            
            if macd and macd_signal:
                indicators_used.append('MACD')
                if macd > macd_signal:
                    buy_signals.append(('MACD_BULLISH', weight))
                else:
                    sell_signals.append(('MACD_BEARISH', weight))
        
        # Bollinger Bands Analysis
        if self.config['indicators']['bollinger_bands']['enabled']:
            bb_config = self.config['indicators']['bollinger_bands']
            weight = bb_config['weight']
            total_weight += weight
            
            bb_upper = indicators.get('upper')
            bb_lower = indicators.get('lower')
            
            if bb_upper and bb_lower:
                indicators_used.append('BB')
                if current_price < bb_lower:
                    buy_signals.append(('BB_OVERSOLD', weight))
                elif current_price > bb_upper:
                    sell_signals.append(('BB_OVERBOUGHT', weight))
        
        # Stochastic Analysis
        if self.config['indicators']['stochastic']['enabled']:
            stoch_config = self.config['indicators']['stochastic']
            weight = stoch_config['weight']
            total_weight += weight
            
            stoch_k = indicators.get('k')
            stoch_d = indicators.get('d')
            
            if stoch_k and stoch_d:
                indicators_used.append('STOCH')
                if stoch_k < stoch_config['oversold'] and stoch_d < stoch_config['oversold']:
                    buy_signals.append(('STOCH_OVERSOLD', weight))
                elif stoch_k > stoch_config['overbought'] and stoch_d > stoch_config['overbought']:
                    sell_signals.append(('STOCH_OVERBOUGHT', weight))
        
        # Williams %R Analysis
        if self.config['indicators']['williams_r']['enabled']:
            wr_config = self.config['indicators']['williams_r']
            weight = wr_config['weight']
            total_weight += weight
            
            williams_r = indicators.get('williams_r')
            if williams_r:
                indicators_used.append('WILLIAMS_R')
                if williams_r < wr_config['oversold']:
                    buy_signals.append(('WR_OVERSOLD', weight))
                elif williams_r > wr_config['overbought']:
                    sell_signals.append(('WR_OVERBOUGHT', weight))
        
        # ADX Analysis
        if self.config['indicators']['adx']['enabled']:
            adx_config = self.config['indicators']['adx']
            weight = adx_config['weight']
            total_weight += weight
            
            adx = indicators.get('adx')
            if adx and adx > adx_config['strong_trend_threshold']:
                indicators_used.append('ADX')
                # ADX confirms trend strength, doesn't give direction
        
        # CCI Analysis
        if self.config['indicators']['cci']['enabled']:
            cci_config = self.config['indicators']['cci']
            weight = cci_config['weight']
            total_weight += weight
            
            cci = indicators.get('cci')
            if cci:
                indicators_used.append('CCI')
                if cci < cci_config['oversold']:
                    buy_signals.append(('CCI_OVERSOLD', weight))
                elif cci > cci_config['overbought']:
                    sell_signals.append(('CCI_OVERBOUGHT', weight))
        
        # Calculate signal strength
        buy_strength = sum([weight for _, weight in buy_signals]) / total_weight if total_weight > 0 else 0
        sell_strength = sum([weight for _, weight in sell_signals]) / total_weight if total_weight > 0 else 0
        
        # Determine signal
        signal_threshold = self.config['trading_settings']['signal_threshold']
        
        if buy_strength >= signal_threshold['strong_buy']:
            signal_type = "BUY"
            strength = "STRONG"
            confidence = buy_strength
            reasoning = f"Strong buy signal from {len(buy_signals)} indicators"
        elif sell_strength >= signal_threshold['strong_sell']:
            signal_type = "SELL"
            strength = "STRONG"
            confidence = sell_strength
            reasoning = f"Strong sell signal from {len(sell_signals)} indicators"
        elif buy_strength >= signal_threshold['weak_buy']:
            signal_type = "BUY"
            strength = "WEAK"
            confidence = buy_strength
            reasoning = f"Weak buy signal from {len(buy_signals)} indicators"
        elif sell_strength >= signal_threshold['weak_sell']:
            signal_type = "SELL"
            strength = "WEAK"
            confidence = sell_strength
            reasoning = f"Weak sell signal from {len(sell_signals)} indicators"
        else:
            signal_type = "HOLD"
            strength = "WEAK"
            confidence = max(buy_strength, sell_strength)
            reasoning = "No clear signal from indicators"
        
        return TradeSignal(signal_type, strength, confidence, indicators_used, reasoning)
    
    def calculate_position_size(self, signal: TradeSignal, current_price: float) -> float:
        """Calculate position size based on risk management rules"""
        if not self.account_info:
            return 0.0
        
        risk_config = self.config['risk_management']['position_sizing']
        
        # Base position size calculation
        account_balance = self.account_info.balance
        risk_per_trade = risk_config['risk_per_trade']
        
        # Calculate stop loss distance
        stop_loss_pips = self.calculate_stop_loss(current_price)
        if stop_loss_pips == 0:
            return 0.0
        
        # Calculate position size based on risk
        risk_amount = account_balance * risk_per_trade
        pip_value = self.get_pip_value()
        position_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Apply maximum position size limit
        max_position_size = account_balance * risk_config['max_position_size']
        max_volume = max_position_size / current_price
        position_size = min(position_size, max_volume)
        
        return round(position_size, 2)
    
    def calculate_stop_loss(self, current_price: float) -> float:
        """Calculate stop loss distance in price units"""
        risk_config = self.config['risk_management']['stop_loss']
        method = risk_config['method']
        
        if method == "fixed_pips":
            # For Gold, convert pips to price units (1 pip = 0.01 for Gold)
            return risk_config['fixed_pips'] * 0.01
        elif method == "percentage":
            return current_price * risk_config['percentage']
        elif method == "atr":
            # This would need ATR data - simplified for now
            # Assume ATR of 2.0 for Gold
            return risk_config['atr_multiplier'] * 2.0
        else:
            # Default: 50 pips = 0.5 price units for Gold
            return 0.5
    
    def calculate_take_profit(self, current_price: float, stop_loss_pips: float) -> float:
        """Calculate take profit distance in price units"""
        risk_config = self.config['risk_management']['take_profit']
        method = risk_config['method']
        
        if method == "risk_reward":
            return stop_loss_pips * risk_config['risk_reward_ratio']
        elif method == "fixed_pips":
            # For Gold, convert pips to price units
            return risk_config['fixed_pips'] * 0.01
        elif method == "percentage":
            return current_price * risk_config['percentage']
        else:
            return stop_loss_pips * 2  # Default 2:1 ratio
    
    def get_pip_value(self) -> float:
        """Get pip value for the symbol (simplified)"""
        # This is a simplified version - in reality, pip value depends on account currency and symbol
        return 10.0  # Assume $10 per pip for EURUSD
    
    def check_risk_limits(self) -> bool:
        """Check if trading is allowed based on risk limits"""
        risk_config = self.config['risk_management']
        
        # Check daily loss limit
        if risk_config['daily_loss_limit']['enabled']:
            if self.daily_stats['loss_today'] >= self.account_info.balance * risk_config['daily_loss_limit']['max_daily_loss']:
                print("Daily loss limit reached. Trading stopped.")
                return False
        
        # Check consecutive losses
        if self.daily_stats['consecutive_losses'] >= risk_config['daily_loss_limit']['max_consecutive_losses']:
            print("Maximum consecutive losses reached. Trading stopped.")
            return False
        
        # Check maximum drawdown
        if risk_config['max_drawdown']['enabled']:
            current_equity = self.account_info.equity
            max_equity = current_equity + self.daily_stats['loss_today']
            drawdown = (max_equity - current_equity) / max_equity
            
            if drawdown >= risk_config['max_drawdown']['max_drawdown_percentage']:
                print(f"Maximum drawdown reached: {drawdown:.2%}")
                return False
        
        return True
    
    def save_portfolio_state(self):
        """Save current portfolio state to JSON file"""
        positions = self.get_positions()
        
        state = {
            "timestamp": datetime.datetime.now().isoformat(),
            "account_info": {
                "login": self.account_info.login,
                "balance": self.account_info.balance,
                "equity": self.account_info.equity,
                "margin": self.account_info.margin,
                "margin_free": self.account_info.margin_free
            },
            "positions": [
                {
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": pos.type,
                    "volume": pos.volume,
                    "price_open": pos.price_open,
                    "price_current": pos.price_current,
                    "profit": pos.profit
                } for pos in positions
            ],
            "daily_stats": self.daily_stats,
            "risk_settings": self.config['risk_management']
        }
        
        with open(self.portfolio_state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def get_positions(self):
        """Get current positions"""
        return mt5.positions_get() or []
    
    def run_analysis(self, symbol: str = None):
        """Run comprehensive market analysis"""
        print("Enhanced Trading Strategy Analysis")
        print("=" * 50)
        
        analysis = self.analyze_market(symbol)
        if 'error' in analysis:
            print(f"Analysis error: {analysis['error']}")
            return
        
        signal = self.generate_trading_signal(analysis)
        
        print(f"\nSymbol: {analysis['symbol']}")
        print(f"Current Price: {analysis['current_price']:.5f}")
        print(f"Timestamp: {analysis['timestamp']}")
        
        print(f"\nTrading Signal: {signal.signal_type} ({signal.strength})")
        print(f"Confidence: {signal.confidence:.2%}")
        print(f"Indicators Used: {', '.join(signal.indicators_used)}")
        print(f"Reasoning: {signal.reasoning}")
        
        # Display indicator values
        print(f"\nIndicator Values:")
        for name, value in analysis['indicators'].items():
            if isinstance(value, dict):
                print(f"  {name}:")
                for key, val in value.items():
                    print(f"    {key}: {val:.5f}")
            else:
                print(f"  {name}: {value:.5f}")
        
        # Risk assessment
        if signal.signal_type != "HOLD":
            position_size = self.calculate_position_size(signal, analysis['current_price'])
            stop_loss_pips = self.calculate_stop_loss(analysis['current_price'])
            take_profit_pips = self.calculate_take_profit(analysis['current_price'], stop_loss_pips)
            
            print(f"\nRisk Management:")
            print(f"  Suggested Position Size: {position_size}")
            print(f"  Stop Loss: {stop_loss_pips:.1f} pips")
            print(f"  Take Profit: {take_profit_pips:.1f} pips")
            print(f"  Risk/Reward Ratio: {take_profit_pips/stop_loss_pips:.1f}:1")

def main():
    """Main function to run the enhanced trading strategy"""
    strategy = EnhancedTradingStrategy()
    
    if not strategy.connect():
        print("Failed to connect to MT5")
        return
    
    # Run analysis
    strategy.run_analysis()
    
    # Save portfolio state
    strategy.save_portfolio_state()
    
    print("\n" + "=" * 50)
    print("Analysis completed!")

if __name__ == "__main__":
    main()
