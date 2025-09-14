#!/usr/bin/env python3
"""
Data Gap Filter
Preprocess historical data to remove weekend gaps and non-trading periods
"""

import pandas as pd
import numpy as np
from data_loader import DataLoader
from datetime import datetime, timedelta
import os

class DataGapFilter:
    """Filter out data gaps and non-trading periods"""
    
    def __init__(self, max_gap_minutes=60):
        """
        Initialize the gap filter
        
        Args:
            max_gap_minutes: Maximum allowed gap in minutes (default: 1 hour)
        """
        self.max_gap_minutes = max_gap_minutes
        self.removed_gaps = []
        self.removed_records = 0
    
    def detect_gaps(self, df):
        """Detect gaps in the data"""
        print("🔍 Detecting data gaps...")
        
        time_diffs = df.index.to_series().diff()
        gaps = time_diffs > pd.Timedelta(minutes=self.max_gap_minutes)
        
        gap_info = []
        for idx in df.index[gaps]:
            gap_duration = time_diffs.loc[idx]
            gap_minutes = gap_duration.total_seconds() / 60
            gap_info.append({
                'timestamp': idx,
                'duration_minutes': gap_minutes,
                'duration_hours': gap_minutes / 60,
                'gap_type': self._classify_gap(gap_minutes)
            })
        
        print(f"   Found {len(gap_info)} gaps > {self.max_gap_minutes} minutes")
        return gap_info
    
    def _classify_gap(self, gap_minutes):
        """Classify the type of gap"""
        if gap_minutes < 60:
            return "small"
        elif gap_minutes < 480:  # 8 hours
            return "medium"
        elif gap_minutes < 2880:  # 48 hours
            return "weekend"
        else:
            return "extreme"
    
    def filter_weekend_gaps(self, df):
        """Remove weekend gaps by creating separate trading sessions"""
        print("🗓️  Filtering weekend gaps...")
        
        # Detect gaps
        gap_info = self.detect_gaps(df)
        
        # Group data into trading sessions (continuous periods without large gaps)
        trading_sessions = []
        current_session = []
        
        for i, (timestamp, row) in enumerate(df.iterrows()):
            if i == 0:
                current_session.append((timestamp, row))
                continue
            
            # Check if there's a gap
            time_diff = (timestamp - df.index[i-1]).total_seconds() / 60
            
            if time_diff <= self.max_gap_minutes:
                # Continue current session
                current_session.append((timestamp, row))
            else:
                # Gap detected - end current session and start new one
                if len(current_session) > 1:  # Only keep sessions with multiple records
                    trading_sessions.append(current_session)
                current_session = [(timestamp, row)]
        
        # Add the last session
        if len(current_session) > 1:
            trading_sessions.append(current_session)
        
        print(f"   Split data into {len(trading_sessions)} trading sessions")
        
        # Create filtered dataframe with only the largest sessions
        filtered_sessions = []
        for session in trading_sessions:
            if len(session) >= 100:  # Only keep sessions with at least 100 records
                filtered_sessions.append(session)
        
        print(f"   Kept {len(filtered_sessions)} sessions with >= 100 records")
        
        # Combine all sessions into one dataframe
        all_data = []
        for session in filtered_sessions:
            for timestamp, row in session:
                all_data.append((timestamp, row))
        
        if not all_data:
            print("❌ No valid trading sessions found!")
            return df
        
        # Create new dataframe
        filtered_df = pd.DataFrame([row for _, row in all_data], 
                                 index=[timestamp for timestamp, _ in all_data])
        
        # Sort by timestamp
        filtered_df = filtered_df.sort_index()
        
        print(f"   Original records: {len(df):,}")
        print(f"   Filtered records: {len(filtered_df):,}")
        print(f"   Removed records: {len(df) - len(filtered_df):,}")
        
        self.removed_records = len(df) - len(filtered_df)
        
        return filtered_df
    
    def filter_extreme_gaps(self, df, max_gap_hours=8):
        """Remove extreme gaps while preserving smaller gaps"""
        print(f"⚡ Filtering gaps > {max_gap_hours} hours...")
        
        time_diffs = df.index.to_series().diff()
        extreme_gaps = time_diffs > pd.Timedelta(hours=max_gap_hours)
        
        # Find indices where extreme gaps occur
        gap_indices = df.index[extreme_gaps]
        
        if len(gap_indices) == 0:
            print("   No extreme gaps found")
            return df
        
        print(f"   Found {len(gap_indices)} extreme gaps")
        
        # Remove data points that create extreme gaps
        mask = pd.Series(True, index=df.index)
        
        for gap_idx in gap_indices:
            # Find the data point that creates the extreme gap
            gap_position = df.index.get_loc(gap_idx)
            if gap_position > 0:
                # Remove the data point that creates the gap
                mask.iloc[gap_position] = False
                print(f"   Removing gap at {gap_idx}")
        
        filtered_df = df[mask]
        
        print(f"   Original records: {len(df):,}")
        print(f"   Filtered records: {len(filtered_df):,}")
        print(f"   Removed records: {len(df) - len(filtered_df):,}")
        
        return filtered_df
    
    def create_continuous_data(self, df):
        """Create continuous data by removing all gaps"""
        print("🔄 Creating continuous data (removing all gaps)...")
        
        # Remove all gaps by keeping only consecutive records
        time_diffs = df.index.to_series().diff()
        consecutive_mask = time_diffs <= pd.Timedelta(minutes=2)  # Allow up to 2-minute gaps
        
        # Start from the first record and keep consecutive ones
        continuous_data = []
        last_timestamp = None
        
        for timestamp, row in df.iterrows():
            if last_timestamp is None:
                continuous_data.append((timestamp, row))
                last_timestamp = timestamp
            else:
                time_diff = (timestamp - last_timestamp).total_seconds() / 60
                if time_diff <= 2:  # 2 minutes max gap
                    continuous_data.append((timestamp, row))
                    last_timestamp = timestamp
                else:
                    break  # Stop at first gap
        
        if not continuous_data:
            print("❌ No continuous data found!")
            return df
        
        # Create new dataframe
        continuous_df = pd.DataFrame([row for _, row in continuous_data],
                                   index=[timestamp for timestamp, _ in continuous_data])
        
        print(f"   Original records: {len(df):,}")
        print(f"   Continuous records: {len(continuous_df):,}")
        print(f"   Removed records: {len(df) - len(continuous_df):,}")
        
        return continuous_df
    
    def save_filtered_data(self, df, original_file, suffix="_filtered"):
        """Save filtered data to a new file"""
        # Create output filename
        base_name = os.path.basename(original_file)
        name, ext = os.path.splitext(base_name)
        output_file = f"{name}{suffix}{ext}"
        
        # Save to CSV
        df.to_csv(output_file)
        
        print(f"💾 Saved filtered data to: {output_file}")
        print(f"   Records: {len(df):,}")
        print(f"   Date range: {df.index.min()} to {df.index.max()}")
        
        return output_file

