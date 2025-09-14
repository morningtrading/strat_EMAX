#!/usr/bin/env python3
"""
Data Loader for Backtesting
Handles loading and preprocessing of historical data from various sources
"""

import pandas as pd
import numpy as np
import os
import glob
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class DataLoader:
    """Universal data loader for backtesting"""
    
    def __init__(self, data_directory: str = "Z:\\"):
        self.data_directory = data_directory
        self.supported_formats = ['.csv', '.txt']
        
    def list_available_files(self) -> List[str]:
        """List all available data files in the directory"""
        files = []
        for format_ext in self.supported_formats:
            pattern = os.path.join(self.data_directory, f"*{format_ext}")
            files.extend(glob.glob(pattern))
            
        # Also check subdirectories
        for root, dirs, filenames in os.walk(self.data_directory):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in self.supported_formats):
                    files.append(os.path.join(root, filename))
        
        return files
    
    def detect_data_format(self, file_path: str) -> Dict:
        """Detect the format and structure of a data file"""
        try:
            # Read first few lines to detect format
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip()
            
            # Parse header
            header = [col.strip() for col in first_line.split(',')]
            
            format_info = {
                'file_path': file_path,
                'columns': header,
                'has_header': True,
                'separator': ',',
                'timestamp_format': None,
                'ohlcv_columns': self._detect_ohlcv_columns(header),
                'additional_columns': []
            }
            
            # Detect timestamp format
            format_info['timestamp_format'] = self._detect_timestamp_format(second_line)
            
            # Identify additional columns
            ohlcv_cols = format_info['ohlcv_columns'].values()
            format_info['additional_columns'] = [col for col in header if col not in ohlcv_cols and col.lower() not in ['timestamp', 'date', 'time']]
            
            return format_info
            
        except Exception as e:
            print(f"Error detecting format for {file_path}: {e}")
            return None
    
    def _detect_ohlcv_columns(self, header: List[str]) -> Dict:
        """Detect OHLCV column names"""
        ohlcv_mapping = {}
        
        for col in header:
            col_lower = col.lower()
            if 'open' in col_lower:
                ohlcv_mapping['open'] = col
            elif 'high' in col_lower:
                ohlcv_mapping['high'] = col
            elif 'low' in col_lower:
                ohlcv_mapping['low'] = col
            elif 'close' in col_lower:
                ohlcv_mapping['close'] = col
            elif 'volume' in col_lower or 'vol' in col_lower:
                ohlcv_mapping['volume'] = col
        
        return ohlcv_mapping
    
    def _detect_timestamp_format(self, sample_line: str) -> str:
        """Detect timestamp format from sample data"""
        parts = sample_line.split(',')
        timestamp_part = parts[0]
        
        # Common timestamp formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%Y.%m.%d %H:%M:%S',
            '%Y-%m-%d',
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(timestamp_part.strip(), fmt)
                return fmt
            except ValueError:
                continue
        
        return '%Y-%m-%d %H:%M:%S'  # Default format
    
    def load_csv_data(self, file_path: str, format_info: Dict = None) -> Optional[pd.DataFrame]:
        """Load CSV data with automatic format detection"""
        if format_info is None:
            format_info = self.detect_data_format(file_path)
            if format_info is None:
                return None
        
        try:
            # Load data
            df = pd.read_csv(file_path)
            
            # Clean column names
            df.columns = [col.strip() for col in df.columns]
            
            # Convert timestamp
            timestamp_col = None
            for col in df.columns:
                if col.lower() in ['timestamp', 'date', 'time']:
                    timestamp_col = col
                    break
            
            if timestamp_col:
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], 
                                                 format=format_info['timestamp_format'],
                                                 errors='coerce')
                df.set_index(timestamp_col, inplace=True)
            
            # Ensure OHLCV columns exist
            ohlcv_mapping = format_info['ohlcv_columns']
            required_columns = ['open', 'high', 'low', 'close']
            
            for req_col in required_columns:
                if req_col not in ohlcv_mapping:
                    print(f"Warning: {req_col} column not found in {file_path}")
                    return None
            
            # Rename columns to standard format
            column_mapping = {v: k for k, v in ohlcv_mapping.items()}
            df = df.rename(columns=column_mapping)
            
            # Ensure we have the required columns
            if not all(col in df.columns for col in required_columns):
                print(f"Error: Missing required OHLC columns in {file_path}")
                return None
            
            # Convert to numeric
            for col in required_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Add volume if available
            if 'volume' in ohlcv_mapping:
                volume_col = ohlcv_mapping['volume']
                if volume_col in df.columns:
                    df['volume'] = pd.to_numeric(df[volume_col], errors='coerce')
            
            # Remove rows with NaN values
            df = df.dropna(subset=required_columns)
            
            # Sort by timestamp
            df = df.sort_index()
            
            # Add additional metadata
            df.attrs['source_file'] = file_path
            df.attrs['data_format'] = format_info
            
            return df
            
        except Exception as e:
            print(f"Error loading data from {file_path}: {e}")
            return None
    
    def load_multiple_files(self, file_paths: List[str]) -> Dict[str, pd.DataFrame]:
        """Load multiple data files"""
        datasets = {}
        
        for file_path in file_paths:
            print(f"Loading {file_path}...")
            df = self.load_csv_data(file_path)
            if df is not None:
                # Extract symbol name from filename
                filename = os.path.basename(file_path)
                symbol = filename.split('_')[0] if '_' in filename else filename.split('.')[0]
                datasets[symbol] = df
                print(f"Loaded {len(df)} records for {symbol}")
            else:
                print(f"Failed to load {file_path}")
        
        return datasets
    
    def resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample data to different timeframe"""
        if timeframe == 'M1':
            return df  # Already 1-minute data
        
        timeframe_map = {
            'M5': '5T',
            'M15': '15T',
            'M30': '30T',
            'H1': '1H',
            'H4': '4H',
            'D1': '1D'
        }
        
        if timeframe not in timeframe_map:
            print(f"Unsupported timeframe: {timeframe}")
            return df
        
        freq = timeframe_map[timeframe]
        
        # Resample OHLCV data
        resampled = df.resample(freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum' if 'volume' in df.columns else 'count'
        }).dropna()
        
        # Preserve attributes
        resampled.attrs = df.attrs.copy()
        resampled.attrs['resampled_from'] = 'M1'
        resampled.attrs['resampled_to'] = timeframe
        
        return resampled
    
    def validate_data(self, df: pd.DataFrame) -> Dict:
        """Validate data quality and return statistics"""
        validation_report = {
            'total_records': len(df),
            'date_range': {
                'start': df.index.min(),
                'end': df.index.max(),
                'duration_days': (df.index.max() - df.index.min()).days
            },
            'data_quality': {},
            'gaps': [],
            'warnings': []
        }
        
        # Check for gaps in data
        expected_freq = pd.infer_freq(df.index)
        if expected_freq:
            full_range = pd.date_range(df.index.min(), df.index.max(), freq=expected_freq)
            missing_dates = full_range.difference(df.index)
            validation_report['gaps'] = list(missing_dates)
        
        # Check data quality
        for col in ['open', 'high', 'low', 'close']:
            validation_report['data_quality'][col] = {
                'null_count': df[col].isnull().sum(),
                'min_value': df[col].min(),
                'max_value': df[col].max(),
                'mean_value': df[col].mean()
            }
        
        # Check for invalid OHLC relationships
        invalid_ohlc = df[(df['high'] < df['low']) | 
                         (df['high'] < df['open']) | 
                         (df['high'] < df['close']) |
                         (df['low'] > df['open']) | 
                         (df['low'] > df['close'])]
        
        if len(invalid_ohlc) > 0:
            validation_report['warnings'].append(f"Found {len(invalid_ohlc)} invalid OHLC relationships")
        
        # Check for zero or negative prices
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            invalid_prices = df[df[col] <= 0]
            if len(invalid_prices) > 0:
                validation_report['warnings'].append(f"Found {len(invalid_prices)} zero or negative prices in {col}")
        
        return validation_report
    
    def get_data_summary(self) -> Dict:
        """Get summary of all available data files"""
        files = self.list_available_files()
        summary = {
            'total_files': len(files),
            'files': []
        }
        
        for file_path in files:
            file_info = {
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'size_mb': os.path.getsize(file_path) / (1024 * 1024)
            }
            
            # Try to detect format
            format_info = self.detect_data_format(file_path)
            if format_info:
                file_info['format'] = format_info
                
                # Try to load a sample to get record count
                try:
                    sample_df = pd.read_csv(file_path, nrows=1000)
                    file_info['estimated_records'] = len(sample_df) * (os.path.getsize(file_path) // len(sample_df.to_csv().encode()))
                except:
                    file_info['estimated_records'] = 'Unknown'
            
            summary['files'].append(file_info)
        
        return summary

def main():
    """Demo function to test the data loader"""
    print("Data Loader Demo")
    print("=" * 30)
    
    loader = DataLoader("Z:\\")
    
    # Get summary of available files
    summary = loader.get_data_summary()
    print(f"Found {summary['total_files']} data files:")
    
    for file_info in summary['files']:
        print(f"\nFile: {file_info['filename']}")
        print(f"  Size: {file_info['size_mb']:.2f} MB")
        if 'format' in file_info:
            format_info = file_info['format']
            print(f"  Columns: {format_info['columns']}")
            print(f"  OHLCV Mapping: {format_info['ohlcv_columns']}")
    
    # Load a sample file
    if summary['files']:
        sample_file = summary['files'][0]['file_path']
        print(f"\nLoading sample file: {sample_file}")
        
        df = loader.load_csv_data(sample_file)
        if df is not None:
            print(f"Loaded {len(df)} records")
            print(f"Date range: {df.index.min()} to {df.index.max()}")
            print(f"Columns: {list(df.columns)}")
            
            # Validate data
            validation = loader.validate_data(df)
            print(f"\nValidation Report:")
            print(f"  Total records: {validation['total_records']}")
            print(f"  Duration: {validation['date_range']['duration_days']} days")
            print(f"  Warnings: {len(validation['warnings'])}")
            
            if validation['warnings']:
                for warning in validation['warnings']:
                    print(f"    - {warning}")

if __name__ == "__main__":
    main()
