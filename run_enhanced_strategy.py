#!/usr/bin/env python3
"""
Run Enhanced Trading Strategy Demo
Simple script to demonstrate the enhanced trading system
"""

import sys
import json
from enhanced_trading_strategy import EnhancedTradingStrategy

def create_sample_config():
    """Create a sample configuration file for testing"""
    sample_config = {
        "symbols": {
            "primary": "EURUSD",
            "secondary": ["GBPUSD", "USDJPY"]
        },
        "timeframe": "H1",
        "indicators": {
            "sma": {
                "enabled": True,
                "periods": [20, 50],
                "weight": 0.20
            },
            "rsi": {
                "enabled": True,
                "period": 14,
                "overbought": 70,
                "oversold": 30,
                "weight": 0.25
            },
            "macd": {
                "enabled": True,
                "fast": 12,
                "slow": 26,
                "signal": 9,
                "weight": 0.20
            },
            "stochastic": {
                "enabled": True,
                "k_period": 14,
                "d_period": 3,
                "overbought": 80,
                "oversold": 20,
                "weight": 0.15
            },
            "bollinger_bands": {
                "enabled": True,
                "period": 20,
                "std_dev": 2.0,
                "weight": 0.10
            },
            "williams_r": {
                "enabled": True,
                "period": 14,
                "overbought": -20,
                "oversold": -80,
                "weight": 0.10
            }
        },
        "risk_management": {
            "position_sizing": {
                "method": "percentage",
                "risk_per_trade": 0.01,
                "max_position_size": 0.05,
                "max_total_exposure": 0.20
            },
            "stop_loss": {
                "method": "fixed_pips",
                "fixed_pips": 30
            },
            "take_profit": {
                "method": "risk_reward",
                "risk_reward_ratio": 2.0
            },
            "daily_loss_limit": {
                "enabled": True,
                "max_daily_loss": 0.03,
                "max_consecutive_losses": 3
            }
        },
        "trading_settings": {
            "signal_threshold": {
                "strong_buy": 0.6,
                "weak_buy": 0.3,
                "strong_sell": 0.6,
                "weak_sell": 0.3
            },
            "confirmation_required": True,
            "min_indicators_agreement": 2
        }
    }
    
    with open('sample_trading_config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print("Created sample_trading_config.json")
    return 'sample_trading_config.json'

def main():
    """Main demo function"""
    print("Enhanced Trading Strategy Demo")
    print("=" * 40)
    
    # Check if config file exists, create sample if not
    config_file = "trading_config.json"
    try:
        with open(config_file, 'r') as f:
            pass
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found.")
        print("Creating sample configuration...")
        config_file = create_sample_config()
    
    # Create strategy instance
    strategy = EnhancedTradingStrategy(config_file)
    
    print(f"\nUsing configuration: {config_file}")
    print(f"Primary symbol: {strategy.config['symbols']['primary']}")
    print(f"Timeframe: {strategy.config['timeframe']}")
    
    # Show enabled indicators
    enabled_indicators = [name for name, config in strategy.config['indicators'].items() if config['enabled']]
    print(f"Enabled indicators: {', '.join(enabled_indicators)}")
    
    # Show risk settings
    risk_config = strategy.config['risk_management']
    print(f"\nRisk Settings:")
    print(f"  Risk per trade: {risk_config['position_sizing']['risk_per_trade']:.1%}")
    print(f"  Max position size: {risk_config['position_sizing']['max_position_size']:.1%}")
    print(f"  Daily loss limit: {risk_config['daily_loss_limit']['max_daily_loss']:.1%}")
    
    # Try to connect (will fail in demo mode, but shows the structure)
    print(f"\nAttempting to connect to MT5...")
    if strategy.connect():
        print("Connected successfully!")
        strategy.run_analysis()
    else:
        print("MT5 connection failed (expected in demo mode)")
        print("\nTo use with real MT5:")
        print("1. Install MetaTrader 5")
        print("2. Create a demo account")
        print("3. Run this script again")
    
    print("\n" + "=" * 40)
    print("Demo completed!")

if __name__ == "__main__":
    main()
