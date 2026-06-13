import urllib.request
import json
import time

PORT = 8765

url = f"http://127.0.0.1:{PORT}/system/shutdown"

req = urllib.request.Request(url, method="POST")
req.add_header("X-DeepFind-Control-Token", "secret_token_123")

try:
    with urllib.request.urlopen(req, timeout=5) as response:
        print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Failed:", e.code, e.read().decode())
except Exception as e:
    print("Error:", str(e))
