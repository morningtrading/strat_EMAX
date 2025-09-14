# Advanced Backtesting System

A comprehensive backtesting framework that uses stored historical data from the Z:\ drive to test and analyze trading strategies with the enhanced indicator system.

## 🚀 Features

### **Data Management**
- **Universal CSV Loader**: Automatically detects and loads various CSV formats
- **Multiple Timeframes**: Supports M1, M5, M15, M30, H1, H4, D1 data
- **Data Validation**: Quality checks and gap detection
- **Flexible Sources**: Works with any OHLCV data format

### **Advanced Backtesting Engine**
- **Realistic Execution**: Includes spread, slippage, and commission simulation
- **Risk Management**: Position sizing, stop loss, take profit integration
- **Multiple Assets**: Test strategies across different symbols
- **Walk-forward Analysis**: Out-of-sample testing capabilities

### **Comprehensive Analysis**
- **Performance Metrics**: Sharpe ratio, Sortino ratio, Calmar ratio, etc.
- **Risk Analysis**: Maximum drawdown, VaR, CVaR calculations
- **Trade Analysis**: Win rate, profit factor, trade duration analysis
- **Visualizations**: Equity curves, drawdown charts, trade distribution plots

### **Enhanced Strategy Integration**
- **All Indicators**: Uses the full enhanced trading strategy with all indicators
- **Configurable**: JSON-based configuration for easy parameter adjustment
- **Weighted Signals**: Multi-factor signal generation with customizable weights

## 📁 File Structure

### **Core Files**
- `data_loader.py` - Universal data loading and preprocessing
- `backtesting_engine.py` - Main backtesting engine with execution simulation
- `backtest_analyzer.py` - Results analysis and visualization
- `run_backtest.py` - Main script to run complete backtesting workflow

### **Supporting Files**
- `enhanced_trading_strategy.py` - Enhanced trading strategy with all indicators
- `trading_config.json` - Configuration file for strategy parameters
- `config_editor.py` - Interactive configuration editor

## 🎯 Quick Start

### **1. Run Complete Backtest**
```bash
python run_backtest.py
```

### **2. Run Quick Demo**
```bash
python run_backtest.py --quick
```

### **3. Test Data Loader**
```bash
python data_loader.py
```

### **4. Test Backtesting Engine**
```bash
python backtesting_engine.py
```

## 📊 Available Data

The system automatically detects and loads data from the Z:\ drive:

### **Detected Files**
- `Z:\15_XAUUSD_1min_1month.csv` - Gold (XAUUSD) 1-minute data
- `Z:\CSV_BTCUSD_M1_full.csv` - Bitcoin (BTCUSD) 1-minute data
- `Z:\MT5 EA test1\data-CSV.csv` - Additional dataset with volume

### **Data Format**
```
timestamp,open,high,low,close,tick_volume,spread,real_volume
2025-08-13 17:44:00,3363.84,3364.16,3363.32,3364.1,64,17,0
```

## ⚙️ Configuration

### **Strategy Configuration**
Edit `trading_config.json` to customize:
- **Indicators**: Enable/disable and adjust parameters
- **Weights**: Set indicator weights for signal generation
- **Risk Management**: Position sizing, stop loss, take profit
- **Timeframes**: Select trading timeframe

### **Execution Parameters**
```python
engine.set_execution_parameters(
    commission=0.0,    # Commission per lot
    slippage=0.5,      # Slippage in pips
    spread=2.0         # Spread in pips
)
```

## 📈 Backtesting Workflow

### **Step 1: Data Analysis**
- Scans Z:\ drive for available data files
- Validates data quality and format
- Extracts symbol information from filenames

### **Step 2: Configuration**
- Loads trading strategy configuration
- Sets backtesting parameters
- Configures execution costs

### **Step 3: Backtest Execution**
- Runs strategy on historical data
- Simulates realistic trade execution
- Tracks positions and risk management

