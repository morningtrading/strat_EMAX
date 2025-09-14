#!/usr/bin/env python3
"""
Advanced Backtesting Engine
Comprehensive backtesting system with enhanced strategy integration
"""

import pandas as pd
import numpy as np
import json
import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from data_loader import DataLoader
from enhanced_trading_strategy import EnhancedTradingStrategy, TradeSignal

@dataclass
class Trade:
    """Individual trade record"""
    entry_time: datetime.datetime
    exit_time: Optional[datetime.datetime]
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    exit_price: Optional[float]
    volume: float
    stop_loss: float
    take_profit: float
    commission: float
    slippage: float
    pnl: Optional[float]
    pnl_pct: Optional[float]
    duration_minutes: Optional[int]
    exit_reason: Optional[str]  # 'SL', 'TP', 'SIGNAL', 'END_OF_DATA'
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
    monthly_returns: pd.DataFrame

class BacktestingEngine:
    """Advanced backtesting engine with realistic execution simulation"""
    
    def __init__(self, config_file: str = "trading_config.json", data_directory: str = "Z:\\"):
        self.config = self.load_config(config_file)
        self.data_loader = DataLoader(data_directory)
        self.strategy = EnhancedTradingStrategy(config_file)
        
        # Execution settings
        self.commission_per_lot = 0.0  # Commission per lot
        self.slippage_pips = 0.5  # Slippage in pips
        self.spread_pips = 2.0  # Spread in pips
        
        # Backtest state
        self.current_balance = 0.0
        self.current_positions = {}
        self.trades_history = []
        self.equity_curve = []
        self.max_balance = 0.0
        
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
    
    def set_execution_parameters(self, commission: float = 0.0, slippage: float = 0.5, spread: float = 2.0):
        """Set execution parameters for realistic backtesting"""
        self.commission_per_lot = commission
        self.slippage_pips = slippage
        self.spread_pips = spread
    
    def load_data(self, symbol: str, timeframe: str = None) -> Optional[pd.DataFrame]:
        """Load data for backtesting"""
        if timeframe is None:
            timeframe = self.config.get('timeframe', 'H1')
        
        # Get available files
        files = self.data_loader.list_available_files()
        
        # Find file for the symbol
        symbol_file = None
        for file_path in files:
            if symbol.lower() in file_path.lower():
                symbol_file = file_path
                break
        
        if symbol_file is None:
            print(f"No data file found for symbol {symbol}")
            return None
        
        # Load data
        df = self.data_loader.load_csv_data(symbol_file)
        if df is None:
            print(f"Failed to load data for {symbol}")
            return None
        
        # Resample if needed
        if timeframe != 'M1':
            df = self.data_loader.resample_data(df, timeframe)
        
        # Validate data
        validation = self.data_loader.validate_data(df)
        if validation['warnings']:
            print(f"Data validation warnings for {symbol}:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        return df
    
    def calculate_position_size(self, balance: float, entry_price: float, stop_loss: float, 
                              risk_per_trade: float) -> float:
        """Calculate position size based on risk management"""
        risk_amount = balance * risk_per_trade
        
        # Calculate risk in price terms (not pips for commodities)
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0.0
        
        # For commodities like Gold, calculate position size based on price risk
        # Standard lot size for Gold is 100 oz, so we need to account for this
        lot_size = 100  # Standard lot size for Gold
        position_size = risk_amount / (price_risk * lot_size)
        
        # Apply maximum position size limit (max 1 lot for demo)
        max_position_size = min(position_size, 1.0)
        
        return round(max_position_size, 2)
    
    def apply_execution_costs(self, price: float, direction: str, volume: float) -> Tuple[float, float]:
        """Apply execution costs (spread, slippage, commission)"""
        # Apply spread (for Gold: 1 pip = 0.01)
        spread_amount = self.spread_pips * 0.01
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
    
    def execute_trade(self, signal: TradeSignal, current_price: float, timestamp: datetime.datetime, 
                     symbol: str) -> Optional[Trade]:
        """Execute a trade based on signal"""
        if signal.signal_type == 'HOLD':
            return None
        
        # Calculate stop loss and take profit (already in price units)
        stop_loss_distance = self.strategy.calculate_stop_loss(current_price)
        take_profit_distance = self.strategy.calculate_take_profit(current_price, stop_loss_distance)
        
        # Set stop loss and take profit prices
        if signal.signal_type == 'BUY':
            direction = 'LONG'
            entry_price = current_price
            stop_loss_price = current_price - stop_loss_distance
            take_profit_price = current_price + take_profit_distance
        else:  # SELL
            direction = 'SHORT'
            entry_price = current_price
            stop_loss_price = current_price + stop_loss_distance
            take_profit_price = current_price - take_profit_distance
        
        # Calculate position size
        risk_per_trade = self.config['risk_management']['position_sizing']['risk_per_trade']
        volume = self.calculate_position_size(self.current_balance, entry_price, stop_loss_price, risk_per_trade)
        
        if volume <= 0:
            return None
        
        # Apply execution costs
        execution_price, commission = self.apply_execution_costs(entry_price, direction, volume)
        
        # Create trade record
        trade = Trade(
            entry_time=timestamp,
            exit_time=None,
            symbol=symbol,
            direction=direction,
            entry_price=execution_price,
            exit_price=None,
            volume=volume,
            stop_loss=stop_loss_price,
            take_profit=take_profit_price,
            commission=commission,
            slippage=self.slippage_pips * 0.0001,
            pnl=None,
            pnl_pct=None,
            duration_minutes=None,
            exit_reason=None,
            indicators_used=signal.indicators_used,
            signal_strength=signal.confidence
        )
        
        # Update balance
        self.current_balance -= commission
        
        # Track position
        self.current_positions[symbol] = trade
        
        return trade
    
    def check_exit_conditions(self, trade: Trade, current_price: float, 
                            timestamp: datetime.datetime) -> Optional[str]:
        """Check if trade should be exited"""
        if trade.direction == 'LONG':
            if current_price <= trade.stop_loss:
                return 'SL'  # Stop loss hit
            elif current_price >= trade.take_profit:
                return 'TP'  # Take profit hit
        else:  # SHORT
            if current_price >= trade.stop_loss:
                return 'SL'  # Stop loss hit
            elif current_price <= trade.take_profit:
                return 'TP'  # Take profit hit
        
        return None
    
    def close_trade(self, trade: Trade, exit_price: float, exit_time: datetime.datetime, 
                   exit_reason: str) -> Trade:
        """Close a trade and calculate P&L"""
        # Apply execution costs
        execution_price, commission = self.apply_execution_costs(exit_price, 
                                                               'SHORT' if trade.direction == 'LONG' else 'LONG', 
                                                               trade.volume)
        
        # Calculate P&L for Gold (commodity)
        # Standard lot size for Gold is 100 oz
        lot_size = 100
        
        if trade.direction == 'LONG':
            pnl = (execution_price - trade.entry_price) * trade.volume * lot_size
        else:  # SHORT
            pnl = (trade.entry_price - execution_price) * trade.volume * lot_size
        
        pnl -= commission  # Subtract exit commission
        
        # Calculate percentage return
        initial_investment = trade.entry_price * trade.volume * lot_size
        pnl_pct = (pnl / initial_investment) * 100 if initial_investment > 0 else 0
        
        # Calculate duration
        duration = exit_time - trade.entry_time
        duration_minutes = int(duration.total_seconds() / 60)
        
        # Update trade record
        trade.exit_time = exit_time
        trade.exit_price = execution_price
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
        trade.duration_minutes = duration_minutes
        trade.exit_reason = exit_reason
        trade.commission += commission  # Add exit commission
        
        # Update balance
        self.current_balance += pnl
        
        return trade
    
    def run_backtest(self, symbol: str, start_date: datetime.datetime = None, 
                    end_date: datetime.datetime = None, initial_balance: float = 10000) -> BacktestResults:
        """Run comprehensive backtest"""
        print(f"Starting backtest for {symbol}")
        print(f"Initial balance: ${initial_balance:,.2f}")
        
        # Load data
        df = self.load_data(symbol)
        if df is None:
            raise ValueError(f"Could not load data for {symbol}")
        
        # Filter date range
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        
        if len(df) < 100:
            raise ValueError("Insufficient data for backtesting")
        
        print(f"Backtesting period: {df.index.min()} to {df.index.max()}")
        print(f"Total bars: {len(df)}")
        
        # Initialize backtest state
        self.current_balance = initial_balance
        self.max_balance = initial_balance
        self.current_positions = {}
        self.trades_history = []
        self.equity_curve = []
        
        # Initialize tracking variables
        cumulative_pnl = 0.0
        wins = 0
        losses = 0
        
        # Minimum bars needed for indicators
        min_bars = 50
        
        # Display header for trade information
        print(f"\n{'='*120}")
        print(f"{'ACTION':<15} {'DIRECTION':<8} {'PRICE':<10} {'REASON':<12} {'P&L':<10} {'CUM_P&L':<10} {'WINS':<5} {'LOSSES':<6} {'WIN_RATE':<8} {'DURATION':<8}")
        print(f"{'='*120}")
        
        # Run backtest
        for i in range(min_bars, len(df)):
            current_bar = df.iloc[i]
            current_price = current_bar['close']
            timestamp = df.index[i]
            
            # Create temporary dataframe for analysis
            analysis_df = df.iloc[:i+1].copy()
            
            # Calculate indicators using the enhanced strategy
            indicators = self.strategy.calculate_all_indicators(analysis_df)
            
            # Create analysis dictionary
            analysis = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': timestamp,
                'indicators': {}
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
            
            # Generate trading signal
            signal = self.strategy.generate_trading_signal(analysis)
            
            # Check for exit conditions on existing positions
            for pos_symbol, trade in list(self.current_positions.items()):
                exit_reason = self.check_exit_conditions(trade, current_price, timestamp)
                if exit_reason:
                    closed_trade = self.close_trade(trade, current_price, timestamp, exit_reason)
                    self.trades_history.append(closed_trade)
                    del self.current_positions[pos_symbol]
                    
                    # Update tracking variables
                    cumulative_pnl += closed_trade.pnl
                    if closed_trade.pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                    
                    # Display trade result with running statistics
                    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
                    duration_minutes = closed_trade.duration_minutes if closed_trade.duration_minutes else 0
                    print(f"{'CLOSED':<15} {trade.direction:<8} {current_price:<10.1f} {exit_reason:<12} "
                          f"${closed_trade.pnl:<9.1f} ${cumulative_pnl:<9.1f} {wins:<5} {losses:<6} {win_rate:<7.1f}% {duration_minutes:<8}m")
            
            # Execute new trades if no position exists
            if symbol not in self.current_positions and signal.signal_type != 'HOLD':
                trade = self.execute_trade(signal, current_price, timestamp, symbol)
                if trade:
                    total_trades = wins + losses
                    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
                    print(f"{'OPENED':<15} {trade.direction:<8} {trade.entry_price:<10.1f} {'SIGNAL':<12} "
                          f"{'--':<10} ${cumulative_pnl:<9.1f} {wins:<5} {losses:<6} {win_rate:<7.1f}% {'--':<8}")
            
            # Update equity curve
            current_equity = self.current_balance
            if symbol in self.current_positions:
                trade = self.current_positions[symbol]
                # For Gold (commodity), use lot size of 100, not 100000 (forex)
                lot_size = 100  # Standard lot size for Gold
                unrealized_pnl = (current_price - trade.entry_price) * trade.volume * lot_size
                if trade.direction == 'SHORT':
                    unrealized_pnl = -unrealized_pnl
                current_equity += unrealized_pnl
            
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
            closed_trade = self.close_trade(trade, final_price, final_time, 'END_OF_DATA')
            self.trades_history.append(closed_trade)
            
            # Update tracking variables for final trades
            cumulative_pnl += closed_trade.pnl
            if closed_trade.pnl > 0:
                wins += 1
            else:
                losses += 1
            
            # Display final trade result
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
            duration_minutes = closed_trade.duration_minutes if closed_trade.duration_minutes else 0
            print(f"{'CLOSED':<15} {trade.direction:<8} {final_price:<10.1f} {'END_OF_DATA':<12} "
                  f"${closed_trade.pnl:<9.1f} ${cumulative_pnl:<9.1f} {wins:<5} {losses:<6} {win_rate:<7.1f}% {duration_minutes:<8}m")
        
        # Calculate results
        results = self.calculate_results(initial_balance, df.index[0], df.index[-1])
        
        print(f"\nBacktest completed!")
        print(f"Final balance: ${results.final_balance:,.2f}")
        print(f"Total return: {results.total_return_pct:.2f}%")
        print(f"Total trades: {results.total_trades}")
        print(f"Win rate: {results.win_rate:.2f}%")
        print(f"Max drawdown: {results.max_drawdown_pct:.2f}%")
        
        return results
    
    def calculate_results(self, initial_balance: float, start_date: datetime.datetime, 
                         end_date: datetime.datetime) -> BacktestResults:
        """Calculate comprehensive backtest results"""
        final_balance = self.current_balance
        total_return = final_balance - initial_balance
        total_return_pct = (total_return / initial_balance) * 100
        
        # Trade statistics
        total_trades = len(self.trades_history)
        winning_trades = len([t for t in self.trades_history if t.pnl > 0])
        losing_trades = len([t for t in self.trades_history if t.pnl < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Average win/loss
        wins = [t.pnl for t in self.trades_history if t.pnl > 0]
        losses = [t.pnl for t in self.trades_history if t.pnl < 0]
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Maximum drawdown - use balance (realized P&L) instead of equity (unrealized P&L)
        equity_curve = pd.DataFrame(self.equity_curve)
        if not equity_curve.empty:
            # Use balance for drawdown calculation (realized P&L only)
            running_max = equity_curve['balance'].expanding().max()
            drawdown = (equity_curve['balance'] - running_max) / running_max
            max_drawdown = drawdown.min()
            max_drawdown_pct = abs(max_drawdown) * 100
        else:
            max_drawdown = 0
            max_drawdown_pct = 0
        
        # Risk-adjusted ratios
        if not equity_curve.empty and len(equity_curve) > 1:
            returns = equity_curve['equity'].pct_change().dropna()
            if len(returns) > 1:
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                downside_returns = returns[returns < 0]
                sortino_ratio = returns.mean() / downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
                calmar_ratio = (total_return_pct / 100) / (max_drawdown_pct / 100) if max_drawdown_pct > 0 else 0
            else:
                sharpe_ratio = sortino_ratio = calmar_ratio = 0
        else:
            sharpe_ratio = sortino_ratio = calmar_ratio = 0
        
        # Monthly returns
        monthly_returns = pd.DataFrame()
        if not equity_curve.empty:
            monthly_returns = equity_curve.set_index('timestamp')['equity'].resample('M').last().pct_change().dropna()
            monthly_returns = monthly_returns.to_frame('returns')
        
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
            equity_curve=equity_curve,
            monthly_returns=monthly_returns
        )
    
    def save_results(self, results: BacktestResults, filename: str = None):
        """Save backtest results to JSON file"""
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_results_{timestamp}.json"
        
        # Convert results to dictionary
        results_dict = asdict(results)
        
        # Convert datetime objects to strings
        results_dict['start_date'] = results.start_date.isoformat()
        results_dict['end_date'] = results.end_date.isoformat()
        
        for trade in results_dict['trades']:
            trade['entry_time'] = trade['entry_time'].isoformat()
            if trade['exit_time']:
                trade['exit_time'] = trade['exit_time'].isoformat()
        
        if not results.equity_curve.empty:
            results_dict['equity_curve'] = results.equity_curve.to_dict('records')
            for record in results_dict['equity_curve']:
                record['timestamp'] = record['timestamp'].isoformat()
        
        if not results.monthly_returns.empty:
            results_dict['monthly_returns'] = results.monthly_returns.to_dict('records')
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"Results saved to {filename}")

def main():
    """Demo function to run backtest"""
    print("Backtesting Engine Demo")
    print("=" * 30)
    
    # Create backtesting engine
    engine = BacktestingEngine()
    
    # Set execution parameters
    engine.set_execution_parameters(commission=0.0, slippage=0.5, spread=2.0)
    
    # Get available symbols
    files = engine.data_loader.list_available_files()
    print("Available data files:")
    for file_path in files:
        print(f"  - {os.path.basename(file_path)}")
    
    # Run backtest on first available symbol
    if files:
        # Extract symbol from filename
        sample_file = files[0]
        symbol = os.path.basename(sample_file).split('_')[0]
        
        print(f"\nRunning backtest for {symbol}...")
        
        try:
            # Run backtest for last 30 days
            end_date = datetime.datetime.now()
            start_date = end_date - timedelta(days=30)
            
            results = engine.run_backtest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_balance=10000
            )
            
            # Save results
            engine.save_results(results)
            
            print(f"\nBacktest Summary:")
            print(f"  Symbol: {symbol}")
            print(f"  Period: {results.start_date} to {results.end_date}")
            print(f"  Initial Balance: ${results.initial_balance:,.2f}")
            print(f"  Final Balance: ${results.final_balance:,.2f}")
            print(f"  Total Return: {results.total_return_pct:.2f}%")
            print(f"  Total Trades: {results.total_trades}")
            print(f"  Win Rate: {results.win_rate:.2f}%")
            print(f"  Max Drawdown: {results.max_drawdown_pct:.2f}%")
            print(f"  Sharpe Ratio: {results.sharpe_ratio:.2f}")
            
        except Exception as e:
            print(f"Error running backtest: {e}")
    
    else:
        print("No data files found!")

if __name__ == "__main__":
    main()
