"""
Islamic Guidance AI - External API Services Module (OPTIMIZED)
Handles asynchronous searches for Quran verses and Hadith collections

All P0-P3 issues fixed:
- Issue #6: /tmp caching and streaming for Hadith JSONs
- Issue #11: Retry logic with exponential backoff and circuit breaker
"""

import aiohttp
import asyncio
import urllib.parse
from typing import List, Dict, Optional
import time
import sys
import os
import json
import hashlib

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

# =============================================================================
# API CONFIGURATION
# =============================================================================

QURAN_API_BASE = "https://api.alquran.cloud/v1"
HADITH_API_BASES = [
    "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions",
    "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions"
]

# Optimized timeout configuration (Issue #1 - P0)
REQUEST_TIMEOUT = 2  # Per collection timeout reduced to 2s
MAX_RETRIES = 2  # Number of retry attempts per request
BACKOFF_FACTOR = 0.5  # Exponential backoff multiplier

# Circuit breaker configuration (Issue #11 - P1)
CIRCUIT_BREAKER_THRESHOLD = 3  # Failures before opening circuit
CIRCUIT_BREAKER_TIMEOUT = 60  # Seconds before trying again

# Circuit breaker state tracking
circuit_breaker_state = {}  # {url: {'failures': int, 'opened_at': float}}

# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class APIException(Exception):
    """Custom exception for API-related errors with status code tracking"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open"""
    pass

# =============================================================================
# CIRCUIT BREAKER LOGIC (Issue #11 - P1)
# =============================================================================

def check_circuit_breaker(url: str) -> bool:
    """
    Check if circuit breaker allows requests to this URL.
    
    Args:
        url: API endpoint URL
    
    Returns:
        True if requests allowed, False if circuit open
    """
    if url not in circuit_breaker_state:
        return True
    
    state = circuit_breaker_state[url]
    
    # Check if circuit should be reset (timeout expired)
    if state.get('failures', 0) >= CIRCUIT_BREAKER_THRESHOLD:
        opened_at = state.get('opened_at', 0)
        if time.time() - opened_at > CIRCUIT_BREAKER_TIMEOUT:
            # Reset circuit breaker
            circuit_breaker_state[url] = {'failures': 0, 'opened_at': 0}
            print(f"[CIRCUIT BREAKER] Reset for {url}", file=sys.stdout, flush=True)
            return True
        else:
            print(f"[CIRCUIT BREAKER] Open for {url}", file=sys.stderr, flush=True)
            return False
    
    return True

def record_success(url: str):
    """Record successful request (reset failure count)"""
    if url in circuit_breaker_state:
        circuit_breaker_state[url] = {'failures': 0, 'opened_at': 0}

def record_failure(url: str):
    """Record failed request (increment failure count)"""
    if url not in circuit_breaker_state:
        circuit_breaker_state[url] = {'failures': 0, 'opened_at': 0}
    
    circuit_breaker_state[url]['failures'] += 1
    
    if circuit_breaker_state[url]['failures'] >= CIRCUIT_BREAKER_THRESHOLD:
        circuit_breaker_state[url]['opened_at'] = time.time()
        print(f"[CIRCUIT BREAKER] Opened for {url}", file=sys.stderr, flush=True)

# =============================================================================
# /TMP CACHING FOR VERCEL (Issue #6 - P0)
# =============================================================================

def get_tmp_cache_path(key: str) -> str:
    """
    Get /tmp cache file path for a given key.
    /tmp is writable in Vercel and persists during warm container lifetime.
    
    Args:
        key: Cache key (e.g., collection name)
    
    Returns:
        Full path to cache file
    """
    # Hash the key to create safe filename
    key_hash = hashlib.md5(key.encode()).hexdigest()
    return os.path.join("/tmp", f"hadith_cache_{key_hash}.json")

