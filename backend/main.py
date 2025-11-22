"""
Islamic Guidance AI - Main FastAPI Backend Application
Provides AI-powered Islamic guidance using Gemini AI and external Islamic text APIs
"""

import os
import sys
import json
import traceback
import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional, List

# Import async services
# Try importing services with fallback for different environments
try:
    # Try absolute import (for Vercel/Root execution)
    from backend.services import (
        search_quran_async,
        search_hadith_async
    )
    print("[SUCCESS] Loaded services from backend.services", file=sys.stdout, flush=True)
except ImportError:
    try:
        # Try relative/direct import (for local backend/ execution)
        from services import (
            search_quran_async,
            search_hadith_async
        )
        print("[SUCCESS] Loaded services from services (local)", file=sys.stdout, flush=True)
    except ImportError as e:
        print(f"[CRITICAL] Could not import services module: {e}", file=sys.stderr, flush=True)
        print(f"Current sys.path: {sys.path}", file=sys.stderr, flush=True)
        raise

# Load environment variables
load_dotenv()

# --- Environment Configuration ---
IS_SERVERLESS = os.getenv("VERCEL") == "1"
API_KEY = os.getenv("GEMINI_API_KEY")

# --- Print Configuration ---
print("="*80, file=sys.stdout, flush=True)
print("Loading IslamicGuideAI Backend Module...", file=sys.stdout, flush=True)
print(f"Environment: {'SERVERLESS (Vercel)' if IS_SERVERLESS else 'LOCAL DEVELOPMENT'}", file=sys.stdout, flush=True)
print("="*80, file=sys.stdout, flush=True)


# --- Helper Functions ---
def truncate_json_for_log(data, max_text_length=200):
    """
    Truncate long text fields in JSON while preserving structure.
    Used to make logs readable without massive text dumps.
    
    Args:
        data: Dictionary or list to truncate
        max_text_length: Maximum length for string fields
        
    Returns:
        Truncated copy of the data structure
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_text_length:
                truncated = value[:max_text_length]
                result[key] = f"{truncated}... [TRUNCATED {len(value)-max_text_length} chars]"
            elif isinstance(value, (dict, list)):
                result[key] = truncate_json_for_log(value, max_text_length)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [truncate_json_for_log(item, max_text_length) for item in data]
    return data


# --- Gemini AI Configuration ---
model = None

try:
    if not API_KEY:
        print("[WARNING] GEMINI_API_KEY not found in environment variables", file=sys.stderr, flush=True)
        print("[WARNING] AI features will be disabled until API key is configured", file=sys.stderr, flush=True)
    else:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("[SUCCESS] Successfully configured Gemini 2.0 Flash model", file=sys.stdout, flush=True)
except Exception as e:
    print(f"[ERROR] Error configuring Gemini model: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()
    model = None


# --- FastAPI Application Setup ---
app = FastAPI(
    title="Islamic Guidance AI",
    description="AI-powered Islamic guidance using Quran and Hadith",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---
class GuidanceRequest(BaseModel):
    """Request model for guidance endpoint"""
    query: str
    source: str = "both"  # Options: internal, external, both
    hadith_collection: Optional[List[str]] = None


class LogRequest(BaseModel):
    """Request model for frontend logging"""
    level: str
    message: str
    timestamp: str


class APIKeyRequest(BaseModel):
    """Request model for API key management"""
    apiKey: str


# --- API Endpoints ---

@app.get("/")
async def root():
    """
    Health check endpoint.
    Returns service status and version information.
    """
    return {
        "status": "ok",
        "service": "IslamicGuideAI",
        "version": "1.0.0",
        "environment": "serverless" if IS_SERVERLESS else "development",
        "ai_model": "gemini-2.0-flash-exp" if model else "unavailable"
    }


@app.post("/api/log")
async def log_frontend(request: LogRequest):
    """
    Endpoint to receive logs from frontend.
    Logs to console for monitoring and debugging.
    
    Args:
        request: LogRequest with level, message, and timestamp
        
    Returns:
        Status confirmation
    """
    try:
        # Map log levels to appropriate output streams
        log_output = sys.stderr if request.level.upper() in ['ERROR', 'WARNING'] else sys.stdout
        print(
            f"[FRONTEND {request.timestamp}] [{request.level.upper()}] {request.message}",
            file=log_output,
            flush=True
        )
        return {"status": "logged"}
    except Exception as e:
        print(f"[LOG ENDPOINT] Error logging frontend message: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.post("/api/guidance")
async def get_guidance(request: GuidanceRequest):
    """
    Main endpoint for AI-powered Islamic guidance.
    
    Process Flow:
    1. Validate query
    2. Extract keywords using Gemini
    3. Search Quran and Hadith APIs concurrently
    4. Generate AI response with context
    5. Return formatted response with citations
    
    Args:
        request: GuidanceRequest with query, source, and optional collections
        
    Returns:
        JSON response with answer and citations
        
    Raises:
        HTTPException: For validation errors, timeouts, or API failures
    """
    print("="*80, file=sys.stdout, flush=True)
    print(f"[GUIDANCE] New request - Query: {request.query}", file=sys.stdout, flush=True)
    print(f"[GUIDANCE] Source: {request.source}, Collections: {request.hadith_collection or 'default'}", file=sys.stdout, flush=True)
    print("="*80, file=sys.stdout, flush=True)
    
    # Validation
    if not request.query or len(request.query) < 10:
        print("[VALIDATION] Query too short (minimum 10 characters)", file=sys.stderr, flush=True)
        raise HTTPException(
            status_code=400,
            detail="Query too short. Please provide at least 10 characters."
        )
    
    if not model:
        print("[ERROR] Gemini model not available", file=sys.stderr, flush=True)
        raise HTTPException(
            status_code=503,
            detail="AI model not available. Please check API key configuration."
        )

    try:
        context_text = ""
        citations = []
        quran_results = []
        unique_hadiths = []
        
        # Perform Search if Source is External or Both
        if request.source in ["external", "both"]:
            print("[SEARCH] Extracting keywords...", file=sys.stdout, flush=True)
            
            # Extract keywords using Gemini
            keyword_prompt = f"""
