
import json
import os

def main():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'trading_config.json')
    
    print(f"Loading config from {config_path}...")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Update/Add dashboard port settings
        if 'dashboard' not in config:
            config['dashboard'] = {}
            
        current_port = config['dashboard'].get('web_port', 'unknown')
        print(f"Current port: {current_port}")
        
        config['dashboard']['web_port'] = 8081
        print(f"New port: 8081")
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        print("Config updated successfully. Please restart the engine.")
        
    except Exception as e:
        print(f"Error updating config: {e}")

if __name__ == "__main__":
    main()