### **Step 4: Results Analysis**
- Calculates comprehensive performance metrics
- Generates visualizations and charts
- Creates detailed reports

### **Step 5: Reporting**
- Saves results to timestamped directory
- Exports JSON reports for further analysis
- Creates visualization plots

## 📊 Performance Metrics

### **Basic Metrics**
- **Total Return**: Absolute and percentage returns
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Average Win/Loss**: Mean profit and loss per trade

### **Risk Metrics**
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure
- **Sortino Ratio**: Downside deviation-adjusted return
- **Calmar Ratio**: Return to maximum drawdown ratio

### **Advanced Metrics**
- **VaR (Value at Risk)**: Potential loss at 95% confidence
- **CVaR (Conditional VaR)**: Expected loss beyond VaR
- **Recovery Factor**: Return relative to maximum drawdown
- **Trade Duration Analysis**: Average holding periods

## 📈 Visualizations

### **Equity Curve**
- Account value over time
- Drawdown visualization
- Balance vs equity comparison

### **Trade Analysis**
- P&L distribution histogram
- Cumulative P&L curve
- Win/loss by direction
- Exit reason distribution

### **Performance Dashboard**
- Key metrics bar chart
- Monthly returns analysis
- Trade duration distribution
- Signal strength vs performance

## 🎯 Example Results

### **Sample Output**
```
📊 BASIC METRICS
  Initial Balance:    $10,000.00
  Final Balance:      $11,250.00
  Total Return:       $1,250.00 (12.50%)
  Total Trades:       45
  Win Rate:           62.22%
  Profit Factor:      1.85

⚠️  RISK METRICS
  Max Drawdown:       8.45%
  Volatility:         15.23%
  Sharpe Ratio:       1.42
  Sortino Ratio:      2.15
  Calmar Ratio:       1.48
```

## 📁 Output Files

### **Generated Files Structure**
```
backtest_results_20250114_143022/
├── backtest_summary.json           # Overall summary
├── EURUSD_results.json            # Individual symbol results
├── EURUSD_analysis.json           # Detailed analysis
├── equity_curve.png               # Equity curve plot
├── trade_analysis.png             # Trade analysis plots
└── performance_dashboard.png      # Performance metrics
```

## 🔧 Customization

### **Adding New Indicators**
1. Implement indicator calculation in `enhanced_trading_strategy.py`
2. Add indicator configuration to `trading_config.json`
3. Update signal generation logic

### **Custom Data Formats**
1. Modify `_detect_ohlcv_columns()` in `data_loader.py`
2. Add new timestamp format detection
3. Update column mapping logic

### **Execution Simulation**
1. Adjust `apply_execution_costs()` in `backtesting_engine.py`
2. Modify spread, slippage, and commission calculations
3. Add market impact simulation if needed

## 📋 Requirements

### **Python Packages**
```bash
pip install pandas numpy matplotlib seaborn MetaTrader5
```

### **Data Requirements**
- CSV files with OHLCV data on Z:\ drive
- Timestamp column in standard format
- Numeric price and volume data

## 🚨 Important Notes

### **Data Quality**
- Ensure data files have consistent formats
- Check for gaps in historical data
- Validate OHLC relationships (High >= Low, etc.)

### **Execution Assumptions**
- Current implementation uses simplified execution
- Real trading may have different costs
- Consider market impact for large positions

### **Risk Management**
- Always test strategies in demo mode first
- Backtesting doesn't guarantee future performance
- Consider transaction costs in live trading

## 🎯 Best Practices

### **Backtesting**
1. **Use Sufficient Data**: At least 6 months of data
2. **Out-of-Sample Testing**: Reserve recent data for validation
3. **Multiple Timeframes**: Test on different timeframes
4. **Walk-Forward Analysis**: Regular re-optimization

### **Risk Management**
1. **Conservative Position Sizing**: Start with 1-2% risk per trade
2. **Diversification**: Test on multiple symbols
3. **Drawdown Limits**: Set maximum acceptable drawdown
4. **Regular Monitoring**: Track performance metrics

