"""
Script to fetch all available Gemini models from Google AI API
"""

import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env file")
    sys.exit(1)

# Configure Gemini
genai.configure(api_key=API_KEY)

print("="*80)
print("FETCHING AVAILABLE GEMINI MODELS")
print("="*80)

# Get all models
models = genai.list_models()

# Filter for generative models only
generative_models = []

for model in models:
    # Only include models that support generateContent
    if 'generateContent' in model.supported_generation_methods:
        model_name = model.name.replace('models/', '')
        display_name = model.display_name if hasattr(model, 'display_name') else model_name
        
        # Format display name (convert kebab-case to Title Case)
        formatted_name = ' '.join(word.capitalize() for word in model_name.replace('-', ' ').split())
        
        generative_models.append({
            'id': model_name,
            'display_name': formatted_name,
            'description': model.description if hasattr(model, 'description') else '',
            'input_token_limit': model.input_token_limit if hasattr(model, 'input_token_limit') else 'Unknown',
            'output_token_limit': model.output_token_limit if hasattr(model, 'output_token_limit') else 'Unknown'
        })

print(f"\nFound {len(generative_models)} generative models:\n")

for idx, model in enumerate(generative_models, 1):
    print(f"{idx}. {model['display_name']}")
    print(f"   ID: {model['id']}")
    print(f"   Input Tokens: {model['input_token_limit']}")
    print(f"   Output Tokens: {model['output_token_limit']}")
    if model['description']:
        print(f"   Description: {model['description'][:100]}...")
    print()

print("="*80)
print("GENERATING PYTHON DICTIONARY")
print("="*80)

# Generate Python code
print("\nGEMINI_MODELS = [")
for model in generative_models:
    print(f"    {{")
    print(f"        'id': '{model['id']}',")
    print(f"        'name': '{model['display_name']}',")
    print(f"        'input_tokens': {model['input_token_limit']},")
    print(f"        'output_tokens': {model['output_token_limit']}")
    print(f"    }},")
print("]")

print("\n" + "="*80)
print("Copy the dictionary above to your backend code!")
print("="*80)