def main():
    """Main function to filter data gaps"""
    print("🔧 DATA GAP FILTER")
    print("=" * 50)
    
    # Load original data
    loader = DataLoader('Z:\\')
    df = loader.load_csv_data('Z:\\15_XAUUSD_1min_1month.csv')
    
    if df is None:
        print("❌ Failed to load data")
        return
    
    print(f"📊 Original data: {len(df):,} records")
    print(f"📅 Date range: {df.index.min()} to {df.index.max()}")
    
    # Initialize gap filter
    gap_filter = DataGapFilter(max_gap_minutes=60)
    
    # Option 1: Filter weekend gaps (keep trading sessions)
    print(f"\n🎯 OPTION 1: Filter Weekend Gaps")
    weekend_filtered = gap_filter.filter_weekend_gaps(df)
    
    if len(weekend_filtered) > 0:
        output_file1 = gap_filter.save_filtered_data(
            weekend_filtered, 
            'Z:\\15_XAUUSD_1min_1month.csv', 
            '_weekend_filtered'
        )
    
    # Option 2: Filter extreme gaps only
    print(f"\n🎯 OPTION 2: Filter Extreme Gaps Only")
    extreme_filtered = gap_filter.filter_extreme_gaps(df, max_gap_hours=8)
    
    if len(extreme_filtered) > 0:
        output_file2 = gap_filter.save_filtered_data(
            extreme_filtered,
            'Z:\\15_XAUUSD_1min_1month.csv',
            '_extreme_filtered'
        )
    
    # Option 3: Create continuous data (remove all gaps)
    print(f"\n🎯 OPTION 3: Create Continuous Data")
    continuous_data = gap_filter.create_continuous_data(df)
    
    if len(continuous_data) > 0:
        output_file3 = gap_filter.save_filtered_data(
            continuous_data,
            'Z:\\15_XAUUSD_1min_1month.csv',
            '_continuous'
        )
    
    print(f"\n✅ DATA FILTERING COMPLETE")
    print(f"Created {3 if len(continuous_data) > 0 else 2} filtered datasets:")
    if len(weekend_filtered) > 0:
        print(f"   1. Weekend filtered: {len(weekend_filtered):,} records")
    if len(extreme_filtered) > 0:
        print(f"   2. Extreme gaps filtered: {len(extreme_filtered):,} records")
    if len(continuous_data) > 0:
        print(f"   3. Continuous data: {len(continuous_data):,} records")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   Use 'weekend_filtered' dataset for backtesting")
    print(f"   This removes weekend gaps while preserving trading sessions")
    print(f"   Duration calculations will be much more realistic!")

if __name__ == "__main__":
    main()
