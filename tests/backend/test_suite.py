"""
Simple Test Suite for Islamic Guidance AI - Windows Console Compatible
"""
import requests
import json
import time
import sys

# Set console encoding to UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

BASE_URL = "http://127.0.0.1:8000"

print("\n" + "=" * 80)
print("  ISLAMIC GUIDANCE AI - COMPREHENSIVE TEST SUITE")
print("=" * 80)

# Wait for server
print("\n[SETUP] Checking if server is running...")
try:
    response = requests.get(f"{BASE_URL}/api/get-api-key", timeout=2)
    print("[OK] Server is ready!\n")
except:
    print("[ERROR] Server not responding. Start it with:")
    print("  python -m uvicorn main:app --host 127.0.0.1 --port 8000\n")
    sys.exit(1)

# Test 1: Gemini Model
print("\n" + "=" * 80)
print("TEST 1: Checking Gemini 3 Pro Model Configuration")
print("=" * 80)
try:
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "gemini-3-pro" in content:
            print("[PASS] Gemini 3 Pro model is configured")
        else:
            print("[FAIL] Gemini 3 Pro model not found in main.py")
except Exception as e:
    print(f"[ERROR] {e}")

# Test 2: No External API Calls
print("\n" + "=" * 80)
print("TEST 2: Verifying No External API Calls in Frontend")
print("=" * 80)
files_to_check = [
    ("src/services/quranService.ts", "localhost"),
    ("src/services/hadithService.ts", "localhost")
]
for filename, expected in files_to_check:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
            if expected in content:
                print(f"[PASS] {filename} calls local backend")
            else:
                print(f"[FAIL] {filename} may call external APIs")
    except Exception as e:
        print(f"[WARN] Cannot check {filename}: {e}")

# Test 3: Backend Endpoints
print("\n" + "=" * 80)
print("TEST 3: Backend API Endpoints")
print("=" * 80)

print("\n[3.1] Testing /api/quran/search...")
try:
    response = requests.get(f"{BASE_URL}/api/quran/search", 
                          params={"keyword": "patience"}, timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"[PASS] Found {len(data)} Quran verses")
    else:
        print(f"[FAIL] Status {response.status_code}")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n[3.2] Testing /api/hadith/search...")
try:
    response = requests.get(f"{BASE_URL}/api/hadith/search",
                          params={"topic": "prayer", "book": "bukhari"}, timeout=15)
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"[PASS] Found Hadith")
        else:
            print(f"[WARN] No Hadith found for search term")
    else:
        print(f"[FAIL] Status {response.status_code}")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n[3.3] Testing /api/get-api-key...")
try:
    response = requests.get(f"{BASE_URL}/api/get-api-key", timeout=5)
    if response.status_code == 200:
        data = response.json()
        if data.get('apiKey'):
            print(f"[PASS] API key endpoint working (key length: {len(data['apiKey'])})")
        else:
            print(f"[WARN] No API key in .env")
    else:
        print(f"[FAIL] Status {response.status_code}")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n[3.4] Testing /api/guidance...")
try:
    response = requests.post(f"{BASE_URL}/api/guidance",
                           json={"query": "I am feeling anxious about my future"},
                           timeout=30)
    if response.status_code == 200:
        data = response.json()
        if data.get('error'):
            print(f"[WARN] Response contains error: {data['error']}")
        elif data.get('answer'):
            print(f"[PASS] Received guidance (answer length: {len(data['answer'])} chars)")
        else:
            print(f"[WARN] Unexpected response format")
    else:
        print(f"[FAIL] Status {response.status_code}")
except Exception as e:
    print(f"[ERROR] {e}")

# Test 4: Static Files
print("\n" + "=" * 80)
print("TEST 4: Static File Serving")
print("=" * 80)
static_files = [
    ("/", "index.html"),
    ("/settings.html", "settings.html"),
    ("/styles.css", "styles.css"),
    ("/script.js", "script.js"),
    ("/settings.js", "settings.js")
]

for path, name in static_files:
    try:
        response = requests.get(f"{BASE_URL}{path}", timeout=5)
        if response.status_code == 200:
            print(f"[PASS] {name} loaded ({len(response.content)} bytes)")
        else:
            print(f"[FAIL] {name} status {response.status_code}")
    except Exception as e:
        print(f"[ERROR] {name}: {e}")

# Summary
print("\n" + "=" * 80)
print("  TEST SUITE COMPLETED")
print("=" * 80)
print("\nManual Testing Required:")
print("  1. Open http://127.0.0.1:8000 in browser")
print("  2. Verify dark mode toggle in top-right corner")
print("  3. Test guidance search with: 'I am feeling anxious'")
print("  4. Navigate to Settings page")
print("  5. Verify API key shows with eye icon toggle")
print("\n")
