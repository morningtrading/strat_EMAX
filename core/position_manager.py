"""
================================================================================
POSITION MANAGER MODULE - EMAX Trading Engine
================================================================================

PURPOSE:
    Manages position sizing, entry/exit execution, stop loss placement, and
    risk management. Acts as the bridge between strategy signals and MT5 order
    execution.

INPUTS:
    - Trading signals from EMAStrategy
    - Account info from MT5Connector
    - Configuration from trading_config.json:
        * max_margin_per_trade_usd: Maximum margin to use (default: $10)
        * stop_loss.type: "fixed" or "atr"
        * stop_loss.fixed_percent_of_margin: SL as % of margin (default: 50%)
        * stop_loss.atr_multiplier: For ATR-based SL

OUTPUTS:
    - Executed trade results
    - Position status updates
    - Risk metrics

HOW TO INSTALL:
    Part of EMAX trading engine. Dependencies: MT5Connector, EMAStrategy

SEQUENCE IN OVERALL SYSTEM:
    [EMA Strategy] -> [Position Manager] -> [MT5 Connector] -> [MT5 Terminal]
                           ^                      |
                           |                      v
                    [Risk Manager] <-------- [Position Updates]

    Position Manager receives signals, calculates position size and SL/TP,
    then sends orders through MT5 Connector.

OBJECTIVE:
    Execute trades with proper position sizing and risk management, ensuring
    margin limits and stop losses are respected.

KEY FEATURES:
    - Position sizing based on margin limits
    - Fixed or ATR-based stop loss
    - Spread checking before entry
    - Session filtering
    - Daily loss limit enforcement

AUTHOR: EMAX Trading Engine
VERSION: 1.0.0
LAST UPDATED: 2026-01-22
================================================================================
"""

import json
import logging
from datetime import datetime, time as dtime
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger('PositionManager')


@dataclass
class TradeResult:
    """Result of a trade execution"""
    success: bool
    action: str  # "OPEN_LONG", "OPEN_SHORT", "CLOSE_LONG", "CLOSE_SHORT"
    symbol: str
    volume: float
    price: float
    sl: Optional[float]
    tp: Optional[float]
    ticket: Optional[int]
    error: Optional[str]
    margin_used: float
    timestamp: str


