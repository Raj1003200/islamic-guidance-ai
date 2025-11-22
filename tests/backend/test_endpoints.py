"""
Quick test script for the new API endpoints
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80, file=sys.stdout, flush=True)
print("Testing Quran Search Endpoint", file=sys.stdout, flush=True)
print("=" * 80, file=sys.stdout, flush=True)

try:
    response = requests.get(f"{BASE_URL}/api/quran/search", params={"keyword": "Heaven"})
    print(f"Status: {response.status_code}", file=sys.stdout, flush=True)
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} verses:", file=sys.stdout, flush=True)
        for verse in data[:2]:  # Print first 2
            print(f"\n  Surah: {verse['surah']}", file=sys.stdout, flush=True)
            print(f"  Verse: {verse['numberInSurah']}", file=sys.stdout, flush=True)
            print(f"  Text: {verse['text'][:100]}...", file=sys.stdout, flush=True)
    else:
        print(f"Error: {response.text}", file=sys.stdout, flush=True)
except Exception as e:
    print(f"Error: {e}", file=sys.stdout, flush=True)

print("\n" + "=" * 80, file=sys.stdout, flush=True)
print("Testing Hadith Search Endpoint", file=sys.stdout, flush=True)
print("=" * 80, file=sys.stdout, flush=True)

try:
    response = requests.get(f"{BASE_URL}/api/hadith/search", params={"topic": "faith", "book": "bukhari"})
    print(f"Status: {response.status_code}", file=sys.stdout, flush=True)
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"\n  Found hadith:", file=sys.stdout, flush=True)
            print(f"  Text: {data.get('text', '')[:150]}...", file=sys.stdout, flush=True)
        else:
            print("  No hadith found", file=sys.stdout, flush=True)
    else:
        print(f"Error: {response.text}", file=sys.stdout, flush=True)
except Exception as e:
    print(f"Error: {e}", file=sys.stdout, flush=True)

print("\n" + "=" * 80, file=sys.stdout, flush=True)
print("Test Complete", file=sys.stdout, flush=True)
print("=" * 80, file=sys.stdout, flush=True)
