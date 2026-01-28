#!/usr/bin/env python3
"""
Dashboard Template Validator
Run this before starting the engine to catch JS/HTML errors
"""
import re
import sys
from pathlib import Path

def validate_dashboard_template():
    """Validate dashboard HTML template for common issues"""
    errors = []
    warnings = []

    template_path = Path(__file__).parent / 'web_dashboard.py'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract DASHBOARD_HTML
    match = re.search(r'DASHBOARD_HTML = """(.+?)"""', content, re.DOTALL)
    if not match:
        errors.append("Could not extract DASHBOARD_HTML template")
        return errors, warnings

    html = match.group(1)

    # Extract JavaScript
    js_match = re.search(r'<script>(.+?)</script>', html, re.DOTALL)
    if not js_match:
        errors.append("No <script> block found")
        return errors, warnings

    js_code = js_match.group(1)

    # Check for duplicate const declarations
    const_pattern = r'const\s+(\w+)\s*='
    const_vars = re.findall(const_pattern, js_code)

    # Group by scope (simple check - assumes functions create new scopes)
    function_starts = [m.start() for m in re.finditer(r'function\s+\w+\s*\(', js_code)]
    function_starts.insert(0, 0)  # Global scope

    for i, start_pos in enumerate(function_starts):
        end_pos = function_starts[i+1] if i+1 < len(function_starts) else len(js_code)
        scope_code = js_code[start_pos:end_pos]

        scope_consts = re.findall(const_pattern, scope_code)
        duplicates = [var for var in scope_consts if scope_consts.count(var) > 1]

        if duplicates:
            errors.append(f"Duplicate const declarations in same scope: {set(duplicates)}")

    # Check for unescaped newlines in strings
    if re.search(r"'[^']*\n[^']*'", js_code) or re.search(r'"[^"]*\n[^"]*"', js_code):
        errors.append("Unescaped newline in string literal (use \\n)")

    # Check for problematic emoji/unicode in JS strings
    emoji_in_strings = re.findall(r"['\"]([^'\"]*[\U0001F300-\U0001F9FF][^'\"]*)['\"]", js_code)
    if emoji_in_strings:
        warnings.append(f"Emojis found in JS strings (may cause encoding issues): {emoji_in_strings[:3]}")

    # Check for missing semicolons in critical places
    if re.search(r'const\s+\w+\s*=\s*[^;]+\n\s*const', js_code):
        warnings.append("Possible missing semicolons between const declarations")

    # Check API endpoints are defined
    required_endpoints = ['/api/status', '/api/trade/enable', '/api/trade/disable']
    for endpoint in required_endpoints:
        if endpoint not in html:
            errors.append(f"Missing API endpoint reference: {endpoint}")

    return errors, warnings

if __name__ == "__main__":
    print("Validating dashboard template...")
    errors, warnings = validate_dashboard_template()

    if errors:
        print("\n❌ ERRORS:")
        for err in errors:
            print(f"  - {err}")

    if warnings:
        print("\n⚠️  WARNINGS:")
        for warn in warnings:
            print(f"  - {warn}")

    if not errors and not warnings:
        print("✅ Dashboard template validation passed!")
        sys.exit(0)
    elif errors:
        print("\n💥 Validation FAILED - fix errors before starting")
        sys.exit(1)
    else:
        print("\n✅ Validation passed with warnings")
        sys.exit(0)
