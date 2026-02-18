"""
================================================================================
TEST MODULE: Telegram Notifier
================================================================================

PURPOSE:
    Unit tests for core/telegram_notifier.py.
    Uses mocks to ensure messages are formatted correctly and requests are sent
    to the correct API endpoint.

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

from core.telegram_notifier import TelegramNotifier

class TestTelegramNotifier(unittest.TestCase):
    
    def setUp(self):
        self.config = {
            "telegram": {
                "enabled": True, # Ensure it attempts to send
                "bot_token": "TEST_TOKEN",
                "chat_id": "TEST_CHAT_ID"
            }
        }
        with patch.object(TelegramNotifier, '_load_config', return_value=self.config):
            self.notifier = TelegramNotifier()

    @patch('core.telegram_notifier.requests.post')
    def test_send_message(self, mock_post):
        """Test sending a simple message"""
        self.notifier.message_prefix = "TEST_PREFIX"
        # Execute
        self.notifier.send_message("Test Message")
        
        # Verify
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertTrue("https://api.telegram.org/botTEST_TOKEN/sendMessage" in args[0])
        self.assertEqual(kwargs['json']['chat_id'], "TEST_CHAT_ID")
        self.assertEqual(kwargs['json']['text'], "[TEST_PREFIX] Test Message")

    @patch('core.telegram_notifier.requests.post')
    def test_notify_trade_entry(self, mock_post):
        """Test trade entry notification formatting"""
        self.notifier.notify_trade_entry(
            symbol="XAUUSD", direction="LONG", volume=0.01, 
            price=2000.0, sl=1990.0, reason="EMA Cross",
            margin=10.0, fast_ema=2001.0, slow_ema=1999.0
        )
        
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        msg = kwargs['json']['text']
        self.assertTrue("LONG" in msg)
        self.assertTrue("XAUUSD" in msg)
        self.assertTrue("EMA Cross" in msg)

if __name__ == '__main__':
    unittest.main()