Extract the 3 most relevant keywords from this query for searching Islamic texts (Quran/Hadith).
Focus on core concepts, not common words.
Return ONLY the keywords separated by commas, nothing else.

Examples:
- Query: "How to deal with a difficult life partner" → marriage, patience, relationship
- Query: "Feeling anxious about the future" → anxiety, trust, future

Query: "{request.query}"
            """
            
            print("[GEMINI REQUEST] Sending keyword extraction request", file=sys.stdout, flush=True)
            
            try:
                kw_response = model.generate_content(keyword_prompt)
                keywords = kw_response.text.strip()
                print(f"[KEYWORDS] Extracted: '{keywords}'", file=sys.stdout, flush=True)
            except Exception as e:
                print(f"[ERROR] Keyword extraction failed: {e}", file=sys.stderr, flush=True)
                # Fallback: use first 3 words from query
                keywords = " ".join(request.query.split()[:3])
                print(f"[KEYWORDS] Using fallback: '{keywords}'", file=sys.stdout, flush=True)
            
            # Prepare for concurrent searches
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            keyword_list = keyword_list[:3]  # Limit to 3 keywords max
            
            print(f"[SEARCH] Using {len(keyword_list)} keywords: {keyword_list}", file=sys.stdout, flush=True)
            
            # Get selected Hadith collections
            selected_collections = request.hadith_collection or [
                "eng-bukhari",
                "eng-muslim",
                "eng-abudawud",
                "eng-tirmidhi",
                "eng-nasai",
                "eng-ibnmajah"
            ]
            
            print(f"[SEARCH] Collections: {[c.replace('eng-', '') for c in selected_collections]}", file=sys.stdout, flush=True)
            print("[SEARCH] Starting concurrent API searches...", file=sys.stdout, flush=True)
            
            # Execute searches concurrently using asyncio.gather
            try:
                # Create search tasks
                quran_task = search_quran_async(keywords, max_results=3)
                
                hadith_tasks = [
                    search_hadith_async(
                        keyword,
                        collections=selected_collections,
                        max_per_collection=1  # Limit to 1 per collection per keyword
                    )
                    for keyword in keyword_list
                ]
                
                # Wait for all searches with timeout
                search_timeout = 8  # seconds (must be less than Vercel's limit)
                search_results = await asyncio.wait_for(
                    asyncio.gather(quran_task, *hadith_tasks, return_exceptions=True),
                    timeout=search_timeout
                )
                
                # Process Quran results
                if isinstance(search_results[0], Exception):
                    print(f"[ERROR] Quran search failed: {search_results[0]}", file=sys.stderr, flush=True)
                    quran_results = []
                else:
                    quran_results = search_results[0]
                    print(f"[SEARCH] Found {len(quran_results)} Quran verses", file=sys.stdout, flush=True)
                
                # Process Hadith results
                all_hadith_results = []
                for idx, result in enumerate(search_results[1:], 1):
                    if isinstance(result, Exception):
                        print(f"[ERROR] Hadith search {idx} failed: {result}", file=sys.stderr, flush=True)
                    elif result:
                        all_hadith_results.extend(result)
                        print(f"[SEARCH] Found {len(all_hadith_results)} total hadiths", file=sys.stdout, flush=True)
                
                # Remove duplicate hadiths
                seen = set()
                unique_hadiths = []
                for hadith in all_hadith_results:
                    key = (hadith.get('book', ''), hadith.get('hadithnumber', ''))
                    if key not in seen:
                        seen.add(key)
                        unique_hadiths.append(hadith)
                
                print(f"[SEARCH] Total unique hadiths: {len(unique_hadiths)}", file=sys.stdout, flush=True)
                
            except asyncio.TimeoutError:
                print(f"[ERROR] Searches timed out after {search_timeout}s", file=sys.stderr, flush=True)
                # Continue with empty results rather than failing
                quran_results = []
                unique_hadiths = []
            
            # Build context from search results
            if quran_results:
                context_text += "\n Quran Verses:\n"
                for idx, verse in enumerate(quran_results, 1):
                    context_text += f"- {verse['text']} (Surah {verse['surah']} {verse['number']})\n"
                    citations.append({
                        "title": f"Quran {verse['surah']} {verse['number']}",
                        "url": f"https://quran.com/{verse['number']}"
                    })
                    print(f"  [VERSE {idx}] {verse['surah']}:{verse['numberInSurah']}", file=sys.stdout, flush=True)
            else:
                print("[SEARCH] No Quran verses found", file=sys.stdout, flush=True)
            
            if unique_hadiths:
                context_text += f"\n Hadiths (Found {len(unique_hadiths)}):\n"
                for idx, hadith in enumerate(unique_hadiths, 1):
                    context_text += (
                        f"- {hadith['text']} "
                        f"({hadith['source']}, Hadith #{hadith['hadithnumber']})\n"
                    )
                    citations.append({
                        "title": f"{hadith['source']} - Hadith {hadith['hadithnumber']}",
                        "url": hadith['citation_url']
                    })
                    print(f"  [HADITH {idx}] {hadith['book']}:{hadith['hadithnumber']}", file=sys.stdout, flush=True)
            else:
                print("[SEARCH] No hadiths found", file=sys.stdout, flush=True)
            
            print("="*80, file=sys.stdout, flush=True)
            print(
                f"[SEARCH SUMMARY] Results: {len(quran_results)} Quran verses, "
                f"{len(unique_hadiths)} Hadiths",
                file=sys.stdout, 
                flush=True
            )
            print("="*80, file=sys.stdout, flush=True)

        # Construct Gemini prompt based on source selection
        base_instruction = """