class PositionManager:
    """
    Position Manager for trade execution and risk management
    
    Handles:
    - Position sizing based on margin limits
    - Stop loss calculation (fixed or ATR-based)
    - Trade execution through MT5Connector
    - Session and spread filtering
    - Daily loss tracking
    """
    
    def __init__(self, mt5_connector, config_path: Optional[str] = None):
        """
        Initialize Position Manager
        
        Args:
            mt5_connector: Instance of MT5Connector
            config_path: Path to trading_config.json
        """
        self.mt5 = mt5_connector
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'trading_config.json'
        self.config = self._load_config(config_path)
        
        # Extract config values
        account_config = self.config.get('account', {})
        self.max_margin = account_config.get('max_margin_per_trade_usd', 10.0)
        self.max_daily_loss_percent = account_config.get('max_daily_loss_percent', 75.0)
        self.leverage = account_config.get('default_leverage', 1000)
        self.position_size_type = account_config.get('position_size_type', 'margin')
        self.fixed_volume = account_config.get('fixed_volume', 0.01)
        
        # Stop loss config
        sl_config = self.config.get('stop_loss', {})
        self.sl_type = sl_config.get('type', 'fixed')  # fixed or atr
        self.sl_fixed_percent = sl_config.get('fixed_percent_of_margin', 50.0)
        self.sl_atr_multiplier = sl_config.get('atr_multiplier', 1.5)
        self.sl_atr_period = sl_config.get('atr_period', 14)
        
        # Session filter config
        session_config = self.config.get('session_filter', {})
        self.session_filter_enabled = session_config.get('enabled', True)
        self.overlap_start = session_config.get('overlap_start_utc', '13:30')
        self.overlap_end = session_config.get('overlap_end_utc', '16:30')
        self.london_open = session_config.get('london_open_utc', '08:00')
        self.ny_close = session_config.get('ny_close_utc', '20:00')
        
        # Symbol settings
        self.symbol_settings = self.config.get('symbols', {}).get('settings', {})
        
        # State tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.starting_balance = None
        self.last_reset_date = None
        self.trade_history: List[TradeResult] = []
        
        logger.info(f"PositionManager initialized: max_margin=${self.max_margin}, SL_type={self.sl_type}")
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return {}
    
    def _reset_daily_stats(self):
        """Reset daily statistics at start of new trading day"""
        today = datetime.now().date()
        if self.last_reset_date != today:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = today
            
            # Get starting balance
            account = self.mt5.get_account_summary()
            if 'balance' in account:
                self.starting_balance = account['balance']
            
            logger.info(f"Daily stats reset. Starting balance: ${self.starting_balance:.2f}")
    
    def check_session_filter(self) -> Tuple[bool, str]:
        """
        Check if current time is within trading session
        
        Returns:
            Tuple of (is_allowed, reason)
        """
        if not self.session_filter_enabled:
            return True, "Session filter disabled"
        
        now_utc = datetime.utcnow().time()
        
        # Parse session times
        london_open = dtime(*map(int, self.london_open.split(':')))
        ny_close = dtime(*map(int, self.ny_close.split(':')))
        overlap_start = dtime(*map(int, self.overlap_start.split(':')))
        overlap_end = dtime(*map(int, self.overlap_end.split(':')))
        
        # Check if within main session (London open to NY close)
        if london_open <= now_utc <= ny_close:
            # Check if we're in overlap (best time)
            if overlap_start <= now_utc <= overlap_end:
                return True, "Within London/NY overlap - optimal"
            return True, "Within main trading session"
        
        return False, f"Outside trading session ({self.london_open}-{self.ny_close} UTC)"
    
    def check_spread(self, symbol: str) -> Tuple[bool, float]:
        """
        Check if spread is acceptable for trading
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tuple of (is_acceptable, current_spread_points)
        """
        symbol_config = self.symbol_settings.get(symbol, {})
        max_spread = symbol_config.get('max_spread_points', 100)
        
        # Get symbol info
        info = self.mt5.get_symbol_info(symbol)
        if info is None:
            return False, 0
        
        current_spread = info.get('spread', 0)
        
        if current_spread > max_spread:
            logger.warning(f"[{symbol}] Spread too wide: {current_spread} > {max_spread}")
            return False, current_spread
        
        return True, current_spread
    
    def check_daily_loss_limit(self) -> Tuple[bool, float]:
        """
        Check if daily loss limit has been reached
        
        Returns:
            Tuple of (can_trade, current_loss_percent)
        """
        self._reset_daily_stats()
        
        if self.starting_balance is None or self.starting_balance == 0:
            return True, 0.0
        
        account = self.mt5.get_account_summary()
        if 'balance' not in account:
            return True, 0.0
        
        current_balance = account['balance']
        loss_percent = ((self.starting_balance - current_balance) / self.starting_balance) * 100
        
        if loss_percent >= self.max_daily_loss_percent:
            logger.error(f"Daily loss limit reached: {loss_percent:.1f}% >= {self.max_daily_loss_percent}%")
            return False, loss_percent
        
        return True, loss_percent
    
    def calculate_position_size(self, symbol: str) -> Tuple[float, Dict]:
        """
        Calculate position size based on margin limit
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tuple of (volume, calculation_details)
        """
        info = self.mt5.get_symbol_info(symbol)
        if info is None:
            return 0.0, {"error": "Symbol info unavailable"}
        
        # Get account info
        account = self.mt5.get_account_summary()
        if 'error' in account:
            return 0.0, {"error": account['error']}
        
        current_price = info.get('bid', 0)
        if current_price == 0:
            return 0.0, {"error": "Price unavailable"}
        
        contract_size = info.get('trade_contract_size', 1)
        min_volume = info.get('volume_min', 0.01)
        volume_step = info.get('volume_step', 0.01)
        leverage = account.get('leverage', self.leverage)
        
        # Calculate margin required for min lot
        # Margin = (Contract Size * Lot Size * Price) / Leverage
        margin_per_lot = (contract_size * 1.0 * current_price) / leverage
        
        # Check position sizing type
        if self.position_size_type == "fixed":
            # Use fixed volume
            volume = self.fixed_volume
            # Round to volume step to be safe
            volume = round(volume / volume_step) * volume_step
        else:
            # MARGIN BASED SIZING
            if margin_per_lot == 0:
                return min_volume, {"error": "Zero margin calculation"}
            
            # Calculate max volume based on margin limit
            max_volume = self.max_margin / margin_per_lot
            
            # Round to volume step
            volume = max(min_volume, round(max_volume / volume_step) * volume_step)
        
        # Cap at minimum for safety
        symbol_config = self.symbol_settings.get(symbol, {})
        min_vol = symbol_config.get('min_volume', min_volume)
        volume = max(volume, min_vol)
        
        details = {
            "calculated_volume": volume,
            "margin_per_lot": margin_per_lot,
            "max_margin": self.max_margin,
            "leverage": leverage,
            "contract_size": contract_size,
            "current_price": current_price,
            "min_volume": min_volume,
            "sizing_type": self.position_size_type
        }
        
        logger.info(f"[{symbol}] Position size: {volume} lots ({self.position_size_type})")
        
        return volume, details
    
    def calculate_stop_loss(self, symbol: str, entry_price: float, 
                           direction: str, atr_value: Optional[float] = None) -> Optional[float]:
        """
        Calculate stop loss price
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            direction: "LONG" or "SHORT"
            atr_value: ATR value if using ATR-based SL
            
        Returns:
            Stop loss price or None
        """
        if self.sl_type == 'atr' and atr_value:
            # ATR-based stop loss
            sl_distance = atr_value * self.sl_atr_multiplier
        else:
            # Fixed percentage of margin -> convert to price distance
            # SL triggers when loss = fixed_percent of margin
            # For a $10 margin with 50% SL, max loss = $5
            
            # Get position size
            volume, _ = self.calculate_position_size(symbol)
            if volume == 0:
                return None
            
            info = self.mt5.get_symbol_info(symbol)
            if info is None:
                return None
            
            contract_size = info.get('trade_contract_size', 1)
            point = info.get('point', 0.00001)
            
            # Max loss in dollars
            max_loss = self.max_margin * (self.sl_fixed_percent / 100)
            
            # Convert to price distance
            # Loss = Volume * Contract_Size * Price_Movement
            # Price_Movement = Loss / (Volume * Contract_Size)
            if volume * contract_size == 0:
                return None
            
            sl_distance = max_loss / (volume * contract_size)
        
        # Calculate SL price based on direction
        if direction == "LONG":
            sl_price = entry_price - sl_distance
        else:
            sl_price = entry_price + sl_distance
        
        # Round to symbol precision
        info = self.mt5.get_symbol_info(symbol)
        if info:
            digits = info.get('digits', 5)
            sl_price = round(sl_price, digits)
        
        logger.info(f"[{symbol}] SL calculated: {sl_price} (distance: {sl_distance})")
        
        return sl_price
    
    def open_position(self, symbol: str, direction: str, 
                      reason: str = "EMA Signal") -> TradeResult:
        """
        Open a new position
        
        Args:
            symbol: Trading symbol
            direction: "LONG" or "SHORT"
            reason: Reason for trade
            
        Returns:
            TradeResult with execution details
        """
        timestamp = datetime.now().isoformat()
        
        # Pre-flight checks
        # 1. Session filter
        session_ok, session_reason = self.check_session_filter()
        if not session_ok:
            return TradeResult(
                success=False, action=f"OPEN_{direction}", symbol=symbol,
                volume=0, price=0, sl=None, tp=None, ticket=None,
                error=f"Session filter: {session_reason}", margin_used=0,
                timestamp=timestamp
            )
        
        # 2. Spread check
        spread_ok, spread = self.check_spread(symbol)
        if not spread_ok:
            return TradeResult(
                success=False, action=f"OPEN_{direction}", symbol=symbol,
                volume=0, price=0, sl=None, tp=None, ticket=None,
                error=f"Spread too wide: {spread}", margin_used=0,
                timestamp=timestamp
            )
        
        # 3. Daily loss check
        can_trade, loss_percent = self.check_daily_loss_limit()
        if not can_trade:
            return TradeResult(
                success=False, action=f"OPEN_{direction}", symbol=symbol,
                volume=0, price=0, sl=None, tp=None, ticket=None,
                error=f"Daily loss limit: {loss_percent:.1f}%", margin_used=0,
                timestamp=timestamp
            )
        
        # 4. Calculate position size
        volume, size_details = self.calculate_position_size(symbol)
        if volume == 0:
            return TradeResult(
                success=False, action=f"OPEN_{direction}", symbol=symbol,
                volume=0, price=0, sl=None, tp=None, ticket=None,
                error=f"Position size error: {size_details.get('error', 'Unknown')}", 
                margin_used=0, timestamp=timestamp
            )
        
        # 5. Get current price
        price_info = self.mt5.get_current_price(symbol)
        if price_info is None:
            return TradeResult(
                success=False, action=f"OPEN_{direction}", symbol=symbol,
                volume=volume, price=0, sl=None, tp=None, ticket=None,
                error="Failed to get price", margin_used=0, timestamp=timestamp
            )
        
        entry_price = price_info['ask'] if direction == "LONG" else price_info['bid']
        
        # 6. Calculate stop loss
        sl_price = self.calculate_stop_loss(symbol, entry_price, direction)
        
        # 7. Execute trade
        order_type = "BUY" if direction == "LONG" else "SELL"
        result = self.mt5.place_order(
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            sl=sl_price,
            comment="EMAX"
        )
        
        if result['success']:
            margin_used = size_details.get('margin_per_lot', 0) * volume
            self.daily_trades += 1
            
            trade_result = TradeResult(
                success=True, action=f"OPEN_{direction}", symbol=symbol,
                volume=volume, price=result.get('price', entry_price), 
                sl=sl_price, tp=None, ticket=result.get('ticket'),
                error=None, margin_used=margin_used, timestamp=timestamp
            )
            
            self.trade_history.append(trade_result)
            logger.info(f"[{symbol}] Position opened: {direction} {volume} @ {entry_price}, SL={sl_price}, Ticket={result.get('ticket')}")
            
            return trade_result
        else:
            return TradeResult(
                success=False, action=f"OPEN_{direction}", symbol=symbol,
                volume=volume, price=entry_price, sl=sl_price, tp=None, ticket=None,
                error=result.get('error', 'Unknown error'), margin_used=0,
                timestamp=timestamp
            )
    
    def close_position(self, symbol: str, ticket: Optional[int] = None,
                       reason: str = "Signal") -> TradeResult:
        """
        Close a position
        
        Args:
            symbol: Trading symbol
            ticket: Optional specific ticket to close
            reason: Reason for closing
            
        Returns:
            TradeResult with execution details
        """
        timestamp = datetime.now().isoformat()
        
        # Get position(s) to close
        if ticket:
            positions = [p for p in self.mt5.get_positions(symbol) if p['ticket'] == ticket]
        else:
            positions = self.mt5.get_positions(symbol)
        
        if not positions:
            return TradeResult(
                success=False, action="CLOSE", symbol=symbol,
                volume=0, price=0, sl=None, tp=None, ticket=ticket,
                error="No position found", margin_used=0, timestamp=timestamp
            )
        
        # Close first/only position
        pos = positions[0]
        result = self.mt5.close_position(pos['ticket'])
        
        if result['success']:
            direction = "LONG" if pos['type'] == "BUY" else "SHORT"
            self.daily_pnl += pos['profit']
            
            trade_result = TradeResult(
                success=True, action=f"CLOSE_{direction}", symbol=symbol,
                volume=pos['volume'], price=result.get('close_price', 0),
                sl=None, tp=None, ticket=pos['ticket'],
                error=None, margin_used=0, timestamp=timestamp
            )
            
            self.trade_history.append(trade_result)
            logger.info(f"[{symbol}] Position closed: {direction} {pos['volume']} PnL=${pos['profit']:.2f}")
            
            return trade_result
        else:
            return TradeResult(
                success=False, action="CLOSE", symbol=symbol,
                volume=pos['volume'], price=0, sl=None, tp=None, ticket=pos['ticket'],
                error=result.get('error', 'Unknown error'), margin_used=0,
                timestamp=timestamp
            )
    
    def close_all_positions(self) -> Dict:
        """
        Close all open positions (panic button)
        
        Returns:
            Dict with summary of closed positions
        """
        result = self.mt5.close_all_positions()
        
        if result['closed'] > 0:
            logger.warning(f"PANIC: Closed {result['closed']} positions")
        
        return result
    
    def get_current_positions(self) -> List[Dict]:
        """Get all current positions"""
        return self.mt5.get_positions()
    
    def get_daily_stats(self) -> Dict:
        """Get daily trading statistics"""
        self._reset_daily_stats()
        
        return {
            "date": datetime.now().date().isoformat(),
            "starting_balance": self.starting_balance,
            "daily_pnl": self.daily_pnl,
            "daily_trades": self.daily_trades,
            "trade_history": [
                {
                    "action": t.action,
                    "symbol": t.symbol,
                    "volume": t.volume,
                    "price": t.price,
                    "success": t.success,
                    "timestamp": t.timestamp
                }
                for t in self.trade_history[-20:]  # Last 20 trades
            ]
        }
    
    def get_manager_status(self) -> Dict:
        """Get current manager status for dashboard"""
        can_trade, loss_percent = self.check_daily_loss_limit()
        session_ok, session_reason = self.check_session_filter()
        
        return {
            "max_margin_per_trade": self.max_margin,
            "sl_type": self.sl_type,
            "sl_fixed_percent": self.sl_fixed_percent,
            "sl_atr_multiplier": self.sl_atr_multiplier,
            "session_filter_enabled": self.session_filter_enabled,
            "session_allowed": session_ok,
            "session_reason": session_reason,
            "daily_loss_limit": self.max_daily_loss_percent,
            "current_daily_loss": loss_percent,
            "can_trade": can_trade,
            "daily_trades": self.daily_trades
        }


def test_position_manager():
    """Test position manager (requires MT5 connection)"""
    print("Position Manager test requires MT5 connection")
    print("Use integration tests with mock connector for unit testing")


if __name__ == "__main__":
    test_position_manager()
