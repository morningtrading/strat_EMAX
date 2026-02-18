
import json
import os

def main():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'trading_config.json')
    
    new_symbols = ["USTEC", "US500"]
    
    # Default settings for indices (Conservative H1 trend following)
    default_settings = {
        "timeframe": "H1",
        "fast_ema": 9,
        "slow_ema": 21,
        "enabled": True,
        "min_volume": 0.01,  # Adjust based on broker
        "volume": 0.01,      # Adjust based on broker
        "max_spread_points": 9999,
        "_note": "Added by User Request (Default H1 9/21)"
        # No backtest pnl yet
    }
    
    print(f"Loading config from {config_path}...")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        enabled = config.get('symbols', {}).get('enabled', [])
        available = config.get('symbols', {}).get('available', [])
        settings = config.get('symbols', {}).get('settings', {})
        
        updated = False
        
        for sym in new_symbols:
            # 1. Add to Available
            if sym not in available:
                available.append(sym)
                print(f"Added {sym} to available list.")
                updated = True
                
            # 2. Add to Enabled
            if sym not in enabled:
                enabled.append(sym)
                print(f"Added {sym} to enabled list.")
                updated = True
            else:
                print(f"{sym} is already enabled.")
                
            # 3. Add Settings if missing
            if sym not in settings:
                settings[sym] = default_settings.copy()
                print(f"Added default settings for {sym}.")
                updated = True
        
        if updated:
            config['symbols']['available'] = available
            config['symbols']['enabled'] = enabled
            config['symbols']['settings'] = settings
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            print("Config updated successfully.")
        else:
            print("No changes needed.")
        
    except Exception as e:
        print(f"Error updating config: {e}")

if __name__ == "__main__":
    main()
