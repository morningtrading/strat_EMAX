import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.validate_config import validate_config

CONFIG_PATH = Path('config/trading_config.json')

def verify():
    print(f"Verifying config at {CONFIG_PATH}...")
    
    if not CONFIG_PATH.exists():
        print("Config file not found!")
        sys.exit(1)
        
    is_valid = validate_config(str(CONFIG_PATH))
    
    if is_valid:
        print("✅ Configuration is VALID.")
        # Load and check symbol count
        with open(CONFIG_PATH, 'r') as f:
            cfg = json.load(f)
            count = len(cfg.get('symbols', {}).get('enabled', []))
            print(f"✅ Enabled Symbols Count: {count}")
    else:
        print("❌ Configuration is INVALID.")
        sys.exit(1)

if __name__ == "__main__":
    verify()
