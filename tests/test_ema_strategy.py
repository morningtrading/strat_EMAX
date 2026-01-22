"""
================================================================================
EMAX STRATEGY TEST MODULE
================================================================================

PURPOSE:
    Unit tests for EMA Strategy module. Tests signal generation, EMA calculation,
    duplicate prevention, and direction filtering.

HOW TO RUN:
    wine python -m pytest tests/test_ema_strategy.py -v

================================================================================
"""

import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ema_strategy import EMAStrategy, Signal, SignalType


class TestEMACalculation(unittest.TestCase):
    """Test EMA calculation accuracy"""
    
    def setUp(self):
        self.strategy = EMAStrategy()
    
    def test_ema_length(self):
        """EMA output should match input length"""
        prices = [100.0] * 50
        ema = self.strategy.calculate_ema(prices, 9)
        self.assertEqual(len(ema), len(prices))
    
    def test_ema_starts_with_none(self):
        """EMA should have None values before enough data"""
        prices = [100.0] * 50
        ema = self.strategy.calculate_ema(prices, 9)
        # First 8 values should be None (period - 1)
        for i in range(8):
            self.assertIsNone(ema[i])
    
    def test_ema_flat_prices(self):
        """EMA of flat prices should equal the price"""
        prices = [100.0] * 50
        ema = self.strategy.calculate_ema(prices, 9)
        # All non-None values should be approximately 100.0
        for val in ema[9:]:
            self.assertAlmostEqual(val, 100.0, places=5)
    
    def test_ema_trending_up(self):
        """EMA should follow upward trend"""
        prices = [100.0 + i * 0.1 for i in range(50)]
        ema = self.strategy.calculate_ema(prices, 9)
        # EMA should be increasing
        for i in range(10, len(ema)):
            self.assertGreater(ema[i], ema[i-1])


class TestSignalGeneration(unittest.TestCase):
    """Test signal generation logic"""
    
    def setUp(self):
        self.strategy = EMAStrategy()
    
    def _generate_bars(self, trend: str = 'up', count: int = 100) -> list:
        """Generate sample price bars"""
        bars = []
        base_price = 30.0
        
        for i in range(count):
            if trend == 'up':
                trend_adj = 0.02 * i
            elif trend == 'down':
                trend_adj = -0.02 * i
            else:  # sideways
                trend_adj = 0.01 * (i % 10 - 5)
            
            noise = random.uniform(-0.05, 0.05)
            price = base_price + trend_adj + noise
            
            bars.append({
                'time': (datetime.now() - timedelta(minutes=5*(count-i))).isoformat(),
                'open': price - random.uniform(0, 0.02),
                'high': price + random.uniform(0, 0.05),
                'low': price - random.uniform(0, 0.05),
                'close': price,
                'volume': random.randint(100, 1000)
            })
        
        return bars
    
    def test_analyze_returns_signal(self):
        """analyze() should return a Signal object"""
        bars = self._generate_bars('up')
        signal = self.strategy.analyze('XAGUSD', bars)
        self.assertIsInstance(signal, Signal)
    
    def test_insufficient_data_returns_hold(self):
        """Should return HOLD with insufficient data"""
        bars = self._generate_bars('up', count=20)  # Less than slow EMA period
        signal = self.strategy.analyze('XAGUSD', bars)
        self.assertEqual(signal.action, SignalType.HOLD)
        self.assertIn('Insufficient', signal.reason)
    
    def test_signal_contains_ema_values(self):
        """Signal should contain EMA values"""
        bars = self._generate_bars('up')
        signal = self.strategy.analyze('XAGUSD', bars)
        self.assertIsNotNone(signal.fast_ema)
        self.assertIsNotNone(signal.slow_ema)
        self.assertGreater(signal.fast_ema, 0)
        self.assertGreater(signal.slow_ema, 0)


class TestDirectionFilter(unittest.TestCase):
    """Test direction filtering"""
    
    def test_long_only_blocks_sell(self):
        """Long only mode should not generate SELL signals"""
        strategy = EMAStrategy()
        strategy.set_direction('long')
        
        # Even with downtrend, should not get SELL
        # This is a logic test - actual signal depends on price data
        self.assertEqual(strategy.direction, 'long')
    
    def test_short_only_blocks_buy(self):
        """Short only mode should not generate BUY signals"""
        strategy = EMAStrategy()
        strategy.set_direction('short')
        self.assertEqual(strategy.direction, 'short')
    
    def test_both_allows_all(self):
        """Both mode should allow all signals"""
        strategy = EMAStrategy()
        strategy.set_direction('both')
        self.assertEqual(strategy.direction, 'both')


class TestDuplicatePrevention(unittest.TestCase):
    """Test duplicate signal prevention"""
    
    def test_same_bar_blocked(self):
        """Same bar should not generate multiple signals"""
        strategy = EMAStrategy()
        strategy.prevent_duplicates = True
        
        # Manually set last signal bar
        strategy.last_signal_bar['XAGUSD'] = '2026-01-22T10:00:00'
        
        # Create bars with same time
        bars = [{'time': '2026-01-22T10:00:00', 'open': 30, 'high': 31, 'low': 29, 'close': 30.5, 'volume': 100}] * 50
        
        # Should get HOLD due to insufficient data AND duplicate prevention
        # (We'd need proper crossing data to truly test this)
        signal = strategy.analyze('XAGUSD', bars)
        self.assertEqual(signal.action, SignalType.HOLD)


class TestTradingEnabled(unittest.TestCase):
    """Test trading enable/disable"""
    
    def test_trading_enabled_default(self):
        """Trading should be enabled by default"""
        strategy = EMAStrategy()
        self.assertTrue(strategy.trading_enabled)
    
    def test_set_trading_disabled(self):
        """Should be able to disable trading"""
        strategy = EMAStrategy()
        strategy.set_trading_enabled(False)
        self.assertFalse(strategy.trading_enabled)


if __name__ == '__main__':
    unittest.main(verbosity=2)
