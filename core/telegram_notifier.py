"""
================================================================================
TELEGRAM NOTIFIER MODULE - EMAX Trading Engine
================================================================================

PURPOSE:
    Sends trading notifications and daily summaries via Telegram bot.
    Supports trade entry/exit alerts, error notifications, and scheduled
    daily P&L reports.

INPUTS:
    - Trade events from PositionManager
    - Configuration from trading_config.json:
        * bot_token: Telegram bot token from @BotFather
        * chat_id: Target chat/channel ID
        * notify_on_entry/exit/error: Toggle notifications
        * daily_summary_utc: Time to send daily summary

OUTPUTS:
    - Telegram messages to configured chat

HOW TO INSTALL:
    1. Create bot via @BotFather on Telegram
    2. Get bot token and add to config
    3. Get chat_id (message @userinfobot or check API)
    4. Set enabled: true in config

SEQUENCE IN OVERALL SYSTEM:
    [Trading Engine] -> [Telegram Notifier] -> [Telegram API] -> [Your Phone]

AUTHOR: EMAX Trading Engine
VERSION: 1.0.0
LAST UPDATED: 2026-01-22
================================================================================
"""

import json
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
from threading import Thread
import time

logger = logging.getLogger('TelegramNotifier')


class TelegramNotifier:
    """
    Telegram notification service for EMAX Trading Engine
    
    Sends:
    - Trade entry notifications
    - Trade exit notifications with P&L
    - Error alerts
    - Daily P&L summary
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Telegram Notifier
        
        Args:
            config_path: Path to trading_config.json
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'trading_config.json'
        self.config = self._load_config(config_path)
        
        # Extract telegram config
        tg_config = self.config.get('telegram', {})
        self.enabled = tg_config.get('enabled', False)
        self.bot_token = tg_config.get('bot_token', '')
        self.chat_id = tg_config.get('chat_id', '')
        self.notify_entry = tg_config.get('notify_on_entry', True)
        self.notify_exit = tg_config.get('notify_on_exit', True)
        self.should_notify_error = tg_config.get('notify_on_error', True)
        self.daily_summary_time = tg_config.get('daily_summary_utc', '21:00')
        
        # API endpoint
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Daily summary scheduler
        self.summary_thread = None
        self.running = False
        
        if self.enabled and self.bot_token and self.chat_id:
            logger.info("TelegramNotifier initialized and enabled")
        else:
            logger.info("TelegramNotifier disabled (check config)")
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
            return {}
    
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.enabled and self.bot_token and self.chat_id)
    
    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Send a message to Telegram
        
        Args:
            text: Message text (supports HTML formatting)
            parse_mode: 'HTML' or 'Markdown'
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_configured():
            logger.debug("Telegram not configured, skipping message")
            return False
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': parse_mode
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("Telegram message sent")
                return True
            else:
                logger.warning(f"Telegram API error: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def notify_trade_entry(self, symbol: str, direction: str, volume: float,
                          price: float, sl: Optional[float], reason: str,
                          margin: Optional[float] = None, fast_ema: Optional[float] = None,
                          slow_ema: Optional[float] = None, balance: Optional[float] = None,
                          equity: Optional[float] = None):
        """
        Send trade entry notification with detailed parameters
        
        Args:
            symbol: Trading symbol
            direction: "LONG" or "SHORT"
            volume: Lot size
            price: Entry price
            sl: Stop loss price
            reason: Entry reason
            margin: Margin used for position
            fast_ema: Fast EMA value at entry
            slow_ema: Slow EMA value at entry
            balance: Account balance at entry
            equity: Account equity at entry
        """
        if not self.notify_entry:
            return
        
        emoji = "🟢" if direction == "LONG" else "🔴"
        arrow = "⬆️" if direction == "LONG" else "⬇️"
        
        # Build base message
        message = f"""
{emoji} <b>TRADE OPENED</b> {arrow}

<b>Symbol:</b> {symbol}
<b>Direction:</b> {direction}
<b>Volume:</b> {volume} lots
<b>Entry:</b> {price}
<b>Stop Loss:</b> {sl if sl else 'None'}
"""
        
        # Add EMA values if provided
        if fast_ema is not None and slow_ema is not None:
            message += f"""
<b>📊 EMA Crossover:</b>
  • Fast EMA: {fast_ema:.4f}
  • Slow EMA: {slow_ema:.4f}
  • Spread: {abs(fast_ema - slow_ema):.4f}
"""
        
        # Add margin info if provided
        if margin is not None:
            message += f"""
<b>💰 Position:</b>
  • Margin Used: ${margin:.2f}
  • Risk: ${abs(price - sl) * volume if sl else 0:.2f}
"""
        
        # Add account info if provided
        if balance is not None and equity is not None:
            message += f"""
<b>💼 Account:</b>
  • Balance: ${balance:.2f}
  • Equity: ${equity:.2f}
  • Free Margin: ${equity - (margin if margin else 0):.2f}
"""
        
        message += f"""
<b>Reason:</b> {reason}

