# CLAUDE.md - AI Assistant Guidelines

> **For Claude Code and other AI assistants working on this project**

## Project Overview

**EMAX Trading Engine** - Multi-symbol EMA crossover trading bot for MT5 with web dashboard.

- **Language**: Python 3.10 (running under Wine for MT5 compatibility)
- **Framework**: Flask (web dashboard)
- **Environment**: Linux + Wine + MetaTrader 5
- **Architecture**: Trading engine + Web dashboard + Telegram notifications

## Critical Safety Rules

1. **NEVER** modify `demo_only: true` in config without explicit user confirmation
2. **NEVER** change position sizes without validation
3. **ALWAYS** test changes on demo account first
4. **ALWAYS** validate syntax before claiming "fixed"
5. **ALWAYS** use curl to test after making dashboard changes
6. **NEVER** use config fallbacks (e.g., `.get('key', default)`). ALWAYS raise explicit errors if config is missing.

## Common Issues & Solutions

### Dashboard Not Connecting

**Systematic Debugging Order** (30 seconds):

```bash
# 1. Validate JavaScript syntax (catches 90% of issues)
curl -s http://localhost:8080/ | sed -n '/<script>/,/<\/script>/p' | sed '1d;$d' > /tmp/d.js
node --check /tmp/d.js
# ✅ Should say: (no output = valid) or show syntax error

# 2. Test API endpoint
curl -s http://localhost:8080/api/status | jq -r '.connection_status.connected'
# ✅ Should return: true

# 3. Check engine is running
ps aux | grep "python.*main.py" | grep -v grep
# ✅ Should show: wine python main.py process
```

**Common Root Causes:**
1. **JavaScript syntax errors** (emoji encoding, unescaped newlines)
2. **Duplicate const declarations** in same scope
3. **Engine not running** or crashed
4. **MT5 not connected**

**Prevention:**
- Run `python3 dashboard/validate_dashboard.py` before starting
- Never use emojis in JavaScript strings
- Add debug logging for all changes
- Test with curl after every change

### MT5 Connection Issues

```bash
# Check MT5 process
ps aux | grep terminal64

# Test MT5 Python binding
wine python -c "import MetaTrader5 as mt5; print(mt5.initialize())"

# Check MT5 settings: Allow algorithmic trading must be enabled
```

## File Structure

```
start_EMAX/
├── main.py                    # Entry point - start here
├── config/trading_config.json # All settings - validate before changing
│
├── core/                      # Core logic - well-tested
│   ├── ema_strategy.py        # EMA crossover logic
│   ├── position_manager.py    # Risk management
│   ├── mt5_connector.py       # MT5 API wrapper
│   └── telegram_notifier.py   # Notifications
│
├── dashboard/                 # Web interface
│   ├── web_dashboard.py       # Flask server + HTML template
│   ├── validate_dashboard.py # Syntax validator ⭐ RUN THIS
│   └── DEBUGGING.md          # Detailed debugging guide ⭐ READ THIS
│
├── .claude/commands/          # Claude Code commands
│   ├── debug-dashboard.md    # /debug-dashboard
│   └── validate-config.md    # /validate-config
│
└── README.md                 # User-facing documentation
```

## Development Workflow

### Before Making Changes

1. **Understand the change request fully**
2. **Locate the relevant files** (see structure above)
3. **Read existing code** to understand context
4. **Check for related test files**

### Making Changes

1. **Read the file first** - always use Read tool before Edit
2. **Make minimal changes** - don't refactor unnecessarily
3. **Preserve exact indentation** - respect existing style
4. **Add logging** if debugging - prefix with `[ComponentName]`
5. **Never add emojis** to JavaScript strings

### After Making Changes

1. **Verify Python Syntax (CRITICAL)**:
   ```bash
   python3 -m py_compile main.py
   python3 -m py_compile core/ema_strategy.py
   # ... check any modified file
   ```

2. **Verify Python Runtime (CRITICAL)**:
   *After editing logic or config, perform a Dry Run:*
   ```bash
   timeout 10 wine python main.py
   # Check logs for "IndentationError", "TypeError", or immediate crash.
   ```

3. **Validate Dashboard Syntax**:
   ```bash
   python3 dashboard/validate_dashboard.py
   
   # For JavaScript
   curl -s http://localhost:8080/ | sed -n '/<script>/,/<\/script>/p' | sed '1d;$d' > /tmp/d.js
   node --check /tmp/d.js
   ```

4. **Verify in logs**:
   ```bash
   tail -f trading_engine.log
   ```

5. **Only then** report to user that it's fixed

## Dashboard-Specific Guidelines

### Known Pitfalls

1. **Emojis in JavaScript strings break parsing**
   - ❌ `confirm('❄️ Freeze?')`
   - ✅ `confirm('FREEZE?')`
   - Reason: Unicode encoding issues in template strings

2. **Duplicate const declarations**
   - Each function has its own scope
   - But within a function, can't declare `const x` twice
   - Check with: `grep "const manager" file | wc -l`

3. **Unescaped newlines**
   - ❌ `'line1\nline2'` (literal newline in source)
   - ✅ `'line1\\nline2'` (escaped in string)

4. **Flask template rendering**
   - HTML is embedded in Python string
   - Triple-quotes preserve formatting
   - Engine restart required for changes

### Adding Debug Logging

```python
# In web_dashboard.py Flask routes
logger.debug(f"[API] /api/status requested")
logger.debug(f"[API] Returning data with {len(data)} keys")

# In JavaScript (browser console)
console.log('[Dashboard] Fetching data from /api/status');
console.log('[Dashboard] Data received:', Object.keys(data));
```

### Testing Dashboard Changes

