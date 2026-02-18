import pandas as pd
import glob
import os
import sys

def main():
    print("="*60)
    print("DIVERSIFIED FILTER SCANNER")
    print("="*60)
    
    # Load Data
    list_of_files = glob.glob('volatility_scan_*.csv')
    if not list_of_files:
        print("No scan files found.")
        return
        
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Loading: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file)
        
        # Ensure we have required columns
        required = ['Symbol', 'Volatility%', 'Spread%', 'Avg Volume', 'Path']
        for col in required:
            if col not in df.columns:
                print(f"Error: Missing column '{col}'")
                return
                
        # 1. Global Volume Filter (Liquidity Check)
        # 40th percentile = Top 60% of volume
        vol_threshold = df['Avg Volume'].quantile(0.40)
        print(f"Global Volume Threshold (Top 60%): {vol_threshold:.1f}")
        df_liquid = df[df['Avg Volume'] >= vol_threshold].copy()
        
        # Identify Categories
        def get_category(path):
            if not isinstance(path, str): return "Unknown"
            path = path.lower()
            if "crypto" in path: return "Crypto"
            if "indices" in path or "index" in path: return "Indices"
            if "forex" in path: return "Forex"
            if "metals" in path or "commod" in path or "energy" in path or "gold" in path or "silver" in path or "oil" in path: return "Commodities"
            if "stock" in path or "share" in path: return "Stocks"
            return "Other"
            
        df_liquid['Category'] = df_liquid['Path'].apply(get_category)
        
        selected_candidates = []
        
        print("\n--- Category Selections ---")
        
        # Helper: Deduplicate by Base Asset
        def deduplicate_category(df_in, suffixes_to_strip):
            if df_in.empty: return df_in
            
            df = df_in.copy()
            
            def get_base(sym):
                s = sym.upper()
                # Sort suffixes by length desc to match longest first (e.g. USDT vs USD)
                for suffix in sorted(suffixes_to_strip, key=len, reverse=True):
                    suff_upper = suffix.upper()
                    if s.endswith(suff_upper) and len(s) > len(suff_upper):
                        return s[:-len(suff_upper)]
                return s
            
            df['BaseAsset'] = df['Symbol'].apply(get_base)
            
            # Priority: 1. USD pair, 2. Volume
            df['IsUSD'] = df['Symbol'].str.endswith('USD')
            
            df = df.sort_values(by=['BaseAsset', 'IsUSD', 'Avg Volume'], ascending=[True, False, False])
            
            # Dropping duplicates, keeping first (which is USD or High Vol)
            df_unique = df.drop_duplicates(subset=['BaseAsset']).copy()
            
            # Cleanup
            df_unique.drop(columns=['BaseAsset', 'IsUSD'], inplace=True)
            return df_unique

        # 1. STOCKS (Strict Spread < 0.15%, Top 30 Volatility)
        # Stocks usually don't have currency suffixes in the same way, skipping dedupe
        stocks = df_liquid[
            (df_liquid['Category'] == 'Stocks') & 
            (df_liquid['Spread%'] < 0.15) &
            (df_liquid['Spread%'] > 0)
        ].copy()
        if not stocks.empty:
            stocks = stocks.sort_values(by='Volatility%', ascending=False).head(30)
            selected_candidates.append(stocks)
            print(f"Stocks      : {len(stocks):2d} (Top Volatility, Low Spread)")
        else:
            print("Stocks      :  0")
        
        # 2. CRYPTO (Deduplicate -> Score -> Top 10)
        crypto = df_liquid[df_liquid['Category'] == 'Crypto'].copy()
        if not crypto.empty:
            # Deduplicate first!
            crypto_suffixes = ['USD', 'USDT', 'EUR', 'JPY', 'GBP', 'AUD', 'CAD', 'CHF', 'XAU', 'ETH', 'BTC', 'LTC']
            crypto = deduplicate_category(crypto, crypto_suffixes)
            
            # Ratio: Higher is better
            crypto['Score'] = crypto['Volatility%'] / (crypto['Spread%'] + 0.0001) 
            crypto = crypto.sort_values(by='Score', ascending=False).head(10)
            selected_candidates.append(crypto)
            print(f"Crypto      : {len(crypto):2d} (Top Vol/Spread Ratio, Unique Assets)")
        else:
            print("Crypto      :  0")
            
        # 3. INDICES (Deduplicate -> Top 5 Volatility)
        indices = df_liquid[df_liquid['Category'] == 'Indices'].copy()
        if not indices.empty:
            # Deduplicate variants like HK50 vs HK50ft
            # Suffixes often used in CFDs
            idx_suffixes = ['ft', 'c', 'cash', '.c', 'mini'] 
            indices = deduplicate_category(indices, idx_suffixes)
            
            indices = indices.sort_values(by='Volatility%', ascending=False).head(5)
            selected_candidates.append(indices)
            print(f"Indices     : {len(indices):2d} (Top Volatility, Unique Assets)")
        else:
             print("Indices     :  0")
            
        # 4. FOREX (Top 5 Volatility)
        # Forex pairs are distinct (EURUSD != GBPUSD). No dedupe needed on "USD".
        forex = df_liquid[df_liquid['Category'] == 'Forex'].copy()
        if not forex.empty:
            forex = forex.sort_values(by='Volatility%', ascending=False).head(5)
            selected_candidates.append(forex)
            print(f"Forex       : {len(forex):2d} (Top Volatility)")
        else:
             print("Forex       :  0")
            
        # 5. COMMODITIES (Top 5 Volatility)
        commodities = df_liquid[df_liquid['Category'] == 'Commodities'].copy()
        if not commodities.empty:
            # Maybe deduplicate XAUUSD vs XAUEUR?
            comm_suffixes = ['USD', 'EUR']
            commodities = deduplicate_category(commodities, comm_suffixes)
            
            commodities = commodities.sort_values(by='Volatility%', ascending=False).head(5)
            selected_candidates.append(commodities)
            print(f"Commodities : {len(commodities):2d} (Top Volatility)")
        else:
             print("Commodities :  0")
            
        # Combine
        if not selected_candidates:
            print("No candidates found.")
            return

        final_df = pd.concat(selected_candidates).drop_duplicates(subset=['Symbol'])
        
        print("\n" + "="*50)
        print(f"FINAL SELECTION: {len(final_df)} Candidates")
        print("="*50)
        print(final_df['Category'].value_counts())
        
        # Save
        output_file = 'filtered_candidates.csv'
        final_df.to_csv(output_file, index=False)
        print(f"\nSaved candidates to {output_file}")
        
    except Exception as e:
        print(f"Error filtering results: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