<i>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        self.send_message(message.strip())
    
    def notify_trade_exit(self, symbol: str, direction: str, volume: float,
                         entry_price: float, exit_price: float, pnl: float,
                         reason: str, hold_time: Optional[str] = None,
                         pips: Optional[float] = None, balance: Optional[float] = None,
                         equity: Optional[float] = None, total_pnl: Optional[float] = None):
        """
        Send trade exit notification with detailed P&L analysis
        
        Args:
            symbol: Trading symbol
            direction: Original direction
            volume: Lot size
            entry_price: Original entry price
            exit_price: Exit price
            pnl: Profit/loss in USD
            reason: Exit reason
            hold_time: How long position was held
            pips: Pips gained/lost
            balance: Account balance after exit
            equity: Account equity after exit
            total_pnl: Total account P&L
        """
        if not self.notify_exit:
            return
        
        pnl_emoji = "💰" if pnl >= 0 else "💸"
        result = "WIN" if pnl >= 0 else "LOSS"
        pnl_percent = ((exit_price - entry_price) / entry_price * 100) if direction == "LONG" else ((entry_price - exit_price) / entry_price * 100)
        
        # Build base message
        message = f"""
{pnl_emoji} <b>TRADE CLOSED - {result}</b>

<b>Symbol:</b> {symbol}
<b>Direction:</b> {direction}
<b>Volume:</b> {volume} lots
<b>Entry:</b> {entry_price}
<b>Exit:</b> {exit_price}
<b>P&L:</b> <code>${pnl:+.2f}</code> ({pnl_percent:+.2f}%)
"""
        
        # Add pips if provided
        if pips is not None:
            message += f"<b>Pips:</b> {pips:+.1f}\n"
        
        # Add hold time if provided
        if hold_time:
            message += f"<b>Duration:</b> {hold_time}\n"
        
        # Add account summary if provided
        if balance is not None and equity is not None:
            message += f"""
<b>💼 Account After Close:</b>
  • Balance: ${balance:.2f}
  • Equity: ${equity:.2f}
"""
            if total_pnl is not None:
                message += f"  • Total P&L: <code>${total_pnl:+.2f}</code>\n"
        
        message += f"""
<b>Reason:</b> {reason}

<i>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        self.send_message(message.strip())
    
    def notify_error(self, error_type: str, message: str, symbol: Optional[str] = None):
        """
        Send error notification
        
        Args:
            error_type: Type of error (e.g., "Connection", "Order Failed")
            message: Error details
            symbol: Related symbol if any
        """
        if not self.should_notify_error:
            return
        
        text = f"""
⚠️ <b>EMAX ERROR</b>

<b>Type:</b> {error_type}
{f'<b>Symbol:</b> {symbol}' if symbol else ''}
<b>Details:</b> {message}

<i>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        self.send_message(text.strip())
    
    def send_daily_summary(self, stats: Dict):
        """
        Send daily P&L summary
        
        Args:
            stats: Daily statistics from PositionManager
        """
        pnl = stats.get('daily_pnl', 0)
        trades = stats.get('daily_trades', 0)
        starting = stats.get('starting_balance', 0)
        
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        
        message = f"""
{pnl_emoji} <b>DAILY SUMMARY</b>

<b>Date:</b> {stats.get('date', 'N/A')}
<b>Starting Balance:</b> ${starting:.2f}
<b>Total P&L:</b> <code>${pnl:+.2f}</code>
<b>Total Trades:</b> {trades}

<b>Return:</b> {(pnl/starting*100) if starting else 0:.2f}%

<i>🤖 EMAX Trading Engine</i>
"""
        self.send_message(message.strip())
    
    def send_status(self, connected: bool, account_info: Dict):
        """
        Send connection status notification
        
        Args:
            connected: Connection status
            account_info: Account details
        """
        if connected:
            message = f"""
✅ <b>EMAX CONNECTED</b>

<b>Account:</b> {account_info.get('login', 'N/A')}
<b>Server:</b> {account_info.get('server', 'N/A')}
<b>Balance:</b> ${account_info.get('balance', 0):.2f}
<b>Equity:</b> ${account_info.get('equity', 0):.2f}
<b>Mode:</b> {'DEMO' if account_info.get('is_demo') else '⚠️ REAL'}

<i>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        else:
            message = f"""
❌ <b>EMAX DISCONNECTED</b>

Connection to MT5 lost.
Attempting to reconnect...

<i>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        self.send_message(message.strip())
    
    def send_panic_alert(self, closed_count: int, total_pnl: float):
        """
        Send panic button alert
        
        Args:
            closed_count: Number of positions closed
            total_pnl: Total P&L from closed positions
        """
        message = f"""
🚨 <b>PANIC BUTTON ACTIVATED</b> 🚨

<b>Positions Closed:</b> {closed_count}
<b>Total P&L:</b> <code>${total_pnl:+.2f}</code>

All positions have been closed immediately.

<i>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        self.send_message(message.strip())
    
    def test_connection(self) -> bool:
        """
        Send a test message to verify Telegram setup
        
        Returns:
            bool: True if test successful
        """
        return self.send_message("🤖 <b>EMAX Test</b>\n\nTelegram notifications are working!")


# Singleton instance for easy access
_notifier_instance = None

def get_notifier(config_path: Optional[str] = None) -> TelegramNotifier:
    """Get or create TelegramNotifier instance"""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = TelegramNotifier(config_path)
    return _notifier_instance


if __name__ == "__main__":
    # Test telegram connection
    notifier = TelegramNotifier()
    if notifier.is_configured():
        print("Testing Telegram connection...")
        if notifier.test_connection():
            print("✅ Telegram test message sent!")
        else:
            print("❌ Failed to send test message")
    else:
        print("Telegram not configured. Please add bot_token and chat_id to config.")
