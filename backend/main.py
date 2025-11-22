import os
import json
import uvicorn
import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# --- Logging Configuration ---
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "backend")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MuslimGuideAI")

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    logger.warning("GEMINI_API_KEY not found in .env")

genai.configure(api_key=API_KEY)
try:
    # Use gemini-2.0-flash as verified
    model = genai.GenerativeModel('gemini-2.0-flash')
    logger.info("Successfully configured Gemini 2.0 Flash model")
except Exception as e:
    logger.error(f"Error configuring model: {e}")
    model = None

app = FastAPI()

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

class LogRequest(BaseModel):
    level: str
    message: str
    timestamp: str

@app.post("/api/log")
async def log_frontend(request: LogRequest):
    """
    Endpoint to receive logs from the frontend.
    """
    frontend_log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "frontend")
    os.makedirs(frontend_log_dir, exist_ok=True)
    frontend_log_file = os.path.join(frontend_log_dir, "frontend.log")
    
    log_entry = f"{request.timestamp} - FRONTEND - {request.level.upper()} - {request.message}\n"
    
    try:
        with open(frontend_log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        return {"status": "logged"}
    except Exception as e:
        logger.error(f"Failed to write frontend log: {e}")
        raise HTTPException(status_code=500, detail="Failed to write log")

@app.post("/api/guidance")
async def get_guidance(request: GuidanceRequest):
    logger.info(f"Received guidance request: {request.query}")
    if not request.query or len(request.query) < 10:
        logger.warning("Query too short")
        raise HTTPException(status_code=400, detail="Query too short")
    
    if not model:
        logger.error("AI model not available")
        raise HTTPException(status_code=503, detail="AI model not available. Please check API key configuration.")

    try:
        prompt = f"""
        You are an Islamic Guidance AI. A user has asked: "{request.query}"
        
        If this is NOT a request for advice, guidance, or related to life situations/Islam (e.g., "hello", "test", "weather"), return exactly this JSON:
        {{ "error": "Irrelevant problem" }}
        
        If it IS a valid request, provide a helpful, empathetic Islamic perspective.
        Return a JSON object with this structure:
        {{
            "answer": "Your advice here...",
            "citations": [
                {{ "title": "Quran 2:153", "url": "https://quran.com/2/153" }},
                {{ "title": "Sahih Bukhari 123", "url": "https://sunnah.com/bukhari:123" }}
            ]
        }}
        
        Ensure the citations are real and relevant if possible. If no specific citation is needed, leave the array empty.
        """
        
        logger.info("Sending request to Gemini...")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        logger.info(f"Gemini response received. Candidate count: {len(response.candidates)}")
        
        response_text = response.text
        logger.debug(f"Raw response text: {response_text[:200]}...") 
        
        # Clean up potential markdown code blocks (redundant with response_mime_type but safe)
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text.strip())
        logger.info("Successfully parsed JSON response")
        
        return data

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        error_msg = str(e)
        if "quota" in error_msg.lower():
            raise HTTPException(status_code=429, detail="API quota exceeded. Please try again later.")
        raise HTTPException(status_code=500, detail=f"Error generating guidance: {str(e)[:100]}")

# New API endpoints for Quran and Hadith search

@app.get("/api/quran/search")
async def quran_search(keyword: str):
    """
    Search Quran verses using the external API via Python backend.
    """
    import requests, urllib.parse
    encoded = urllib.parse.quote(keyword)
    url = f"https://api.alquran.cloud/v1/search/{encoded}/all/en"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data") and data["data"].get("matches"):
                # Return top 3 matches
                return [
                    {
                        "text": m["text"],
                        "surah": m["surah"]["englishName"],
                        "number": m["number"],
                        "numberInSurah": m["numberInSurah"],
                    }
                    for m in data["data"]["matches"][:3]
                ]
    except Exception as e:
        logger.error(f"Error searching Quran: {e}")
    return []

@app.get("/api/hadith/search")
async def hadith_search(topic: str, book: str = "muslim"):
    """
    Search Hadiths for a topic within a given collection.
    """
    import requests
    base = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
    urls = [
        f"{base}/eng-{book}.min.json",
        f"{base}/eng-{book}.json",
        f"https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions/eng-{book}.min.json",
    ]
    hadiths = None
    for u in urls:
        try:
            r = requests.get(u, timeout=10)
            if r.status_code == 200 and r.json().get("hadiths"):
                hadiths = r.json()["hadiths"]
                break
        except Exception:
            continue
    if not hadiths:
        return None
    topic_lower = topic.lower()
    matches = [h for h in hadiths if topic_lower in h.get("text", "").lower()]
    return matches[0] if matches else None


@app.get("/api/get-api-key")
async def get_api_key():
    """
    Return the Gemini API key from environment for settings page.
    """
    return {"apiKey": API_KEY or ""}

@app.post("/api/save-api-key")
async def save_api_key(request: dict):
    """
    Save API key to .env file (development only).
    """
    try:
        new_key = request.get("apiKey", "").strip()
        if not new_key:
            raise HTTPException(status_code=400, detail="API key cannot be empty")
        
        # Path to .env in root directory (one level up from backend)
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        
        # Read existing .env content
        env_lines = []
        key_found = False
        
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
            
            # Update existing key or mark for addition
            for i, line in enumerate(env_lines):
                if line.startswith("GEMINI_API_KEY="):
                    env_lines[i] = f"GEMINI_API_KEY={new_key}\n"
                    key_found = True
                    break
        
        # Add new key if not found
        if not key_found:
            env_lines.append(f"GEMINI_API_KEY={new_key}\n")
        
        # Write back to .env
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(env_lines)
        
        # Reload environment (requires server restart for full effect)
        os.environ["GEMINI_API_KEY"] = new_key
        
        logger.info("API key updated successfully")
        return {"success": True, "message": "API key saved. Please restart the server for changes to take full effect."}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving API key: {str(e)}")

# Mount static files (HTML, CSS, JS) - must be AFTER all API routes
# Pointing to the 'frontend' directory which is one level up from 'backend'
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

