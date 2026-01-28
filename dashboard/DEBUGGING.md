# Dashboard Debugging Guide

## Lessons Learned from the Emoji Bug

### The Problem
Dashboard showed "Connecting..." but never loaded data. Root cause: Emoji characters in JavaScript `confirm()` strings broke JS parsing.

### Why it took so long to diagnose:
1. **Assumed connection issue** instead of syntax error
2. **Didn't validate before claiming "fixed"**
3. **Fixed one bug, missed the real bug** (duplicate const vs emoji encoding)
4. **No systematic debugging approach**

---

## Quick Diagnosis Checklist

When dashboard shows "Connecting..." or doesn't update:

### 1. Check JavaScript Syntax (30 seconds)
```bash
# Extract and validate JavaScript from served HTML
curl -s http://localhost:8080/ | sed -n '/<script>/,/<\/script>/p' | sed '1d;$d' > /tmp/dash.js
node --check /tmp/dash.js
```

✅ If valid: "✓ JavaScript syntax is VALID"
❌ If invalid: Shows exact line/error

### 2. Check API Endpoint (10 seconds)
```bash
# Test if backend is responding
curl -s http://localhost:8080/api/status | jq -r '.connection_status.connected'
```

✅ Should return: `true`
❌ If fails: Engine not running or not connected to MT5

### 3. Check Browser Console (10 seconds)
Open browser DevTools (F12) → Console tab
- Look for red error messages
- Check Network tab for failed requests

### 4. Run Template Validator (5 seconds)
```bash
python3 dashboard/validate_dashboard.py
```

Catches:
- Duplicate const declarations
- Unescaped newlines in strings
- Emojis in JavaScript strings
- Missing API endpoints

---

## Improved Architecture

### Before (Problems):
```
web_dashboard.py (1000+ lines)
├── HTML template embedded as string
├── CSS embedded in template
└── JavaScript embedded in template
    → Hard to test
    → No syntax validation
    → Emojis break encoding
```

### After (Recommended):
```
dashboard/
├── web_dashboard.py          # Flask routes only
├── templates/
│   └── dashboard.html         # HTML template
├── static/
│   ├── css/dashboard.css     # Styles
│   └── js/dashboard.js       # JavaScript (testable!)
├── validate_dashboard.py     # Pre-flight checks
└── DEBUGGING.md              # This file
```

**Benefits:**
- JavaScript can be tested with `node --check`
- Separate files = better IDE support
- No encoding issues with emojis in HTML
- Easy to add automated tests

---

## Debug Logging Added

### Browser Console Logs
Now the dashboard logs:
```javascript
[Dashboard] Initializing dashboard...
[Dashboard] API_BASE:
[Dashboard] Fetching data from /api/status
[Dashboard] Response status: 200
[Dashboard] Data received: (9) ['connection_status', 'account_info', ...]
[Dashboard] Dashboard initialized. Auto-refresh every 5 seconds
```

### Server Logs
Flask now logs:
```
[API] Dashboard page requested
[API] /api/status requested
[API] Returning data with 9 keys
```

To enable verbose logging:
```python
# In main.py or web_dashboard.py
logging.getLogger('WebDashboard').setLevel(logging.DEBUG)
```

---

## Testing Strategy

### Pre-Start Validation
```bash
# Before starting engine:
python3 dashboard/validate_dashboard.py && echo "Safe to start"
```

### Runtime Testing
```bash
# While running:
# 1. Test API
curl -s http://localhost:8080/api/status | jq '.connection_status.connected'

# 2. Validate JS syntax
curl -s http://localhost:8080/ | sed -n '/<script>/,/<\/script>/p' | sed '1d;$d' > /tmp/d.js && node --check /tmp/d.js

# 3. Check logs
tail -f trading_engine.log | grep -E "\[API\]|\[Dashboard\]"
```

### Automated Tests (TODO)
```python
# tests/test_dashboard.py
def test_dashboard_loads():
    response = client.get('/')
    assert response.status_code == 200

def test_api_status_returns_data():
    response = client.get('/api/status')
    assert 'connection_status' in response.json()

def test_javascript_syntax():
    """Extract and validate JS has no syntax errors"""
    # Use esprima or similar to parse JS
```

---

## Common Issues & Solutions

### Issue: "Connecting..." forever
**Diagnosis:**
1. Open F12 console → Check for JS errors
2. `curl http://localhost:8080/api/status` → Check API works

**Solutions:**
- JS syntax error → Run validator
- API not responding → Check engine is running
- CORS error → Check same origin (localhost:8080)

### Issue: Stale data in browser
**Solution:** Hard refresh (Ctrl+Shift+R) or incognito mode

### Issue: Dashboard changes not reflected
**Solution:** Restart engine (changes to Python need restart):
```bash
pkill -f "python.*main.py"
nohup wine python main.py > /dev/null 2>&1 &
```

### Issue: Emojis break JavaScript
**Solution:** Never use emojis in JS string literals. Use them in:
- ✅ HTML text content
- ✅ CSS content
- ❌ JavaScript strings (breaks encoding)

---

## Prevention Checklist

Before committing dashboard changes:

- [ ] Run `python3 dashboard/validate_dashboard.py`
- [ ] Test `curl http://localhost:8080/` returns HTML
- [ ] Test `curl http://localhost:8080/api/status` returns JSON
- [ ] Extract JS and run `node --check`
- [ ] Open in browser and check console (F12) for errors
- [ ] Test all buttons/controls work

---

## Future Improvements

1. **Split files**: Move JS/CSS to separate files
2. **Add unit tests**: Test each function independently
3. **Add integration tests**: Test full dashboard flow
4. **CI/CD validation**: Run validator on every commit
5. **Source maps**: For easier debugging of minified code
6. **Error boundary**: Catch and display JS errors in UI
7. **Health check endpoint**: `/health` returns dashboard status
8. **Debug mode**: Add `?debug=1` to show detailed info

---

## Quick Reference

**Validate before start:**
```bash
python3 dashboard/validate_dashboard.py
```

**Debug during runtime:**
```bash
# Check JS syntax
curl -s http://localhost:8080/ | sed -n '/<script>/,/<\/script>/p' | sed '1d;$d' | node --check

# Check API
curl -s http://localhost:8080/api/status | jq

# View logs
tail -f trading_engine.log
```

**Browser debugging:**
- F12 → Console (JS errors)
- F12 → Network (API calls)
- Ctrl+Shift+R (Hard refresh)
