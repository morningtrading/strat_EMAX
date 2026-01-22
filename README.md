# 🚀 EMAX Trading Engine

**EMA Crossover Trading System for MetaTrader 5 on Linux**

A fully automated trading engine that uses EMA (Exponential Moving Average) crossovers to generate buy and sell signals, running on Linux through Wine.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![MT5](https://img.shields.io/badge/Platform-MetaTrader5-green.svg)](https://www.metatrader5.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📊 Features

### Trading Strategy
- **EMA Crossover**: Fast EMA (9) / Slow EMA (41) crossover signals
- **Direction Control**: Trade both, long-only, or short-only
- **Duplicate Prevention**: Prevents multiple signals on same candle
- **Session Filter**: Trade only during London/NY overlap sessions
- **Spread Filter**: Skip trades when spread is too wide

### Risk Management
- **Position Sizing**: Based on max margin limit ($10 default)
- **Stop Loss**: Fixed (50% of margin) or ATR-based
- **Daily Loss Limit**: Stop trading at 75% daily loss
- **Demo Account Only**: Safety block for real accounts

### Dashboard & Monitoring
- **Web Dashboard**: Real-time browser-based monitoring
- **Position Tracking**: Open positions with live P&L
- **Order History**: Last 20 orders with details
- **Trading Controls**: Enable/disable, direction, panic button

### Notifications
- **Telegram Alerts**: Trade entry/exit notifications
- **Error Alerts**: Connection and order failures
- **Daily Summary**: End-of-day P&L report

---

## 🏗️ Architecture

```
start_EMAX/
├── config/
│   └── trading_config.json      # All parameters (editable)
├── core/
│   ├── mt5_connector.py         # MT5 connection manager
│   ├── ema_strategy.py          # EMA crossover logic
│   ├── position_manager.py      # Entry/exit/sizing
│   └── telegram_notifier.py     # Telegram alerts
├── dashboard/
│   └── web_dashboard.py         # Flask web UI
├── tests/
│   └── test_ema_strategy.py     # Unit tests
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

---

## ⚡ Quick Start

### Prerequisites
1. **Wine** installed on Linux
2. **Python 3.10+** installed in Wine
3. **MetaTrader 5** installed in Wine (Axi broker)
4. **MT5 logged in** to a demo account

### Installation

```bash
# 1. Clone/navigate to the project
cd ~/projects/axibot/start_EMAX

# 2. Install dependencies in Wine Python
wine pip install -r requirements.txt

# 3. Start MT5 terminal
wine "C:/Program Files/Axi MetaTrader 5 Terminal/terminal64.exe" &

# 4. Wait for MT5 to login, then start the engine
wine python main.py
```

### Access Dashboard
Open in browser: **http://localhost:8080**

---

## ⚙️ Configuration

Edit `config/trading_config.json`:

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `account.demo_only` | `true` | Block real accounts (safety) |
| `account.max_margin_per_trade_usd` | `10.0` | Max margin per trade |
| `account.max_daily_loss_percent` | `75.0` | Stop at this daily loss |
| `strategy.fast_ema_period` | `9` | Fast EMA period |
| `strategy.slow_ema_period` | `41` | Slow EMA period |
| `strategy.direction` | `"both"` | Trading direction |
| `symbols.enabled` | `["XAGUSD"]` | Active symbols |
| `stop_loss.type` | `"fixed"` | SL type (fixed/atr) |
| `stop_loss.fixed_percent_of_margin` | `50.0` | SL as % of margin |
| `session_filter.enabled` | `true` | Trade only during sessions |
| `telegram.enabled` | `false` | Enable Telegram alerts |

### Available Symbols
- XAUUSD (Gold)
- XAGUSD (Silver) - **default**
- NAS100.fs (NASDAQ)
- US500.fs (S&P 500)
- GER40 (DAX)
- FRA40 (CAC40)

---

## 📱 Dashboard Controls

| Button | Action |
|--------|--------|
| ▶️ Enable Trading | Start generating and executing signals |
| ⏸️ Disable Trading | Stop trading but keep monitoring |
| 📊 Direction Selector | Choose: Both / Long Only / Short Only |
| 🚨 PANIC | Close ALL positions immediately |

---

## 🧪 Running Tests

```bash
# Run all tests
wine python tests/test_ema_strategy.py

# Expected output:
# Ran 13 tests in 0.019s
# OK
```

---

## 📊 Trading Logic

### Entry Signals
- **BUY**: Fast EMA crosses ABOVE Slow EMA
- **SELL**: Fast EMA crosses BELOW Slow EMA

### Exit Signals
- **EMA Cross**: Opposite crossover
- **Price Deviation**: Price 0.1% below/above slow EMA

### Stop Loss
- **Fixed**: 50% of margin used ($5 on $10 trade)
- **ATR-based**: 1.5x ATR (configurable)

---

## 🔧 Troubleshooting

### MT5 Connection Failed
```
Error: IPC initialize failed, MetaTrader 5 x64 not found
```
**Solution**: Start MT5 terminal first: `wine terminal64.exe`

### Real Account Blocked
```
Error: Real account blocked - demo_only mode
```
**Solution**: This is a safety feature. Use a demo account or set `demo_only: false` (at your own risk).

### Telegram Not Sending
**Solution**: 
1. Create bot with @BotFather
2. Add `bot_token` and `chat_id` to config
3. Set `telegram.enabled: true`

---

## 📝 Development Guidelines

1. Always test on demo accounts
2. Run syntax check before deploying: `wine python -m py_compile main.py`
3. Commit to git before major changes
4. Update this README with code changes
5. Use config file for all parameters

---

## 📜 License

MIT License - Use at your own risk. Trading involves financial risk.

---

## 🤝 Support

For issues, check the logs in `trading_engine.log` or the dashboard.

**Built with ❤️ for algorithmic trading on Linux**
