"""
Test API key save and guidance endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8004"

print("=" * 80)
print("Testing API Key Save Endpoint")
print("=" * 80)

# Test 1: Save API key
print("\n[TEST 1] POST /api/save-api-key with valid key...")
response = requests.post(f"{BASE_URL}/api/save-api-key",
                        json={"apiKey": "AIzaSyTest123"},
                        timeout=5)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"✓ SUCCESS: {response.json()}")
else:
    print(f"✗ FAILED: {response.text}")

# Test 2: Empty key
print("\n[TEST 2] POST /api/save-api-key with empty key...")
response = requests.post(f"{BASE_URL}/api/save-api-key",
                        json={"apiKey": ""},
                        timeout=5)
print(f"Status: {response.status_code}")
if response.status_code == 400:
    print(f"✓ SUCCESS: Correctly rejected empty key")
else:
    print(f"✗ FAILED: Expected 400, got {response.status_code}")

print("\n" + "=" * 80)
print("Testing Guidance Endpoint")
print("=" * 80)

# Test 3: Valid query
print("\n[TEST 3] POST /api/guidance with valid query...")
response = requests.post(f"{BASE_URL}/api/guidance",
                        json={"query": "I don't have a house and need guidance"},
                        timeout=30)
print(f"Status: {response.status_code}")
if response.status_code in [200, 429, 503]:
    print(f"✓ Response received")
    if response.status_code == 200:
        data = response.json()
        if 'error' in data:
            print(f"  Error: {data.get('error')}")
        elif 'answer' in data:
            print(f"  Answer: {data['answer'][:100]}...")
    elif response.status_code == 429:
        print("  API quota exceeded (expected)")
    elif response.status_code == 503:
        print("  Service unavailable - check API key")
else:
    print(f"✗ FAILED: Status {response.status_code}")
    try:
        error = response.json()
        print(f"  Error detail: {error.get('detail', 'N/A')}")
    except:
        print(f"  Response: {response.text[:200]}")

# Test 4: Short query
print("\n[TEST 4] POST /api/guidance with short query...")
response = requests.post(f"{BASE_URL}/api/guidance",
                        json={"query": "help"},
                        timeout=5)
print(f"Status: {response.status_code}")
if response.status_code == 400:
    print(f"✓ SUCCESS: Correctly rejected short query")
else:
    print(f"✗ FAILED: Expected 400, got {response.status_code}")

print("\n" + "=" * 80)
print("Tests Complete")
print("=" * 80)
