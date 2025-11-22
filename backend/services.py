import requests
import urllib.parse
import logging
import time

logger = logging.getLogger("IslamicGuideAI")

def search_quran(keyword: str):
    """
    Search Quran verses using the external API.
    Returns top 3 matches.
    """
    if not keyword:
        logger.warning("[QURAN API] No keyword provided, returning empty results")
        return []
        
    encoded = urllib.parse.quote(keyword)
    url = f"https://api.alquran.cloud/v1/search/{encoded}/all/en"
    logger.info(f"[QURAN API] Request URL: {url}")
    logger.info(f"[QURAN API] Request Method: GET")
    logger.info(f"[QURAN API] Request Timeout: 10 seconds")
    
    try:
        start_time = time.time()
        resp = requests.get(url, timeout=10)
        elapsed_time = time.time() - start_time
        
        logger.info(f"[QURAN API] Response Status: {resp.status_code}")
        logger.info(f"[QURAN API] Response Time: {elapsed_time:.2f} seconds")
        logger.info(f"[QURAN API] Response Headers: {dict(resp.headers)}")
        logger.info(f"[QURAN API] Response Size: {len(resp.content)} bytes")
        
        if resp.status_code == 200:
            data = resp.json()
            total_matches = data.get("data", {}).get("count", 0)
            logger.info(f"[QURAN API] Total matches found: {total_matches}")
            logger.info(f"[QURAN API] Response JSON structure: code={data.get('code')}, status={data.get('status')}")
            
            if data.get("data") and data["data"].get("matches"):
                results = [
                    {
                        "text": m["text"],
                        "surah": m["surah"]["englishName"],
                        "number": m["number"],
                        "numberInSurah": m["numberInSurah"],
                        "source": "Quran"
                    }
                    for m in data["data"]["matches"][:3]
                ]
                logger.info(f"[QURAN API] Returning top {len(results)} results")
                for idx, result in enumerate(results, 1):
                    logger.info(f"[QURAN API] Result {idx}: Surah {result['surah']}, Verse {result['numberInSurah']}")
                    logger.info(f"[QURAN API] Result {idx} Text: {result['text'][:100]}...")
                return results
        else:
            logger.error(f"[QURAN API] API returned status code {resp.status_code}")
            logger.error(f"[QURAN API] Response Body: {resp.text[:500]}...")
    except requests.exceptions.Timeout:
        logger.error(f"[QURAN API] Request timed out after 10 seconds")
    except requests.exceptions.RequestException as e:
        logger.error(f"[QURAN API] Request failed: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"[QURAN API] Error searching Quran: {e}", exc_info=True)
    
    logger.info("[QURAN API] No results found, returning empty list")
    return []

def search_hadith(topic: str, collections: list = None):
    """
    Search Hadiths for a topic across specified or all major collections.
    Returns a list of matching hadiths from all collections.
    
    Args:
        topic: The topic to search for
        collections: List of collection codes (e.g., ['eng-bukhari', 'eng-muslim'])
                    If None, searches all major collections
    """
    if not topic:
        logger.warning("[HADITH API] No topic provided, returning empty list")
        return []
    
    # Default to all major collections if none specified
    if not collections:
        collections = ["eng-bukhari", "eng-muslim", "eng-abudawud", "eng-tirmidhi", "eng-nasai", "eng-ibnmajah"]
    
    # Remove 'eng-' prefix if present for logging
    collection_names = [c.replace('eng-', '') for c in collections]
    
    all_matches = []
    
    logger.info(f"[HADITH SEARCH] Starting search for topic: '{topic}' across {len(collections)} collections")
    logger.info(f"[HADITH SEARCH] Collections: {', '.join(collection_names)}")
    logger.info("="*80)
    
    for collection_code in collections:
        # Extract book name (remove 'eng-' prefix if present)
        book = collection_code.replace('eng-', '') if collection_code.startswith('eng-') else collection_code
        logger.info(f"[HADITH API] Searching in collection: '{book}'")
        
        base = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
        urls = [
            f"{base}/eng-{book}.min.json",
            f"{base}/eng-{book}.json",
            f"https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions/eng-{book}.min.json",
        ]
        
        hadiths = None
        for idx, u in enumerate(urls, 1):
            try:
                logger.info(f"[HADITH API] Attempt {idx}/{len(urls)} - Request URL: {u}")
                logger.info(f"[HADITH API] Request Method: GET")
                logger.info(f"[HADITH API] Request Timeout: 10 seconds")
                
                start_time = time.time()
                r = requests.get(u, timeout=10)
                elapsed_time = time.time() - start_time
                
                logger.info(f"[HADITH API] Response Status: {r.status_code}")
                logger.info(f"[HADITH API] Response Time: {elapsed_time:.2f} seconds")
                logger.info(f"[HADITH API] Response Headers: {dict(r.headers)}")
                logger.info(f"[HADITH API] Response Size: {len(r.content)} bytes")
                
                if r.status_code == 200:
                    json_data = r.json()
                    logger.info(f"[HADITH API] Response JSON keys: {list(json_data.keys())}")
                    
                    if json_data.get("hadiths"):
                        hadiths = json_data["hadiths"]
                        logger.info(f"[HADITH API] Successfully loaded {len(hadiths)} hadiths from '{book}' collection")
                        metadata = json_data.get('metadata', {})
                        if metadata:
                            logger.info(f"[HADITH API] Metadata - Name: {metadata.get('name', 'N/A')}, Sections: {len(metadata.get('sections', {}))}")
                        break
                    else:
                        logger.warning(f"[HADITH API] No 'hadiths' key in response from URL {idx}")
                else:
                    logger.warning(f"[HADITH API] Status {r.status_code} from URL {idx}")
                    logger.warning(f"[HADITH API] Response Body: {r.text[:200]}...")
            except requests.exceptions.Timeout:
                logger.warning(f"[HADITH API] Request timed out for URL {idx}")
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"[HADITH API] Request failed for URL {idx}: {e}")
                continue
            except Exception as e:
                logger.warning(f"[HADITH API] Failed to load from URL {idx}: {e}")
                continue
                
        if not hadiths:
            logger.warning(f"[HADITH API] Could not load hadith collection '{book}' from any URL")
            continue
            
        topic_lower = topic.lower()
        logger.info(f"[HADITH API] Searching for '{topic}' in {len(hadiths)} hadiths from '{book}'...")
        
        # Search for topic in hadith text
        matches = [h for h in hadiths if topic_lower in h.get("text", "").lower()]
        
        if matches:
            logger.info(f"[HADITH API] Found {len(matches)} matches in '{book}'")
            # Take top 2 matches from each collection to avoid overwhelming results
            for match in matches[:2]:
                hadith_number = match.get("hadithnumber", "")
                # Create proper citation URL
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
                
                # Log each match details
                logger.info(f"  [MATCH] Collection: {book}, Hadith #: {hadith_number}")
                logger.info(f"  [MATCH] URL: {citation_url}")
                logger.info(f"  [MATCH] Text Preview: {match.get('text', '')[:150]}...")
        else:
            logger.info(f"[HADITH API] No matches found in '{book}'")
    
    logger.info("="*80)
    logger.info(f"[HADITH SEARCH] Total matches found across all collections: {len(all_matches)}")
    
    if all_matches:
        logger.info(f"[HADITH SEARCH] Returning {len(all_matches)} Hadith results")
        for idx, h in enumerate(all_matches, 1):
            logger.info(f"  [{idx}] {h['book'].capitalize()}: {h['hadithnumber']} - {h['citation_url']}")
    else:
        logger.info("[HADITH SEARCH] No matching hadiths found in any collection")
    
    return all_matches
