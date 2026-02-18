
import csv
import re
from pathlib import Path
from datetime import datetime

import_data = """2026.02.16 21:38:05	43602296	AUDUSD	buy	out	0.14	0.70764	47851641	0.00	0.00	0.00	-4.34	995.66	
2026.02.16 21:38:05	43602297	BTCUSD	sell	out	0.1	68037.11	47851642	0.00	0.00	0.00	38.29	1 033.95	
2026.02.16 21:38:06	43602298	GER40ft	buy	out	0.1	24882.80	47851643	0.00	0.00	0.00	-0.30	1 033.65	
2026.02.16 21:38:06	43602299	BTCUSD	buy	in	0.15	68054.13	47851644	0.00	0.00	0.00	0.00	1 033.65	EMAX
2026.02.16 21:38:06	43602300	BTCUSD	sell	out	0.15	68037.11	47851645	0.00	0.00	0.00	-2.55	1 031.10	
2026.02.16 21:38:07	43602301	GER40ft	buy	out	0.1	24882.80	47851646	0.00	0.00	0.00	-0.24	1 030.86	
2026.02.16 21:38:08	43602302	GER40ft	buy	out	0.1	24882.80	47851647	0.00	0.00	0.00	-0.12	1 030.74	
2026.02.16 21:38:22	43602303	BTCUSD	buy	in	0.15	68099.17	47851648	0.00	0.00	0.00	0.00	1 030.74	EMAX
2026.02.16 21:43:02	43602313	BTCUSD	sell	out	0.15	68031.18	47851657	0.00	0.00	0.00	-10.20	1 020.54	[sl 68031.18]
2026.02.16 21:59:20	43602418	BTCUSD	sell	in	0.15	67906.14	47851760	0.00	0.00	0.00	0.00	1 020.54	EMAX
2026.02.16 22:15:29	43602680	BTCUSD	buy	out	0.15	67972.81	47852017	0.00	0.00	0.00	-10.00	1 010.54	[sl 67972.81]
2026.02.16 22:16:32	43602696	BTCUSD	buy	in	0.15	68043.23	47852031	0.00	0.00	0.00	0.00	1 010.54	EMAX
2026.02.16 22:19:58	43602706	BTCUSD	sell	out	0.15	67976.56	47852040	0.00	0.00	0.00	-10.00	1 000.54	[sl 67976.56]
2026.02.16 22:23:24	43602716	BTCUSD	buy	in	0.15	68032.78	47852049	0.00	0.00	0.00	0.00	1 000.54	EMAX
2026.02.17 00:52:21	43610865	BTCUSD	sell	out	0.15	68521.98	47860190	0.00	0.00	-5.74	73.38	1 068.18	Close by EMAX
2026.02.17 03:50:01	43652487	BTCUSD	sell	in	0.15	68814.88	47910600	0.00	0.00	0.00	0.00	1 068.18	EMAX
2026.02.17 04:10:42	43655775	BTCUSD	buy	out	0.15	68880.27	47915094	0.00	0.00	0.00	-9.81	1 058.37	[sl 68880.27]
2026.02.17 04:12:51	43656172	BTCUSD	buy	in	0.14	69095.98	47915578	0.00	0.00	0.00	0.00	1 058.37	EMAX
2026.02.17 04:19:26	43656954	BTCUSD	sell	out	0.14	69024.54	47916693	0.00	0.00	0.00	-10.00	1 048.37	[sl 69024.54]
2026.02.17 05:00:00	43661067	BTCUSD	sell	in	0.15	68829.03	47923362	0.00	0.00	0.00	0.00	1 048.37	EMAX
2026.02.17 19:31:12	43864472	USDPLN	sell	in	0.03	3.56222	48196849	0.00	0.00	0.00	0.00	1 048.37	EMAX
2026.02.17 19:33:20	43864903	USDPLN	buy	out	0.03	3.56555	48197548	0.00	0.00	0.00	-2.80	1 045.57	[sl 3.56555]
2026.02.17 19:47:08	43869068	USDPLN	sell	in	0.03	3.56475	48203405	0.00	0.00	0.00	0.00	1 045.57	EMAX
2026.02.17 20:00:00	43873136	PLTR	sell	in	76.7	130.36	48209220	0.00	0.00	0.00	0.00	1 045.57	EMAX
2026.02.17 20:00:02	43873170	PLTR	buy	out	76.7	130.49	48209258	0.00	0.00	0.00	-9.97	1 035.60	[sl 130.49]
2026.02.17 20:14:21	43876966	BTCUSD	buy	out	0.15	67401.08	48214873	0.00	0.00	0.00	214.19	1 249.79	Close by EMAX
2026.02.17 20:20:32	43878226	BTCUSD	buy	in	0.15	67473.46	48216857	0.00	0.00	0.00	0.00	1 249.79	EMAX
2026.02.17 20:22:40	43878927	BTCUSD	sell	out	0.15	67758.31	48217824	0.00	0.00	0.00	42.73	1 292.52	Close by EMAX
2026.02.17 20:24:26	43879212	BTCUSD	buy	in	0.15	67627.24	48218327	0.00	0.00	0.00	0.00	1 292.52	EMAX
2026.02.17 20:37:05	43882272	USDPLN	buy	out	0.03	3.56124	48222972	0.00	0.00	0.00	2.96	1 295.48	Close by EMAX
2026.02.17 22:07:30	43900882	BTCUSD	sell	out	0.15	67560.52	48252669	0.00	0.00	0.00	-10.01	1 285.47	[sl 67560.52]"""


