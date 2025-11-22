"""
Test the /api/guidance endpoint and show the actual error
"""
import requests
import json

url = "http://127.0.0.1:8004/api/guidance"
data = {"query": "I am feeling anxious about my future"}

print("Testing /api/guidance endpoint...")
print(f"POST {url}")
print(f"Data: {json.dumps(data)}\n")

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}\n")
    
    if response.status_code == 200:
        print("SUCCESS!")
        print(json.dumps(response.json(), indent=2))
    else:
        print("FAILED!")
        print(f"Response Text:\n{response.text}")
except Exception as e:
    print(f"ERROR: {e}")