### **Strategy Development**
1. **Simple First**: Start with basic strategies
2. **Add Complexity Gradually**: Introduce indicators one by one
3. **Parameter Sensitivity**: Test robustness of parameters
4. **Market Conditions**: Test in different market environments

## 🆘 Troubleshooting

### **Common Issues**
- **No Data Found**: Check Z:\ drive and file paths
- **Import Errors**: Install required packages
- **Memory Issues**: Reduce data size or use chunking
- **Plot Errors**: Check matplotlib backend

### **Data Issues**
- **Format Detection**: Verify CSV format and headers
- **Timestamp Parsing**: Check date format consistency
- **Missing Data**: Handle gaps appropriately
- **Invalid OHLC**: Clean data before backtesting

## 📞 Support

For issues or questions:
1. Check data file formats and paths
2. Verify configuration file syntax
3. Review error messages and logs
4. Test with smaller datasets first

---

**⚠️ Disclaimer**: This system is for educational and research purposes. Past performance does not guarantee future results. Always test strategies thoroughly before live trading.

## 🔍 **Analysis of the Backtesting Results:**

### **⚠️ Critical Issues Identified:**

#### **1. Extreme Duration Anomalies:**
- **Trade #2**: SHORT position held for **3315 minutes** (55+ hours) - This is unrealistic for 1-minute data
- **Trade #45**: SHORT position held for **3285 minutes** (54+ hours)
- **Trade #20**: LONG position held for **650 minutes** (10+ hours)

#### **2. Declining Performance Pattern:**
- **Start**: Strong performance with 100% win rate initially
- **Middle**: Win rate drops to ~25-30% and stays there
- **Cumulative P&L**: Goes from +$1665 to **-$3565** (massive decline)

#### **3. Over-Trading Behavior:**
- **112 trades** in the period (very high frequency)
- Many trades closed within **5-15 minutes** (likely noise trading)
- Strategy seems to be chasing losses

#### **4. Risk Management Issues:**
- **Stop losses** are being hit frequently
- **Win rate** dropped from 100% to 35%
- **Average loss** seems larger than average wins in later trades

### ** Root Causes:**

#### **1. Data Quality Issues:**
- The **3315-minute duration** suggests data gaps or timestamp issues
- Possible missing data points causing incorrect duration calculations

#### **2. Strategy Over-Optimization:**
- Strategy may be too sensitive to short-term price movements
- Generating too many signals in choppy/consolidating markets

#### **3. Risk Management Problems:**
- Stop loss levels may be too tight for Gold's volatility
- Position sizing might be too aggressive

### ** Recommended Fixes:**

#### **1. Fix Duration Calculation:**
```python
<code_block_to_apply_changes_from>
```

#### **2. Improve Signal Filtering:**
- Add minimum time between trades
- Increase signal threshold requirements
- Add trend confirmation

#### **3. Adjust Risk Parameters:**
- Increase stop loss distance for Gold's volatility
- Reduce position size
- Add maximum daily loss limits

#### **4. Add Market Condition Filters:**
- Only trade during high volatility periods
- Avoid trading during consolidation
- Add volume confirmation

### **📊 Performance Summary:**
- **Total Return**: -35.65% (significant loss)
- **Win Rate**: 35.5% (below 50% threshold)
- **Total Trades**: 112 (over-trading)
- **Strategy Status**: ❌ **NEEDS MAJOR REVISION**

### **🚨 Immediate Actions Needed:**
1. **Fix duration calculation bugs**
2. **Increase signal thresholds** (require stronger confirmation)
3. **Widen stop losses** for Gold's volatility
4. **Add cooldown periods** between trades
5. **Implement maximum daily loss limits**

The strategy shows classic signs of over-optimization and poor risk management. The extreme duration calculations suggest data processing issues that need immediate attention.
