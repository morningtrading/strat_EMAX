"""
================================================================================
WEB DASHBOARD MODULE - EMAX Trading Engine
================================================================================

PURPOSE:
    Provides a web-based dashboard for monitoring and controlling the trading
    engine. Features real-time data display, trading controls, and position
    management.

INPUTS:
    - Dashboard data from TradingEngine
    - Configuration from trading_config.json

OUTPUTS:
    - Web interface on configured port (default: 8080)
    - REST API for data and controls

HOW TO RUN:
    # Start from main.py (includes dashboard)
    wine python main.py
    
    # Or run dashboard standalone for testing
    wine python dashboard/web_dashboard.py

ENDPOINTS:
    GET  /               - Main dashboard page
    GET  /api/status     - Current engine status
    GET  /api/positions  - Open positions
    GET  /api/history    - Order history
    POST /api/trade/enable   - Enable trading
    POST /api/trade/disable  - Disable trading
    POST /api/trade/freeze   - Freeze trading (stop new trades, keep TP/SL)
    POST /api/trade/unfreeze - Unfreeze trading (resume new trades)
    POST /api/direction      - Set direction (long/short/both)
    POST /api/panic          - Close all positions

AUTHOR: EMAX Trading Engine
VERSION: 1.0.0
LAST UPDATED: 2026-01-22
================================================================================
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path
from threading import Thread

# Use Flask for web server
try:
    from flask import Flask, render_template_string, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not installed. Install with: pip install flask")

logger = logging.getLogger('WebDashboard')

# Dashboard HTML template
# ... (HTML content truncated for brevity, available in DASHBOARD_HTML variable)

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class SafeJSONEncoder(json.JSONEncoder):
    """
    JSON Encoder that handles NaN/Infinity by converting to null
    """
    def default(self, obj):
        try:
            if isinstance(obj, float):
                if obj != obj: # NaN check
                    return None
                if obj == float('inf') or obj == float('-inf'):
                    return None
            return super().default(obj)
        except:
             return str(obj)

def clean_nans(data):
    """Recursively convert NaNs to None for JSON safety"""
    if isinstance(data, dict):
        return {k: clean_nans(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_nans(v) for v in data]
    elif isinstance(data, float):
        if data != data or data == float('inf') or data == float('-inf'):
            return None
    return data

app.json_encoder = SafeJSONEncoder

# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EMAX Dashboard [{self.instance_id}]</title>
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #020024 0%, #090979 35%, #00d4ff 100%);
            min-height: 100vh;
            color: #e4e4e4;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            padding: 20px;
            margin-bottom: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .instance-badge {
            font-size: 0.4em;
            vertical-align: middle;
            background: rgba(0, 212, 255, 0.2);
            padding: 4px 10px;
            border-radius: 8px;
            border: 1px solid rgba(0, 212, 255, 0.4);
            -webkit-text-fill-color: #00d4ff;
        }
        
        .header .status {
            font-size: 1.2em;
            color: #888;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .status-connected { background: #00ff88; }
        .status-disconnected { background: #ff4444; }
        .status-paused { background: #ffaa00; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #00d4ff;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card h2 .icon {
            font-size: 1.5em;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        
        .stat-item {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 10px;
        }
        
        .stat-label {
            font-size: 0.85em;
            color: #888;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 1.4em;
            font-weight: bold;
        }
        
        .stat-value.positive { color: #00ff88; }
        .stat-value.negative { color: #ff4444; }
        
        .controls {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        
        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(90deg, #00d4ff, #0099cc);
            color: white;
        }
        
        .btn-success {
            background: linear-gradient(90deg, #00ff88, #00cc6a);
            color: black;
        }
        
        .btn-danger {
            background: linear-gradient(90deg, #ff4444, #cc0000);
            color: white;
        }
        
        .btn-warning {
            background: linear-gradient(90deg, #ffaa00, #cc8800);
            color: black;
        }
        
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .panic-btn {
            background: linear-gradient(90deg, #ff0000, #880000);
            color: white;
            font-size: 1.2em;
            padding: 15px 40px;
        }
        
        .positions-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .positions-table th,
        .positions-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .positions-table th {
            background: rgba(0,212,255,0.1);
            color: #00d4ff;
        }
        
        .positions-table tr:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .direction-select {
            padding: 10px 20px;
            font-size: 1em;
            border: 2px solid #00d4ff;
            border-radius: 10px;
            background: transparent;
            color: white;
            cursor: pointer;
        }
        
        .direction-select option {
            background: #1a1a2e;
        }
        
        .ema-display {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }
        
        .ema-item {
            padding: 10px 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
        }
        
        .ema-fast { border-left: 3px solid #00ff88; }
        .ema-slow { border-left: 3px solid #ff6666; }
        
        .signal-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .signal-buy { background: #00ff88; color: black; }
        .signal-sell { background: #ff4444; color: white; }
        .signal-hold { background: #666; color: white; }
        
        .refresh-time {
            text-align: center;
            padding: 10px;
            color: #666;
            font-size: 0.9em;
        }
        
        .config-display {
            font-family: monospace;
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
        }
        .market-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        .market-table th, .market-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .market-table th {
            color: #888;
            font-weight: normal;
        }
        .trend-badge {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            display: inline-block;
        }
        .trend-bull { background: rgba(0, 255, 136, 0.2); color: #00ff88; }
        .trend-bear { background: rgba(255, 68, 68, 0.2); color: #ff4444; }
        .trend-wait { background: rgba(255, 170, 0, 0.2); color: #ffaa00; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{self.instance_id} <span style="font-size: 0.5em; color: #ccc; font-weight: normal;">Trading Dashboard</span></h1>
        <div class="status">
            <span class="status-indicator" id="connection-indicator"></span>
            <span id="connection-status">Connecting...</span>
            | <strong>Timeframe:</strong> <span id="timeframe" style="color: #00d4ff;">M5</span>
            | Uptime: <span id="uptime">0s</span>
        </div>
        <div class="status" style="margin-top: 8px; font-size: 0.95em;">
            ⏱️ Next refresh: <span id="countdown" style="color: #00ff88; font-weight: bold;">35</span>s
            | Last check: <span id="last-check-status" style="color: #00ff88;">OK</span>
            | <span id="last-bar-time" style="color: #888;">-</span>
        </div>
    </div>
    
    <div class="controls">
        <button class="btn btn-success" id="btn-enable" onclick="toggleTrading(true)">
            ▶️ Enable Trading
        </button>
        <button class="btn btn-warning" id="btn-disable" onclick="toggleTrading(false)">
            ⏸️ Disable Trading
        </button>

        <button class="btn btn-warning" id="btn-freeze" onclick="freezeTrading()" style="background: linear-gradient(90deg, #3b82f6, #1e40af);">
            ❄️ Freeze Trading
        </button>
        <button class="btn btn-success" id="btn-unfreeze" onclick="unfreezeTrading()" style="background: linear-gradient(90deg, #10b981, #059669); display:none;">
            ▶️ Unfreeze Trading
        </button>

        <select class="direction-select" id="direction-select" onchange="setDirection(this.value)">
            <option value="both">📊 Both Directions</option>
            <option value="long">📈 Long Only</option>
            <option value="short">📉 Short Only</option>
        </select>

        <button class="btn panic-btn" onclick="panicCloseAll()">
            🚨 PANIC - Close All
        </button>
    </div>

    <div id="freeze-indicator" style="display: none; text-align: center; padding: 15px; margin-bottom: 20px; background: rgba(59, 130, 246, 0.2); border: 2px solid #3b82f6; border-radius: 10px;">
        <span style="font-size: 1.3em; color: #3b82f6;">❄️ TRADING FROZEN</span>
        <div style="margin-top: 5px; color: #888;">
            <strong>Reason:</strong> <span id="freeze-reason">-</span> |
            <strong>Since:</strong> <span id="freeze-time">-</span>
        </div>
        <div style="margin-top: 5px; font-size: 0.9em; color: #666;">
            ⚠️ No new trades will be opened. Existing positions continue with TP/SL active.
        </div>
    </div>
    
    <div class="grid">
        <!-- Cycle Status -->
        <div class="card">
            <h2><span class="icon">🔄</span> Cycle Status <span style="font-size:0.6em; color:#666; font-weight:normal; margin-left:auto" id="cycle-duration">0ms</span></h2>
            
            <div class="stat-grid" style="grid-template-columns: repeat(3, 1fr);">
                <!-- Row 1: Scan & Positions -->
                <div class="stat-item">
                    <div class="stat-label">Scanned</div>
                    <div class="stat-value"><span id="cycle-scanned">0</span> <span style="font-size:0.5em; color:#888;">(<span id="cycle-open" style="color:#00ff88">0</span>/<span id="cycle-closed" style="color:#ff4444">0</span>)</span></div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Positions</div>
                    <div class="stat-value" id="cycle-positions">0</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Errors</div>
                    <div class="stat-value" id="cycle-errors" style="color: #888;">0</div>
                </div>

                <!-- Row 2: Trends -->
                <div class="stat-item" style="grid-column: span 3;">
                    <div class="stat-label">Trend Analysis</div>
                    <div style="display: flex; gap: 15px; align-items: center; margin-top: 5px;">
                        <span style="color:#00ff88">BULL: <b id="cycle-bull">0</b></span>
                        <span style="color:#ff4444">BEAR: <b id="cycle-bear">0</b></span>
                        <span style="color:#ffaa00">WAIT: <b id="cycle-wait">0</b></span>
                    </div>
                </div>

                <!-- Row 3: Modifications -->
                <div class="stat-item" style="grid-column: span 3;">
                     <div class="stat-label">Modifications: <b id="cycle-mods-total" style="color:#fff">0</b></div>
                     <div style="display: flex; gap: 15px; align-items: center; margin-top: 5px; font-size: 0.9em;">
                        <span>SL: <b id="cycle-mods-sl" style="color:#00d4ff">0</b></span>
                        <span>TP: <b id="cycle-mods-tp" style="color:#00d4ff">0</b></span>
                     </div>
                </div>

                <!-- Row 4: Last Error -->
                <div id="cycle-last-error" class="stat-item" style="grid-column: span 3; display: none; background: rgba(255, 68, 68, 0.1); border: 1px solid rgba(255, 68, 68, 0.3);">
                    <div class="stat-label" style="color:#ff4444">Last Exception</div>
                    <div id="cycle-error-msg" style="font-size: 0.85em; color: #ffcccc; margin-top: 5px; word-break: break-all;">-</div>
                </div>
            </div>
        </div>

        <!-- Account Info -->
        <div class="card">
            <h2><span class="icon">💰</span> Account</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-label">Balance</div>
                    <div class="stat-value" id="balance">$0.00</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Equity</div>
                    <div class="stat-value" id="equity">$0.00</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Margin Used</div>
                    <div class="stat-value" id="margin">$0.00</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Floating P&L</div>
                    <div class="stat-value" id="floating-pnl">$0.00</div>
                </div>
            </div>
        </div>
        
        <!-- Performance Stats -->
        <div class="card">
            <h2><span class="icon">📊</span> Performance</h2>
            <div style="margin-bottom: 5px; font-weight: bold; color: #888; font-size: 0.8em;">DAILY (Since 00:00)</div>
            <div class="stat-grid" style="margin-bottom: 15px;">
                <div class="stat-item">
                    <div class="stat-label">today's P&L</div>
                    <div class="stat-value" id="daily-pnl">$0.00</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Today's Trades</div>
                    <div class="stat-value" id="daily-trades">0</div>
                </div>
                 <div class="stat-item">
                    <div class="stat-label">Session Status</div>
                    <div class="stat-value" id="session-status">-</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Daily Loss Limit</div>
                    <div class="stat-value" id="loss-limit">0%</div>
                </div>
            </div>
            
            <div style="margin-bottom: 5px; font-weight: bold; color: #888; font-size: 0.8em;">SESSION (Since Start)</div>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-label">Total P&L</div>
                    <div class="stat-value" id="session-pnl">$0.00</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Total Trades</div>
                    <div class="stat-value" id="session-trades">0</div>
                </div>
                 <div class="stat-item">
                    <div class="stat-label">Uptime</div>
                    <div class="stat-value" id="session-uptime">-</div>
                </div>
            </div>
        </div>
        
        <!-- Market Status -->
        <div class="card" style="grid-column: span 2;">
            <h2><span class="icon">🌍</span> Market Status</h2>
            <table class="market-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Market</th>
                        <th>TF</th>
                        <th>EMA</th>
                        <th>Price</th>
                        <th>Min Vol</th>
                        <th>Trend</th>
                        <th>Momentum</th>
                    </tr>
                </thead>
                <tbody id="market-status-body">
                    <tr><td colspan="8" style="text-align: center; color: #666;">Loading market data...</td></tr>
                </tbody>
            </table>
        </div>
        
        <!-- Account Info -->
        <div class="card">
            <h2><span class="icon">🏦</span> Account Info</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.95em;">
                <div><strong>Broker:</strong></div>
                <div id="broker-name" style="color: #00d4ff;">-</div>
                
                <div><strong>Account:</strong></div>
                <div id="account-number" style="color: #00d4ff;">-</div>
                
                <div><strong>Server:</strong></div>
                <div id="server-name" style="color: #888;">-</div>
                
                <div><strong>Mode:</strong></div>
                <div id="account-mode">-</div>
                
                <div><strong>Strategy:</strong></div>
                <div id="strategy-name" style="color: #00ff88;">-</div>
                
                <div><strong>Leverage:</strong></div>
                <div id="account-leverage" style="color: #888;">-</div>
            </div>
        </div>
        
        <!-- Configuration -->
        <div class="card">
            <h2><span class="icon">⚙️</span> Configuration</h2>
            <div class="config-display" id="config-display">
                Loading...
            </div>
        </div>
    </div>
    
    <!-- Positions -->
    <div class="card">
        <h2><span class="icon">📋</span> Open Positions</h2>
        <table class="positions-table">
            <thead>
                <tr>
                    <th>Ticket</th>
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Volume</th>
                    <th>Entry</th>
                    <th>Current</th>
                    <th>SL</th>
                    <th>Margin</th>
                    <th>P&L</th>
                </tr>
            </thead>
            <tbody id="positions-body">
                <tr><td colspan="9" style="text-align: center; color: #666;">No open positions</td></tr>
            </tbody>
        </table>
    </div>
    
    <!-- Order History -->
    <div class="card" style="margin-top: 20px;">
        <h2><span class="icon">📜</span> Recent Orders (Last 100)</h2>
        <table class="positions-table">
            <thead>
                <tr>
                    <th>Ticket</th>
                    <th>Time</th>
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Volume</th>
                    <th>Price</th>
                    <th>P&L</th>
                </tr>
            </thead>
            <tbody id="history-body">
                <tr><td colspan="7" style="text-align: center; color: #666;">No recent orders</td></tr>
            </tbody>
        </table>
    </div>
    
    <div class="refresh-time">
        Last updated: <span id="last-update">-</span>
        | Symbol: <span id="active-symbol" style="color: #00d4ff;">XAGUSD</span>
        | Refresh: <span id="refresh-rate">35</span>s
    </div>
    
    <script>
        const API_BASE = '';
        let refreshInterval;
        let countdownInterval;
        let countdown = 35;
        const REFRESH_SECONDS = 35;
        
        function updateCountdown() {
            countdown--;
            if (countdown <= 0) {
                countdown = REFRESH_SECONDS;
            }
            document.getElementById('countdown').textContent = countdown;
        }
        
        async function fetchData() {
            countdown = REFRESH_SECONDS;
            document.getElementById('countdown').textContent = countdown;
            try {
                console.log('[Dashboard] Fetching data from /api/status');
                const response = await fetch(API_BASE + '/api/status');
                console.log('[Dashboard] Response status:', response.status);
                const data = await response.json();
                console.log('[Dashboard] Data received:', Object.keys(data));
                updateDashboard(data);
                document.getElementById('last-check-status').textContent = 'OK';
                document.getElementById('last-check-status').style.color = '#00ff88';
            } catch (error) {
                console.error('[Dashboard] ERROR fetching data:', error);
                console.error('[Dashboard] Stack:', error.stack);
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('connection-indicator').className = 'status-indicator status-disconnected';
                document.getElementById('last-check-status').textContent = 'Error';
                document.getElementById('last-check-status').style.color = '#ff4444';
            }
        }
        
        function updateDashboard(data) {
            // Connection status
            const connected = data.connection_status?.connected;
            document.getElementById('connection-indicator').className = 
                'status-indicator ' + (connected ? 'status-connected' : 'status-disconnected');
            document.getElementById('connection-status').textContent = 
                connected ? 'Connected' : 'Disconnected';
            
            // Cycle Stats
            const cycle = data.last_cycle_stats || {};
            document.getElementById('cycle-duration').textContent = (cycle.duration_ms || 0) + 'ms';
            document.getElementById('cycle-scanned').textContent = cycle.symbols_scanned || 0;
            document.getElementById('cycle-open').textContent = cycle.markets_open || 0;
            document.getElementById('cycle-closed').textContent = cycle.markets_closed || 0;
            document.getElementById('cycle-errors').textContent = cycle.errors || 0;
            
            // New Fields
            document.getElementById('cycle-positions').textContent = cycle.open_positions || 0;
            document.getElementById('cycle-bull').textContent = cycle.bull_count || 0;
            document.getElementById('cycle-bear').textContent = cycle.bear_count || 0;
            document.getElementById('cycle-wait').textContent = cycle.wait_count || 0;
            
            const slMods = cycle.sl_modifications || 0;
            const tpMods = cycle.tp_modifications || 0;
            document.getElementById('cycle-mods-total').textContent = slMods + tpMods;
            document.getElementById('cycle-mods-sl').textContent = slMods;
            document.getElementById('cycle-mods-tp').textContent = tpMods;
            
            // Error Message
            const errorMsg = cycle.last_error;
            const errorContainer = document.getElementById('cycle-last-error');
            const errorText = document.getElementById('cycle-error-msg');
            
            if (errorMsg && cycle.errors > 0) {
                errorContainer.style.display = 'block';
                errorText.textContent = errorMsg;
            } else {
                errorContainer.style.display = 'none';
            }
            
            // Uptime
            document.getElementById('uptime').textContent = 
                formatUptime(data.engine_status?.uptime || 0);
            
            // Account info
            const account = data.account_info || {};
            document.getElementById('balance').textContent = '$' + (account.balance || 0).toFixed(2);
            document.getElementById('equity').textContent = '$' + (account.equity || 0).toFixed(2);
            document.getElementById('margin').textContent = '$' + (account.margin || 0).toFixed(2);
            
            const profit = account.profit || 0;
            const profitEl = document.getElementById('floating-pnl');
            profitEl.textContent = '$' + profit.toFixed(2);
            profitEl.className = 'stat-value ' + (profit >= 0 ? 'positive' : 'negative');
            
            // Daily stats
            const daily = data.daily_stats || {};
            const dailyPnl = daily.daily_pnl || 0;
            const dailyPnlEl = document.getElementById('daily-pnl');
            dailyPnlEl.textContent = '$' + dailyPnl.toFixed(2);
            dailyPnlEl.className = 'stat-value ' + (dailyPnl >= 0 ? 'positive' : 'negative');
            document.getElementById('daily-trades').textContent = daily.daily_trades || 0;
            
            // Session Stats
            const session = data.session_stats || {};
            const sessionPnl = session.pnl || 0;
            const sessionPnlEl = document.getElementById('session-pnl');
            if (sessionPnlEl) {
                sessionPnlEl.textContent = '$' + sessionPnl.toFixed(2);
                sessionPnlEl.className = 'stat-value ' + (sessionPnl >= 0 ? 'positive' : 'negative');
                document.getElementById('session-trades').textContent = session.trades || 0;
                document.getElementById('session-uptime').textContent = formatUptime(data.engine_status?.uptime || 0);
            }
            
            // Manager status
            const manager = data.manager_status || {};
            document.getElementById('session-status').textContent = 
                manager.session_allowed ? '✅ Active' : '⏸️ Closed';
            document.getElementById('loss-limit').textContent = 
                (manager.current_daily_loss || 0).toFixed(1) + '% / ' + (manager.daily_loss_limit || 75) + '%';
            
            // Trading controls
            const engine = data.engine_status || {};
            document.getElementById('btn-enable').disabled = engine.trading_enabled;
            document.getElementById('btn-disable').disabled = !engine.trading_enabled;
            document.getElementById('direction-select').value = engine.direction || 'both';

            // Freeze/Unfreeze controls
            const isFrozen = manager.trading_frozen || false;
            document.getElementById('btn-freeze').style.display = isFrozen ? 'none' : 'flex';
            document.getElementById('btn-unfreeze').style.display = isFrozen ? 'flex' : 'none';

            // Freeze indicator banner
            const freezeIndicator = document.getElementById('freeze-indicator');
            if (isFrozen) {
                freezeIndicator.style.display = 'block';
                document.getElementById('freeze-reason').textContent = manager.freeze_reason || 'Unknown';
                const freezeTime = manager.freeze_timestamp ? new Date(manager.freeze_timestamp).toLocaleTimeString() : '-';
                document.getElementById('freeze-time').textContent = freezeTime;
            } else {
                freezeIndicator.style.display = 'none';
            }
            
            // Update timeframe display
            document.getElementById('timeframe').textContent = engine.timeframe || 'M5';
            
            // Config display
            document.getElementById('config-display').textContent = JSON.stringify({
                trading_enabled: engine.trading_enabled,
                direction: engine.direction,
                symbols: engine.enabled_symbols,
                sl_type: manager.sl_type,
                max_margin: manager.max_margin_per_trade
            }, null, 2);
            
            // Account Info card
            const conn = data.connection_status || {};
            const strategy = data.strategy_status || {};
            document.getElementById('broker-name').textContent = conn.company || 'Unknown';
            document.getElementById('account-number').textContent = conn.account || '-';
            document.getElementById('server-name').textContent = conn.server || '-';
            document.getElementById('account-leverage').textContent = account.leverage ? `1:${account.leverage}` : '-';
            document.getElementById('strategy-name').textContent = strategy.fast_period && strategy.slow_period 
                ? `EMA ${strategy.fast_period}/${strategy.slow_period}` : 'EMA Crossover';
            
            // Mode badge (DEMO/LIVE)
            const modeEl = document.getElementById('account-mode');
            if (conn.is_demo === true) {
                modeEl.innerHTML = '<span style="color: #00ff88; font-weight: bold;">🧪 DEMO</span>';
            } else if (conn.is_demo === false) {
                modeEl.innerHTML = '<span style="color: #ff4444; font-weight: bold;">⚠️ LIVE</span>';
            } else {
                modeEl.textContent = '-';
            }
            
            // Positions table
            updatePositionsTable(data.positions || []);
            
            // History table
            updateHistoryTable(data.orders_history || []);
            
            // Market Status table
            updateMarketStatus(data.market_overview || {});
            
            // Update time
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }
        
        function updateMarketStatus(marketData) {
            const tbody = document.getElementById('market-status-body');
            const symbols = Object.keys(marketData);
            
            if (symbols.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #666;">No market data yet</td></tr>';
                return;
            }

            // Group by category
            const categories = {};
            symbols.forEach(sym => {
                const cat = marketData[sym].category || 'Other';
                if (!categories[cat]) categories[cat] = [];
                categories[cat].push(sym);
            });

            // Define category order
            const catOrder = ['Crypto', 'Metals', 'Stocks', 'Indices', 'Forex', 'Commodities', 'Other'];
            
            let html = '';
            
            catOrder.forEach(cat => {
                if (categories[cat]) {
                    // Add Category Header
                    html += `<tr style="background: rgba(255, 255, 255, 0.1);"><td colspan="8" style="padding: 10px; font-weight: bold; color: #fff; letter-spacing: 1px;">${cat.toUpperCase()}</td></tr>`;
                    
                    // Sort symbols within category
                    categories[cat].sort();
                    
                    categories[cat].forEach(sym => {
                        const d = marketData[sym];
                        if (!d) return;
                        
                        const trendClass = d.trend === 'BULL' ? 'trend-bull' : (d.trend === 'BEAR' ? 'trend-bear' : 'trend-wait');
                        const trendIcon = d.trend === 'BULL' ? '🟢 BULL' : (d.trend === 'BEAR' ? '🔴 BEAR' : '⏳ WAIT');
                        
                        // Market status badge
                        const marketStatus = d.trade_allowed ? 
                            '<span style="color: #00ff88; font-weight: bold;">🟢 OPEN</span>' : 
                            '<span style="color: #ff4444; font-weight: bold;">🔴 CLOSED</span>';
                        
                        html += `
                            <tr>
                                <td style="font-weight: bold; color: #00d4ff; padding-left: 20px;">${sym}</td>
                                <td>${marketStatus}</td>
                                <td style="color: #00ff88; font-size: 0.85em;">${d.timeframe || 'M5'}</td>
                                <td style="color: #ffa500;">${d.fast_ema || 9}/${d.slow_ema || 41}</td>
                                <td>${d.price ? d.price.toFixed(2) : '-'}</td>
                                <td style="color: #888;">${d.min_volume || 0.01}</td>
                                <td><span class="trend-badge ${trendClass}">${trendIcon}</span></td>
                                <td>Momentum: ${d.momentum}</td>
                            </tr>
                        `;
                    });
                }
            });
            
            tbody.innerHTML = html;
        }
        
        function updatePositionsTable(positions) {
            const tbody = document.getElementById('positions-body');
            
            if (positions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: #666;">No open positions</td></tr>';
                return;
            }
            
            tbody.innerHTML = positions.map(p => `
                <tr>
                    <td style="font-weight: bold; color: #00d4ff;">${p.ticket}</td>
                    <td>${p.symbol}</td>
                    <td>${p.type}</td>
                    <td>${p.volume}</td>
                    <td>${p.price_open?.toFixed(5)}</td>
                    <td>${p.price_current?.toFixed(5)}</td>
                    <td>${p.sl?.toFixed(5) || '-'}</td>
                    <td style="color: #888;">$${(p.margin || 0).toFixed(2)}</td>
                    <td class="${p.profit >= 0 ? 'positive' : 'negative'}">$${p.profit?.toFixed(2)}</td>
                </tr>
            `).join('');
        }
        
        function updateHistoryTable(orders) {
            const tbody = document.getElementById('history-body');
            
            if (orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #666;">No recent orders</td></tr>';
                return;
            }
            
            tbody.innerHTML = orders.slice(-100).reverse().map(o => `
                <tr>
                    <td style="color: #666; font-size: 0.9em;">${o.ticket}</td>
                    <td>${o.time?.split('T')[1]?.split('.')[0] || o.time}</td>
                    <td>${o.symbol}</td>
                    <td>${o.type}</td>
                    <td>${o.volume}</td>
                    <td>${o.price?.toFixed(5)}</td>
                    <td class="${(o.profit || 0) >= 0 ? 'positive' : 'negative'}">$${(o.profit || 0).toFixed(2)}</td>
                </tr>
            `).join('');
        }
        
        function formatUptime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            if (h > 0) return `${h}h ${m}m`;
            if (m > 0) return `${m}m ${s}s`;
            return `${s}s`;
        }
        
        async function toggleTrading(enable) {
            const endpoint = enable ? '/api/trade/enable' : '/api/trade/disable';
            await fetch(API_BASE + endpoint, { method: 'POST' });
            fetchData();
        }
        
        async function setDirection(dir) {
            await fetch(API_BASE + '/api/direction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ direction: dir })
            });
            fetchData();
        }
        
        async function freezeTrading() {
            if (!confirm('FREEZE Trading?\\n\\nThis will:\\n- Stop opening NEW trades\\n- Keep existing positions running (TP/SL active)\\n\\nContinue?')) return;

            await fetch(API_BASE + '/api/trade/freeze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'Manual freeze' })
            });
            fetchData();
        }

        async function unfreezeTrading() {
            await fetch(API_BASE + '/api/trade/unfreeze', { method: 'POST' });
            fetchData();
        }

        async function panicCloseAll() {
            if (!confirm('PANIC: Close ALL positions immediately?')) return;
            if (!confirm('WARNING: This cannot be undone. Are you absolutely sure?')) return;

            await fetch(API_BASE + '/api/panic', { method: 'POST' });
            fetchData();
        }
        
        // Initial fetch and auto-refresh
        console.log('[Dashboard] Initializing dashboard...');
        console.log('[Dashboard] API_BASE:', API_BASE);
        fetchData();
        refreshInterval = setInterval(fetchData, REFRESH_SECONDS * 1000);
        countdownInterval = setInterval(updateCountdown, 1000);
        console.log('[Dashboard] Dashboard initialized. Auto-refresh every', REFRESH_SECONDS, 'seconds');
    </script>
</body>
</html>
"""


