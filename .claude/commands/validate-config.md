---
description: Validate trading configuration and system readiness
---

Validate trading configuration before starting the engine.

## Configuration Checks

1. **Validate JSON Syntax**
```bash
python3 -m json.tool config/trading_config.json > /dev/null && echo "✓ JSON valid"
```

2. **Check Symbol Settings**
```bash
cat config/trading_config.json | jq -r '.symbols.enabled[] as $sym | "\($sym): \(.symbols.settings[$sym].timeframe) - EMA \(.symbols.settings[$sym].fast_ema)/\(.symbols.settings[$sym].slow_ema)"'
```

3. **Verify MT5 Connection**
```bash
wine python -c "import MetaTrader5 as mt5; mt5.initialize(); print('MT5:', 'Connected' if mt5.terminal_info() else 'Failed'); mt5.shutdown()"
```

4. **Test Dashboard Template**
```bash
python3 dashboard/validate_dashboard.py
```

5. **Check File Permissions**
```bash
ls -la menu.sh reset_dashboard.sh | grep -E "^-rwx"
```

## Pre-Flight Checklist

- [ ] JSON config is valid
- [ ] All enabled symbols have settings
- [ ] MT5 is running and connected
- [ ] Dashboard template validates
- [ ] Scripts are executable
- [ ] Python dependencies installed (`wine pip list`)
