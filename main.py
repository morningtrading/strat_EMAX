"""
================================================================================
EMAX TRADING ENGINE - Main Entry Point
================================================================================

PURPOSE:
    The main trading engine that orchestrates all components:
    - MT5 connection and data retrieval
    - EMA strategy signal generation
    - Position management and execution
    - Telegram notifications

INPUTS:
    - Configuration from config/trading_config.json
    - MT5 terminal running under Wine

OUTPUTS:
    - Trading signals and executions
    - Web dashboard on configured port
    - Telegram notifications

HOW TO START:
    # Start MT5 terminal first
    wine terminal64.exe
    
    # Then run the engine
    wine python main.py

SEQUENCE:
    1. Load configuration
    2. Connect to MT5
    3. Initialize strategy and position manager
    4. Start web dashboard
    5. Main loop: fetch data -> analyze -> execute

AUTHOR: EMAX Trading Engine
VERSION: 1.0.0
LAST UPDATED: 2026-01-22
================================================================================
"""

import os
import sys
import json
import time
import logging
import signal
import threading
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.mt5_connector import MT5Connector
from core.ema_strategy import EMAStrategy, SignalType
from core.position_manager import PositionManager
from core.telegram_notifier import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trading_engine.log')
    ]
)
logger = logging.getLogger('TradingEngine')


