#!/usr/bin/env python3
"""
Backtest Results Analyzer
Comprehensive analysis and visualization of backtesting results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import asdict
from backtesting_engine_optimized import BacktestResults, Trade
import warnings
warnings.filterwarnings('ignore')

# Set style for better plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class BacktestAnalyzer:
    """Comprehensive backtest results analyzer and visualizer"""
    
    def __init__(self, results: BacktestResults):
        self.results = results
        self.trades_df = self._trades_to_dataframe()
        self.equity_df = self._equity_to_dataframe()
        
    def _trades_to_dataframe(self) -> pd.DataFrame:
        """Convert trades to DataFrame for analysis"""
        trades_data = []
        for trade in self.results.trades:
            trade_dict = asdict(trade)
            # Convert datetime objects to strings for JSON serialization
            trade_dict['entry_time'] = trade.entry_time.isoformat()
            if trade.exit_time:
                trade_dict['exit_time'] = trade.exit_time.isoformat()
            trades_data.append(trade_dict)
        
        df = pd.DataFrame(trades_data)
        if not df.empty:
            df['entry_time'] = pd.to_datetime(df['entry_time'])
            if 'exit_time' in df.columns:
                df['exit_time'] = pd.to_datetime(df['exit_time'])
        
        return df
    
    def _equity_to_dataframe(self) -> pd.DataFrame:
        """Convert equity curve to DataFrame"""
        if self.results.equity_curve.empty:
            return pd.DataFrame()
        
        df = self.results.equity_curve.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df
    
    def generate_summary_report(self) -> Dict:
        """Generate comprehensive summary report"""
        report = {
            'basic_metrics': self._calculate_basic_metrics(),
            'risk_metrics': self._calculate_risk_metrics(),
            'trade_analysis': self._analyze_trades(),
            'time_analysis': self._analyze_by_time(),
            'drawdown_analysis': self._analyze_drawdowns(),
            'performance_attribution': self._analyze_performance_attribution()
        }
        return report
    
    def _calculate_basic_metrics(self) -> Dict:
        """Calculate basic performance metrics"""
        return {
            'initial_balance': self.results.initial_balance,
            'final_balance': self.results.final_balance,
            'total_return': self.results.total_return,
            'total_return_pct': self.results.total_return_pct,
            'total_trades': self.results.total_trades,
            'winning_trades': self.results.winning_trades,
            'losing_trades': self.results.losing_trades,
            'win_rate': self.results.win_rate,
            'avg_win': self.results.avg_win,
            'avg_loss': self.results.avg_loss,
            'profit_factor': self.results.profit_factor,
            'sharpe_ratio': self.results.sharpe_ratio,
            'sortino_ratio': self.results.sortino_ratio,
            'calmar_ratio': self.results.calmar_ratio
        }
    
    def _calculate_risk_metrics(self) -> Dict:
        """Calculate risk-related metrics"""
        if self.trades_df.empty:
            return {}
        
        # Calculate additional risk metrics
        returns = self.trades_df['pnl_pct'].values
        
        return {
            'max_drawdown_pct': self.results.max_drawdown_pct,
            'volatility': np.std(returns) if len(returns) > 1 else 0,
            'var_95': np.percentile(returns, 5) if len(returns) > 0 else 0,  # 95% VaR
            'cvar_95': np.mean(returns[returns <= np.percentile(returns, 5)]) if len(returns) > 0 else 0,  # Conditional VaR
            'max_consecutive_wins': self._max_consecutive_wins(),
            'max_consecutive_losses': self._max_consecutive_losses(),
            'recovery_factor': self.results.total_return / abs(self.results.max_drawdown) if self.results.max_drawdown != 0 else 0
        }
    
    def _analyze_trades(self) -> Dict:
        """Analyze trade patterns and characteristics"""
        if self.trades_df.empty:
            return {}
        
        # Trade direction analysis
        direction_analysis = self.trades_df.groupby('direction').agg({
            'pnl': ['count', 'sum', 'mean'],
            'pnl_pct': 'mean',
            'duration_minutes': 'mean'
        }).round(2)
        
        # Exit reason analysis
        exit_analysis = self.trades_df['exit_reason'].value_counts().to_dict()
        
        # Signal strength analysis
        signal_analysis = self.trades_df.groupby(pd.cut(self.trades_df['signal_strength'], 
                                                       bins=5, labels=['Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong']))['pnl'].agg(['count', 'mean']).round(2)
        
        return {
            'direction_analysis': direction_analysis.to_dict(),
            'exit_reason_distribution': exit_analysis,
            'signal_strength_analysis': signal_analysis.to_dict(),
            'avg_trade_duration_minutes': self.trades_df['duration_minutes'].mean(),
            'largest_win': self.trades_df['pnl'].max(),
            'largest_loss': self.trades_df['pnl'].min()
        }
    
    def _analyze_by_time(self) -> Dict:
        """Analyze performance by time periods"""
        if self.trades_df.empty:
            return {}
        
        # Monthly performance
        monthly_perf = {}
        if not self.results.monthly_returns.empty:
            monthly_df = self.results.monthly_returns
            monthly_perf = {
                'best_month': monthly_df['returns'].max(),
                'worst_month': monthly_df['returns'].min(),
                'avg_monthly_return': monthly_df['returns'].mean(),
                'positive_months': (monthly_df['returns'] > 0).sum(),
                'total_months': len(monthly_df)
            }
        
        # Hourly performance (if we have time data)
        if 'entry_time' in self.trades_df.columns:
            self.trades_df['hour'] = self.trades_df['entry_time'].dt.hour
            hourly_perf = self.trades_df.groupby('hour')['pnl'].agg(['count', 'mean', 'sum']).round(2)
            hourly_perf_dict = hourly_perf.to_dict()
        else:
            hourly_perf_dict = {}
        
        return {
            'monthly_performance': monthly_perf,
            'hourly_performance': hourly_perf_dict
        }
    
    def _analyze_drawdowns(self) -> Dict:
        """Analyze drawdown periods"""
        if self.equity_df.empty:
            return {}
        
        equity = self.equity_df['equity']
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max
        
        # Find drawdown periods
        drawdown_periods = []
        in_drawdown = False
        start_idx = None
        
        for i, dd in enumerate(drawdown):
            if dd < -0.01 and not in_drawdown:  # Start of drawdown (>1%)
                in_drawdown = True
                start_idx = i
            elif dd >= -0.01 and in_drawdown:  # End of drawdown
                in_drawdown = False
                if start_idx is not None:
                    period = {
                        'start': equity.index[start_idx],
                        'end': equity.index[i],
                        'max_drawdown': drawdown.iloc[start_idx:i].min(),
                        'duration_days': (equity.index[i] - equity.index[start_idx]).days
                    }
                    drawdown_periods.append(period)
        
        return {
            'drawdown_periods': drawdown_periods,
            'max_drawdown_duration_days': max([p['duration_days'] for p in drawdown_periods]) if drawdown_periods else 0,
            'avg_drawdown_duration_days': np.mean([p['duration_days'] for p in drawdown_periods]) if drawdown_periods else 0
        }
    
    def _analyze_performance_attribution(self) -> Dict:
        """Analyze what drives performance"""
        if self.trades_df.empty:
            return {}
        
        # Analyze by indicators used
        indicator_performance = {}
        for indicators in self.trades_df['indicators_used']:
            for indicator in indicators:
                if indicator not in indicator_performance:
                    indicator_performance[indicator] = []
        
        # Group trades by indicators
        for _, trade in self.trades_df.iterrows():
            for indicator in trade['indicators_used']:
                if indicator in indicator_performance:
                    indicator_performance[indicator].append(trade['pnl'])
        
        # Calculate performance by indicator
        indicator_stats = {}
        for indicator, pnls in indicator_performance.items():
            if pnls:
                indicator_stats[indicator] = {
                    'count': len(pnls),
                    'avg_pnl': np.mean(pnls),
                    'win_rate': len([p for p in pnls if p > 0]) / len(pnls) * 100,
                    'total_pnl': sum(pnls)
                }
        
        return {
            'indicator_performance': indicator_stats,
            'best_performing_indicator': max(indicator_stats.items(), key=lambda x: x[1]['total_pnl'])[0] if indicator_stats else None,
            'worst_performing_indicator': min(indicator_stats.items(), key=lambda x: x[1]['total_pnl'])[0] if indicator_stats else None
        }
    
    def _max_consecutive_wins(self) -> int:
        """Calculate maximum consecutive wins"""
        if self.trades_df.empty:
            return 0
        
        wins = self.trades_df['pnl'] > 0
        max_consecutive = 0
        current_consecutive = 0
        
        for win in wins:
            if win:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _max_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losses"""
        if self.trades_df.empty:
            return 0
        
        losses = self.trades_df['pnl'] < 0
        max_consecutive = 0
        current_consecutive = 0
        
        for loss in losses:
            if loss:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def create_visualizations(self, save_plots: bool = True, output_dir: str = ".") -> List[str]:
        """Create comprehensive visualizations"""
        plot_files = []
        
        # 1. Equity Curve
        if not self.equity_df.empty:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
            
            # Equity curve
            ax1.plot(self.equity_df.index, self.equity_df['equity'], linewidth=2, label='Equity')
            ax1.plot(self.equity_df.index, self.equity_df['balance'], linewidth=1, alpha=0.7, label='Balance')
            ax1.set_title('Equity Curve', fontsize=16, fontweight='bold')
            ax1.set_ylabel('Account Value ($)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Drawdown
            running_max = self.equity_df['equity'].expanding().max()
            drawdown = (self.equity_df['equity'] - running_max) / running_max * 100
            ax2.fill_between(self.equity_df.index, drawdown, 0, alpha=0.3, color='red')
            ax2.plot(self.equity_df.index, drawdown, color='red', linewidth=1)
            ax2.set_title('Drawdown (%)', fontsize=16, fontweight='bold')
            ax2.set_ylabel('Drawdown (%)')
            ax2.set_xlabel('Date')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_plots:
                filename = f"{output_dir}/equity_curve.png"
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                plot_files.append(filename)
            
            plt.show()
        
        # 2. Trade Analysis
        if not self.trades_df.empty:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # P&L Distribution
            ax1.hist(self.trades_df['pnl'], bins=20, alpha=0.7, edgecolor='black')
            ax1.axvline(0, color='red', linestyle='--', alpha=0.7)
            ax1.set_title('P&L Distribution', fontweight='bold')
            ax1.set_xlabel('P&L ($)')
            ax1.set_ylabel('Frequency')
            ax1.grid(True, alpha=0.3)
            
            # Cumulative P&L
            cumulative_pnl = self.trades_df['pnl'].cumsum()
            ax2.plot(range(len(cumulative_pnl)), cumulative_pnl, linewidth=2)
            ax2.axhline(0, color='red', linestyle='--', alpha=0.7)
            ax2.set_title('Cumulative P&L', fontweight='bold')
            ax2.set_xlabel('Trade Number')
            ax2.set_ylabel('Cumulative P&L ($)')
            ax2.grid(True, alpha=0.3)
            
            # Win/Loss by Direction
            direction_pnl = self.trades_df.groupby('direction')['pnl'].sum()
            ax3.bar(direction_pnl.index, direction_pnl.values, alpha=0.7)
            ax3.set_title('Total P&L by Direction', fontweight='bold')
            ax3.set_ylabel('Total P&L ($)')
            ax3.grid(True, alpha=0.3)
            
            # Exit Reason Distribution
            exit_reasons = self.trades_df['exit_reason'].value_counts()
            ax4.pie(exit_reasons.values, labels=exit_reasons.index, autopct='%1.1f%%')
            ax4.set_title('Exit Reason Distribution', fontweight='bold')
            
            plt.tight_layout()
            
            if save_plots:
                filename = f"{output_dir}/trade_analysis.png"
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                plot_files.append(filename)
            
            plt.show()
        
        # 3. Performance Metrics Dashboard
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Key Metrics
        metrics = {
            'Total Return %': self.results.total_return_pct,
            'Win Rate %': self.results.win_rate,
            'Profit Factor': self.results.profit_factor,
            'Sharpe Ratio': self.results.sharpe_ratio,
            'Max DD %': self.results.max_drawdown_pct,
            'Calmar Ratio': self.results.calmar_ratio
        }
        
        bars = ax1.bar(range(len(metrics)), list(metrics.values()), alpha=0.7)
        ax1.set_xticks(range(len(metrics)))
        ax1.set_xticklabels(list(metrics.keys()), rotation=45, ha='right')
        ax1.set_title('Key Performance Metrics', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Color bars based on values
        for i, (metric, value) in enumerate(metrics.items()):
            if 'Return' in metric or 'Rate' in metric or 'Factor' in metric or 'Ratio' in metric:
                color = 'green' if value > 0 else 'red'
            elif 'DD' in metric:
                color = 'red' if abs(value) > 10 else 'orange' if abs(value) > 5 else 'green'
            else:
                color = 'blue'
            bars[i].set_color(color)
        
        # Monthly Returns (if available)
        if not self.results.monthly_returns.empty:
            monthly_returns = self.results.monthly_returns['returns'] * 100
            colors = ['green' if x > 0 else 'red' for x in monthly_returns.values]
            ax2.bar(range(len(monthly_returns)), monthly_returns.values, color=colors, alpha=0.7)
            ax2.set_title('Monthly Returns (%)', fontweight='bold')
            ax2.set_ylabel('Return (%)')
            ax2.set_xlabel('Month')
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'No Monthly Data Available', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Monthly Returns', fontweight='bold')
        
        # Trade Duration Analysis
        if not self.trades_df.empty:
            duration_hours = self.trades_df['duration_minutes'] / 60
            ax3.hist(duration_hours, bins=20, alpha=0.7, edgecolor='black')
            ax3.set_title('Trade Duration Distribution', fontweight='bold')
            ax3.set_xlabel('Duration (Hours)')
            ax3.set_ylabel('Frequency')
            ax3.grid(True, alpha=0.3)
        
        # Signal Strength vs Performance
        if not self.trades_df.empty:
            signal_strength = self.trades_df['signal_strength']
            pnl = self.trades_df['pnl']
            scatter = ax4.scatter(signal_strength, pnl, alpha=0.6)
            ax4.set_title('Signal Strength vs P&L', fontweight='bold')
            ax4.set_xlabel('Signal Strength')
            ax4.set_ylabel('P&L ($)')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plots:
            filename = f"{output_dir}/performance_dashboard.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plot_files.append(filename)
        
        plt.show()
        
        return plot_files
    
    def export_detailed_report(self, filename: str = None) -> str:
        """Export detailed report to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_analysis_{timestamp}.json"
        
        # Generate comprehensive report
        report = self.generate_summary_report()
        
        # Add raw data
        report['raw_data'] = {
            'trades': self.trades_df.to_dict('records') if not self.trades_df.empty else [],
            'equity_curve': self.equity_df.to_dict('records') if not self.equity_df.empty else [],
            'monthly_returns': self.results.monthly_returns.to_dict('records') if not self.results.monthly_returns.empty else []
        }
        
        # Convert datetime objects to strings
        for trade in report['raw_data']['trades']:
            if 'entry_time' in trade:
                trade['entry_time'] = pd.to_datetime(trade['entry_time']).isoformat()
            if 'exit_time' in trade and trade['exit_time']:
                trade['exit_time'] = pd.to_datetime(trade['exit_time']).isoformat()
        
        for record in report['raw_data']['equity_curve']:
            if 'timestamp' in record:
                record['timestamp'] = pd.to_datetime(record['timestamp']).isoformat()
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Detailed report saved to {filename}")
        return filename
    
    def print_summary(self):
        """Print formatted summary report"""
        report = self.generate_summary_report()
        
        print("=" * 60)
        print("BACKTEST ANALYSIS SUMMARY")
        print("=" * 60)
        
        # Basic Metrics
        basic = report['basic_metrics']
        print(f"\n📊 BASIC METRICS")
        print(f"  Initial Balance:    ${basic['initial_balance']:,.2f}")
        print(f"  Final Balance:      ${basic['final_balance']:,.2f}")
        print(f"  Total Return:       ${basic['total_return']:,.2f} ({basic['total_return_pct']:.2f}%)")
        print(f"  Total Trades:       {basic['total_trades']}")
        print(f"  Win Rate:           {basic['win_rate']:.2f}%")
        print(f"  Profit Factor:      {basic['profit_factor']:.2f}")
        
        # Risk Metrics
        risk = report['risk_metrics']
        print(f"\n⚠️  RISK METRICS")
        print(f"  Max Drawdown:       {risk['max_drawdown_pct']:.2f}%")
        print(f"  Volatility:         {risk['volatility']:.2f}%")
        print(f"  Sharpe Ratio:       {basic['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio:      {basic['sortino_ratio']:.2f}")
        print(f"  Calmar Ratio:       {basic['calmar_ratio']:.2f}")
        
        # Trade Analysis
        if report['trade_analysis']:
            trade_analysis = report['trade_analysis']
            print(f"\n📈 TRADE ANALYSIS")
            print(f"  Average Win:        ${basic['avg_win']:.2f}")
            print(f"  Average Loss:       ${basic['avg_loss']:.2f}")
            print(f"  Largest Win:        ${trade_analysis['largest_win']:.2f}")
            print(f"  Largest Loss:       ${trade_analysis['largest_loss']:.2f}")
            print(f"  Avg Duration:       {trade_analysis['avg_trade_duration_minutes']:.0f} minutes")
        
        print("\n" + "=" * 60)

def main():
    """Demo function"""
    print("Backtest Analyzer Demo")
    print("=" * 30)
    
    # This would typically load results from a saved backtest
    print("This analyzer is designed to work with BacktestResults objects.")
    print("Run a backtest first using backtesting_engine.py, then use this analyzer.")
    
    # Example of how to use:
    print("\nExample usage:")
    print("1. Run backtest: results = engine.run_backtest('EURUSD')")
    print("2. Create analyzer: analyzer = BacktestAnalyzer(results)")
    print("3. Generate report: analyzer.print_summary()")
    print("4. Create plots: analyzer.create_visualizations()")

if __name__ == "__main__":
    main()
