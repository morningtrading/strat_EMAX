
import json
import os

def main():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'trading_config.json')
    
    # Symbols to remove as requested
    to_remove = [
        "BKNG", "MRVL", "USDPLN", "APH", "KKR", "GBTC", "SNOW", "CRWD", 
        "RELX", "BITB", "BTCO", "USDILS", "EBAY", "XPDUSD", "XPTUSD"
    ]
    
    print(f"Loading config from {config_path}...")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        enabled = config.get('symbols', {}).get('enabled', [])
        print(f"Current enabled count: {len(enabled)}")
        
        # Filter
        new_enabled = [s for s in enabled if s not in to_remove]
        removed_count = len(enabled) - len(new_enabled)
        
        print(f"Removed {removed_count} symbols.")
        print(f"New enabled count: {len(new_enabled)}")
        
        # Verify what was removed
        actual_removed = [s for s in enabled if s in to_remove]
        print(f"Successfully removed: {actual_removed}")
        
        # Verify if any weren't found
        not_found = [s for s in to_remove if s not in enabled]
        if not_found:
            print(f"Warning: These symbols were not found in the list: {not_found}")
            
        # Update config
        config['symbols']['enabled'] = new_enabled
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        print("Config updated successfully.")
        
    except Exception as e:
        print(f"Error updating config: {e}")

if __name__ == "__main__":
    main()
