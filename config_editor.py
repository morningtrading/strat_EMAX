#!/usr/bin/env python3
"""
Trading Configuration Editor
Interactive tool to modify trading configuration settings
"""

import json
import os
from typing import Dict, Any

class TradingConfigEditor:
    """Interactive configuration editor for trading settings"""
    
    def __init__(self, config_file: str = "trading_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "symbols": {"primary": "EURUSD"},
            "timeframe": "H1",
            "indicators": {
                "sma": {"enabled": True, "periods": [20, 50], "weight": 0.15},
                "rsi": {"enabled": True, "period": 14, "overbought": 70, "oversold": 30, "weight": 0.20}
            },
            "risk_management": {
                "position_sizing": {"risk_per_trade": 0.02}
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"Configuration saved to {self.config_file}")
    
    def edit_symbols(self):
        """Edit symbol settings"""
        print("\n=== Symbol Configuration ===")
        current = self.config['symbols']['primary']
        print(f"Current primary symbol: {current}")
        
        new_symbol = input("Enter new primary symbol (or press Enter to keep current): ").strip().upper()
        if new_symbol:
            self.config['symbols']['primary'] = new_symbol
            print(f"Primary symbol changed to: {new_symbol}")
    
    def edit_timeframe(self):
        """Edit timeframe settings"""
        print("\n=== Timeframe Configuration ===")
        timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
        current = self.config['timeframe']
        print(f"Current timeframe: {current}")
        print(f"Available timeframes: {', '.join(timeframes)}")
        
        new_timeframe = input("Enter new timeframe (or press Enter to keep current): ").strip().upper()
        if new_timeframe and new_timeframe in timeframes:
            self.config['timeframe'] = new_timeframe
            print(f"Timeframe changed to: {new_timeframe}")
        elif new_timeframe:
            print("Invalid timeframe. Keeping current setting.")
    
    def edit_indicators(self):
        """Edit indicator settings"""
        print("\n=== Indicator Configuration ===")
        indicators = self.config['indicators']
        
        while True:
            print("\nAvailable indicators:")
            for i, (name, config) in enumerate(indicators.items(), 1):
                status = "ENABLED" if config['enabled'] else "DISABLED"
                weight = config.get('weight', 0)
                print(f"{i}. {name.upper()} - {status} (weight: {weight})")
            
            print(f"{len(indicators) + 1}. Back to main menu")
            
            try:
                choice = int(input("\nSelect indicator to edit (number): "))
                if choice == len(indicators) + 1:
                    break
                elif 1 <= choice <= len(indicators):
                    indicator_name = list(indicators.keys())[choice - 1]
                    self.edit_single_indicator(indicator_name, indicators[indicator_name])
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def edit_single_indicator(self, name: str, config: Dict):
        """Edit a single indicator's settings"""
        print(f"\n--- Editing {name.upper()} ---")
        
        # Toggle enabled/disabled
        current_status = "enabled" if config['enabled'] else "disabled"
        toggle = input(f"Currently {current_status}. Toggle? (y/n): ").lower()
        if toggle == 'y':
            config['enabled'] = not config['enabled']
            print(f"{name} is now {'enabled' if config['enabled'] else 'disabled'}")
        
        # Edit weight
        if 'weight' in config:
            current_weight = config['weight']
            new_weight = input(f"Current weight: {current_weight}. New weight (0-1): ")
            try:
                weight = float(new_weight)
                if 0 <= weight <= 1:
                    config['weight'] = weight
                    print(f"Weight changed to: {weight}")
                else:
                    print("Weight must be between 0 and 1")
            except ValueError:
                print("Invalid weight value")
        
        # Edit period-specific settings
        if name == 'sma' and 'periods' in config:
            current_periods = config['periods']
            print(f"Current periods: {current_periods}")
            new_periods = input("Enter new periods (comma-separated): ")
            try:
                periods = [int(p.strip()) for p in new_periods.split(',') if p.strip()]
                if periods:
                    config['periods'] = periods
                    print(f"Periods changed to: {periods}")
            except ValueError:
                print("Invalid periods format")
        
        elif name == 'rsi':
            if 'period' in config:
                current_period = config['period']
                new_period = input(f"Current RSI period: {current_period}. New period: ")
                try:
                    period = int(new_period)
                    if period > 0:
                        config['period'] = period
                        print(f"RSI period changed to: {period}")
                except ValueError:
                    print("Invalid period value")
            
            # Edit overbought/oversold levels
            if 'overbought' in config:
                current_ob = config['overbought']
                new_ob = input(f"Current overbought level: {current_ob}. New level: ")
                try:
                    ob = float(new_ob)
                    if 50 <= ob <= 100:
                        config['overbought'] = ob
                        print(f"Overbought level changed to: {ob}")
                except ValueError:
                    print("Invalid overbought level")
            
            if 'oversold' in config:
                current_os = config['oversold']
                new_os = input(f"Current oversold level: {current_os}. New level: ")
                try:
                    os_level = float(new_os)
                    if 0 <= os_level <= 50:
                        config['oversold'] = os_level
                        print(f"Oversold level changed to: {os_level}")
                except ValueError:
                    print("Invalid oversold level")
    
    def edit_risk_management(self):
        """Edit risk management settings"""
        print("\n=== Risk Management Configuration ===")
        risk_config = self.config['risk_management']
        
        # Position sizing
        if 'position_sizing' in risk_config:
            pos_config = risk_config['position_sizing']
            current_risk = pos_config.get('risk_per_trade', 0.02)
            print(f"Current risk per trade: {current_risk:.1%}")
            
            new_risk = input("Enter new risk per trade (as decimal, e.g., 0.02 for 2%): ")
            try:
                risk = float(new_risk)
                if 0 < risk <= 0.1:  # Max 10% risk
                    pos_config['risk_per_trade'] = risk
                    print(f"Risk per trade changed to: {risk:.1%}")
                else:
                    print("Risk must be between 0 and 0.1 (10%)")
            except ValueError:
                print("Invalid risk value")
        
        # Stop loss settings
        if 'stop_loss' in risk_config:
            sl_config = risk_config['stop_loss']
            current_method = sl_config.get('method', 'fixed_pips')
            print(f"Current stop loss method: {current_method}")
            
            methods = ['fixed_pips', 'percentage', 'atr']
            print(f"Available methods: {', '.join(methods)}")
            new_method = input("Enter new method (or press Enter to keep current): ")
            if new_method in methods:
                sl_config['method'] = new_method
                print(f"Stop loss method changed to: {new_method}")
            
            if new_method == 'fixed_pips' or current_method == 'fixed_pips':
                current_pips = sl_config.get('fixed_pips', 50)
                new_pips = input(f"Current fixed pips: {current_pips}. New value: ")
                try:
                    pips = int(new_pips)
                    if pips > 0:
                        sl_config['fixed_pips'] = pips
                        print(f"Fixed pips changed to: {pips}")
                except ValueError:
                    print("Invalid pips value")
    
    def edit_trading_settings(self):
        """Edit trading settings"""
        print("\n=== Trading Settings Configuration ===")
        
        if 'trading_settings' not in self.config:
            self.config['trading_settings'] = {}
        
        trading_config = self.config['trading_settings']
        
        # Signal thresholds
        if 'signal_threshold' not in trading_config:
            trading_config['signal_threshold'] = {
                'strong_buy': 0.7,
                'weak_buy': 0.4,
                'strong_sell': 0.7,
                'weak_sell': 0.4
            }
        
        threshold_config = trading_config['signal_threshold']
        
        print("Current signal thresholds:")
        for signal_type, threshold in threshold_config.items():
            print(f"  {signal_type}: {threshold}")
        
        new_strong_buy = input("Enter new strong buy threshold (0-1): ")
        try:
            threshold = float(new_strong_buy)
            if 0 <= threshold <= 1:
                threshold_config['strong_buy'] = threshold
                threshold_config['strong_sell'] = threshold  # Keep symmetric
                print(f"Strong signal threshold changed to: {threshold}")
        except ValueError:
            print("Invalid threshold value")
    
    def show_current_config(self):
        """Display current configuration"""
        print("\n=== Current Configuration ===")
        print(f"Primary Symbol: {self.config['symbols']['primary']}")
        print(f"Timeframe: {self.config['timeframe']}")
        
        print("\nEnabled Indicators:")
        for name, config in self.config['indicators'].items():
            if config.get('enabled', False):
                weight = config.get('weight', 0)
                print(f"  {name}: weight {weight}")
        
        print("\nRisk Management:")
        risk_config = self.config['risk_management']
        if 'position_sizing' in risk_config:
            risk_per_trade = risk_config['position_sizing'].get('risk_per_trade', 0)
            print(f"  Risk per trade: {risk_per_trade:.1%}")
        
        if 'stop_loss' in risk_config:
            sl_method = risk_config['stop_loss'].get('method', 'unknown')
            print(f"  Stop loss method: {sl_method}")
    
    def run(self):
        """Run the configuration editor"""
        print("Trading Configuration Editor")
        print("=" * 30)
        
        while True:
            print("\nMain Menu:")
            print("1. Show current configuration")
            print("2. Edit symbols")
            print("3. Edit timeframe")
            print("4. Edit indicators")
            print("5. Edit risk management")
            print("6. Edit trading settings")
            print("7. Save configuration")
            print("8. Exit")
            
            try:
                choice = int(input("\nSelect option (1-8): "))
                
                if choice == 1:
                    self.show_current_config()
                elif choice == 2:
                    self.edit_symbols()
                elif choice == 3:
                    self.edit_timeframe()
                elif choice == 4:
                    self.edit_indicators()
                elif choice == 5:
                    self.edit_risk_management()
                elif choice == 6:
                    self.edit_trading_settings()
                elif choice == 7:
                    self.save_config()
                elif choice == 8:
                    print("Exiting configuration editor.")
                    break
                else:
                    print("Invalid choice. Please select 1-8.")
            
            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                print("\nExiting configuration editor.")
                break

def main():
    """Main function"""
    editor = TradingConfigEditor()
    editor.run()

if __name__ == "__main__":
    main()
