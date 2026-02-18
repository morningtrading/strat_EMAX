"""
================================================================================
TEST MODULE: Configuration Validator
================================================================================

PURPOSE:
    Unit tests for config/validate_config.py.
    Ensures that valid configs pass and invalid configs (missing keys, bad types,
    unsafe values) are correctly rejected.

CONTEXT:
    Runs as part of the test suite.

VERSION HISTORY:
    1.0.0 (2026-01-28) - Initial creation
"""

import unittest
import os
import json
import tempfile
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.validate_config import validate_config

class TestConfigValidator(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary valid config file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.valid_config = {
            "account": {
                "demo_only": True,
                "max_daily_loss_percent": 10.0
            },
            "symbols": {
                "enabled": ["XAUUSD"],
                "settings": {
                    "XAUUSD": {"volume": 0.01}
                }
            },
            "strategy": {
                "name": "EMA"
            }
        }
        json.dump(self.valid_config, self.temp_file)
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_valid_config(self):
        """Test that a compliant config passes validation"""
        self.assertTrue(validate_config(self.temp_file.name))

    def test_missing_account_section(self):
        """Test failure when 'account' section is missing"""
        config = self.valid_config.copy()
        del config['account']
        with open(self.temp_file.name, 'w') as f:
            json.dump(config, f)
        self.assertFalse(validate_config(self.temp_file.name))

    def test_missing_demo_only(self):
        """Test failure when critical safety flag 'demo_only' is missing"""
        config = self.valid_config.copy()
        del config['account']['demo_only']
        with open(self.temp_file.name, 'w') as f:
            json.dump(config, f)
        self.assertFalse(validate_config(self.temp_file.name))

    def test_symbol_volume_limits(self):
        """Test failure when volume is out of bounds"""
        config = self.valid_config.copy()
        config['symbols']['settings']['XAUUSD']['volume'] = 1000.0  # Too high
        with open(self.temp_file.name, 'w') as f:
            json.dump(config, f)
        self.assertFalse(validate_config(self.temp_file.name))

if __name__ == '__main__':
    unittest.main()
