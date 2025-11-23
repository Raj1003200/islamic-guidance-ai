"""
Comprehensive Test Suite for Islamic Guidance AI
Tests all components from backend to frontend
"""
import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def print_header(text):
    print("\n" + "=" * 80, file=sys.stdout, flush=True)
    print(f"  {text}", file=sys.stdout, flush=True)
    print("=" * 80, file=sys.stdout, flush=True)

def test_backend_endpoints():
    """Test all backend API endpoints"""
    print_header("BACKEND ENDPOINT TESTING")
    
    # Test 1: Quran Search
    print("\n[TEST 1] Testing /api/quran/search...", file=sys.stdout, flush=True)
    try:
        response = requests.get(f"{BASE_URL}/api/quran/search", params={"keyword": "patience"}, timeout=10)
        print(f"  Status: {response.status_code}", file=sys.stdout, flush=True)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ SUCCESS: Found {len(data)} verses", file=sys.stdout, flush=True)
            if data:
                print(f"  Sample: {data[0].get('surah', 'N/A')} - {data[0].get('text', 'N/A')[:50]}...", file=sys.stdout, flush=True)
        else:
            print(f"  ✗ FAILED: {response.text}", file=sys.stdout, flush=True)
    except Exception as e:
        print(f"  ✗ ERROR: {e}", file=sys.stdout, flush=True)
    
    # Test 2: Hadith Search
    print("\n[TEST 2] Testing /api/hadith/search...", file=sys.stdout, flush=True)
    try:
        response = requests.get(f"{BASE_URL}/api/hadith/search", 
                              params={"topic": "prayer", "book": "bukhari"}, timeout=15)
        print(f"  Status: {response.status_code}", file=sys.stdout, flush=True)
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"  ✓ SUCCESS: Found hadith", file=sys.stdout, flush=True)
                print(f"  Sample: {str(data.get('text', 'N/A'))[:50]}...", file=sys.stdout, flush=True)
            else:
                print(f"  ✓ SUCCESS: No hadith found (expected for some searches)", file=sys.stdout, flush=True)
        else:
            print(f"  ✗ FAILED: {response.text}", file=sys.stdout, flush=True)
    except Exception as e:
        print(f"  ✗ ERROR: {e}", file=sys.stdout, flush=True)
    

    
    # Test 4: Guidance Endpoint
    print("\n[TEST 4] Testing /api/guidance...", file=sys.stdout, flush=True)
    try:
        response = requests.post(f"{BASE_URL}/api/guidance", 
                               json={"query": "I am feeling anxious about my future"},
                               timeout=30)
        print(f"  Status: {response.status_code}", file=sys.stdout, flush=True)
        if response.status_code == 200:
            data = response.json()
            if data.get('error'):
                print(f"   Response has error: {data['error']}", file=sys.stdout, flush=True)
            elif data.get('answer'):
                print(f"  SUCCESS: Received guidance", file=sys.stdout, flush=True)
                print(f"  Answer preview: {data['answer'][:100]}...", file=sys.stdout, flush=True)
            else:
                print(f"  Unexpected response format", file=sys.stdout, flush=True)
        else:
            print(f"  FAILED: {response.text}", file=sys.stdout, flush=True)
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stdout, flush=True)

def test_static_files():
    """Test that static files are served"""
    print_header("STATIC FILE TESTING")
    
    files_to_test = [
        ("index.html", "/"),
        ("settings.html", "/settings.html"),
        ("styles.css", "/styles.css"),
        ("script.js", "/script.js"),
        ("settings.js", "/settings.js")
    ]
    
    for name, path in files_to_test:
        print(f"\n[TEST] Loading {name}...", file=sys.stdout, flush=True)
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            if response.status_code == 200:
                print(f"  ✓ SUCCESS: {name} loaded ({len(response.content)} bytes)", file=sys.stdout, flush=True)
            else:
                print(f"  ✗ FAILED: Status {response.status_code}", file=sys.stdout, flush=True)
        except Exception as e:
            print(f"  ✗ ERROR: {e}", file=sys.stdout, flush=True)

def verify_no_external_calls():
    """Verify frontend doesn't call external APIs"""
    print_header("VERIFYING NO EXTERNAL API CALLS IN FRONTEND")
    
    print("\n[CHECK 1] Checking script.js for external API calls...")
    try:
        with open("script.js", "r", encoding="utf-8") as f:
            content = f.read()
            external_apis = []
            if "api.alquran.cloud" in content:
                external_apis.append("api.alquran.cloud")
            if "cdn.jsdelivr.net" in content and "hadith-api" in content:
                external_apis.append("hadith-api")
            if "sunnah.com" in content:
                external_apis.append("sunnah.com")
            
            if external_apis:
                print(f"  ✗ FAILED: Found external API calls: {external_apis}")
            else:
                print(f"  ✓ SUCCESS: No external API calls found")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    print("\n[CHECK 2] Checking TypeScript services...")
    services = [
        "src/services/quranService.ts",
        "src/services/hadithService.ts"
    ]
    
    for service in services:
        try:
            with open(service, "r", encoding="utf-8") as f:
                content = f.read()
                if "localhost:8000" in content or "127.0.0.1:8000" in content:
                    print(f"  SUCCESS: {service} calls local backend")
                elif "api.alquran.cloud" in content or "cdn.jsdelivr.net" in content:
                    print(f"  FAILED: {service} still calls external APIs")
                else:
                    print(f"  WARNING: Cannot determine for {service}")
        except Exception as e:
            print(f"  Cannot check {service}: {e}")

def check_gemini_model():
    """Check Gemini 3 Pro model configuration"""
    print_header("VERIFYING GEMINI 3 PRO MODEL")
    
    print("\n[CHECK] Reading main.py...")
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "gemini-3-pro" in content or "gemini-3-pro-preview" in content:
                print(f"  ✓ SUCCESS: Gemini 3 Pro model configured")
            else:
                print(f"  ✗ FAILED: Gemini 3 Pro model not found")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" " * 10 + "ISLAMIC GUIDANCE AI - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    # Wait for server to be ready
    print("\n[SETUP] Waiting for server to be ready...")
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=2)
            if response.status_code == 200:
                print("  ✓ Server is ready!")
                break
        except:
            if i < max_retries - 1:
                print(f"  Attempt {i+1}/{max_retries} - waiting...")
                time.sleep(2)
            else:
                print("  ✗ Server not responding. Please start it with:")
                print("     python -m uvicorn main:app --host 127.0.0.1 --port 8000")
                return
    
    # Run all tests
    check_gemini_model()
    verify_no_external_calls()
    test_backend_endpoints()
    test_static_files()
    
    print("\n" + "=" * 80)
    print("  TEST SUITE COMPLETED")
    print("=" * 80)
    print("\nNext Steps:")
    print("  1. Open browser to http://127.0.0.1:8000")
    print("  2. Test dark mode toggle (top right corner)")
    print("  3. Test search: 'I am feeling anxious about my future'")
    print("  4. Go to Settings and test API key eye icon")
    print("\n")

if __name__ == "__main__":
    main()
