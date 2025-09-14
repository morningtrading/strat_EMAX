#!/usr/bin/env python3
"""
Optimized Backtesting Engine with Accurate Signal Generation
Maintains original signal logic while optimizing performance
"""

import pandas as pd
import numpy as np
import json
import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from data_loader import DataLoader
from enhanced_trading_strategy import EnhancedTradingStrategy, TradeSignal

@dataclass
class Trade:
    """Trade record"""
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    entry_time: datetime.datetime
    exit_time: datetime.datetime
    volume: float
    pnl: float
    commission: float
    exit_reason: str
    duration_minutes: int
    indicators_used: List[str]
    signal_strength: float

@dataclass
class BacktestResults:
    """Backtest results container"""
    start_date: datetime.datetime
    end_date: datetime.datetime
    initial_balance: float
    final_balance: float
    total_return: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    trades: List[Trade]
    equity_curve: pd.DataFrame

class OptimizedBacktestingEngine:
    """Optimized backtesting engine that maintains accuracy while improving speed"""
    
    def __init__(self, config_file: str = "trading_config.json", data_directory: str = "Z:\\"):
        self.config = self.load_config(config_file)
        self.data_loader = DataLoader(data_directory)
        self.strategy = EnhancedTradingStrategy(config_file)
        
        # Execution settings
        self.commission_per_lot = 0.0
        self.slippage_pips = 0.5
        self.spread_pips = 2.0
        
        # Backtest state
        self.current_balance = 0.0
        self.current_positions = {}
        self.trades_history = []
        self.equity_curve = []
        self.max_balance = 0.0
        
        # Performance optimization: Pre-calculate indicators
        self.indicators_cache = {}
        self.indicators_calculated = False
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found. Using default settings.")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "symbols": {"primary": "EURUSD"},
            "timeframe": "H1",
            "indicators": {
                "sma": {"enabled": True, "periods": [20, 50], "weight": 0.15},
                "rsi": {"enabled": True, "period": 14, "weight": 0.20}
            },
            "risk_management": {
                "position_sizing": {"risk_per_trade": 0.02}
            }
        }
    
    def precalculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Pre-calculate all indicators once for the entire dataset"""
        print("🔄 Pre-calculating indicators for performance optimization...")
        
        indicators = {}
        
        if df is None or len(df) < 50:
            return indicators
        
        close = df['close']
        high = df['high']
        low = df['low']
        
        # Calculate all indicators at once using the same logic as EnhancedTradingStrategy
        config = self.strategy.config
        
        # SMA - vectorized calculation
        if config['indicators']['sma']['enabled']:
            for period in config['indicators']['sma']['periods']:
                indicators[f'sma_{period}'] = close.rolling(window=period).mean()
        
        # EMA - vectorized calculation
        if config['indicators']['ema']['enabled']:
            for period in config['indicators']['ema']['periods']:
                indicators[f'ema_{period}'] = close.ewm(span=period).mean()
        
        # RSI - vectorized calculation
        if config['indicators']['rsi']['enabled']:
            period = config['indicators']['rsi']['period']
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD - vectorized calculation
        if config['indicators']['macd']['enabled']:
            fast = config['indicators']['macd']['fast']
            slow = config['indicators']['macd']['slow']
            signal = config['indicators']['macd']['signal']
            
            ema_fast = close.ewm(span=fast).mean()
            ema_slow = close.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            indicators['macd'] = macd_line
            indicators['macd_signal'] = signal_line
            indicators['macd_histogram'] = histogram
        
        # Bollinger Bands - vectorized calculation
        if config['indicators']['bollinger_bands']['enabled']:
            period = config['indicators']['bollinger_bands']['period']
            std_dev = config['indicators']['bollinger_bands']['std_dev']
            
            sma = close.rolling(window=period).mean()
            std = close.rolling(window=period).std()
            
            indicators['bb_upper'] = sma + (std * std_dev)
            indicators['bb_middle'] = sma
            indicators['bb_lower'] = sma - (std * std_dev)
        
        # Stochastic - vectorized calculation
        if config['indicators']['stochastic']['enabled']:
            k_period = config['indicators']['stochastic']['k_period']
            d_period = config['indicators']['stochastic']['d_period']
            
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            indicators['stoch_k'] = k_percent
            indicators['stoch_d'] = d_percent
        
        # Williams %R - vectorized calculation
        if config['indicators']['williams_r']['enabled']:
            period = config['indicators']['williams_r']['period']
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            indicators['williams_r'] = -100 * ((highest_high - close) / (highest_high - lowest_low))
        
        # ADX - vectorized calculation
        if config['indicators']['adx']['enabled']:
            period = config['indicators']['adx']['period']
            
            # Calculate True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate Directional Movement
            dm_plus = high.diff()
            dm_minus = -low.diff()
            
            dm_plus = dm_plus.where((dm_plus > dm_minus) & (dm_plus > 0), 0)
            dm_minus = dm_minus.where((dm_minus > dm_plus) & (dm_minus > 0), 0)
            
            # Calculate smoothed values
            atr = tr.rolling(window=period).mean()
            di_plus = 100 * (dm_plus.rolling(window=period).mean() / atr)
            di_minus = 100 * (dm_minus.rolling(window=period).mean() / atr)
            
            # Calculate ADX
            dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
            indicators['adx'] = dx.rolling(window=period).mean()
        
        # CCI - vectorized calculation
        if config['indicators']['cci']['enabled']:
            period = config['indicators']['cci']['period']
            typical_price = (high + low + close) / 3
            sma_tp = typical_price.rolling(window=period).mean()
            mean_deviation = typical_price.rolling(window=period).apply(
                lambda x: np.mean(np.abs(x - x.mean())) if len(x) > 0 else np.nan
            )
            indicators['cci'] = (typical_price - sma_tp) / (0.015 * mean_deviation)
        
        # ATR - vectorized calculation
        if config['indicators']['atr']['enabled']:
            period = config['indicators']['atr']['period']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            indicators['atr'] = tr.rolling(window=period).mean()
        
        print(f"✅ Pre-calculated {len(indicators)} indicator series")
        return indicators
    
    def create_analysis_from_indicators(self, current_indicators: Dict, current_price: float, 
                                       symbol: str, timestamp: datetime.datetime) -> Dict:
        """Create analysis dictionary from pre-calculated indicators (same format as original)"""
        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'timestamp': timestamp,
            'indicators': {}
        }
        
        # Convert indicator values to the same format as original
        for name, value in current_indicators.items():
            if not pd.isna(value):
                analysis['indicators'][name] = value
        
        return analysis
    
    def calculate_position_size_optimized(self, balance: float, entry_price: float, 
                                        stop_loss: float, risk_per_trade: float) -> float:
        """Optimized position size calculation"""
        risk_amount = balance * risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0.0
        
        # For Gold (commodity), calculate position size based on price risk
        lot_size = 100  # Standard lot size for Gold
        position_size = risk_amount / (price_risk * lot_size)
        
        # Apply maximum position size limit
        max_position_size = min(position_size, 1.0)
        
        return round(max_position_size, 2)
    
    def apply_execution_costs_optimized(self, price: float, direction: str, volume: float) -> Tuple[float, float]:
        """Optimized execution cost calculation"""
        spread_amount = self.spread_pips * 0.01  # For Gold
        
        if direction == 'LONG':
            execution_price = price + spread_amount
        else:  # SHORT
            execution_price = price - spread_amount
        
        # Apply slippage
        slippage_amount = self.slippage_pips * 0.01
        if direction == 'LONG':
            execution_price += slippage_amount
        else:
            execution_price -= slippage_amount
        
        # Calculate commission
        commission = volume * self.commission_per_lot
        
        return execution_price, commission
    
    def execute_trade_optimized(self, symbol: str, direction: str, price: float, 
                               timestamp: datetime.datetime, volume: float, signal: TradeSignal) -> Trade:
        """Optimized trade execution"""
        # Apply execution costs
        execution_price, commission = self.apply_execution_costs_optimized(price, direction, volume)
        
        # Calculate stop loss and take profit using strategy methods
        stop_loss_distance = self.strategy.calculate_stop_loss(execution_price)
        take_profit_distance = self.strategy.calculate_take_profit(execution_price, stop_loss_distance)
        
        if direction == 'LONG':
            stop_loss = execution_price - stop_loss_distance
            take_profit = execution_price + take_profit_distance
        else:  # SHORT
            stop_loss = execution_price + stop_loss_distance
            take_profit = execution_price - take_profit_distance
        
        # Create trade
        trade = Trade(
            symbol=symbol,
            direction=direction,
            entry_price=execution_price,
            exit_price=0.0,
            entry_time=timestamp,
            exit_time=None,
            volume=volume,
            pnl=0.0,
            commission=commission,
            exit_reason="",
            duration_minutes=0,
            indicators_used=signal.indicators_used,
            signal_strength=signal.confidence
        )
        
        # Store stop loss and take profit
        trade.stop_loss = stop_loss
        trade.take_profit = take_profit
        
        return trade
    
    def close_trade_optimized(self, trade: Trade, exit_price: float, exit_time: datetime.datetime, 
                             exit_reason: str) -> Trade:
        """Optimized trade closing"""
        trade.exit_price = exit_price
        trade.exit_time = exit_time
        trade.exit_reason = exit_reason
        
        # Calculate duration
        duration = exit_time - trade.entry_time
        trade.duration_minutes = int(duration.total_seconds() / 60)
        
        # Calculate P&L for Gold
        lot_size = 100  # Standard lot size for Gold
        price_diff = exit_price - trade.entry_price
        if trade.direction == 'SHORT':
            price_diff = -price_diff
        
        trade.pnl = price_diff * trade.volume * lot_size - trade.commission
        
        return trade
    
    def run_backtest_optimized(self, symbol: str, start_date: datetime.datetime = None, 
                              end_date: datetime.datetime = None, initial_balance: float = 10000) -> BacktestResults:
        """Optimized backtesting that maintains original accuracy"""
        
        print(f"⚡ OPTIMIZED BACKTESTING MODE (Accurate + Fast)")
        print(f"Starting backtest for {symbol}")
        print(f"Initial balance: ${initial_balance:,.2f}")
        
        # Load data
        df = self.load_data(symbol)
        if df is None:
            raise ValueError(f"Failed to load data for {symbol}")
        
        # Filter data by date range
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        
        if len(df) < 100:
            raise ValueError("Insufficient data for backtesting")
        
        print(f"Backtesting period: {df.index[0]} to {df.index[-1]}")
        print(f"Total bars: {len(df)}")
        
        # Initialize state
        self.current_balance = initial_balance
        self.current_positions = {}
        self.trades_history = []
        self.equity_curve = []
        self.max_balance = initial_balance
        
        # MAJOR OPTIMIZATION: Pre-calculate all indicators once
        print("📊 Pre-calculating indicators...")
        indicators = self.precalculate_indicators(df)
        self.indicators_calculated = True
        
        # Find minimum bars needed for indicators
        min_bars = 50  # Conservative estimate
        
        # Tracking variables for display
        cumulative_pnl = 0.0
        wins = 0
        losses = 0
        win_rate = 0.0
        
        print(f"\n{'='*120}")
        print(f"{'ACTION':<15} {'DIRECTION':<8} {'PRICE':<10} {'REASON':<12} {'P&L':<10} {'CUM_P&L':<9} {'WINS':<5} {'LOSSES':<6} {'WIN_RATE':<7} {'DURATION':<8}")
        print(f"{'='*120}")
        
        # Run backtest - MAIN LOOP
        for i in range(min_bars, len(df)):
            current_bar = df.iloc[i]
            current_price = current_bar['close']
            timestamp = df.index[i]
            
            # MAJOR OPTIMIZATION: Get current indicator values from pre-calculated series
            current_indicators = {}
            for name, indicator_series in indicators.items():
                if not pd.isna(indicator_series.iloc[i]):
                    current_indicators[name] = indicator_series.iloc[i]
            
            # Create analysis dictionary (same format as original)
            analysis = self.create_analysis_from_indicators(current_indicators, current_price, symbol, timestamp)
            
            # Generate trading signal using ORIGINAL strategy logic
            signal = self.strategy.generate_trading_signal(analysis)
            
            # Check for exit conditions on existing positions
            if symbol in self.current_positions:
                trade = self.current_positions[symbol]
                exit_reason = None
                exit_price = current_price
                
                # Check stop loss and take profit
                if trade.direction == 'LONG':
                    if current_price <= trade.stop_loss:
                        exit_reason = 'SL'
                    elif current_price >= trade.take_profit:
                        exit_reason = 'TP'
                else:  # SHORT
                    if current_price >= trade.stop_loss:
                        exit_reason = 'SL'
                    elif current_price <= trade.take_profit:
                        exit_reason = 'TP'
                
                # Close trade if exit condition met
                if exit_reason:
                    closed_trade = self.close_trade_optimized(trade, exit_price, timestamp, exit_reason)
                    self.trades_history.append(closed_trade)
                    self.current_balance += closed_trade.pnl
                    
                    # Update tracking variables
                    cumulative_pnl += closed_trade.pnl
                    if closed_trade.pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                    
                    # Display trade result
                    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
                    duration_minutes = closed_trade.duration_minutes
                    print(f"{'CLOSED':<15} {trade.direction:<8} {exit_price:<10.1f} {exit_reason:<12} "
                          f"${closed_trade.pnl:<9.1f} ${cumulative_pnl:<9.1f} {wins:<5} {losses:<6} {win_rate:<7.1f}% {duration_minutes:<8}m")
                    
                    del self.current_positions[symbol]
            
            # Check for new trading signals
            if symbol not in self.current_positions and signal.signal_type != 'HOLD':
                # Calculate position size
                risk_per_trade = self.config['risk_management']['position_sizing']['risk_per_trade']
                volume = self.calculate_position_size_optimized(self.current_balance, current_price, 
                                                              current_price * 0.98, risk_per_trade)
                
                if volume > 0:
                    # Execute trade
                    direction = 'LONG' if signal.signal_type == 'BUY' else 'SHORT'
                    trade = self.execute_trade_optimized(symbol, direction, current_price, timestamp, volume, signal)
                    
                    self.current_positions[symbol] = trade
                    
                    # Display trade opening
                    print(f"{'OPENED':<15} {trade.direction:<8} {trade.entry_price:<10.1f} {'SIGNAL':<12} "
                          f"{'--':<10} ${cumulative_pnl:<9.1f} {wins:<5} {losses:<6} {win_rate:<7.1f}% {'--':<8}")
            
            # Update equity curve (optimized - every 10 bars)
            current_equity = self.current_balance
            if symbol in self.current_positions:
                trade = self.current_positions[symbol]
                lot_size = 100
                unrealized_pnl = (current_price - trade.entry_price) * trade.volume * lot_size
                if trade.direction == 'SHORT':
                    unrealized_pnl = -unrealized_pnl
                current_equity += unrealized_pnl
            
            # Only store equity curve every 10 bars to reduce memory usage
            if i % 10 == 0:
                self.equity_curve.append({
                    'timestamp': timestamp,
                    'equity': current_equity,
                    'balance': self.current_balance,
                    'drawdown': (self.max_balance - current_equity) / self.max_balance if self.max_balance > 0 else 0
                })
            
            self.max_balance = max(self.max_balance, current_equity)
        
        # Close any remaining positions at end of data
        for trade in self.current_positions.values():
            final_price = df.iloc[-1]['close']
            final_time = df.index[-1]
            closed_trade = self.close_trade_optimized(trade, final_price, final_time, 'END_OF_DATA')
            self.trades_history.append(closed_trade)
            
            # Update tracking variables
            cumulative_pnl += closed_trade.pnl
            if closed_trade.pnl > 0:
                wins += 1
            else:
                losses += 1
            
            # Display final trade
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
            duration_minutes = closed_trade.duration_minutes
            print(f"{'CLOSED':<15} {trade.direction:<8} {final_price:<10.1f} {'END_OF_DATA':<12} "
                  f"${closed_trade.pnl:<9.1f} ${cumulative_pnl:<9.1f} {wins:<5} {losses:<6} {win_rate:<7.1f}% {duration_minutes:<8}m")
        
        # Calculate results
        results = self.calculate_results_optimized(initial_balance, df.index[0], df.index[-1])
        
        print(f"\nBacktest completed!")
        print(f"Final balance: ${results.final_balance:,.2f}")
        print(f"Total return: {results.total_return_pct:.2f}%")
        print(f"Total trades: {results.total_trades}")
        print(f"Win rate: {results.win_rate:.2f}%")
        print(f"Max drawdown: {results.max_drawdown_pct:.2f}%")
        
        return results
    
    def calculate_results_optimized(self, initial_balance: float, start_date: datetime.datetime, 
                                   end_date: datetime.datetime) -> BacktestResults:
        """Optimized results calculation"""
        
        # Basic metrics
        final_balance = self.current_balance
        total_return = final_balance - initial_balance
        total_return_pct = (total_return / initial_balance) * 100
        
        # Trade statistics
        total_trades = len(self.trades_history)
        winning_trades = len([t for t in self.trades_history if t.pnl > 0])
        losing_trades = len([t for t in self.trades_history if t.pnl < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # P&L statistics
        wins = [t.pnl for t in self.trades_history if t.pnl > 0]
        losses = [t.pnl for t in self.trades_history if t.pnl < 0]
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Maximum drawdown - use balance (realized P&L)
        equity_curve = pd.DataFrame(self.equity_curve)
        if not equity_curve.empty:
            running_max = equity_curve['balance'].expanding().max()
            drawdown = (equity_curve['balance'] - running_max) / running_max
            max_drawdown = drawdown.min()
            max_drawdown_pct = abs(max_drawdown) * 100
        else:
            max_drawdown = 0
            max_drawdown_pct = 0
        
        # Risk-adjusted ratios (simplified for speed)
        if not equity_curve.empty and len(equity_curve) > 1:
            returns = equity_curve['balance'].pct_change().dropna()
            if len(returns) > 1:
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                downside_returns = returns[returns < 0]
                sortino_ratio = returns.mean() / downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
                calmar_ratio = (total_return_pct / 100) / (max_drawdown_pct / 100) if max_drawdown_pct > 0 else 0
            else:
                sharpe_ratio = sortino_ratio = calmar_ratio = 0
        else:
            sharpe_ratio = sortino_ratio = calmar_ratio = 0
        
        return BacktestResults(
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            final_balance=final_balance,
            total_return=total_return,
            total_return_pct=total_return_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            trades=self.trades_history,
            equity_curve=equity_curve
        )
    
    def load_data(self, symbol: str, timeframe: str = None) -> Optional[pd.DataFrame]:
        """Load data for backtesting"""
        if timeframe is None:
            timeframe = self.config.get('timeframe', 'M1')
        
        # Try to load from filtered data first
        filtered_files = [
            f"{symbol}_XAUUSD_1min_1month_extreme_filtered.csv",
            f"{symbol}_XAUUSD_1min_1month_weekend_filtered.csv",
            f"{symbol}_XAUUSD_1min_1month.csv"
        ]
        
        for filename in filtered_files:
            try:
                df = self.data_loader.load_csv_data(f"Z:\\{filename}")
                if df is not None:
                    print(f"✅ Loaded data from {filename}")
                    return df
            except:
                continue
        
        print(f"❌ Failed to load data for {symbol}")
        return None

def main():
    """Demo function to test optimized backtesting"""
    print("⚡ OPTIMIZED BACKTESTING ENGINE DEMO (Accurate + Fast)")
    print("=" * 60)
    
    engine = OptimizedBacktestingEngine()
    
    # Run optimized backtest
    results = engine.run_backtest_optimized(
        symbol="15",
        start_date=datetime.datetime(2025, 9, 7),
        end_date=datetime.datetime(2025, 9, 14),
        initial_balance=10000
    )
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Total Return: {results.total_return_pct:.2f}%")
    print(f"Win Rate: {results.win_rate:.2f}%")
    print(f"Max Drawdown: {results.max_drawdown_pct:.2f}%")
    print(f"Total Trades: {results.total_trades}")

if __name__ == "__main__":
    main()
