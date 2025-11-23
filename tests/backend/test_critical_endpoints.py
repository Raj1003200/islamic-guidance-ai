"""
Test API key save and guidance endpoints
"""
import sys

BASE_URL = "http://127.0.0.1:8004"



print("\n" + "=" * 80, file=sys.stdout, flush=True)
print("Testing Guidance Endpoint", file=sys.stdout, flush=True)
print("=" * 80, file=sys.stdout, flush=True)

# Test 3: Valid query
print("\n[TEST 3] POST /api/guidance with valid query...", file=sys.stdout, flush=True)
response = requests.post(f"{BASE_URL}/api/guidance",
                        json={"query": "I don't have a house and need guidance"},
                        timeout=30)
print(f"Status: {response.status_code}", file=sys.stdout, flush=True)
if response.status_code in [200, 429, 503]:
    print(f"✓ Response received", file=sys.stdout, flush=True)
    if response.status_code == 200:
        data = response.json()
        if 'error' in data:
            print(f"  Error: {data.get('error')}", file=sys.stdout, flush=True)
        elif 'answer' in data:
            print(f"  Answer: {data['answer'][:100]}...", file=sys.stdout, flush=True)
    elif response.status_code == 429:
        print("  API quota exceeded (expected)", file=sys.stdout, flush=True)
    elif response.status_code == 503:
        print("  Service unavailable - check API key", file=sys.stdout, flush=True)
else:
    print(f"✗ FAILED: Status {response.status_code}", file=sys.stdout, flush=True)
    try:
        error = response.json()
        print(f"  Error detail: {error.get('detail', 'N/A')}", file=sys.stdout, flush=True)
    except:
        print(f"  Response: {response.text[:200]}", file=sys.stdout, flush=True)

# Test 4: Short query
print("\n[TEST 4] POST /api/guidance with short query...", file=sys.stdout, flush=True)
response = requests.post(f"{BASE_URL}/api/guidance",
                        json={"query": "help"},
                        timeout=5)
print(f"Status: {response.status_code}", file=sys.stdout, flush=True)
if response.status_code == 400:
    print(f"✓ SUCCESS: Correctly rejected short query", file=sys.stdout, flush=True)
else:
    print(f"✗ FAILED: Expected 400, got {response.status_code}", file=sys.stdout, flush=True)

print("\n" + "=" * 80, file=sys.stdout, flush=True)
print("Tests Complete", file=sys.stdout, flush=True)
print("=" * 80, file=sys.stdout, flush=True)