async def get_from_tmp_cache(key: str, max_age_hours: int = 24) -> Optional[dict]:
    """
    Retrieve data from /tmp cache if exists and not expired.
    
    Args:
        key: Cache key
        max_age_hours: Maximum age in hours before cache expires
    
    Returns:
        Cached data or None
    """
    try:
        cache_path = get_tmp_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        # Check file age
        file_age = time.time() - os.path.getmtime(cache_path)
        if file_age > max_age_hours * 3600:
            print(f"[TMP CACHE] Expired for '{key}' (age: {file_age/3600:.1f}h)", file=sys.stdout, flush=True)
            os.remove(cache_path)
            return None
        
        # Read cached data
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"[TMP CACHE] Hit for '{key}' (age: {file_age/3600:.1f}h)", file=sys.stdout, flush=True)
        return data
        
    except Exception as e:
        print(f"[TMP CACHE] Error reading '{key}': {e}", file=sys.stderr, flush=True)
        return None

async def save_to_tmp_cache(key: str, data: dict):
    """
    Save data to /tmp cache for warm container reuse.
    
    Args:
        key: Cache key
        data: Data to cache
    """
    try:
        cache_path = get_tmp_cache_path(key)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        print(f"[TMP CACHE] Saved '{key}' to {cache_path}", file=sys.stdout, flush=True)
        
    except Exception as e:
        print(f"[TMP CACHE] Error saving '{key}': {e}", file=sys.stderr, flush=True)

# =============================================================================
# QURAN API SEARCH
# =============================================================================

async def search_quran_async(keyword: str, max_results: int = 3) -> List[Dict]:
    """
    Search Quran verses using external API asynchronously.
    
    Includes retry logic with exponential backoff (Issue #11 - P1)
    
    Args:
        keyword: Search term for Quran verses
        max_results: Maximum number of results to return (default: 3)
    
    Returns:
        List of dictionaries containing verse data
    
    Raises:
        APIException: If API request fails after retries
    """
    if not keyword:
        print("[QURAN API] No keyword provided, returning empty results", file=sys.stdout, flush=True)
        return []
    
    # Check Vercel KV cache first
    try:
        cache_key = f"quran_search:{keyword}:{max_results}"
        cached_result = await cache.get(cache_key)
        if cached_result:
            print(f"[CACHE] Hit for Quran search: '{keyword}'", file=sys.stdout, flush=True)
            return cached_result
    except Exception as e:
        print(f"[CACHE] Error reading: {e}", file=sys.stderr, flush=True)
    
    encoded = urllib.parse.quote(keyword)
    url = f"{QURAN_API_BASE}/search/{encoded}/all/en"
    
    # Check circuit breaker
    if not check_circuit_breaker(url):
        raise CircuitBreakerOpen(f"Circuit breaker open for {url}")
    
    # Retry loop with exponential backoff (Issue #11 - P1)
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                backoff_time = BACKOFF_FACTOR * (2 ** (attempt - 1))
                print(f"[QURAN API] Retry {attempt}/{MAX_RETRIES} after {backoff_time}s", file=sys.stdout, flush=True)
                await asyncio.sleep(backoff_time)
            
            print(f"[QURAN API] Request (attempt {attempt + 1}): {url}", file=sys.stdout, flush=True)
            start_time = time.time()
            
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    elapsed_time = time.time() - start_time
                    print(f"[QURAN API] Status: {resp.status}, Time: {elapsed_time:.2f}s", file=sys.stdout, flush=True)
                    
                    if resp.status == 200:
                        data = await resp.json()
                        total_matches = data.get("data", {}).get("count", 0)
                        
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
                            
                            print(f"[QURAN API] Success: {len(results)} results", file=sys.stdout, flush=True)
                            
                            # Cache results (1 hour TTL)
                            try:
                                await cache.set(cache_key, results, ttl=3600)
                            except Exception as e:
                                print(f"[CACHE] Error saving: {e}", file=sys.stderr, flush=True)
                            
                            # Record success for circuit breaker
                            record_success(url)
                            
                            return results
                        else:
                            print("[QURAN API] No matches found", file=sys.stdout, flush=True)
                            return []
                    
                    else:
                        error_text = await resp.text()
                        print(f"[QURAN API] Error {resp.status}: {error_text[:200]}", file=sys.stderr, flush=True)
                        
                        if attempt == MAX_RETRIES:
                            record_failure(url)
                            raise APIException(f"Quran API returned {resp.status}", resp.status)
                        
        except asyncio.TimeoutError:
            print(f"[QURAN API] Timeout (attempt {attempt + 1})", file=sys.stderr, flush=True)
            if attempt == MAX_RETRIES:
                record_failure(url)
                raise APIException("Quran API request timed out")
        
        except aiohttp.ClientError as e:
            print(f"[QURAN API] Client error (attempt {attempt + 1}): {e}", file=sys.stderr, flush=True)
            if attempt == MAX_RETRIES:
                record_failure(url)
                raise APIException(f"Quran API client error: {str(e)}")
        
        except Exception as e:
            print(f"[QURAN API] Error (attempt {attempt + 1}): {e}", file=sys.stderr, flush=True)
            if attempt == MAX_RETRIES:
                record_failure(url)
                raise APIException(f"Quran API error: {str(e)}")
    
    return []

