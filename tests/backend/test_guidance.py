"""
Test the /api/guidance endpoint and show the actual error
"""
import requests
import json
import sys

url = "http://127.0.0.1:8004/api/guidance"
data = {"query": "I am feeling anxious about my future"}

print("Testing /api/guidance endpoint...", file=sys.stdout, flush=True)
print(f"POST {url}", file=sys.stdout, flush=True)
print(f"Data: {json.dumps(data)}\n", file=sys.stdout, flush=True)

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status Code: {response.status_code}", file=sys.stdout, flush=True)
    print(f"Response Headers: {dict(response.headers)}\n", file=sys.stdout, flush=True)
    
    if response.status_code == 200:
        print("SUCCESS!", file=sys.stdout, flush=True)
        print(json.dumps(response.json(), indent=2), file=sys.stdout, flush=True)
    else:
        print("FAILED!", file=sys.stdout, flush=True)
        print(f"Response Text:\n{response.text}", file=sys.stdout, flush=True)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stdout, flush=True)
