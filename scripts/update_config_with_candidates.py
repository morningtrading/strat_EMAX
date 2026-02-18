import pandas as pd
import json
import os
import shutil

def update_config(csv_file='filtered_candidates.csv', config_file='config/trading_config.json'):
    print(f"Reading candidates from {csv_file}...")
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found.")
        return

    try:
        df = pd.read_csv(csv_file)
        symbols = df['Symbol'].tolist()
        print(f"Found {len(symbols)} candidates.")
        
        # Read existing config
        if not os.path.exists(config_file):
            print(f"Error: {config_file} not found.")
            return
            
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Backup config
        backup_file = config_file + ".bak"
        shutil.copy2(config_file, backup_file)
        print(f"Backed up config to {backup_file}")
        
        # Update Enabled/Available Lists
        config['symbols']['enabled'] = symbols
        config['symbols']['available'] = symbols # Limit available list to what we want to trade for clarity? Or keep full list? Usually best to sync them if we are filtering.
        
        # Update/Create Settings for each symbol
        current_settings = config['symbols'].get('settings', {})
        new_settings = {}
        
        for _, row in df.iterrows():
            symbol = row['Symbol']
            min_vol = float(row['Min Vol'])
            
            # Preserve existing settings if any, else default
            if symbol in current_settings:
                # Keep existing customization but update volume if needed? 
                # Let's overwrite specific fields to enforce standard but keep notes
                setting = current_settings[symbol]
                setting['enabled'] = True
                # setting['volume'] = min_vol # Update volume? User asked to use candidates. Min Vol is safe.
            else:
                setting = {
                    "timeframe": "M5",
                    "fast_ema": 9,
                    "slow_ema": 41,
                    "enabled": True,
                    "min_volume": min_vol,
                    "volume": min_vol, # Start with min volume
                    "max_spread_points": 9999,
                    "_note": "Auto-added from Volatility Scan"
                }
            
            # Ensure volume key exists and is valid
            if 'volume' not in setting:
                setting['volume'] = min_vol
            
            new_settings[symbol] = setting
            
        config['symbols']['settings'] = new_settings
        
        # Write back
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
            
        print(f"Successfully updated {config_file} with {len(symbols)} symbols.")
        print(f"Enabled List: {config['symbols']['enabled'][:5]} ...")

    except Exception as e:
        print(f"Error updating config: {e}")

if __name__ == "__main__":
    update_config()
