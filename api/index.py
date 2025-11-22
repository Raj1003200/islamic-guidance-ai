"""
Vercel serverless function entry point
This file is required by Vercel to run the FastAPI application
"""

from backend.main import app

# Vercel expects a variable named 'app' or 'handler'
# FastAPI app is already defined in backend.main