You are an Islamic Guidance AI assistant. Provide helpful, empathetic Islamic perspective 
to the user's question with wisdom from Islamic teachings.
        """
        
        if request.source == "internal":
            # Use only Gemini's internal knowledge
            prompt = f"""
{base_instruction}

User Query: "{request.query}"

Use your internal knowledge of Islamic teachings to provide guidance.
            """
            
        elif request.source == "external":
            # Use only external sources
            has_sources = bool(quran_results or unique_hadiths)
            
            if not has_sources:
                prompt = f"""
{base_instruction}

User Query: "{request.query}"

CONTEXT FROM SOURCES:
[NO RESULTS] Quran: No specific verses found
[NO RESULTS] Hadith: No specific hadiths found

INSTRUCTION: No specific Quran verses or Hadiths were found for this query. 
Politely inform the user that no specific sources were found in our search, 
but offer general Islamic comfort and guidance based on well-known Islamic principles.
Suggest they can search directly on Quran.com and Sunnah.com for more references.
                """
            else:
                prompt = f"""
{base_instruction}

User Query: "{request.query}"

CONTEXT FROM SOURCES:
{context_text}

INSTRUCTION: Use ONLY the provided context above to answer. 
Reference the specific sources provided. If the context doesn't fully 
answer the question, acknowledge this limitation.
                """
                
        else:  # both
            prompt = f"""
{base_instruction}

User Query: "{request.query}"

CONTEXT FROM SOURCES:
{context_text}

