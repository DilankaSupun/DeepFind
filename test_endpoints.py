import urllib.request
import json
import time

PORT = 8765

endpoints = [
    "/health",
    "/db/status",
    "/scan-scope/status",
    "/pipeline/status"
]

results = {}

for ep in endpoints:
    url = f"http://127.0.0.1:{PORT}{ep}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read()
            results[ep] = json.loads(data)
    except Exception as e:
        results[ep] = {"error": str(e)}

with open("test_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Endpoints tested successfully.")
