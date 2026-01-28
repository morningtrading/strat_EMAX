---
description: Debug dashboard issues with systematic checks
---

Run systematic dashboard diagnostics to identify issues quickly.

## Steps

1. **Check JavaScript Syntax**
```bash
curl -s http://localhost:8080/ | sed -n '/<script>/,/<\/script>/p' | sed '1d;$d' > /tmp/dash.js
node --check /tmp/dash.js
```

2. **Validate Dashboard Template**
```bash
python3 dashboard/validate_dashboard.py
```

3. **Test API Endpoint**
```bash
curl -s http://localhost:8080/api/status | jq -r '.connection_status.connected, .account_info.balance'
```

4. **Check Engine Process**
```bash
ps aux | grep "python.*main.py" | grep -v grep
```

5. **Check Port Binding**
```bash
netstat -tlnp 2>/dev/null | grep 8080 || ss -tlnp | grep 8080
```

6. **View Live Logs**
```bash
tail -f trading_engine.log | grep -E "\[API\]|\[Dashboard\]|ERROR"
```

## Quick Fix Commands

**Restart Engine:**
```bash
pkill -f "python.*main.py" && sleep 2
nohup wine python main.py > /dev/null 2>&1 &
```

**Test in Browser:**
- Open http://localhost:8080
- Press F12 for console
- Look for `[Dashboard]` log messages
