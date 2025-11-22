"""
Quick test script for the new API endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("Testing Quran Search Endpoint")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/api/quran/search", params={"keyword": "Heaven"})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} verses:")
        for verse in data[:2]:  # Print first 2
            print(f"\n  Surah: {verse['surah']}")
            print(f"  Verse: {verse['numberInSurah']}")
            print(f"  Text: {verse['text'][:100]}...")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("Testing Hadith Search Endpoint")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/api/hadith/search", params={"topic": "faith", "book": "bukhari"})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"\n  Found hadith:")
            print(f"  Text: {data.get('text', '')[:150]}...")
        else:
            print("  No hadith found")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