class WebDashboard:
    """
    Web Dashboard for EMAX Trading Engine
    
    Provides:
    - Real-time monitoring interface
    - Trading controls
    - Position management
    """
    
    def __init__(self, trading_engine=None, port: int = 8080):
        """
        Initialize Web Dashboard
        
        Args:
            trading_engine: TradingEngine instance (optional)
            port: Web server port
        """
        self.engine = trading_engine
        self.port = port
        self.app = None
        self.server_thread = None
        
        # Load Instance ID
        self.instance_id = "EMAX"
        try:
            import os
            # Default to directory name if possible
            current_dir_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # value-add: strip common prefixes if falling back to dir name
            if current_dir_name.startswith("start_"):
                current_dir_name = current_dir_name.replace("start_", "")
            
            config_id = None
            if self.engine:
                config_id = self.engine.config.get('telegram', {}).get('message_prefix')
            else:
                # Standalone mode - load from file
                import json
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'trading_config.json')
                with open(config_path, 'r') as f:
                    cfg = json.load(f)
                    config_id = cfg.get('telegram', {}).get('message_prefix')
            
            # Use config ID if valid, otherwise directory name
            if config_id and config_id != "EMAX":
                self.instance_id = config_id
            else:
                self.instance_id = current_dir_name
                
        except Exception:
            pass
        
        if FLASK_AVAILABLE:
            self._create_app()
        else:
            logger.error("Flask not available. Install with: pip install flask")
    
    def _create_app(self):
        """Create Flask application"""
        self.app = Flask(__name__)
        self.app.config['JSON_SORT_KEYS'] = False
        
        # Disable Flask's default logging
        import logging as log
        log.getLogger('werkzeug').setLevel(log.WARNING)
        
        # Routes
        @self.app.route('/')
        def index():
            logger.debug("[API] Dashboard page requested")
            # Manually interpolate instance_id because DASHBOARD_HTML is static
            html_content = DASHBOARD_HTML.replace('{self.instance_id}', self.instance_id)
            return render_template_string(html_content)
        
        @self.app.route('/api/status')
        def api_status():
            logger.debug("[API] /api/status requested")
            if self.engine:
                data = self.engine.get_dashboard_data()
                logger.debug(f"[API] Returning data with {len(data)} keys")
                return jsonify(clean_nans(data))
            logger.error("[API] Engine not connected")
            return jsonify({"error": "Engine not connected"})
        
        @self.app.route('/api/positions')
        def api_positions():
            if self.engine:
                return jsonify(self.engine.get_dashboard_data().get('positions', []))
            return jsonify([])
        
        @self.app.route('/api/history')
        def api_history():
            if self.engine:
                return jsonify(self.engine.get_dashboard_data().get('orders_history', []))
            return jsonify([])
        
        @self.app.route('/api/trade/enable', methods=['POST'])
        def api_enable_trading():
            if self.engine:
                self.engine.set_trading_enabled(True)
                return jsonify({"success": True, "trading_enabled": True})
            return jsonify({"error": "Engine not connected"})
        
        @self.app.route('/api/trade/disable', methods=['POST'])
        def api_disable_trading():
            if self.engine:
                self.engine.set_trading_enabled(False)
                return jsonify({"success": True, "trading_enabled": False})
            return jsonify({"error": "Engine not connected"})
        
        @self.app.route('/api/direction', methods=['POST'])
        def api_set_direction():
            if self.engine:
                data = request.get_json() or {}
                direction = data.get('direction', 'both')
                self.engine.set_direction(direction)
                return jsonify({"success": True, "direction": direction})
            return jsonify({"error": "Engine not connected"})
        
        @self.app.route('/api/panic', methods=['POST'])
        def api_panic():
            if self.engine:
                result = self.engine.panic_close_all()
                return jsonify(result)
            return jsonify({"error": "Engine not connected"})

        @self.app.route('/api/trade/freeze', methods=['POST'])
        def api_freeze_trading():
            if self.engine:
                data = request.get_json() or {}
                reason = data.get('reason', 'Manual freeze')
                self.engine.freeze_trading(reason)
                return jsonify({"success": True, "trading_frozen": True, "reason": reason})
            return jsonify({"error": "Engine not connected"})

        @self.app.route('/api/trade/unfreeze', methods=['POST'])
        def api_unfreeze_trading():
            if self.engine:
                self.engine.unfreeze_trading()
                return jsonify({"success": True, "trading_frozen": False})
            return jsonify({"error": "Engine not connected"})
    
    def start(self, threaded: bool = True):
        """
        Start the web dashboard
        
        Args:
            threaded: Run in background thread
        """
        if not FLASK_AVAILABLE or not self.app:
            logger.error("Cannot start dashboard: Flask not available")
            return
        
        if threaded:
            self.server_thread = Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            logger.info(f"Dashboard started at http://localhost:{self.port}")
        else:
            self._run_server()
    
    def _run_server(self):
        """Run Flask server"""
        self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
    
    def stop(self):
        """Stop the dashboard (note: Flask doesn't have clean shutdown)"""
        logger.info("Dashboard stop requested (will stop with main thread)")


def run_standalone():
    """Run dashboard standalone for testing"""
    import json
    import os
    
    print("Starting Web Dashboard in standalone mode...")
    
    # Load port from config
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'trading_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        port = config.get('dashboard', {}).get('web_port', 8080)
    except Exception as e:
        print(f"Failed to load config, using default 8080: {e}")
        port = 8080
        
    print(f"Open http://localhost:{port} in your browser")
    
    dashboard = WebDashboard(trading_engine=None, port=port)
    dashboard.start(threaded=False)


if __name__ == "__main__":
    run_standalone()