class TradingEngine:
    """
    Main EMAX Trading Engine
    
    Coordinates all trading components:
    - MT5 connection
    - Strategy analysis
    - Position execution
    - Notifications
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Trading Engine
        
        Args:
            config_path: Path to trading_config.json
        """
        self.running = False
        self.paused = False
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent / 'config' / 'trading_config.json'
        self.config_path = config_path
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.mt5 = MT5Connector(config_path)
        self.strategy = EMAStrategy(config_path)
        self.position_manager = PositionManager(self.mt5, config_path)
        self.telegram = TelegramNotifier(config_path)
        
        # Trading state
        self.trading_enabled = self.config.get('strategy', {}).get('trading_enabled', True)
        self.direction = self.config.get('strategy', {}).get('direction', 'both')
        self.enabled_symbols = self.config.get('symbols', {}).get('enabled', [])
        
        # Data refresh settings
        data_config = self.config.get('data_refresh', {})
        self.price_refresh_ms = data_config.get('price_refresh_ms', 1000)
        self.order_refresh_ms = data_config.get('order_refresh_ms', 2000)
        
        # Dashboard data (shared with web server)
        self.dashboard_data = {
            'connection_status': {},
            'account_info': {},
            'positions': [],
            'orders_history': [],
            'strategy_status': {},
            'manager_status': {},
            'last_signals': {},
            'ema_values': {},
            'daily_stats': {},
            'engine_status': {
                'trading_enabled': self.trading_enabled,
                'direction': self.direction,
                'enabled_symbols': self.enabled_symbols,
                'running': False,
                'uptime': 0
            }
        }
        self.market_overview = {}
        self.dashboard_lock = threading.Lock()
        
        # Track last bar times to detect new bars
        self.last_bar_time: Dict[str, str] = {}
        
        # Start time for uptime stats and history filtering
        self.start_time = datetime.now()
        self.stats_reset_time = self.start_time
        
        # Connect to MT5 first to validate symbols
        if self.mt5.connect():
            self.enabled_symbols = self._validate_symbols()
        else:
            logger.warning("Could not connect to MT5 for symbol validation. Using config symbols.")
        
        logger.info("Trading Engine initialized")
        logger.info(f"Enabled symbols: {self.enabled_symbols}")
        
    def _validate_symbols(self):
        """Validate that enabled symbols exist on the broker"""
        valid_symbols = []
        
        # Ensure connected
        if not self.mt5.connected:
            return self.enabled_symbols
            
        for symbol in self.enabled_symbols:
            info = self.mt5.get_symbol_info(symbol)
            if info:
                valid_symbols.append(symbol)
                logger.info(f"Symbol verified: {symbol}")
            else:
                logger.error(f"Symbol NOT FOUND: {symbol}. Please check Market Watch.")
            
        return valid_symbols
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_config(self.config_path)
        self.trading_enabled = self.config.get('strategy', {}).get('trading_enabled', True)
        self.direction = self.config.get('strategy', {}).get('direction', 'both')
        self.enabled_symbols = self.config.get('symbols', {}).get('enabled', [])
        
        # Re-validate symbols
        if self.mt5.connected:
            self.enabled_symbols = self._validate_symbols()
            
        logger.info("Configuration reloaded")
    
    def connect(self) -> bool:
        """
        Connect to MT5
        
        Returns:
            bool: True if connected successfully
        """
        if self.mt5.connect():
            # Verify demo account
            status = self.mt5.get_connection_status()
            if self.config.get('account', {}).get('demo_only', True):
                if not status.get('is_demo', False):
                    logger.error("SAFETY: Real account detected! Demo only mode is enabled.")
                    self.telegram.notify_error("Safety", "Real account blocked - demo_only mode")
                    self.mt5.disconnect()
                    return False
            
            # Send connection notification
            account_info = self.mt5.get_account_summary()
            self.telegram.send_status(True, account_info)
            
            return True
        
        return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        self.mt5.disconnect()
    
    def set_trading_enabled(self, enabled: bool):
        """Enable or disable trading"""
        self.trading_enabled = enabled
        self.strategy.set_trading_enabled(enabled)
        logger.info(f"Trading {'enabled' if enabled else 'disabled'}")
    
    def set_direction(self, direction: str):
        """Set trading direction (both, long, short)"""
        if direction in ['both', 'long', 'short']:
            self.direction = direction
            self.strategy.set_direction(direction)
            logger.info(f"Direction set to: {direction}")
    
    def panic_close_all(self):
        """Close all positions immediately"""
        logger.warning("PANIC BUTTON PRESSED!")
        
        # Get current positions for PnL calculation
        positions = self.mt5.get_positions()
        total_pnl = sum(p.get('profit', 0) for p in positions)
        
        # Close all
        result = self.position_manager.close_all_positions()
        
        # Notify
        self.telegram.send_panic_alert(result.get('closed', 0), total_pnl)
        
        return result
    
    def _update_dashboard_data(self):
        """Update data for dashboard display"""
        with self.dashboard_lock:
            # Connection status
            self.dashboard_data['connection_status'] = self.mt5.get_connection_status()
            
            # Account info
            self.dashboard_data['account_info'] = self.mt5.get_account_summary()
            
            # Current positions
            self.dashboard_data['positions'] = self.mt5.get_positions()
            
            # Recent deals/orders (Session only)
            recent_deals = self.mt5.get_history_deals(days=1)
            cutoff = self.stats_reset_time.isoformat()
            self.dashboard_data['orders_history'] = [d for d in recent_deals if d['time'] >= cutoff][-20:]
            
            # Strategy and manager status
            self.dashboard_data['strategy_status'] = self.strategy.get_strategy_status()
            self.dashboard_data['manager_status'] = self.position_manager.get_manager_status()
            
            # Daily stats
            self.dashboard_data['daily_stats'] = self.position_manager.get_daily_stats()
            
            # Engine status
            # Get timeframe from first enabled symbol's config
            first_symbol = self.enabled_symbols[0] if self.enabled_symbols else 'XAUUSD'
            symbol_settings = self.config.get('symbols', {}).get('settings', {}).get(first_symbol, {})
            current_timeframe = symbol_settings.get('timeframe', 'M5')
            
            self.dashboard_data['engine_status'] = {
                'trading_enabled': self.trading_enabled,
                'direction': self.direction,
                'enabled_symbols': self.enabled_symbols,
                'running': self.running,
                'paused': self.paused,
                'uptime': (datetime.now() - self.start_time).seconds if self.start_time else 0,
                'timeframe': current_timeframe
            }
            
            # Market Overview
            self.dashboard_data['market_overview'] = dict(self.market_overview)
    
    def _process_symbol(self, symbol: str):
        """
        Process a single symbol: get data, analyze, execute
        
        Args:
            symbol: Trading symbol
        """
        # Get current position for this symbol
        positions = self.mt5.get_positions(symbol)
        current_position = None
        if positions:
            current_position = "LONG" if positions[0]['type'] == "BUY" else "SHORT"
        
        # Get price data with enough bars for EMA calculation
        symbol_config = self.config.get('symbols', {}).get('settings', {}).get(symbol, {})
        timeframe = symbol_config.get('timeframe', 'M5')
        
        bars = self.mt5.get_rates(symbol, timeframe, count=100)
        if not bars:
            logger.warning(f"[{symbol}] Failed to get price data")
            return
        
        # Check for new bar
        current_bar_time = bars[-1]['time']
        if current_bar_time != self.last_bar_time.get(symbol):
            self.last_bar_time[symbol] = current_bar_time
            logger.debug(f"[{symbol}] New bar: {current_bar_time}")
        
        # Analyze with strategy
        self.strategy.set_position(symbol, current_position)
        signal = self.strategy.analyze(symbol, bars, current_position)
        
        # Store signal for dashboard
        with self.dashboard_lock:
            self.dashboard_data['last_signals'][symbol] = {
                'action': signal.action.value,
                'reason': signal.reason,
                'strength': signal.strength,
                'timestamp': signal.timestamp
            }
            self.dashboard_data['ema_values'][symbol] = self.strategy.get_ema_values(symbol)
            
        # Update Market Status (Sequential / Thread-Safe)
        ema_vals = self.strategy.get_ema_values(symbol)
        if ema_vals:
            fast = ema_vals.get('fast_ema', [])
            slow = ema_vals.get('slow_ema', [])
            analysis = self.strategy.analyze_trend_momentum(fast, slow)
            
            with self.dashboard_lock:
                self.market_overview[symbol] = {
                    'price': bars[-1]['close'],
                    'trend': analysis['trend'],
                    'momentum': analysis['momentum'],
                    'diff': analysis.get('diff', 0.0),
                    'polling': 'OK',
                    'updated': datetime.now().isoformat()
                }
        
        # Execute if trading enabled and we have a trading signal
        if not self.trading_enabled or self.paused:
            return
        
        if signal.action == SignalType.BUY:
            result = self.position_manager.open_position(symbol, "LONG", signal.reason)
            if result.success:
                self.telegram.notify_trade_entry(
                    symbol, "LONG", result.volume, result.price, result.sl, signal.reason
                )
            elif result.error:
                self.telegram.notify_error("Order Failed", result.error, symbol)
        
        elif signal.action == SignalType.SELL:
            result = self.position_manager.open_position(symbol, "SHORT", signal.reason)
            if result.success:
                self.telegram.notify_trade_entry(
                    symbol, "SHORT", result.volume, result.price, result.sl, signal.reason
                )
            elif result.error:
                self.telegram.notify_error("Order Failed", result.error, symbol)
        
        elif signal.action in [SignalType.EXIT_LONG, SignalType.EXIT_SHORT]:
            if positions:
                pos = positions[0]
                result = self.position_manager.close_position(symbol, pos['ticket'], signal.reason)
                if result.success:
                    direction = "LONG" if signal.action == SignalType.EXIT_LONG else "SHORT"
                    self.telegram.notify_trade_exit(
                        symbol, direction, pos['volume'],
                        pos['price_open'], result.price, pos['profit'], signal.reason
                    )
    
    def run(self, dashboard_only: bool = False):
        """
        Main trading loop
        
        Args:
            dashboard_only: If True, only update dashboard data without trading
        """
        if not self.connect():
            logger.error("Failed to connect to MT5")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("Trading engine started")
        logger.info(f"Trading enabled: {self.trading_enabled}")
        logger.info(f"Direction: {self.direction}")
        logger.info(f"Symbols: {self.enabled_symbols}")
        
        try:
            while self.running:
                # Update dashboard data
                self._update_dashboard_data()
                
                # Process each enabled symbol
                if not dashboard_only:
                    for symbol in self.enabled_symbols:
                        try:
                            self._process_symbol(symbol)
                        except Exception as e:
                            logger.error(f"Error processing {symbol}: {e}")
                            self.telegram.notify_error("Processing Error", str(e), symbol)
                
                # Wait before next cycle
                time.sleep(self.price_refresh_ms / 1000)
        
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        
        finally:
            self.running = False
            self.disconnect()
            logger.info("Trading engine stopped")
    
    def stop(self):
        """Stop the trading engine"""
        self.running = False
    
    def pause(self):
        """Pause trading (but keep data updating)"""
        self.paused = True
        logger.info("Trading paused")
    
    def resume(self):
        """Resume trading"""
        self.paused = False
        logger.info("Trading resumed")
    
    def get_dashboard_data(self) -> Dict:
        """Get current dashboard data (thread-safe)"""
        with self.dashboard_lock:
            return dict(self.dashboard_data)


def main():
    """Main entry point"""
    print("="*60)
    print("   EMAX Trading Engine")
    print("   EMA Crossover Strategy for MT5")
    print("="*60)
    
    # Import dashboard
    from dashboard.web_dashboard import WebDashboard
    
    # Create engine
    engine = TradingEngine()
    
    # Load dashboard port from config
    dashboard_port = engine.config.get('dashboard', {}).get('web_port', 8080)
    
    # Create and start dashboard
    dashboard = WebDashboard(trading_engine=engine, port=dashboard_port)
    dashboard.start(threaded=True)
    
    print(f"\n📊 Dashboard running at: http://localhost:{dashboard_port}")
    print("="*60)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        print("\nShutting down...")
        engine.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start engine
    engine.run()


if __name__ == "__main__":
    main()

