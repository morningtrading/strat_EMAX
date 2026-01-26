"""
Generate Trading Performance Charts
===================================
Generates charts for each ticker showing price action and trade entries.
Uses MT5 history data filtered by "EMAX" comment.

Usage:
    python3 generate_charts.py [--days DAYS]

Output:
    Saves PNG charts to 'charts/' directory.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ChartGenerator')

try:
    import MetaTrader5 as mt5
    from core.mt5_connector import MT5Connector
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 or core modules not found. Running in simulation/mock mode.")

def load_config(config_path='config/trading_config.json'):
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

def get_symbol_timeframe(symbol, config):
    """Get configured timeframe for symbol, default to M5"""
    setting = config.get('symbols', {}).get('settings', {}).get(symbol, {})
    tf_str = setting.get('timeframe', 'M5')
    
    # Map string to MT5 constant
    tf_map = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30,
        'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1
    }
    return tf_map.get(tf_str, mt5.TIMEFRAME_M5)

def fetch_data(symbol, timeframe, start_time):
    """Fetch price data and trade history"""
    # Fetch Rates (Price)
    rates = mt5.copy_rates_range(symbol, timeframe, start_time, datetime.now())
    if rates is None or len(rates) == 0:
        logger.warning(f"[{symbol}] No price data found")
        return None, None
    
    df_rates = pd.DataFrame(rates)
    df_rates['time'] = pd.to_datetime(df_rates['time'], unit='s')
    
    # Fetch Deals (Trades)
    deals = mt5.history_deals_get(start_time, datetime.now(), group=symbol)
    df_deals = pd.DataFrame()
    
    if deals and len(deals) > 0:
        raw_deals = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        mask = (raw_deals['entry'] == 0) & (raw_deals['comment'].str.contains('EMAX', na=False))
        df_deals = raw_deals[mask].copy()
        if not df_deals.empty:
            df_deals['time'] = pd.to_datetime(df_deals['time'], unit='s')
    return df_rates, df_deals

def get_mock_data(symbol, start_time):
    """Generate mock data for testing"""
    periods = 100
    times = [start_time + timedelta(hours=i) for i in range(periods)]
    prices = np.cumsum(np.random.randn(periods)) + 100
    df_rates = pd.DataFrame({'time': times, 'close': prices})
    
    deal_times = [times[10], times[30], times[50]]
    deal_prices = [prices[10], prices[30], prices[50]]
    df_deals = pd.DataFrame({
        'time': deal_times,
        'price': deal_prices,
        'type': [0, 1, 0], # 0=Buy, 1=Sell
    })
    return df_rates, df_deals

def plot_chart(symbol, df_rates, df_deals, output_dir='charts'):
    """Generate and save chart"""
    plt.figure(figsize=(14, 7))
    sns.set_style("darkgrid")
    
    plt.plot(df_rates['time'], df_rates['close'], label='Close Price', color='black', alpha=0.6, linewidth=1)
    
    if not df_deals.empty:
        buys = df_deals[df_deals['type'] == 0]
        if not buys.empty:
            plt.scatter(buys['time'], buys['price'], color='green', marker='^', s=100, label='Buy Entry', zorder=5)
            
        sells = df_deals[df_deals['type'] == 1]
        if not sells.empty:
            plt.scatter(sells['time'], sells['price'], color='red', marker='v', s=100, label='Sell Entry', zorder=5)

    plt.title(f"{symbol} - EMAX Bot Performance", fontsize=16)
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.legend()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.gcf().autofmt_xdate()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{output_dir}/{symbol}_performance.png"
    plt.savefig(filename)
    plt.close()
    logger.info(f"[{symbol}] Chart saved to {filename}")

def main():
    global MT5_AVAILABLE
    parser = argparse.ArgumentParser(description='Generate EMAX Bot Performance Charts')
    parser.add_argument('--days', type=int, default=30, help='Days of history to look back')
    args = parser.parse_args()
    
    config = load_config()
    enabled_symbols = config.get('symbols', {}).get('enabled', [])
    
    if not enabled_symbols:
        enabled_symbols = ['XAUUSD', 'SP500ft']
        logger.info(f"Using fallback symbols: {enabled_symbols}")

    if MT5_AVAILABLE:
        connector = MT5Connector()
        if not connector.connect():
            logger.error("Failed to connect to MT5. Switching to mock mode.")
            MT5_AVAILABLE = False
    
    start_time = datetime.now() - timedelta(days=args.days)
    
    for symbol in enabled_symbols:
        logger.info(f"Processing {symbol}...")
        if MT5_AVAILABLE:
            tf = get_symbol_timeframe(symbol, config)
            df_rates, df_deals = fetch_data(symbol, tf, start_time)
        else:
            df_rates, df_deals = get_mock_data(symbol, start_time)
        
        if df_rates is not None:
            plot_chart(symbol, df_rates, df_deals)
            
    if MT5_AVAILABLE:
        mt5.shutdown()
    logger.info("Done.")

if __name__ == "__main__":
    main()