INSTRUCTION: Combine the provided context with your knowledge of Islamic 
teachings to provide comprehensive guidance. Prioritize the provided sources 
when available, and supplement with general Islamic knowledge where appropriate.
            """

        # Add response format instruction
        prompt += """

RESPONSE FORMAT:
If the query is NOT related to Islamic guidance, life situations, or faith questions, return:
{ "error": "This question is not related to Islamic guidance. Please ask about Islamic teachings, life situations from an Islamic perspective, or faith-related matters." }

Otherwise return JSON:
{
    "answer": "Your detailed, compassionate guidance here...",
    "citations": []
}

Note: Citations will be added automatically from the sources. Focus on providing a thoughtful answer.
        """
        
        print("[GEMINI] Sending final guidance request...", file=sys.stdout, flush=True)
        print(f"[GEMINI] Prompt length: {len(prompt)} characters", file=sys.stdout, flush=True)
        print(f"[GEMINI] Context length: {len(context_text)} characters", file=sys.stdout, flush=True)
        
        try:
            # Generate response with JSON format
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            print("[GEMINI] Received response", file=sys.stdout, flush=True)
            response_text = response.text
            print(f"[GEMINI] Response length: {len(response_text)} characters", file=sys.stdout, flush=True)
            
            # Clean up JSON response
            if response_text.startswith("```"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            data = json.loads(response_text.strip())
            print("[GEMINI] Successfully parsed JSON", file=sys.stdout, flush=True)
            
            # Print truncated response for debugging
            truncated_data = truncate_json_for_log(data, max_text_length=150)
            print(f"[GEMINI] Data preview: {json.dumps(truncated_data, indent=2)}", file=sys.stdout, flush=True)
            
            # Merge citations if we have a valid answer
            if "answer" in data and request.source in ["external", "both"]:
                if request.source == "external":
                    # Use only our found citations for external mode
                    data["citations"] = citations
                else:
                    # Merge citations for 'both' mode (avoid duplicates)
                    existing_urls = {c.get("url") for c in data.get("citations", [])}
                    for citation in citations:
                        if citation["url"] not in existing_urls:
                            data.setdefault("citations", []).append(citation)
            
            print("[SUCCESS] Returning guidance response", file=sys.stdout, flush=True)
            print("="*80, file=sys.stdout, flush=True)
            return data
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON response: {e}", file=sys.stderr, flush=True)
            print(f"[ERROR] Raw response: {response_text[:500]}", file=sys.stderr, flush=True)
            raise HTTPException(
                status_code=500,
                detail="AI model returned invalid response format"
            )

    except asyncio.TimeoutError:
        print("[TIMEOUT] Request exceeded time limit", file=sys.stderr, flush=True)
        raise HTTPException(
            status_code=504,
            detail="Request timed out. Please try a simpler query or try again."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        
        # Check for specific error types
        error_msg = str(e).lower()
        if "quota" in error_msg or "resource exhausted" in error_msg or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exhausted API request from server"
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error generating guidance: {str(e)[:100]}"
        )


@app.get("/api/quran/search")
async def quran_search_endpoint(keyword: str):
    """
    Direct Quran search endpoint.
    
    Args:
        keyword: Search term for Quran verses
        
    Returns:
        List of matching verses
    """
    try:
        print(f"[API ENDPOINT] Quran search request: '{keyword}'", file=sys.stdout, flush=True)
        results = await search_quran_async(keyword, max_results=5)
        return {"results": results, "count": len(results)}
    except Exception as e:
        print(f"[QURAN ENDPOINT] Error: {e}", file=sys.stdout, flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hadith/search")
async def hadith_search_endpoint(
    topic: str,
    collections: Optional[str] = None
):
    """
    Direct Hadith search endpoint.
    
    Args:
        topic: Search term for Hadiths
        collections: Comma-separated collection codes (optional)
        
    Returns:
        List of matching hadiths
    """
    try:
        print(f"[API ENDPOINT] Hadith search request: '{topic}'", file=sys.stdout, flush=True)
        
        # Parse collections if provided
        collection_list = None
        if collections:
            collection_list = [c.strip() for c in collections.split(',') if c.strip()]
        
        results = await search_hadith_async(
            topic,
            collections=collection_list,
            max_per_collection=3
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        print(f"[ERROR] HADITH ENDPOINT: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get-api-key")
async def get_api_key():
    """
    Return the Gemini API key (masked in production).
    Used by settings page to display current configuration.
    
    Returns:
        API key (masked if in production) and environment flag
    """
    try:
        print("[GET-API-KEY] Request received", file=sys.stdout, flush=True)
        print(f"[GET-API-KEY] Environment: {'Serverless' if IS_SERVERLESS else 'Development'}", file=sys.stdout, flush=True)
        
        if IS_SERVERLESS:
            # In production, return masked key for security
            if API_KEY:
                masked_key = (
                    API_KEY[:8] + "..." + API_KEY[-4:]
                    if len(API_KEY) > 12
                    else "***"
                )
                print("[GET-API-KEY] Returning masked key", file=sys.stdout, flush=True)
                return {"apiKey": masked_key, "isProduction": True}
            else:
                print("[WARNING] GET-API-KEY: No API key configured", file=sys.stderr, flush=True)
                return {"apiKey": "", "isProduction": True}
        else:
            # In development, return full key
            print("[GET-API-KEY] Returning full key (development mode)", file=sys.stdout, flush=True)
            return {"apiKey": API_KEY or "", "isProduction": False}
            
    except Exception as e:
        print(f"[ERROR] GET-API-KEY: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving API key: {str(e)}"
        )


@app.post("/api/save-api-key")
async def save_api_key(request: APIKeyRequest):
    """
    Save API key to .env file (development only).
    Disabled in serverless/production environments.
    
    Args:
        request: APIKeyRequest with new API key
        
    Returns:
        Success message and instructions
        
    Raises:
        HTTPException: If used in production or if save fails
    """
    try:
        print("[SAVE-API-KEY] Request received", file=sys.stdout, flush=True)
        
        # Disable in serverless environment
        if IS_SERVERLESS:
            print("[WARNING] SAVE-API-KEY: Attempted in serverless environment", file=sys.stderr, flush=True)
            raise HTTPException(
                status_code=403,
                detail=(
                    "API key saving is disabled in production. "
                    "Please set GEMINI_API_KEY environment variable in Vercel dashboard."
                )
            )
        
        new_key = request.apiKey.strip()
        
        if not new_key:
            print("[WARNING] SAVE-API-KEY: Empty API key provided", file=sys.stderr, flush=True)
            raise HTTPException(status_code=400, detail="API key cannot be empty")
        
        # Path to .env file in root directory
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        print(f"[SAVE-API-KEY] .env path: {env_path}", file=sys.stdout, flush=True)
        
        # Read existing .env content
        env_lines = []
        key_found = False
        
        if os.path.exists(env_path):
            print("[SAVE-API-KEY] Reading existing .env file", file=sys.stdout, flush=True)
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
            
            # Update existing key
            for i, line in enumerate(env_lines):
                if line.startswith("GEMINI_API_KEY="):
                    env_lines[i] = f"GEMINI_API_KEY={new_key}\n"
                    key_found = True
                    print("[SAVE-API-KEY] Updated existing key", file=sys.stdout, flush=True)
                    break
        else:
            print("[SAVE-API-KEY] Creating new .env file", file=sys.stdout, flush=True)
        
        # Add new key if not found
        if not key_found:
            env_lines.append(f"GEMINI_API_KEY={new_key}\n")
            print("[SAVE-API-KEY] Added new key", file=sys.stdout, flush=True)
        
        # Write to .env file
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(env_lines)
        
        print("[SAVE-API-KEY] Successfully saved to .env", file=sys.stdout, flush=True)
        
        # Update environment variable (requires restart for full effect)
        os.environ["GEMINI_API_KEY"] = new_key
        
        return {
            "success": True,
            "message": (
                "API key saved successfully. "
                "Please restart the server for changes to take full effect."
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] SAVE-API-KEY: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error saving API key: {str(e)}"
        )


# Mount static files for local development only
if not IS_SERVERLESS:
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
        if os.path.exists(frontend_path):
            app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
            print(f"[SUCCESS] Mounted static files from: {frontend_path}", file=sys.stdout, flush=True)
        else:
            print(f"[WARNING] Frontend directory not found: {frontend_path}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[ERROR] Error mounting static files: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()


# Main entry point for local development
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("="*80, file=sys.stdout, flush=True)
    print(">>> Starting Islamic Guidance AI server...", file=sys.stdout, flush=True)
    print(f"[HOST] {host}", file=sys.stdout, flush=True)
    print(f"[PORT] {port}", file=sys.stdout, flush=True)
    print(f"[URL] http://localhost:{port}", file=sys.stdout, flush=True)
    print("="*80, file=sys.stdout, flush=True)
    
    uvicorn.run(app, host=host,port=port, log_level="info")
