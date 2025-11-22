import os
import sys
import json
import traceback
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# Import services
from backend.services import search_quran, search_hadith

# Load environment variables
load_dotenv()

# --- Configuration ---
# Check if running in serverless environment (Vercel)
IS_SERVERLESS = os.getenv("VERCEL") == "1"

print("Loading IslamicGuideAI Backend Module...", file=sys.stdout, flush=True)

# Helper function to truncate long JSON for logging
def truncate_json_for_log(data, max_text_length=200):
    """Truncate long text fields in JSON while preserving structure"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_text_length:
                result[key] = value[:max_text_length] + f"... [TRUNCATED {len(value)-max_text_length} chars]"
            elif isinstance(value, (dict, list)):
                result[key] = truncate_json_for_log(value, max_text_length)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [truncate_json_for_log(item, max_text_length) for item in data]
    return data

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
model = None

try:
    if not API_KEY:
        print("GEMINI_API_KEY not found in .env", file=sys.stdout, flush=True)
    else:
        genai.configure(api_key=API_KEY)
        # Use gemini-2.0-flash as verified
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("Successfully configured Gemini 2.0 Flash model", file=sys.stdout, flush=True)
except Exception as e:
    print(f"Error configuring model: {e}", file=sys.stdout, flush=True)
    # Don't crash, just leave model as None

app = FastAPI()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "IslamicGuideAI", "version": "1.0.0"}

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GuidanceRequest(BaseModel):
    query: str
    source: str = "both" # internal, external, both
    hadith_collection: list = None  # Optional list of hadith book codes

class LogRequest(BaseModel):
    level: str
    message: str
    timestamp: str

@app.post("/api/log")
async def log_frontend(request: LogRequest):
    """
    Endpoint to receive logs from the frontend.
    Logs to console only (no file writing).
    """
    print(f"[FRONTEND - {request.level.upper()}] {request.message}", file=sys.stdout, flush=True)
    return {"status": "logged"}

@app.post("/api/guidance")
async def get_guidance(request: GuidanceRequest):
    print("="*80, file=sys.stdout, flush=True)
    print(f"[USER REQUEST] Received guidance request", file=sys.stdout, flush=True)
    print(f"Query: {request.query}", file=sys.stdout, flush=True)
    print(f"Source: {request.source}", file=sys.stdout, flush=True)
    print("="*80, file=sys.stdout, flush=True)
    
    if not request.query or len(request.query) < 10:
        print("Query validation failed: Query too short", file=sys.stdout, flush=True)
        raise HTTPException(status_code=400, detail="Query too short")
    
    if not model:
        print("AI model not available", file=sys.stdout, flush=True)
        raise HTTPException(status_code=503, detail="AI model not available. Please check API key configuration.")

    try:
        # 1. Check relevance (skip if clearly irrelevant, but let's assume relevant for now to save a call or do it in one go)
        # We will do it in one go with the main prompt to be efficient.
        
        context_text = ""
        citations = []
        
        # 2. Perform Search if Source is External or Both
        if request.source in ["external", "both"]:
            print("[KEYWORD EXTRACTION] Extracting keywords for search...", file=sys.stdout, flush=True)
            # Ask Gemini to extract keywords - improved to handle multi-word queries
            keyword_prompt = f"""
            Extract ALL relevant keywords from this query for searching Islamic texts (Quran/Hadith). 
            Include multi-word concepts as separate keywords.
            Return ONLY the keywords separated by commas.
            
            Examples:
            - Query: "good life partner" → life, partner, marriage, spouse
            - Query: "dealing with anxiety" → anxiety, worry, stress, peace
            
            Query: "{request.query}"
            """
            print(f"[GEMINI REQUEST] Sending keyword extraction request", file=sys.stdout, flush=True)
            print(f"[GEMINI REQUEST] Prompt: {keyword_prompt}", file=sys.stdout, flush=True)
            kw_response = model.generate_content(keyword_prompt)
            keywords = kw_response.text.strip()
            print(f"[GEMINI RESPONSE] Extracted keywords: '{keywords}'", file=sys.stdout, flush=True)
            
            
            # Search Quran
            print(f"[QURAN SEARCH] Searching Quran with keywords: '{keywords}'", file=sys.stdout, flush=True)
            quran_results = search_quran(keywords)
            print(f"[QURAN SEARCH] Found {len(quran_results, file=sys.stdout, flush=True)} Quran verses")
            
            # Search Hadith - use all keywords for better search coverage
            # Convert comma-separated keywords to list and search for each
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            all_hadith_results = []
            
            # Get selected hadith collections from request, default to Kutub al-Sittah
            selected_collections = request.hadith_collection or [
                "eng-bukhari", "eng-muslim", "eng-abudawud", 
                "eng-tirmidhi", "eng-nasai", "eng-ibnmajah"
            ]
            
            print(f"[HADITH SEARCH] Using collections: {selected_collections}", file=sys.stdout, flush=True)
            print(f"[HADITH SEARCH] Searching with {len(keyword_list, file=sys.stdout, flush=True)} keywords: {keyword_list}")
            for keyword in keyword_list:
                print(f"[HADITH SEARCH] Searching Hadith with keyword: '{keyword}'", file=sys.stdout, flush=True)
                hadith_results = search_hadith(keyword, collections=selected_collections)
                if hadith_results:
                    all_hadith_results.extend(hadith_results)
                    print(f"[HADITH SEARCH] Found {len(hadith_results, file=sys.stdout, flush=True)} Hadiths for keyword '{keyword}'")
            
            # Remove duplicates based on hadithnumber and book
            seen = set()
            unique_hadiths = []
            for h in all_hadith_results:
                key = (h.get('book', ''), h.get('hadithnumber', ''))
                if key not in seen:
                    seen.add(key)
                    unique_hadiths.append(h)
            
            print(f"[HADITH SEARCH] Total unique Hadiths found: {len(unique_hadiths, file=sys.stdout, flush=True)}")
            
            # Build Context
            if quran_results:
                context_text += "\nQuran Verses:\n"
                for idx, q in enumerate(quran_results, 1):
                    context_text += f"- {q['text']} (Surah {q['surah']} {q['number']})\n"
                    citations.append({"title": f"Quran {q['surah']} {q['number']}", "url": f"https://quran.com/{q['number']}"})
                    # Log each verse details
                    print(f"  [VERSE {idx}] Surah: {q['surah']}, Number: {q['number']}, Verse in Surah: {q['numberInSurah']}", file=sys.stdout, flush=True)
                    print(f"  [VERSE {idx}] Text: {q['text'][:200]}{'...' if len(q['text'], file=sys.stdout, flush=True) > 200 else ''}")
            else:
                print("[QURAN SEARCH] No Quran verses found", file=sys.stdout, flush=True)
            
            if unique_hadiths:
                context_text += f"\nHadiths (Found {len(unique_hadiths)}):\n"
                for idx, hadith in enumerate(unique_hadiths, 1):
                    context_text += f"- {hadith['text']} ({hadith['source']}, Hadith #{hadith['hadithnumber']})\n"
                    citations.append({
                        "title": f"{hadith['source']} - Hadith {hadith['hadithnumber']}", 
                        "url": hadith['citation_url']
                    })
                    # Log COMPLETE Hadith details being sent to Gemini (not truncated)
                    print(f"  [HADITH {idx}] Collection: {hadith.get('book', 'Unknown', file=sys.stdout, flush=True)}")
                    print(f"  [HADITH {idx}] Hadith Number: {hadith.get('hadithnumber', 'N/A', file=sys.stdout, flush=True)}")
                    print(f"  [HADITH {idx}] Arabic Number: {hadith.get('arabicnumber', 'N/A', file=sys.stdout, flush=True)}")
                    print(f"  [HADITH {idx}] Reference: {hadith.get('reference', {}, file=sys.stdout, flush=True)}")
                    print(f"  [HADITH {idx}] Citation URL: {hadith.get('citation_url', '', file=sys.stdout, flush=True)}")
                    print(f"  [HADITH {idx}] FULL Text: {hadith.get('text', '', file=sys.stdout, flush=True)}")  # Full text, not truncated
            else:
                print("[HADITH SEARCH] No Hadiths found", file=sys.stdout, flush=True)
                
            print("="*80, file=sys.stdout, flush=True)
            print(f"[SEARCH SUMMARY] Found {len(quran_results, file=sys.stdout, flush=True)} Quran verses and {len(unique_hadiths)} Hadiths")
            print("="*80, file=sys.stdout, flush=True)

        # 3. Construct Main Prompt based on Source
        base_instruction = """
        You are an Islamic Guidance AI. Provide a helpful, empathetic Islamic perspective to the user's situation.
        """
        
        if request.source == "internal":
            prompt = f"""
            {base_instruction}
            User Query: "{request.query}"
            
            Use your internal knowledge to answer.
            """
        elif request.source == "external":
            # Check if we have any sources
            has_sources = bool(quran_results or unique_hadiths)
            
            if not has_sources:
                prompt = f"""
                {base_instruction}
                User Query: "{request.query}"
                
                CONTEXT FROM SOURCES:
                Quran: No sources found
                Hadith: No sources found
                
                INSTRUCTION: No specific Quran verses or Hadiths were found for this query in our search. 
                Politely inform the user that no specific sources were found, but offer general Islamic comfort and guidance.
                Suggest they can search directly on Quran.com and Sunnah.com for more specific references.
                """
            else:
                prompt = f"""
                {base_instruction}
                User Query: "{request.query}"
                
                CONTEXT FROM SOURCES:
                {context_text}
                
                INSTRUCTION: Use ONLY the provided context above to answer. Reference the specific sources provided.
                """
        else: # both
            prompt = f"""
            {base_instruction}
            User Query: "{request.query}"
            
            CONTEXT FROM SOURCES:
            {context_text}
            
            INSTRUCTION: Combine the provided context with your own knowledge to provide a comprehensive answer. Reference the sources if they are relevant.
            """

        # Add JSON formatting instruction
        prompt += """
        
        If the query is NOT related to life situations/Islam, return: { "error": "Irrelevant problem" }
        
        Otherwise return JSON:
        {
            "answer": "Your advice here...",
            "citations": [ ... ] 
        }
        """
        
        # Note: We append our manually found citations to the AI's response later, 
        # or we can ask AI to include them. Let's append them manually to ensure they are accurate to what we found.
        
        print("[GEMINI REQUEST] Sending final guidance request to Gemini...", file=sys.stdout, flush=True)
        print(f"[GEMINI REQUEST] Prompt: {prompt}", file=sys.stdout, flush=True)
        print(f"[GEMINI REQUEST] Prompt length: {len(prompt, file=sys.stdout, flush=True)} characters")
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        print("[GEMINI RESPONSE] Received response from Gemini", file=sys.stdout, flush=True)
        response_text = response.text
        print(f"[GEMINI RESPONSE] Response length: {len(response_text, file=sys.stdout, flush=True)} characters")
        
        # Clean up
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text.strip())
        print(f"[GEMINI RESPONSE] Parsed JSON successfully", file=sys.stdout, flush=True)
        
        # Log truncated response
        truncated_data = truncate_json_for_log(data, max_text_length=150)
        print(f"[GEMINI RESPONSE] Response data: {json.dumps(truncated_data, indent=2)}", file=sys.stdout, flush=True)
        
        # Merge citations if valid answer
        if "answer" in data and request.source in ["external", "both"]:
            # We prioritize our found citations, but AI might have added some too (internal knowledge).
            # Let's just use ours for 'external' mode, and merge for 'both'.
            if request.source == "external":
                data["citations"] = citations
            else:
                # Merge avoiding duplicates (simple check)
                existing_urls = {c.get("url") for c in data.get("citations", [])}
                for c in citations:
                    if c["url"] not in existing_urls:
                        data.setdefault("citations", []).append(c)
        
        print("[SUCCESS] Returning guidance response to user", file=sys.stdout, flush=True)
        print("="*80, file=sys.stdout, flush=True)
        return data

    except Exception as e:
        print(f"Error processing request: {e}", file=sys.stdout, flush=True)
        error_msg = str(e).lower()
        if "quota" in error_msg or "resource exhausted" in error_msg or "429" in error_msg:
            raise HTTPException(status_code=429, detail="API quota exceeded. Please try again later.")
        raise HTTPException(status_code=500, detail=f"Error generating guidance: {str(e)[:100]}")

# New API endpoints for Quran and Hadith search

@app.get("/api/quran/search")
async def quran_search_endpoint(keyword: str):
    """
    Search Quran verses using the external API via Python backend.
    """
    return search_quran(keyword)

@app.get("/api/hadith/search")
async def hadith_search_endpoint(topic: str, book: str = "bukhari"):
    """
    Search Hadiths for a topic within a given collection.
    """
    return search_hadith(topic, book)



@app.get("/api/get-api-key")
async def get_api_key():
    """
    Return the Gemini API key from environment for settings page.
    In serverless/production, this returns a masked version for security.
    """
    try:
        print("[GET-API-KEY] Endpoint called", file=sys.stdout, flush=True)
        print(f"[GET-API-KEY] IS_SERVERLESS: {IS_SERVERLESS}", file=sys.stdout, flush=True)
        print(f"[GET-API-KEY] API_KEY exists: {bool(API_KEY, file=sys.stdout, flush=True)}")
        
        if IS_SERVERLESS:
            # In production, return masked key for security
            if API_KEY:
                masked_key = API_KEY[:8] + "..." + API_KEY[-4:] if len(API_KEY) > 12 else "***"
                print(f"[GET-API-KEY] Returning masked key in serverless mode", file=sys.stdout, flush=True)
                return {"apiKey": masked_key, "isProduction": True}
            else:
                print("[GET-API-KEY] No API key found in serverless environment", file=sys.stdout, flush=True)
                return {"apiKey": "", "isProduction": True}
        else:
            # In development, return full key
            print(f"[GET-API-KEY] Returning full key in development mode", file=sys.stdout, flush=True)
            return {"apiKey": API_KEY or "", "isProduction": False}
    except Exception as e:
        print(f"[GET-API-KEY] Error: {str(e)}", file=sys.stdout, flush=True)
        print(f"[GET-API-KEY] Traceback: {traceback.format_exc()}", file=sys.stdout, flush=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving API key: {str(e)}"
        )

@app.post("/api/save-api-key")
async def save_api_key(request: Request):
    """
    Save API key to .env file (development only).
    Note: This endpoint is disabled in serverless/production environments.
    """
    try:
        print("[SAVE-API-KEY] Endpoint called", file=sys.stdout, flush=True)
        print(f"[SAVE-API-KEY] IS_SERVERLESS: {IS_SERVERLESS}", file=sys.stdout, flush=True)
        
        # Disable in serverless environment
        if IS_SERVERLESS:
            print("[SAVE-API-KEY] Attempted to save API key in serverless environment", file=sys.stdout, flush=True)
            raise HTTPException(
                status_code=403,
                detail="API key saving is disabled in production. Please set GEMINI_API_KEY environment variable in Vercel dashboard."
            )
        
        # Parse request body
        try:
            body = await request.json()
            print(f"[SAVE-API-KEY] Request body parsed successfully", file=sys.stdout, flush=True)
        except Exception as e:
            print(f"[SAVE-API-KEY] Failed to parse request body: {str(e, file=sys.stdout, flush=True)}")
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        
        new_key = body.get("apiKey", "").strip()
        print(f"[SAVE-API-KEY] API key length: {len(new_key, file=sys.stdout, flush=True) if new_key else 0}")
        
        if not new_key:
            print("[SAVE-API-KEY] Empty API key provided", file=sys.stdout, flush=True)
            raise HTTPException(status_code=400, detail="API key cannot be empty")
        
        # Path to .env in root directory (one level up from backend)
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        print(f"[SAVE-API-KEY] .env path: {env_path}", file=sys.stdout, flush=True)
        
        # Read existing .env content
        env_lines = []
        key_found = False
        
        if os.path.exists(env_path):
            print(f"[SAVE-API-KEY] .env file exists, reading...", file=sys.stdout, flush=True)
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
            
            # Update existing key or mark for addition
            for i, line in enumerate(env_lines):
                if line.startswith("GEMINI_API_KEY="):
                    env_lines[i] = f"GEMINI_API_KEY={new_key}\n"
                    key_found = True
                    print(f"[SAVE-API-KEY] Updated existing key at line {i}", file=sys.stdout, flush=True)
                    break
        else:
            print(f"[SAVE-API-KEY] .env file doesn't exist, will create new", file=sys.stdout, flush=True)
        
        # Add new key if not found
        if not key_found:
            env_lines.append(f"GEMINI_API_KEY={new_key}\n")
            print(f"[SAVE-API-KEY] Added new API key", file=sys.stdout, flush=True)
        
        # Write back to .env
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(env_lines)
        print(f"[SAVE-API-KEY] Successfully wrote to .env file", file=sys.stdout, flush=True)
        
        # Reload environment (requires server restart for full effect)
        os.environ["GEMINI_API_KEY"] = new_key
        
        print("[SAVE-API-KEY] API key updated successfully", file=sys.stdout, flush=True)
        return {"success": True, "message": "API key saved. Please restart the server for changes to take full effect."}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SAVE-API-KEY] Unexpected error: {str(e)}", file=sys.stdout, flush=True)
        print(f"[SAVE-API-KEY] Traceback: {traceback.format_exc()}", file=sys.stdout, flush=True)
        raise HTTPException(status_code=500, detail=f"Error saving API key: {str(e)}")


# Mount static files (HTML, CSS, JS) - must be AFTER all API routes
# Note: In Vercel, static files are served directly by Vercel's CDN, not by the Python app
if not IS_SERVERLESS:
    # Only mount static files in local development
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    port = os.getenv("PORT", 8000)
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=port)
    print("Server started on http://localhost:" + port)
