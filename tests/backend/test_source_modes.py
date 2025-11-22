"""
Test script to verify the three source modes work correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"  # Change to your server URL

def test_source_mode(mode, query):
    """Test a specific source mode"""
    print(f"\n{'='*80}")
    print(f"Testing {mode.upper()} mode")
    print(f"Query: {query}")
    print(f"{'='*80}\n")
    
    payload = {
        "query": query,
        "source": mode,
        "hadith_collection": ["eng-bukhari", "eng-muslim"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/guidance",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\nAnswer Preview (first 200 chars):")
            print(f"{data.get('answer', '')[:200]}...")
            
            print(f"\nCitations Count: {len(data.get('citations', []))}")
            
            if data.get('citations'):
                print("\nCitations:")
                for i, citation in enumerate(data.get('citations', [])[:3], 1):
                    print(f"  {i}. {citation.get('title')} - {citation.get('url')}")
                if len(data.get('citations', [])) > 3:
                    print(f"  ... and {len(data.get('citations', [])) - 3} more")
            
            # Verify mode-specific behavior
            if mode == "external":
                has_gemini_markers = any(phrase in data.get('answer', '').lower() 
                                        for phrase in ['i recommend', 'i suggest', 'in my', 'as an ai'])
                if has_gemini_markers:
                    print("\n⚠️  WARNING: External mode appears to use AI synthesis!")
                else:
                    print("\n✅ PASS: External mode returns raw text only")
                    
            elif mode == "internal":
                if data.get('citations'):
                    print("\n⚠️  WARNING: Internal mode should not have external citations!")
                else:
                    print("\n✅ PASS: Internal mode has no external citations")
                    
            elif mode == "both":
                if data.get('citations'):
                    print("\n✅ PASS: Both mode has citations")
                else:
                    print("\n⚠️  WARNING: Both mode should have citations!")
        else:
            print(f"\n❌ FAILED: {response.text}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def main():
    """Run all tests"""
    test_query = "How to deal with anxiety and worry"
    
    print("\n" + "="*80)
    print("SOURCE MODE TESTING")
    print("="*80)
    
    # Test all three modes
    test_source_mode("external", test_query)
    test_source_mode("internal", test_query)
    test_source_mode("both", test_query)
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
