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
    <title>EMAX Trading Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
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
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 EMAX Trading Dashboard</h1>
        <div class="status">
            <span class="status-indicator" id="connection-indicator"></span>
            <span id="connection-status">Connecting...</span>
            | <strong>Timeframe:</strong> <span id="timeframe" style="color: #00d4ff;">M5</span>
            | Uptime: <span id="uptime">0s</span>
        </div>
        <div class="status" style="margin-top: 8px; font-size: 0.95em;">
            ⏱️ Next refresh: <span id="countdown" style="color: #00ff88; font-weight: bold;">5</span>s
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
        
        <select class="direction-select" id="direction-select" onchange="setDirection(this.value)">
            <option value="both">📊 Both Directions</option>
            <option value="long">📈 Long Only</option>
            <option value="short">📉 Short Only</option>
        </select>
        
        <button class="btn panic-btn" onclick="panicCloseAll()">
            🚨 PANIC - Close All
        </button>
    </div>
    
    <div class="grid">
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
        
        <!-- Daily Stats -->
        <div class="card">
            <h2><span class="icon">📊</span> Daily Stats</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-label">Today's P&L</div>
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
        </div>
        
        <!-- Market Status -->
        <div class="card" style="grid-column: span 2;">
            <h2><span class="icon">🌍</span> Market Status</h2>
            <table class="market-table">
                <thead>
                    <tr>
                        <th style="width: 20%;">Symbol</th>
                        <th>Status</th>
                        <th>Trend (M5)</th>
                        <th>Momentum</th>
                    </tr>
                </thead>
                <tbody id="market-status-body">
                    <tr><td colspan="4" style="text-align: center; color: #666;">Loading market data...</td></tr>
                </tbody>
            </table>
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
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Volume</th>
                    <th>Entry</th>
                    <th>Current</th>
                    <th>SL</th>
                    <th>P&L</th>
                </tr>
            </thead>
            <tbody id="positions-body">
                <tr><td colspan="7" style="text-align: center; color: #666;">No open positions</td></tr>
            </tbody>
        </table>
    </div>
    
    <!-- Order History -->
    <div class="card" style="margin-top: 20px;">
        <h2><span class="icon">📜</span> Recent Orders (Last 20)</h2>
        <table class="positions-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Volume</th>
                    <th>Price</th>
                    <th>P&L</th>
                </tr>
            </thead>
            <tbody id="history-body">
                <tr><td colspan="6" style="text-align: center; color: #666;">No recent orders</td></tr>
            </tbody>
        </table>
    </div>
    
    <div class="refresh-time">
        Last updated: <span id="last-update">-</span>
        | Symbol: <span id="active-symbol" style="color: #00d4ff;">XAGUSD</span>
        | Refresh: <span id="refresh-rate">5</span>s
    </div>
    
    <script>
        const API_BASE = '';
        let refreshInterval;
        let countdownInterval;
        let countdown = 5;
        const REFRESH_SECONDS = 5;
        
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
                const response = await fetch(API_BASE + '/api/status');
                const data = await response.json();
                updateDashboard(data);
                document.getElementById('last-check-status').textContent = '✅ OK';
                document.getElementById('last-check-status').style.color = '#00ff88';
            } catch (error) {
                console.error('Failed to fetch data:', error);
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('connection-indicator').className = 'status-indicator status-disconnected';
                document.getElementById('last-check-status').textContent = '❌ Error';
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
            
            // Config display
            document.getElementById('config-display').textContent = JSON.stringify({
                trading_enabled: engine.trading_enabled,
                direction: engine.direction,
                symbols: engine.enabled_symbols,
                sl_type: manager.sl_type,
                max_margin: manager.max_margin_per_trade
            }, null, 2);
            
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
            const symbols = Object.keys(marketData).sort();
            
            if (symbols.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #666;">No market data yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = symbols.map(sym => {
                const d = marketData[sym];
                if (!d) return '';
                
                const trendClass = d.trend === 'BULL' ? 'trend-bull' : (d.trend === 'BEAR' ? 'trend-bear' : '');
                const trendIcon = d.trend === 'BULL' ? '🟢 BULL' : (d.trend === 'BEAR' ? '🔴 BEAR' : '-');
                
                let momIcon = '➡️';
                if (d.momentum === 'INCREASING') momIcon = '↗️';
                if (d.momentum === 'DECREASING') momIcon = '↘️';
                
                return `
                    <tr>
                        <td style="font-weight: bold; color: #00d4ff;">${sym}</td>
                        <td>${d.price ? d.price.toFixed(2) : '-'}</td>
                        <td><span class="trend-badge ${trendClass}">${trendIcon}</span></td>
                        <td>${momIcon} ${d.momentum}</td>
                    </tr>
                `;
            }).join('');
        }
        
        function updatePositionsTable(positions) {
            const tbody = document.getElementById('positions-body');
            
            if (positions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #666;">No open positions</td></tr>';
                return;
            }
            
            tbody.innerHTML = positions.map(p => `
                <tr>
                    <td>${p.symbol}</td>
                    <td>${p.type}</td>
                    <td>${p.volume}</td>
                    <td>${p.price_open?.toFixed(5)}</td>
                    <td>${p.price_current?.toFixed(5)}</td>
                    <td>${p.sl?.toFixed(5) || '-'}</td>
                    <td class="${p.profit >= 0 ? 'positive' : 'negative'}">$${p.profit?.toFixed(2)}</td>
                </tr>
            `).join('');
        }
        
        function updateHistoryTable(orders) {
            const tbody = document.getElementById('history-body');
            
            if (orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #666;">No recent orders</td></tr>';
                return;
            }
            
            tbody.innerHTML = orders.slice(-20).reverse().map(o => `
                <tr>
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
        
        async function panicCloseAll() {
            if (!confirm('⚠️ PANIC: Close ALL positions immediately?')) return;
            if (!confirm('🚨 This cannot be undone. Are you absolutely sure?')) return;
            
            await fetch(API_BASE + '/api/panic', { method: 'POST' });
            fetchData();
        }
        
        // Initial fetch and auto-refresh
        fetchData();
        refreshInterval = setInterval(fetchData, REFRESH_SECONDS * 1000);
        countdownInterval = setInterval(updateCountdown, 1000);
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
            return render_template_string(DASHBOARD_HTML)
        
        @self.app.route('/api/status')
        def api_status():
            if self.engine:
                data = self.engine.get_dashboard_data()
                return jsonify(clean_nans(data))
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
    print("Starting Web Dashboard in standalone mode...")
    print(f"Open http://localhost:8080 in your browser")
    
    dashboard = WebDashboard(trading_engine=None, port=8080)
    dashboard.start(threaded=False)


if __name__ == "__main__":
    run_standalone()
