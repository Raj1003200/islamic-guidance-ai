"""
Islamic Guidance AI - External API Services Module
Handles asynchronous searches for Quran verses and Hadith collections
"""

import aiohttp
import asyncio
import urllib.parse
from typing import List, Dict, Optional
import time
import sys

# Import cache service
try:
    from backend.cache import cache
except ImportError:
    try:
        from cache import cache
    except ImportError:
        # Fallback mock if cache module completely fails
        class MockCache:
            async def get(self, k): return None
            async def set(self, k, v, t=0): pass
            async def connect(self): pass
        cache = MockCache()

# API Configuration Constants
QURAN_API_BASE = "https://api.alquran.cloud/v1"
HADITH_API_BASES = [
    "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions",
    "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions"
]

# Timeout and retry configuration optimized for Vercel
# Timeout and retry configuration optimized for Vercel
REQUEST_TIMEOUT = 5  # Reduced from 8s to 5s to ensure Vercel 10s limit isn't hit
MAX_RETRIES = 2      # Reduced from 3 to minimize latency
MAX_CONCURRENT_REQUESTS = 3  # Limit concurrent API calls


class APIException(Exception):
    """
    Custom exception for API-related errors with status code tracking
    """
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def search_quran_async(keyword: str, max_results: int = 3) -> List[Dict]:
    """
    Search Quran verses using external API asynchronously.
    
    Args:
        keyword: Search term for Quran verses
        max_results: Maximum number of results to return (default: 3)
        
    Returns:
        List of dictionaries containing verse data with:
        - text: Verse text in English
        - surah: Surah name
        - number: Verse number in Quran
        - numberInSurah: Verse number within surah
        - source: Always "Quran"
        
    Raises:
        APIException: If API request fails or times out
        
    Example:
        results = await search_quran_async("patience", max_results=5)
    """
    if not keyword:
        print("[QURAN API] No keyword provided, returning empty results", file=sys.stdout, flush=True)
        return []
        
    try:
        # Check cache first
        cache_key = f"quran_search:{keyword}:{max_results}"
        cached_result = await cache.get(cache_key)
        if cached_result:
            print(f"[CACHE] Hit for Quran search: '{keyword}'", file=sys.stdout, flush=True)
            return cached_result

        encoded = urllib.parse.quote(keyword)
        url = f"{QURAN_API_BASE}/search/{encoded}/all/en"
        
        print(f"[QURAN API] Request URL: {url}", file=sys.stdout, flush=True)
        print("[QURAN API] Method: GET (Async)", file=sys.stdout, flush=True)
        print(f"[QURAN API] Timeout: {REQUEST_TIMEOUT}s", file=sys.stdout, flush=True)
        
        start_time = time.time()
        
        # Configure timeout for this specific request
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                elapsed_time = time.time() - start_time
                
                print(f"[QURAN API] Response Status: {resp.status}", file=sys.stdout, flush=True)
                print(f"[QURAN API] Response Time: {elapsed_time:.2f}s", file=sys.stdout, flush=True)
                print(f"[QURAN API] Response Size: {resp.content_length} bytes", file=sys.stdout, flush=True)
                
                if resp.status == 200:
                    data = await resp.json()
                    total_matches = data.get("data", {}).get("count", 0)
                    print(f"[QURAN API] Total matches found: {total_matches}", file=sys.stdout, flush=True)
                    
                    # Extract and format results
                    if data.get("data") and data["data"].get("matches"):
                        results = [
                            {
                                "text": match["text"],
                                "surah": match["surah"]["englishName"],
                                "number": match["number"],
                                "numberInSurah": match["numberInSurah"],
                                "source": "Quran"
                            }
                            for match in data["data"]["matches"][:max_results]
                        ]
                        
                        print(f"[QURAN API] Returning {len(results)} results", file=sys.stdout, flush=True)
                        
                        # Log each result for debugging
                        for idx, result in enumerate(results, 1):
                            print(f"[QURAN API] Result {idx}: Surah {result['surah']}, Verse {result['numberInSurah']}", file=sys.stdout, flush=True)
                            print(f"[QURAN API] Text preview: {result['text'][:100]}...", file=sys.stdout, flush=True)
                        
                        # Cache the results (TTL: 1 hour)
                        await cache.set(cache_key, results, ttl=3600)
                        return results
                    else:
                        print("[QURAN API] No matches found in response", file=sys.stdout, flush=True)
                        return []
                        
                else:
                    # Handle non-200 responses
                    error_text = await resp.text()
                    print(f"[QURAN API] API returned status {resp.status}", file=sys.stderr, flush=True)
                    print(f"[QURAN API] Error body: {error_text[:500]}", file=sys.stderr, flush=True)
                    raise APIException(
                        f"Quran API returned status {resp.status}",
                        status_code=resp.status
                    )
                    
    except asyncio.TimeoutError:
        print(f"[QURAN API] Request timed out after {REQUEST_TIMEOUT}s", file=sys.stderr, flush=True)
        raise APIException("Quran API request timed out")
        
    except aiohttp.ClientError as e:
        print(f"[QURAN API] Client error: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        raise APIException(f"Quran API client error: {str(e)}")
        
    except Exception as e:
        print(f"[QURAN API] Unexpected error: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        raise APIException(f"Quran API error: {str(e)}")


async def fetch_hadith_collection(
    session: aiohttp.ClientSession,
    collection_code: str
) -> Optional[List[Dict]]:
    """
    Fetch a single Hadith collection with retry logic across multiple CDNs.
    
    Args:
        session: Active aiohttp ClientSession for connection pooling
        collection_code: Collection identifier (e.g., 'eng-bukhari')
        
    Returns:
        List of hadith dictionaries or None if all attempts fail
        
    Note:
        Tries multiple CDN sources with fallback logic for reliability
    """
    book = collection_code.replace('eng-', '') if collection_code.startswith('eng-') else collection_code
    
    # Check cache first (Critical for performance - these are large files)
    cache_key = f"hadith_collection:{book}"
    cached_data = await cache.get(cache_key)
    if cached_data:
        print(f"[CACHE] Hit for Hadith collection: '{book}'", file=sys.stdout, flush=True)
        return cached_data

    print(f"[HADITH API] Fetching collection: '{book}'", file=sys.stdout, flush=True)
    
    # Generate URLs to try with priority order
    urls = []
    for base in HADITH_API_BASES:
        urls.append(f"{base}/eng-{book}.min.json")  # Try minified first (smaller)
        urls.append(f"{base}/eng-{book}.json")       # Then full version
    
    # Try each URL with retry logic
    for idx, url in enumerate(urls[:MAX_RETRIES], 1):
        try:
            print(f"[HADITH API] Attempt {idx}/{MAX_RETRIES} - URL: {url}", file=sys.stdout, flush=True)
            start_time = time.time()
            
            async with session.get(url) as resp:
                elapsed_time = time.time() - start_time
                
                print(f"[HADITH API] Status: {resp.status}", file=sys.stdout, flush=True)
                print(f"[HADITH API] Time: {elapsed_time:.2f}s", file=sys.stdout, flush=True)
                print(f"[HADITH API] Size: {resp.content_length} bytes", file=sys.stdout, flush=True)
                
                if resp.status == 200:
                    json_data = await resp.json()
                    
                    if json_data.get("hadiths"):
                        hadiths = json_data["hadiths"]
                        print(f"[HADITH API] Successfully loaded {len(hadiths)} hadiths from '{book}'", file=sys.stdout, flush=True)
                        
                        # Log metadata if available
                        metadata = json_data.get('metadata', {})
                        if metadata:
                            print(f"[HADITH API] Metadata - Name: {metadata.get('name', 'N/A')}, Sections: {len(metadata.get('sections', {}))}", file=sys.stdout, flush=True)
                        
                        # Cache the entire collection (TTL: 24 hours)
                        # These are static files, so we can cache for a long time
                        await cache.set(cache_key, hadiths, ttl=86400)
                        return hadiths
                    else:
                        print("[HADITH API] No 'hadiths' key in response", file=sys.stderr, flush=True)
                else:
                    print(f"[HADITH API] Status {resp.status} from URL {idx}", file=sys.stderr, flush=True)
                    
        except asyncio.TimeoutError:
            print(f"[HADITH API] Timeout for URL {idx}", file=sys.stderr, flush=True)
            continue
            
        except aiohttp.ClientError as e:
            print(f"[HADITH API] Client error for URL {idx}: {e}", file=sys.stderr, flush=True)
            continue
            
        except Exception as e:
            print(f"[HADITH API] Failed URL {idx}: {e}", file=sys.stderr, flush=True)
            continue
    
    # All attempts failed
    print(f"[HADITH API] Could not load collection '{book}' from any URL", file=sys.stderr, flush=True)
    return None


async def search_hadith_async(
    topic: str,
    collections: Optional[List[str]] = None,
    max_per_collection: int = 2
) -> List[Dict]:
    """
    Search Hadiths asynchronously across multiple collections.
    
    Args:
        topic: Search term to find in hadith texts
        collections: List of collection codes to search (defaults to Kutub al-Sittah)
        max_per_collection: Maximum results to return per collection (default: 2)
        
    Returns:
        List of dictionaries containing hadith data with:
        - text: Hadith text in English
        - hadithnumber: Hadith number within collection
        - arabicnumber: Arabic numbering system number
        - book: Collection name (e.g., 'bukhari')
        - reference: Reference metadata
        - source: Formatted source string
        - citation_url: Direct link to Sunnah.com
        
    Raises:
        APIException: If critical search failure occurs
        
    Example:
        results = await search_hadith_async(
            "prayer",
            collections=["eng-bukhari", "eng-muslim"],
            max_per_collection=3
        )
    """
    if not topic:
        print("[HADITH API] No topic provided, returning empty list", file=sys.stderr, flush=True)
        return []
    
    # Default to Kutub al-Sittah (The Six Authentic Books)
    if not collections:
        collections = [
            "eng-bukhari",   # Sahih al-Bukhari
            "eng-muslim",    # Sahih Muslim
            "eng-abudawud",  # Sunan Abu Dawud
            "eng-tirmidhi",  # Jami' at-Tirmidhi
            "eng-nasai",     # Sunan an-Nasa'i
            "eng-ibnmajah"   # Sunan Ibn Majah
        ]
    
    collection_names = [c.replace('eng-', '') for c in collections]
    print(f"[HADITH SEARCH] Starting async search for '{topic}' across {len(collections)} collections", file=sys.stdout, flush=True)
    print(f"[HADITH SEARCH] Collections: {', '.join(collection_names)}", file=sys.stdout, flush=True)
    print("="*80, file=sys.stdout, flush=True)
    
    all_matches = []
    topic_lower = topic.lower()
    
    try:
        # Configure session timeout
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Fetch all collections concurrently for efficiency
            print("[HADITH SEARCH] Fetching collections concurrently...", file=sys.stdout, flush=True)
            
            tasks = [
                fetch_hadith_collection(session, collection_code)
                for collection_code in collections
            ]
            
            # Wait for all collections to load (with exception handling)
            collections_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process each collection's results
            for collection_code, hadiths in zip(collections, collections_data):
                book = collection_code.replace('eng-', '')
                
                # Handle exceptions from individual collection fetches
                if isinstance(hadiths, Exception):
                    print(f"[HADITH SEARCH] Error loading '{book}': {hadiths}", file=sys.stderr, flush=True)
                    continue
                    
                if not hadiths:
                    print(f"[HADITH SEARCH] No hadiths loaded for '{book}'", file=sys.stderr, flush=True)
                    continue
                
                # Search for topic in hadith texts (case-insensitive)
                print(f"[HADITH SEARCH] Searching {len(hadiths)} hadiths in '{book}'...", file=sys.stdout, flush=True)
                
                matches = [
                    hadith for hadith in hadiths
                    if topic_lower in hadith.get("text", "").lower()
                ]
                
                if matches:
                    print(f"[HADITH SEARCH] Found {len(matches)} matches in '{book}'", file=sys.stdout, flush=True)
                    
                    # Take top N matches from this collection
                    for match in matches[:max_per_collection]:
                        hadith_number = match.get("hadithnumber", "")
                        citation_url = f"https://sunnah.com/{book}:{hadith_number}"
                        
                        hadith_data = {
                            "text": match.get("text", ""),
                            "hadithnumber": hadith_number,
                            "arabicnumber": match.get("arabicnumber", ""),
                            "book": book,
                            "reference": match.get("reference", {}),
                            "source": f"Hadith ({book.capitalize()})",
                            "citation_url": citation_url
                        }
                        all_matches.append(hadith_data)
                        
                        # Log match details
                        print(f"  [MATCH] {book.capitalize()}: #{hadith_number} - {citation_url}", file=sys.stdout, flush=True)
                        print(f"  [MATCH] Text preview: {match.get('text', '')[:150]}...", file=sys.stdout, flush=True)
                else:
                    print(f"[HADITH SEARCH] No matches in '{book}'", file=sys.stdout, flush=True)
        
        print("="*80, file=sys.stdout, flush=True)
        print(f"[HADITH SEARCH] Completed: {len(all_matches)} total matches across all collections", file=sys.stdout, flush=True)
        
        return all_matches
        
    except Exception as e:
        print(f"[HADITH SEARCH] Critical error: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        # Don't crash - return empty results on error
        return []


# Synchronous wrappers for backward compatibility with existing code
def search_quran(keyword: str, max_results: int = 3) -> List[Dict]:
    """
    Synchronous wrapper for search_quran_async.
    
    Note: This creates a new event loop if needed. Prefer using
    the async version directly in async contexts.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        search_quran_async(keyword, max_results)
    )


def search_hadith(
    topic: str,
    collections: Optional[List[str]] = None,
    max_per_collection: int = 2
) -> List[Dict]:
    """
    Synchronous wrapper for search_hadith_async.
    
    Note: This creates a new event loop if needed. Prefer using
    the async version directly in async contexts.
    """
    try:
        # Check if we're in an async context
        try:
            asyncio.get_running_loop()
            # If we get here, we're in an async context
            print("[HADITH SEARCH] Using sync wrapper in async context. Consider using search_hadith_async directly.", 
                  file=sys.stderr, flush=True)
            
            # Create a new event loop for the thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                search_hadith_async(topic, collections, max_per_collection)
            )
            
        except RuntimeError:
            # No running event loop, we can use asyncio.run()
            return asyncio.run(
                search_hadith_async(topic, collections, max_per_collection)
            )
            
    except Exception as e:
        print(f"[HADITH SEARCH] Error in sync wrapper: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        return []