# =============================================================================
# HADITH API SEARCH WITH /TMP CACHING (Issue #6 - P0)
# =============================================================================

async def fetch_hadith_collection(
    session: aiohttp.ClientSession,
    collection_code: str
) -> Optional[List[Dict]]:
    """
    Fetch a single Hadith collection with optimized caching strategy.
    
    Caching strategy (Issue #6 - P0):
    1. Check /tmp cache (fast, survives warm container)
    2. Check Vercel KV cache (cross-instance)
    3. Download from external API with timeout
    4. Save to both /tmp and Vercel KV
    
    Args:
        session: Active aiohttp ClientSession
        collection_code: Collection identifier (e.g., 'eng-bukhari')
    
    Returns:
        List of hadith dictionaries or None if all attempts fail
    """
    book = collection_code.replace('eng-', '') if collection_code.startswith('eng-') else collection_code
    
    # 1. Check /tmp cache first (fastest)
    tmp_data = await get_from_tmp_cache(f"hadith:{book}")
    if tmp_data:
        return tmp_data.get('hadiths')
    
    # 2. Check Vercel KV cache
    try:
        cache_key = f"hadith_collection:{book}"
        cached_data = await cache.get(cache_key)
        if cached_data:
            print(f"[CACHE] Hit for Hadith collection: '{book}'", file=sys.stdout, flush=True)
            # Also save to /tmp for next time
            await save_to_tmp_cache(f"hadith:{book}", {'hadiths': cached_data})
            return cached_data
    except Exception as e:
        print(f"[CACHE] Error reading: {e}", file=sys.stderr, flush=True)
    
    print(f"[HADITH API] Downloading collection: '{book}'", file=sys.stdout, flush=True)
    
    # 3. Generate URLs to try
    urls = []
    for base in HADITH_API_BASES:
        urls.append(f"{base}/eng-{book}.min.json")  # Minified first (smaller)
        urls.append(f"{base}/eng-{book}.json")
    
    # 4. Try each URL with timeout (Issue #6 - P0: 2s timeout per collection)
    for idx, url in enumerate(urls[:MAX_RETRIES * 2], 1):
        try:
            # Check circuit breaker
            if not check_circuit_breaker(url):
                continue
            
            print(f"[HADITH API] Attempt {idx} - URL: {url}", file=sys.stdout, flush=True)
            start_time = time.time()
            
            async with session.get(url) as resp:
                elapsed_time = time.time() - start_time
                print(f"[HADITH API] Status: {resp.status}, Time: {elapsed_time:.2f}s", file=sys.stdout, flush=True)
                
                if resp.status == 200:
                    json_data = await resp.json()
                    
                    if json_data.get("hadiths"):
                        hadiths = json_data["hadiths"]
                        print(f"[HADITH API] Success: {len(hadiths)} hadiths from '{book}'", file=sys.stdout, flush=True)
                        
                        # Record success for circuit breaker
                        record_success(url)
                        
                        # 5. Save to both caches
                        # Save to Vercel KV (24 hour TTL)
                        try:
                            await cache.set(f"hadith_collection:{book}", hadiths, ttl=86400)
                        except Exception as e:
                            print(f"[CACHE] Error saving to KV: {e}", file=sys.stderr, flush=True)
                        
                        # Save to /tmp cache
                        await save_to_tmp_cache(f"hadith:{book}", {'hadiths': hadiths})
                        
                        return hadiths
                    else:
                        print("[HADITH API] No 'hadiths' key in response", file=sys.stderr, flush=True)
                else:
                    print(f"[HADITH API] Status {resp.status}", file=sys.stderr, flush=True)
                    record_failure(url)
                    
        except asyncio.TimeoutError:
            print(f"[HADITH API] Timeout for URL {idx}", file=sys.stderr, flush=True)
            record_failure(url)
            continue
        except aiohttp.ClientError as e:
            print(f"[HADITH API] Client error for URL {idx}: {e}", file=sys.stderr, flush=True)
            record_failure(url)
            continue
        except Exception as e:
            print(f"[HADITH API] Error for URL {idx}: {e}", file=sys.stderr, flush=True)
            record_failure(url)
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
        collections: List of collection codes to search
        max_per_collection: Maximum results per collection
    
    Returns:
        List of hadith dictionaries
    """
    if not topic:
        print("[HADITH API] No topic provided", file=sys.stderr, flush=True)
        return []
    
    # Default to Kutub al-Sittah
    if not collections:
        collections = [
            "eng-bukhari", "eng-muslim", "eng-abudawud",
            "eng-tirmidhi", "eng-nasai", "eng-ibnmajah"
        ]
    
    print(f"[HADITH SEARCH] Searching for '{topic}' across {len(collections)} collections", file=sys.stdout, flush=True)
    
    all_matches = []
    topic_lower = topic.lower()
    
    try:
        # Configure session timeout (2s per collection)
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Fetch all collections concurrently
            tasks = [fetch_hadith_collection(session, code) for code in collections]
            collections_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process each collection
            for collection_code, hadiths in zip(collections, collections_data):
                book = collection_code.replace('eng-', '')
                
                if isinstance(hadiths, Exception):
                    print(f"[HADITH SEARCH] Error loading '{book}': {hadiths}", file=sys.stderr, flush=True)
                    continue
                
                if not hadiths:
                    print(f"[HADITH SEARCH] No hadiths for '{book}'", file=sys.stderr, flush=True)
                    continue
                
                # Search for topic in hadith texts
                matches = [h for h in hadiths if topic_lower in h.get("text", "").lower()]
                
                if matches:
                    print(f"[HADITH SEARCH] Found {len(matches)} matches in '{book}'", file=sys.stdout, flush=True)
                    
                    for match in matches[:max_per_collection]:
                        hadith_number = match.get("hadithnumber", "")
                        citation_url = f"https://sunnah.com/{book}:{hadith_number}"
                        
                        all_matches.append({
                            "text": match.get("text", ""),
                            "hadithnumber": hadith_number,
                            "arabicnumber": match.get("arabicnumber", ""),
                            "book": book,
                            "reference": match.get("reference", {}),
                            "source": f"Hadith ({book.capitalize()})",
                            "citation_url": citation_url
                        })
        
        print(f"[HADITH SEARCH] Total matches: {len(all_matches)}", file=sys.stdout, flush=True)
        return all_matches
        
    except Exception as e:
        print(f"[HADITH SEARCH] Critical error: {e}", file=sys.stderr, flush=True)
        traceback.print_exc()
        return []

# =============================================================================
# SYNCHRONOUS WRAPPERS (Backward compatibility)
# =============================================================================

def search_quran(keyword: str, max_results: int = 3) -> List[Dict]:
    """Synchronous wrapper for search_quran_async"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(search_quran_async(keyword, max_results))

def search_hadith(
    topic: str,
    collections: Optional[List[str]] = None,
    max_per_collection: int = 2
) -> List[Dict]:
    """Synchronous wrapper for search_hadith_async"""
    try:
        return asyncio.run(search_hadith_async(topic, collections, max_per_collection))
    except Exception as e:
        print(f"[HADITH SEARCH] Error in sync wrapper: {e}", file=sys.stderr, flush=True)
        return []