def convert_line(line):
    parts = line.strip().split('\t')
    if len(parts) < 13: # at least 13 columns, comment is optional
        # Retry space split if tabs failed
        parts = re.split(r'\s{2,}', line.strip())
        if len(parts) < 13:
            return None

    # Column Mapping based on MT5 export:
    # 0: Date Time (2026.02.16 21:38:05)
    # 1: Ticket (43602296)
    # 2: Symbol (AUDUSD)
    # 3: Type (buy)
    # 4: Direction (out)
    # 5: Volume (0.14)
    # 6: Price (0.70764)
    # 7: Order Ticket (47851641)
    # 8: Commission (0.00)
    # 9: Swap (0.00)
    # 10: Fee/Extra? (0.00) or maybe the line varies.
    # 11: Profit
    # 12: Balance
    # 13: Comment (Optional)

    # Date Time
    dt_str = parts[0].replace('.', '-')
    try:
        timestamp = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").isoformat()
    except ValueError:
        return None

    ticket = parts[1]
    symbol = parts[2]
    type_str = parts[3]
    dir_str = parts[4]
    
    # Determine Action
    action = "UNKNOWN"
    if dir_str == "in":
        if type_str == "buy": action = "OPEN_LONG"
        elif type_str == "sell": action = "OPEN_SHORT"
    elif dir_str == "out":
        if type_str == "buy": action = "CLOSE_SHORT" # Buying to close
        elif type_str == "sell": action = "CLOSE_LONG" # Selling to close
        
    volume = parts[5]
    price = parts[6]
    
    # Financials at the end
    # Clean balance (last numeric field)
    # 1 033.65 -> 1033.65
    
    # Let's count from end backward to be safe against variable columns in middle?
    # No, usually middle is fixed.
    # Let's count from end:
    # Last might be Comment.
    # Before that Balance.
    # Before that Profit.
    # Before that Swap.
    # Before that Commission.
    
    comment = ""
    balance_idx = -1
    
    # Check if last element is numeric (after removing spaces)
    last_clean = parts[-1].replace(' ', '').replace('[', '').replace(']', '')
    try:
        float(last_clean)
        # It is numeric -> it's Balance
        balance_idx = -1
    except ValueError:
        # It is NOT numeric -> it's Comment
        comment = parts[-1] 
        balance_idx = -2
        
    balance_str = parts[balance_idx].replace(' ', '')
    profit_str = parts[balance_idx-1].replace(' ', '')
    
    # Swap/Commission
    # We have 3 columns before profit: 8, 9, 10.
    # Let's take 9 as Swap, 8 as Comm. 10 is ?
    # From "0.00 0.00 -5.74 73.38", 73.38 is profit.
    # -5.74 is at index -3 relative to balance? 
    # Let's use negative indexing from balance.
    
    swap_str = parts[balance_idx-2].replace(' ', '')
    comm_str = parts[balance_idx-3].replace(' ', '')
    
    try:
        balance = float(balance_str)
        profit = float(profit_str)
        swap = float(swap_str)
        commission = float(comm_str)
    except ValueError:
        return None # Failed to parse numbers
    
    margin_used = 0
    equity = balance
    
    return [
        timestamp,
        ticket,
        symbol,
        action,
        volume,
        price,
        0, # SL
        0, # TP
        profit,
        swap,
        commission,
        margin_used,
        balance,
        equity,
        comment
    ]

rows = []
header = ['Timestamp', 'Ticket', 'Symbol', 'Action', 'Volume', 'Price', 'SL', 'TP', 'Profit', 'Swap', 'Commission', 'Margin_Used', 'Balance', 'Equity', 'Comment']

for line in import_data.strip().split('\n'):
    if not line.strip(): continue
    try:
        row = convert_line(line)
        if row:
            rows.append(row)
    except Exception as e:
        print(f"Error parsing line: {line[:50]}... {e}")

# Write to CSV
out_path = Path(__file__).parent.parent / 'data' / 'trade_history.csv'
out_path.parent.mkdir(exist_ok=True)

with open(out_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print(f"Successfully imported {len(rows)} trades to {out_path}")
