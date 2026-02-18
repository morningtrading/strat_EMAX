import json

# Helper to create cells
def new_markdown_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True)
    }

def new_code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True)
    }

cells = []

# Cell 1: Title and Description
text1 = """# Volatility Scan Analysis

This notebook analyzes the results from the volatility scanner to identify optimal trading candidates with high volatility and low spread.
We filter for symbols with:
1. Spread% < 0.15% (and > 0%)
2. Avg Volume in the top 60% (>= 40th percentile)
"""
cells.append(new_markdown_cell(text1))

# Cell 2: Imports and Style
code1 = """import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = [12, 6]"""
cells.append(new_code_cell(code1))

# Cell 3: Load Data
text2 = """## Load Data

Find the latest volatility scan CSV file."""
cells.append(new_markdown_cell(text2))

code2 = """# Find latest scan file
list_of_files = glob.glob('volatility_scan_*.csv') 
if not list_of_files:
    print("No scan files found.")
else:
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Loading: {latest_file}")
    
    df = pd.read_csv(latest_file)
    # Ensure Avg Volume exists, if not compatible with old scans fill with 0
    if 'Avg Volume' not in df.columns:
        df['Avg Volume'] = 0
        
    print(f"Total symbols: {len(df)}")
    display(df.head())"""
cells.append(new_code_cell(code2))

# Cell 4: Data Overview
text3 = """## Data Overview"""
cells.append(new_markdown_cell(text3))

code3 = """df.describe()"""
cells.append(new_code_cell(code3))

# Cell 5: EDA - Volatility & Spread
text4 = """## Exploratory Data Analysis

Let's look at the distribution of Volatility and Spread."""
cells.append(new_markdown_cell(text4))

code4 = """fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Volatility Distribution
sns.histplot(data=df, x='Volatility%', bins=50, kde=True, ax=axes[0])
axes[0].set_title('Distribution of Volatility%')

# Spread Distribution (filtering outliers for better view)
spread_view = df[df['Spread%'] < 2.0]  # Filter extreme spreads for visualization
sns.histplot(data=spread_view, x='Spread%', bins=50, kde=True, ax=axes[1], color='orange')
axes[1].set_title('Distribution of Spread% (View < 2.0%)')

plt.tight_layout()
plt.show()"""
cells.append(new_code_cell(code4))

# Cell 6: EDA - Volume
text5 = """## Volume Analysis

Analyze the volume distribution to filter out illiquid symbols.
We will filter for the top 45% of symbols by volume (>= 55th percentile)."""
cells.append(new_markdown_cell(text5))

code5 = """# Calculate Thresholds
vol_cutoff = df['Volatility%'].quantile(0.55)
spread_cutoff = df['Spread%'].quantile(0.45)
volume_cutoff = df['Avg Volume'].quantile(0.55)

print(f"Volatility Cutoff (Top 45%): >= {vol_cutoff:.4f}%")
print(f"Spread Cutoff (Bottom 45%): <= {spread_cutoff:.4f}%")
print(f"Volume Cutoff (Top 45%): >= {volume_cutoff:.0f}")

plt.figure(figsize=(10, 5))
# Filter extreme volume outliers for better visualization if needed
sns.histplot(data=df, x='Avg Volume', bins=50, log_scale=True, kde=False)
plt.axvline(x=volume_cutoff, color='r', linestyle='--', label=f'55th Percentile ({volume_cutoff:.0f})')
plt.title('Distribution of Avg Volume (Log Scale)')
plt.legend()
plt.show()"""
cells.append(new_code_cell(code5))


# Cell 7: Volatility vs Spread
text6 = """### Volatility vs Spread Scatter Plot

Ideally, we want symbols in the **top-left corner** (High Volatility, Low Spread).
We color code by Volume to see liquidity."""
cells.append(new_markdown_cell(text6))

code6 = """plt.figure(figsize=(12, 8))
# Filter for better visualization focus
plot_df = df[(df['Spread%'] < 1.0) & (df['Volatility%'] < 5.0)]

sns.scatterplot(
    data=plot_df, 
    x='Spread%', 
    y='Volatility%', 
    hue='Avg Volume',
    size='Avg Volume',
    sizes=(10, 200),
    alpha=0.6,
    palette='viridis'
)

plt.title('Volatility% vs Spread% (Sized/Colored by Volume)')
plt.axvline(x=0.15, color='r', linestyle='--', label='Spread Target < 0.15%')
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
plt.show()"""
cells.append(new_code_cell(code6))


# Cell 8: Filtering Candidates
text7 = """## Filter Candidates

We apply the intersection of the "Best 45%" for each metric to find the **Sweet Spot**:
1. **Volatility%**: Top 45% (>= 55th percentile)
2. **Spread%**: Bottom 45% (<= 45th percentile)
3. **Avg Volume**: Top 45% (>= 55th percentile)"""
cells.append(new_markdown_cell(text7))

code7 = """# Apply Filters
candidates = df[
    (df['Volatility%'] >= vol_cutoff) &
    (df['Spread%'] <= spread_cutoff) &
    (df['Avg Volume'] >= volume_cutoff)
].copy()

# --- Filter Analysis ---
print(f"--- Filter Efficiency Analysis ---")
print(f"Total Symbols: {len(df)}")

pass_vol = len(df[df['Volatility%'] >= vol_cutoff])
pass_spread = len(df[df['Spread%'] <= spread_cutoff])
pass_volume = len(df[df['Avg Volume'] >= volume_cutoff])

print(f"Pass Volatility (>= {vol_cutoff:.4f}%): {pass_vol} ({pass_vol/len(df):.1%})")
print(f"Pass Spread     (<= {spread_cutoff:.4f}%): {pass_spread} ({pass_spread/len(df):.1%})")
print(f"Pass Volume     (>= {volume_cutoff:.0f}):   {pass_volume} ({pass_volume/len(df):.1%})")

# Calculate drops
print(f"Intersection (All 3): {len(candidates)} ({len(candidates)/len(df):.1%})")
print("-" * 30)

# Sort by Volatility
candidates = candidates.sort_values(by='Volatility%', ascending=False)

print(f"Found {len(candidates)} candidates in the 'Sweet Spot'.")

# Display Top 20
display_cols = ['Symbol', 'Volatility%', 'Spread%', 'Avg Volume', 'Price', 'Path']
display(candidates[display_cols].head(20))"""
cells.append(new_code_cell(code7))

# Cell 9: Export
text8 = """## Export Results"""
cells.append(new_markdown_cell(text8))

code8 = """output_file = 'filtered_candidates.csv'
candidates.to_csv(output_file, index=False)
print(f"Saved {len(candidates)} candidates to {output_file}")"""
cells.append(new_code_cell(code8))

notebook_content = {
 "cells": cells,
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

# Write the notebook
with open('volatility_analysis.ipynb', 'w') as f:
    json.dump(notebook_content, f, indent=1)

print("Notebook generated successfully.")
