#!/usr/bin/env python3
"""
Calculate margin requirements for default position sizes
"""

import MetaTrader5 as mt5
import json

# Load config
with open('config/trading_config.json', 'r') as f:
    config = json.load(f)

SYMBOLS = config['symbols']['enabled']
FIXED_VOLUME = config['account']['fixed_volume']
DEFAULT_LEVERAGE = config['account']['default_leverage']

print("="*80)
print("MARGIN CALCULATION FOR DEFAULT POSITION SIZES")
print("="*80)
print(f"Default Volume: {FIXED_VOLUME} lots")
print(f"Configured Leverage: {DEFAULT_LEVERAGE}")
print("="*80)

if not mt5.initialize():
    print(f"MT5 initialization failed: {mt5.last_error()}")
    exit(1)

print("\nSymbol          | Price      | Contract Size | Margin (USD) | Actual Leverage")
print("-"*80)

total_margin = 0

for symbol in SYMBOLS:
    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol:<15} | ERROR - Symbol not found")
        continue
    
    # Get current price
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"{symbol:<15} | ERROR - No tick data")
        continue
    
    current_price = tick.ask
    
    # Calculate margin requirement
    # Method 1: Use MT5's built-in calculation
    margin_required = mt5.order_calc_margin(
        mt5.ORDER_TYPE_BUY,
        symbol,
        FIXED_VOLUME,
        current_price
    )
    
    if margin_required is None:
        print(f"{symbol:<15} | ERROR - Cannot calculate margin")
        continue
    
    # Get contract size
    contract_size = symbol_info.trade_contract_size
    
    # Calculate actual leverage being used
    position_value = FIXED_VOLUME * contract_size * current_price
    actual_leverage = position_value / margin_required if margin_required > 0 else 0
    
    total_margin += margin_required
    
    print(f"{symbol:<15} | {current_price:>10.2f} | {contract_size:>13.0f} | ${margin_required:>11.2f} | {actual_leverage:>14.0f}x")

print("-"*80)
print(f"{'TOTAL MARGIN':<15} | {'':>10} | {'':>13} | ${total_margin:>11.2f} |")
print("="*80)

print(f"\nWith max margin per trade: ${config['account']['max_margin_per_trade_usd']}")
print(f"Total margin for all symbols: ${total_margin:.2f}")
print(f"Number of active symbols: {len(SYMBOLS)}")

# Additional info
print("\n" + "="*80)
print("POSITION SIZE CALCULATIONS")
print("="*80)

for symbol in SYMBOLS:
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        continue
    
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        continue
    
    current_price = tick.ask
    contract_size = symbol_info.trade_contract_size
    
    # Position value
    position_value = FIXED_VOLUME * contract_size * current_price
    
    # Margin required
    margin_required = mt5.order_calc_margin(
        mt5.ORDER_TYPE_BUY,
        symbol,
        FIXED_VOLUME,
        current_price
    )
    
    if margin_required is None:
        continue
    
    # Calculate pip value for 0.01 lots
    point_value = symbol_info.trade_tick_value
    pip_size = symbol_info.point * 10  # Usually 1 pip = 10 points
    
    print(f"\n{symbol}:")
    print(f"  Volume:           {FIXED_VOLUME} lots")
    print(f"  Current Price:    ${current_price:.2f}")
    print(f"  Contract Size:    {contract_size:.0f}")
    print(f"  Position Value:   ${position_value:.2f}")
    print(f"  Margin Required:  ${margin_required:.2f}")
    print(f"  Actual Leverage:  {position_value/margin_required:.0f}x")
    print(f"  Point Value:      ${point_value:.2f}")
    print(f"  Min Volume:       {symbol_info.volume_min}")
    print(f"  Max Volume:       {symbol_info.volume_max}")
    print(f"  Volume Step:      {symbol_info.volume_step}")

mt5.shutdown()
print("\nCalculation complete!")
