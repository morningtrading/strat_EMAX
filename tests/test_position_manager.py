"""
================================================================================
TEST MODULE: Position Manager
================================================================================

PURPOSE:
    Unit tests for core/position_manager.py.
    Tests risk calculation, position sizing, and session filtering logic.

CONTEXT:
    Runs as part of the test suite.

VERSION HISTORY:
    1.0.0 (2026-01-28) - Initial creation
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock MT5 before import
sys.modules['MetaTrader5'] = MagicMock()

from core.position_manager import PositionManager

class TestPositionManager(unittest.TestCase):
    
    def setUp(self):
        self.mock_mt5 = MagicMock()
        self.config = {
            "account": {
                "max_margin_per_trade_usd": 20.0,
                "position_size_type": "symbol_specific"
            },
            "symbols": {
                "settings": {
                    "XAUUSD": {"volume": 0.01}
                }
            }
        }
        
        # Patch the _load_config method to avoid file I/O
        with patch.object(PositionManager, '_load_config', return_value=self.config):
             self.manager = PositionManager(self.mock_mt5, config_path=None)

    def test_calculate_position_size(self):
        """Test position size calculation based on config"""
        # Configure Mocks for math operations
        self.mock_mt5.get_symbol_info.return_value = {
            'trade_contract_size': 100.0,
            'volume_min': 0.01,
            'volume_step': 0.01,
            'bid': 2000.0,
            'ask': 2000.1,
            'trade_mode': 4
        }
        self.mock_mt5.get_account_summary.return_value = {
            'leverage': 100,
            'balance': 10000.0,
            'equity': 10000.0
        }

        # Should return volume from config for symbol
        vol, details = self.manager.calculate_position_size("XAUUSD")
        self.assertEqual(vol, 0.01)
        
    def test_check_spread_ok(self):
        """Test spread check passes when spread is low"""
        self.mock_mt5.get_symbol_info.return_value = {'spread': 10}
        # In current config, XAUUSD max_spread is 9999 so it should pass
        result, spread = self.manager.check_spread("XAUUSD")
        self.assertTrue(result)

    def test_open_position(self):
        """Test open_position calls place_order with correct magic number"""
        # Setup mocks
        self.mock_mt5.get_symbol_info.return_value = {
            'trade_allowed': True, 'spread': 10, 'trade_contract_size': 100, 
            'volume_min': 0.01, 'volume_step': 0.01, 'digits': 2, 'point': 0.01
        }
        self.mock_mt5.get_current_price.return_value = {'ask': 2000.0, 'bid': 1999.0}
        self.mock_mt5.get_account_summary.return_value = {'balance': 10000, 'leverage': 500}
        self.mock_mt5.place_order.return_value = {'success': True, 'ticket': 999, 'price': 2000.0}
        
        # Test
        self.manager.open_position("XAUUSD", "LONG", "Test Reason")
        
        # Verify
        self.mock_mt5.place_order.assert_called_once()
        _, kwargs = self.mock_mt5.place_order.call_args
        # self.manager.magic_number should be 123456 (default from config mock?)
        # Actually our mock config in setUp doesn't set it, so it might default to None or 123456 depending on implementation.
        # In implementation: self.magic_number = self.config.get('magic_number', 123456)
        # So it should be 123456.
        self.assertEqual(kwargs['magic'], 123456)

if __name__ == '__main__':
    unittest.main()
