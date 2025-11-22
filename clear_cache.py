"""
Quick script to clear the cache via API
Run this to clear cached Quran search results after code changes
"""

import requests

def clear_cache():
    """Clear all cache patterns"""
    try:
        response = requests.post("http://localhost:8000/api/admin/clear-cache")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Cache cleared successfully!")
            print(f"   Patterns cleared: {', '.join(data['patterns'])}")
        else:
            print(f"❌ Failed to clear cache: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n⚠️  Make sure the server is running on http://localhost:8000")

if __name__ == "__main__":
    print("Clearing cache...")
    clear_cache()
