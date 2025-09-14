#!/usr/bin/env python3
"""
Comprehensive Data Quality Check
Analyze the Gold data for gaps, bugs, and issues that could affect backtesting
"""

import pandas as pd
import numpy as np
from data_loader import DataLoader
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def comprehensive_data_analysis():
    """Run comprehensive data quality analysis"""
    print("🔍 COMPREHENSIVE DATA QUALITY ANALYSIS")
    print("=" * 60)
    
    # Load the data
    loader = DataLoader('Z:\\')
    df = loader.load_csv_data('Z:\\15_XAUUSD_1min_1month.csv')
    
    if df is None:
        print("❌ Failed to load data")
        return None
    
    print(f"✅ Data loaded successfully")
    print(f"📊 Total records: {len(df):,}")
    print(f"📅 Date range: {df.index.min()} to {df.index.max()}")
    print(f"⏱️  Duration: {(df.index.max() - df.index.min()).days} days")
    
    # Basic statistics
    print(f"\n📈 PRICE STATISTICS:")
    print(f"   Open:  {df['open'].min():.2f} - {df['open'].max():.2f}")
    print(f"   High:  {df['high'].min():.2f} - {df['high'].max():.2f}")
    print(f"   Low:   {df['low'].min():.2f} - {df['low'].max():.2f}")
    print(f"   Close: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    # Check for gaps
    print(f"\n🔍 GAP ANALYSIS:")
    expected_freq = pd.infer_freq(df.index)
    print(f"   Detected frequency: {expected_freq}")
    
    if expected_freq:
        # Create expected time range
        full_range = pd.date_range(df.index.min(), df.index.max(), freq=expected_freq)
        missing_dates = full_range.difference(df.index)
        
        print(f"   Expected records: {len(full_range):,}")
        print(f"   Missing records: {len(missing_dates):,}")
        print(f"   Data completeness: {len(df)/len(full_range)*100:.2f}%")
        
        if len(missing_dates) > 0:
            print(f"\n   📋 First 10 missing timestamps:")
            for i, missing in enumerate(missing_dates[:10]):
                print(f"      {missing}")
            
            if len(missing_dates) > 10:
                print(f"      ... and {len(missing_dates)-10} more")
    else:
        print("   ⚠️  Could not detect frequency - checking time differences manually")
    
    # Check for duplicate timestamps
    print(f"\n🔄 DUPLICATE CHECK:")
    duplicates = df.index.duplicated()
    duplicate_count = duplicates.sum()
    print(f"   Duplicate timestamps: {duplicate_count}")
    
    if duplicate_count > 0:
        print(f"   📋 Duplicate timestamps:")
        duplicate_times = df.index[duplicates].unique()
        for i, dup_time in enumerate(duplicate_times[:5]):
            count = (df.index == dup_time).sum()
            print(f"      {dup_time}: {count} occurrences")
    
    # Check for time jumps - THIS IS CRITICAL FOR DURATION CALCULATIONS
    print(f"\n⏰ TIME JUMP ANALYSIS (CRITICAL FOR DURATION BUGS):")
    time_diffs = df.index.to_series().diff()
    expected_diff = pd.Timedelta(minutes=1)
    
    # Find large time jumps
    large_jumps = time_diffs > expected_diff * 2
    large_jump_count = large_jumps.sum()
    print(f"   Large time jumps (>2 minutes): {large_jump_count}")
    
    if large_jump_count > 0:
        print(f"   📋 First 10 large time jumps:")
        jump_indices = df.index[large_jumps]
        jump_diffs = time_diffs[large_jumps]
        for i in range(min(10, len(jump_indices))):
            print(f"      {jump_indices[i]}: {jump_diffs.iloc[i]}")
    
    # Check for extremely large gaps that could cause 3000+ minute durations
    print(f"\n🚨 EXTREME GAP ANALYSIS:")
    extreme_gaps = time_diffs > pd.Timedelta(hours=12)
    extreme_gap_count = extreme_gaps.sum()
    print(f"   Extreme gaps (>12 hours): {extreme_gap_count}")
    
    if extreme_gap_count > 0:
        print(f"   📋 All extreme gaps:")
        extreme_gap_indices = df.index[extreme_gaps]
        extreme_gap_diffs = time_diffs[extreme_gaps]
        for i, (idx, diff) in enumerate(zip(extreme_gap_indices, extreme_gap_diffs)):
            duration_minutes = diff.total_seconds() / 60
            print(f"      {idx}: {diff} ({duration_minutes:.0f} minutes)")
    
    # Check OHLC data quality
    print(f"\n📊 OHLC DATA QUALITY:")
    invalid_ohlc = df[(df['high'] < df['low']) | 
                     (df['high'] < df['open']) | 
                     (df['high'] < df['close']) |
                     (df['low'] > df['open']) | 
                     (df['low'] > df['close'])]
    print(f"   Invalid OHLC relationships: {len(invalid_ohlc)}")
    
    if len(invalid_ohlc) > 0:
        print(f"   📋 First 5 invalid OHLC records:")
        for i, (idx, row) in enumerate(invalid_ohlc.head().iterrows()):
            print(f"      {idx}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
    
    # Check for zero/negative prices
    zero_prices = (df[['open', 'high', 'low', 'close']] <= 0).any(axis=1)
    print(f"   Zero/negative prices: {zero_prices.sum()}")
    
    # Check for extreme price movements
    print(f"\n📈 PRICE MOVEMENT ANALYSIS:")
    price_changes = df['close'].pct_change().abs()
    extreme_moves = price_changes > 0.05  # 5% moves
    print(f"   Extreme price movements (>5%): {extreme_moves.sum()}")
    
    if extreme_moves.sum() > 0:
        print(f"   📋 Largest price movements:")
        largest_moves = price_changes.nlargest(5)
        for i, (idx, change) in enumerate(largest_moves.items()):
            print(f"      {idx}: {change*100:.2f}%")
    
    # Check for weekend gaps (should be normal for forex)
    print(f"\n📅 WEEKEND GAP ANALYSIS:")
    weekend_gaps = time_diffs > pd.Timedelta(hours=24)
    print(f"   Gaps > 24 hours: {weekend_gaps.sum()}")
    
    if weekend_gaps.sum() > 0:
        print(f"   📋 Long gaps (>24 hours):")
        long_gap_indices = df.index[weekend_gaps]
        long_gap_diffs = time_diffs[weekend_gaps]
        for i in range(min(5, len(long_gap_indices))):
            duration_hours = long_gap_diffs.iloc[i].total_seconds() / 3600
            print(f"      {long_gap_indices[i]}: {duration_hours:.1f} hours")
    
    # Check for data quality issues that could affect backtesting
    print(f"\n⚠️  BACKTESTING IMPACT ANALYSIS:")
    
    issues_found = []
    if 'missing_dates' in locals() and len(missing_dates) > len(df) * 0.01:  # More than 1% missing
        issues_found.append(f"High missing data: {len(missing_dates)} gaps")
    
    if duplicate_count > 0:
        issues_found.append(f"Duplicate timestamps: {duplicate_count}")
    
    if len(invalid_ohlc) > 0:
        issues_found.append(f"Invalid OHLC data: {len(invalid_ohlc)} records")
    
    if zero_prices.sum() > 0:
        issues_found.append(f"Zero/negative prices: {zero_prices.sum()} records")
    
    if large_jump_count > 100:  # More than 100 large jumps
        issues_found.append(f"Many time jumps: {large_jump_count}")
    
    if extreme_gap_count > 0:
        issues_found.append(f"Extreme gaps (>12h): {extreme_gap_count}")
    
    if issues_found:
        print("   🚨 Issues that could affect backtesting:")
        for issue in issues_found:
            print(f"      - {issue}")
    else:
        print("   ✅ No major data quality issues found")
    
    # Sample data around potential problem areas
    print(f"\n📋 SAMPLE DATA AROUND POTENTIAL ISSUES:")
    
    if extreme_gap_count > 0:
        print(f"   Data around extreme gaps:")
        extreme_gap_indices = df.index[extreme_gaps]
        for i, gap_time in enumerate(extreme_gap_indices[:3]):
            # Show data before and after the gap
            try:
                before_gap = df.loc[:gap_time].tail(3)
                after_gap = df.loc[gap_time:].head(3)
                
                print(f"      Gap at {gap_time}:")
                print(f"        Before gap:")
                for idx, row in before_gap.iterrows():
                    print(f"          {idx}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
                print(f"        After gap:")
                for idx, row in after_gap.iterrows():
                    print(f"          {idx}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
            except Exception as e:
                print(f"      Error showing gap data: {e}")
    
    # Show sample of normal data
    print(f"\n   Normal data sample:")
    sample_data = df.head(5)
    for idx, row in sample_data.iterrows():
        print(f"      {idx}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
    
    return df

def create_gap_visualization(df):
    """Create visualization showing time gaps"""
    print(f"\n📊 Creating gap visualization...")
    
    # Calculate time differences
    time_diffs = df.index.to_series().diff()
    time_diffs_minutes = time_diffs.dt.total_seconds() / 60
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    # Time gaps over time
    ax1.plot(df.index[1:], time_diffs_minutes[1:], linewidth=0.5, alpha=0.7)
    ax1.axhline(y=1, color='g', linestyle='--', alpha=0.5, label='Expected 1 minute')
    ax1.axhline(y=60, color='orange', linestyle='--', alpha=0.5, label='1 hour')
    ax1.axhline(y=1440, color='r', linestyle='--', alpha=0.5, label='1 day')
    ax1.set_title('Time Gaps Between Records (minutes)')
    ax1.set_ylabel('Gap (minutes)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')  # Log scale to better see large gaps
    
    # Price chart
    ax2.plot(df.index, df['close'], linewidth=0.5)
    ax2.set_title('Gold Price Over Time')
    ax2.set_ylabel('Price')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('data_gap_analysis.png', dpi=300, bbox_inches='tight')
    print("   ✅ Gap visualization saved as 'data_gap_analysis.png'")

if __name__ == "__main__":
    df = comprehensive_data_analysis()
    if df is not None:
        create_gap_visualization(df)
        print(f"\n🎯 CONCLUSION:")
        print(f"The data quality analysis is complete.")
        print(f"Check the visualization file 'data_gap_analysis.png' for graphical analysis.")
        print(f"Any extreme gaps found above will explain the 3000+ minute duration issues in backtesting.")
