
import pandas as pd
import io

# Create dummy data mimicking the issue
csv_data = """Timestamp,Ticket
2026-02-16T21:38:05,1
2026-02-16T21:38:06,2
2026-02-16T21:38:06.223549,3
"""

print("Testing default to_datetime...")
try:
    df = pd.read_csv(io.StringIO(csv_data))
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    print("Success with default!")
except Exception as e:
    print(f"Failed with default: {e}")

print("\nTesting with format='mixed'...")
try:
    df = pd.read_csv(io.StringIO(csv_data))
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed')
    print("Success with format='mixed'!")
    print(df)
except Exception as e:
    print(f"Failed with format='mixed': {e}")
