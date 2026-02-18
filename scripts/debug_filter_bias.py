
import pandas as pd
import glob
import os

# Load latest scan
list_of_files = glob.glob('volatility_scan_*.csv')
if not list_of_files:
    print("No scan files found.")
else:
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Loading: {latest_file}")
    df = pd.read_csv(latest_file)
    
    # Identify Categories based on Path
    # Common paths: 'Forex\...', 'Stocks\...', 'Crypto\...', 'Indices\...', 'Metals\...'
    # If Path is not present or clear, we might need to guess from Symbol
    
    if 'Path' not in df.columns:
        print("Error: 'Path' column not found in scan data.")
    else:
        # Create a simplified category column
        df['Category'] = df['Path'].apply(lambda x: x.split('\\')[0] if isinstance(x, str) else 'Unknown')
        
        print("\n--- Distribution by Category (Total Scanned) ---")
        print(df['Category'].value_counts())
        
        # Define current thresholds
        vol_threshold = df['Volatility%'].quantile(0.55) # Top 45%
        spread_limit = 0.15
        volume_threshold = df['Avg Volume'].quantile(0.55) # Top 45%
        
        print(f"\n--- Current Thresholds ---")
        print(f"Volatility > {vol_threshold:.4f}%")
        print(f"Spread < {spread_limit}%")
        print(f"Volume > {volume_threshold:.1f}")
        
        # Analyze why each non-stock category failed
        categories = ['Crypto', 'Metals', 'Indices', 'Commodities', 'Forex']
        
        for cat in categories:
            # Flexible matching for category in Path
            cat_df = df[df['Path'].str.contains(cat, case=False, na=False)]
            
            if cat_df.empty:
                continue
                
            print(f"\n[{cat.upper()}] - {len(cat_df)} symbols")
            
            # Check pass rates
            pass_vol = cat_df[cat_df['Volatility%'] >= vol_threshold]
            pass_spread = cat_df[cat_df['Spread%'] < spread_limit]
            pass_vol_metric = cat_df[cat_df['Avg Volume'] >= volume_threshold]
            
            print(f"  Pass Volatility: {len(pass_vol)} ({len(pass_vol)/len(cat_df)*100:.1f}%)")
            print(f"  Pass Spread: {len(pass_spread)} ({len(pass_spread)/len(cat_df)*100:.1f}%)")
            print(f"  Pass Volume: {len(pass_vol_metric)} ({len(pass_vol_metric)/len(cat_df)*100:.1f}%)")
            
            # Show avg metrics for category
            print(f"  Avg Stats: Vol={cat_df['Volatility%'].mean():.4f}%, Spread={cat_df['Spread%'].mean():.4f}%, Vol={cat_df['Avg Volume'].mean():.1f}")
            
            # Show best candidates if any
            passed_all = cat_df[
                (cat_df['Volatility%'] >= vol_threshold) &
                (cat_df['Spread%'] < spread_limit) &
                (cat_df['Avg Volume'] >= volume_threshold)
            ]
            if not passed_all.empty:
                print(f"  Successful Candidates: {passed_all['Symbol'].tolist()}")
            else:
                print("  NO CANDIDATES passed all filters.")