```bash
# 1. Validate template
python3 dashboard/validate_dashboard.py

# 2. Restart engine
pkill -f "python.*main.py" && sleep 2
nohup wine python main.py > /dev/null 2>&1 &

# 3. Test JS syntax
curl -s http://localhost:8080/ | sed -n '/<script>/,/<\/script>/p' | sed '1d;$d' > /tmp/d.js
node --check /tmp/d.js && echo "✓ Valid"

# 4. Test API
curl -s http://localhost:8080/api/status | jq -r '.connection_status.connected'

# 5. Check browser console (F12)
# Look for [Dashboard] log messages
```

## Trading Logic Guidelines

### Position Manager

- **Don't modify** stop loss logic without backtesting
- **Don't change** position sizing without margin validation
- **Don't touch** session filters without understanding market hours

### EMA Strategy

- **Don't change** EMA calculation (validated)
- **Don't modify** crossover detection logic
- **Configuration only** - change EMA periods in config, not code

### MT5 Connector

- **Don't change** order placement logic (well-tested)
- **Don't modify** position closing (critical for P&L)
- **Add logging** if debugging, don't change behavior

## Configuration Changes

### Safe Changes (via config/trading_config.json)

- ✅ EMA periods per symbol
- ✅ Timeframes per symbol
- ✅ Session trading hours
- ✅ Dashboard port

### Unsafe Changes (need validation)

- ⚠️ Position sizes (validate margin)
- ⚠️ Stop loss settings (backtest first)
- ⚠️ Max daily loss (risk management)

### Never Change Without Explicit Approval

- 🚫 `demo_only: false` (enables live trading)
- 🚫 Core trading logic in Python files
- 🚫 MT5 connection parameters

## Debugging Tools

### Slash Commands (Claude Code)

```bash
/debug-dashboard   # Run systematic dashboard checks
/validate-config   # Validate configuration files
```

### Manual Commands

```bash
# Quick status check
curl -s http://localhost:8080/api/status | jq -r '"Connected: \(.connection_status.connected), Balance: $\(.account_info.balance)"'

# Watch logs live
tail -f trading_engine.log | grep -E "ERROR|WARNING|TRADE|API"

# Check all processes
ps aux | grep -E "terminal64|python.*main.py" | grep -v grep

# Test MT5 connection
wine python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.terminal_info()); mt5.shutdown()"
```

## Error Messages You'll See

### Normal (Ignore)
```
Wine: fixme:...  (harmless Wine debug messages)
```

### Warning (Check but non-critical)
```
[WARNING] Symbol XAGUSD: Spread too high (85 > 80)
[WARNING] Session filter: Market closed
```

### Error (Must fix)
```
[ERROR] MT5 connection failed
[ERROR] Failed to place order
SyntaxError: Invalid or unexpected token  (JavaScript)
json.decoder.JSONDecodeError              (Config file)
```

## Useful References

- **Trading Logic**: See `core/ema_strategy.py` docstrings
- **Dashboard API**: See `dashboard/web_dashboard.py` routes
- **Configuration**: See `config/trading_config.json` comments
- **Debugging**: See `dashboard/DEBUGGING.md` ⭐
- **Architecture**: See `README.md` flowcharts

## Response Style

When helping users:

1. **Be systematic** - follow debugging checklist
2. **Validate before claiming "fixed"** - always test with curl
3. **Show your work** - share test output
4. **Explain why** - don't just fix, teach
5. **Add prevention** - suggest validation tools/scripts

## Example: Good vs Bad Response

### ❌ Bad
```
I've fixed the dashboard connection issue.
It should work now.
```

### ✅ Good
```
I found the issue: emoji character in JavaScript string on line 836
broke the parser.

Fixed by removing emoji from confirm() dialog.

Testing the fix:
1. JS syntax: ✓ Valid
2. API endpoint: ✓ Responding (Balance: $816.43)
3. Engine running: ✓ PID 7760

Please refresh your browser (Ctrl+Shift+R) to load the new code.
```

## Lessons from Recent Debugging

**The Emoji Bug Incident** (2026-01-28):

- **Problem**: Dashboard stuck on "Connecting..."
- **Root cause**: Emoji in JS `confirm()` broke parsing
- **Time to fix**: Too long (multiple iterations)
- **Why it took long**:
  1. Assumed cache issue instead of syntax error
  2. Didn't validate before claiming fixed
  3. Fixed symptom (duplicate const) not root cause
  4. No systematic debugging approach

- **What we learned**:
  1. Always validate JS syntax first
  2. Test with curl after every change
  3. Never use emojis in JavaScript strings
  4. Add validation scripts (now created)
  5. Systematic debugging > guesswork

**Prevention added**:
- `validate_dashboard.py` - catches syntax errors
- Enhanced logging - browser + Flask
- `DEBUGGING.md` - systematic approach
- This file (`CLAUDE.md`) - guidelines for AI

## Quick Decision Tree

```
User reports dashboard issue
│
├─→ "Connecting..." stuck
│   ├─→ Run JS syntax check (30s)
│   ├─→ Check API endpoint (10s)
│   └─→ Verify engine running (5s)
│
├─→ "Error" or "Disconnected"
│   ├─→ Check MT5 running
│   ├─→ Check engine logs
│   └─→ Test MT5 connection
│
├─→ Stale data / not updating
│   ├─→ Hard refresh browser
│   ├─→ Check API returns new data
│   └─→ Verify auto-refresh working
│
└─→ Button/feature not working
    ├─→ Check browser console (F12)
    ├─→ Check Flask route exists
    └─→ Test API endpoint with curl
```

## Contact & Updates

- **Last Updated**: 2026-01-28
- **Major Changes**: Added dashboard validation + debugging tools
- **Next Review**: When major features added

---

**Remember**: Measure twice, cut once. Test everything. Never assume it works - prove it works.
