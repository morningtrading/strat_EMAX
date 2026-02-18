
import sys
import os
import time
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import tabulate

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mt5_connector import MT5Connector

def calculate_atr_percent(high, low, close, period=14):
    """
    Calculate ATR as a percentage of price.
    (ATR / Close) * 100
    Simple TR approximation for speed: High - Low
    """
    # Simple average of High-Low range for speed on large datasets
    # Logic: 
    # TR = max(High-Low, abs(High-PrevClose), abs(Low-PrevClose))
    # We'll use High-Low average over N periods for a quick scan
    # This is close enough for ranking volatility
    
    # Calculate True Range (simplified to High - Low for speed on 1000s of symbols)
    # For more accuracy we would need previous close, but for a scanner this is effective
    tr = high - low
    atr = tr.rolling(window=period).mean()
    atr_percent = (atr / close) * 100
    return atr_percent.iloc[-1]

def main():
    print("Initializing MT5 Connection...")
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    print("Fetching all symbols...")
    symbols = mt5.symbols_get()
    if not symbols:
        print("No symbols found")
        connector.disconnect()
        return

    print(f"Found {len(symbols)} symbols. Scanning for volatility (M5 Timeframe)...")
    print("This may take a minute...")

    results = []
    count = 0
    
    # Filter for visibly enabled or common symbols to speed up
    # or just scan everything?
    # Scanning everything might be slow (thousands of symbols).
    # Let's prioritize major categories or just scan all but skip checks if data fails.

    for sym in symbols:
        try:
            symbol_name = sym.name
            
            # Skip custom or weird symbols if needed
            # if not sym.visible: continue # Optional: only scan visible? No, user wants best.
            
            # Get simplified symbol info
            # We need volume stats
            
            # Fetch Price Data (M5)
            # Get last 20 bars to calc ATR(14)
            rates = mt5.copy_rates_from_pos(symbol_name, mt5.TIMEFRAME_M5, 0, 20)
            
            if rates is None or len(rates) < 15:
                continue

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calculate Volatility
            vol_percent = calculate_atr_percent(df['high'], df['low'], df['close'], period=14)
            
            if pd.isna(vol_percent):
                continue

            # Ensure symbol is selected in Market Watch to get fresh tick data
            if not mt5.symbol_select(symbol_name, True):
                continue
            
            # Small sleep to ensure data propagation
            time.sleep(0.01)
                
            tick = mt5.symbol_info_tick(symbol_name)
            spread_percent = 0.0
            
            if tick is not None and tick.bid > 0:
                spread_val = tick.ask - tick.bid
                spread_percent = (spread_val / tick.bid) * 100
            
            # Calculate Average Volume
            avg_volume = df['tick_volume'].mean() if 'tick_volume' in df.columns else 0
            
            results.append({
                "Symbol": symbol_name,
                "Volatility%": round(vol_percent, 4),
                "Price": rates[-1]['close'],
                "Spread": sym.spread,
                "Spread%": round(spread_percent, 4),
                "Avg Volume": round(avg_volume, 0),
                "Min Vol": sym.volume_min,
                "Vol Step": sym.volume_step,
                "Contract": sym.trade_contract_size,
                "Path": sym.path 
            })
            
            count += 1
            if count % 100 == 0:
                print(f"Scanned {count}...", end='\r')

        except Exception as e:
            continue

    print(f"\nScanning complete. Found {len(results)} valid symbols.")
    
    print(f"\nScanning complete. Found {len(results)} valid symbols.")
    
    # Sort by Volatility (High to Low)
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(by="Volatility%", ascending=False)
    
    # Save ALL results to CSV
    filename = f"volatility_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_results.to_csv(filename, index=False)
    print(f"\nResults saved to {filename}")
    
    # Display Top 100 for reference
    top_100 = df_results.head(100)
    print("\n" + "="*80)
    print("TOP 100 MOST VOLATILE SYMBOLS (M5 Timeframe)")
    print("="*80)
    
    # Select columns for display
    display_cols = ["Symbol", "Volatility%", "Price", "Spread", "Spread%", "Avg Volume", "Min Vol", "Vol Step"]
    print(tabulate.tabulate(top_100[display_cols], headers='keys', tablefmt='psql', showindex=False))

    connector.disconnect()

if __name__ == "__main__":
    main()
