# Enhanced MetaTrader 5 Trading System

This enhanced trading system provides advanced technical analysis with configurable indicators and comprehensive risk management features.

## Features

### Technical Indicators
- **Moving Averages**: SMA (Simple) and EMA (Exponential)
- **Momentum Indicators**: RSI, Stochastic Oscillator, Williams %R, CCI
- **Trend Indicators**: MACD, ADX (Average Directional Index)
- **Volatility Indicators**: Bollinger Bands, ATR (Average True Range)

### Risk Management
- **Position Sizing**: Percentage-based risk per trade
- **Stop Loss**: Fixed pips, percentage, or ATR-based
- **Take Profit**: Risk-reward ratio, fixed pips, or percentage
- **Daily Loss Limits**: Maximum daily loss and consecutive loss limits
- **Drawdown Protection**: Maximum drawdown thresholds
- **Correlation Limits**: Prevent overexposure to correlated positions

### Configuration System
- **JSON-based Configuration**: Easy to modify without code changes
- **Interactive Editor**: User-friendly configuration tool
- **Weighted Signals**: Customizable indicator weights for signal generation

## Files Overview

### Core Files
- `enhanced_trading_strategy.py` - Main trading strategy with all indicators and risk management
- `trading_config.json` - Configuration file with all settings
- `run_enhanced_strategy.py` - Demo script to run the strategy
- `config_editor.py` - Interactive configuration editor

### Original Files
- `mt5_trading_strategy.py` - Original trading strategy
- `mt5_trading_demo.py` - Original demo with simulated data

## Quick Start

### 1. Run the Demo
```bash
python run_enhanced_strategy.py
```

### 2. Edit Configuration
```bash
python config_editor.py
```

### 3. Run Enhanced Strategy
```bash
python enhanced_trading_strategy.py
```

## Configuration Options

### Symbols and Timeframe
```json
{
  "symbols": {
    "primary": "EURUSD",
    "secondary": ["GBPUSD", "USDJPY", "AUDUSD"]
  },
  "timeframe": "H1"
}
```

### Indicator Settings
Each indicator can be enabled/disabled and has configurable parameters:

```json
{
  "indicators": {
    "sma": {
      "enabled": true,
      "periods": [20, 50, 200],
      "weight": 0.15
    },
    "rsi": {
      "enabled": true,
      "period": 14,
      "overbought": 70,
      "oversold": 30,
      "weight": 0.20
    }
  }
}
```

### Risk Management
```json
{
  "risk_management": {
    "position_sizing": {
      "method": "percentage",
      "risk_per_trade": 0.02,
      "max_position_size": 0.1,
      "max_total_exposure": 0.3
    },
    "stop_loss": {
      "method": "atr",
      "atr_multiplier": 2.0,
      "fixed_pips": 50
    },
    "take_profit": {
      "method": "risk_reward",
      "risk_reward_ratio": 2.0
    }
  }
}
```

## Signal Generation

The system uses weighted signals from multiple indicators:

1. **Strong Buy/Sell**: High confidence from multiple indicators
2. **Weak Buy/Sell**: Lower confidence or fewer indicators
3. **Hold**: No clear signal or conflicting indicators

### Signal Thresholds
```json
{
  "trading_settings": {
    "signal_threshold": {
      "strong_buy": 0.7,
      "weak_buy": 0.4,
      "strong_sell": 0.7,
      "weak_sell": 0.4
    }
  }
}
```

## Risk Management Features

### Position Sizing
- **Percentage Method**: Risk a fixed percentage of account balance
- **ATR Method**: Position size based on volatility
- **Fixed Method**: Use a fixed lot size

### Stop Loss Options
- **Fixed Pips**: Set stop loss at fixed pip distance
- **Percentage**: Stop loss as percentage of entry price
- **ATR**: Stop loss based on Average True Range

### Take Profit Options
- **Risk-Reward Ratio**: Take profit at multiple of stop loss distance
- **Fixed Pips**: Take profit at fixed pip distance
- **Percentage**: Take profit as percentage of entry price

### Daily Limits
- **Maximum Daily Loss**: Stop trading if daily loss exceeds threshold
- **Consecutive Losses**: Stop trading after consecutive losing trades
- **Maximum Drawdown**: Stop trading if account drawdown exceeds limit

## Usage Examples

### Basic Analysis
```python
from enhanced_trading_strategy import EnhancedTradingStrategy

# Create strategy with custom config
strategy = EnhancedTradingStrategy("my_config.json")

# Connect to MT5
if strategy.connect():
    # Run analysis
    analysis = strategy.analyze_market("EURUSD")
    signal = strategy.generate_trading_signal(analysis)
    
    print(f"Signal: {signal.signal_type} ({signal.strength})")
    print(f"Confidence: {signal.confidence:.2%}")
```

### Custom Configuration
```python
import json

# Load and modify configuration
with open("trading_config.json", "r") as f:
    config = json.load(f)

# Enable/disable indicators
config["indicators"]["stochastic"]["enabled"] = True
config["indicators"]["williams_r"]["enabled"] = False

# Adjust risk settings
config["risk_management"]["position_sizing"]["risk_per_trade"] = 0.01

# Save modified configuration
with open("custom_config.json", "w") as f:
    json.dump(config, f, indent=2)
```

## Requirements

- Python 3.7+
- MetaTrader5 package
- pandas
- numpy
- MetaTrader 5 terminal (for live trading)

## Installation

```bash
pip install MetaTrader5 pandas numpy
```

## Safety Features

- **Demo Mode**: Test strategies without real money
- **Configuration Validation**: Check settings before trading
- **Risk Limits**: Multiple safety nets to prevent large losses
- **Portfolio State Tracking**: Save and monitor account state

## Notes

- This system is for educational and research purposes
- Always test strategies in demo mode first
- Risk management is crucial - never risk more than you can afford to lose
- Past performance does not guarantee future results
- Consider transaction costs and slippage in live trading

## Support

For questions or issues:
1. Check the configuration file syntax
2. Verify MT5 connection
3. Review indicator calculations
4. Check risk management settings
