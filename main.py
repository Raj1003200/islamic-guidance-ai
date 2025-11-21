import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Warning: GEMINI_API_KEY not found in .env")

genai.configure(api_key=API_KEY)
try:
    model = genai.GenerativeModel('gemini-3-pro-preview')
    print("Successfully configured Gemini 3 Pro Preview model")
except Exception as e:
    print(f"Error configuring model: {e}")

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

@app.post("/api/guidance")
async def get_guidance(request: GuidanceRequest):
    print(f"Received guidance request: {request.query}")
    if not request.query or len(request.query) < 10:
        print("Query too short")
        raise HTTPException(status_code=400, detail="Query too short")

    try:
        # Check for "irrelevant" queries (simple heuristic or ask Gemini)
        # We'll ask Gemini to be the judge and format the response as JSON
        
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
        
        print("Sending request to Gemini...")
        response = model.generate_content(prompt)
        print(f"Gemini response received. Candidate count: {len(response.candidates)}")
        
        response_text = response.text
        print(f"Raw response text: {response_text[:200]}...") # Log first 200 chars
        
        # Clean up potential markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text.strip())
        print("Successfully parsed JSON response")
        
        return data

    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files (HTML, CSS, JS)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
