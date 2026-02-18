"""
================================================================================
TEST MODULE: MT5 Connector
================================================================================

PURPOSE:
    Unit tests for core/mt5_connector.py.
    Uses unittest.mock to simulate MetaTrader 5 terminal interactions, allowing
    testing without a running MT5 instance or Wine environment.

CONTEXT:
    Runs as part of the test suite.

VERSION HISTORY:
    1.0.0 (2026-01-28) - Initial creation
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the MetaTrader5 module BEFORE importing mt5_connector
sys.modules['MetaTrader5'] = MagicMock()

from core.mt5_connector import MT5Connector

class TestMT5Connector(unittest.TestCase):
    
    def setUp(self):
        self.connector = MT5Connector(config_path=None)
        # Mock the internal config to avoid file I/O issues during test
        self.connector.config = {"account": {"demo_only": True}}

    @patch('core.mt5_connector.mt5')
    def test_connect_success(self, mock_mt5):
        """Test successful connection"""
        # Setup mocks
        mock_mt5.initialize.return_value = True
        mock_mt5.terminal_info.return_value = MagicMock(name="MetaQuotes", company="MetaQuotes")
        
        # Mock account info for demo check
        mock_account = MagicMock()
        mock_account.trade_mode = 0 # Demo
        mock_account.login = 123456
        mock_account.balance = 10000.0  # Float for formatting
        mock_mt5.account_info.return_value = mock_account
        
        # Execute
        result = self.connector.connect()
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(self.connector.connected)
        mock_mt5.initialize.assert_called_once()

    @patch('core.mt5_connector.mt5')
    def test_connect_fail_init(self, mock_mt5):
        """Test connection failure during initialization"""
        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (1, "Generic Error")
        
        result = self.connector.connect()
        
        self.assertFalse(result)
        self.assertFalse(self.connector.connected)

    @patch('core.mt5_connector.mt5')
    def test_place_order_buy(self, mock_mt5):
        """Test placing a BUY order"""
        # Connect first (mocked)
        self.connector.connected = True
        self.connector.is_demo = True 
        
        # Mock symbol info and tick
        mock_info = MagicMock()
        mock_info.visible = True
        mock_mt5.symbol_info.return_value = mock_info
        
        mock_tick = MagicMock()
        mock_tick.ask = 2000.0
        mock_mt5.symbol_info_tick.return_value = mock_tick
        
        # Mock order_send result
        mock_result = MagicMock()
        mock_result.retcode = 10009 # TRADE_RETCODE_DONE
        mock_result.order = 99999
        mock_mt5.order_send.return_value = mock_result
        mock_mt5.TRADE_RETCODE_DONE = 10009
        
        # Execute
        result = self.connector.place_order("XAUUSD", "BUY", 0.01)
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['ticket'], 99999)
        self.assertEqual(result['price'], 2000.0)

if __name__ == '__main__':
    unittest.main()
