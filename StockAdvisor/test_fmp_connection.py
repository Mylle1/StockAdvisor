import requests
import json

# Test new FMP stable endpoints
api_key = "kOw9sF17DldZ1ioqDg9nOX8UzZNnivmj"

print(f"Testing FMP API key: {api_key[:10]}...")
print("\n=== Testing NEW /stable/ endpoints ===\n")

# Test each endpoint and show actual field names
test_endpoints = [
    ("/stable/profile?symbol=AAPL", "Company Profile"),
    ("/stable/income-statement?symbol=AAPL&limit=2", "Income Statement"),
    ("/stable/balance-sheet-statement?symbol=AAPL&limit=1", "Balance Sheet"),
    ("/stable/cash-flow-statement?symbol=AAPL&limit=1", "Cash Flow"),
]

for endpoint, name in test_endpoints:
    url = f"https://financialmodelingprep.com{endpoint}&apikey={api_key}"
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print(f"{'='*60}")
    try:
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                print(json.dumps(data[0], indent=2))
        else:
            print(f"❌ Error {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"❌ Exception: {e}")

