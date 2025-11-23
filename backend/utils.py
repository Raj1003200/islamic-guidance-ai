import os
import sys

# List of example guidance prompts
EXAMPLE_PROMPTS = [
    "I am feeling anxious about my future and need guidance.",
    "How can I control my anger when provoked?",
    "I feel lonely and depressed, what does Islam say?",
    "I am struggling with financial difficulties.",
    "How do I improve my relationship with my parents?",
    "I am having doubts about my faith, how do I strengthen it?",
    "What is the Islamic perspective on dealing with difficult neighbors?",
    "How can I balance my work and religious obligations?",
    "I committed a sin and feel guilty, how do I seek forgiveness?",
    "How should I deal with jealousy and envy?",
    "What does Islam say about mental health and seeking therapy?",
    "How can I be more patient in times of hardship?",
    "I am struggling to wake up for Fajr prayer, any advice?",
    "How do I deal with negative thoughts and whispers (waswasa)?",
    "What is the importance of maintaining family ties?",
    "How can I improve my character and manners (Akhlaq)?",
    "I feel disconnected from Allah, how can I reconnect?",
    "What is the reward for visiting the sick?",
    "How should I handle disagreements with my spouse?",
    "What are the benefits of giving charity (Sadaqah)?",
    "How can I stop backbiting and gossiping?",
    "What is the significance of the night prayer (Tahajjud)?",
    "How do I deal with the loss of a loved one?",
    "What does Islam say about honesty and truthfulness?",
    "How can I avoid extravagance and wastefulness?",
    "What is the importance of gratitude (Shukr)?",
    "How should I treat non-Muslim colleagues and friends?",
    "What are the rights of children in Islam?",
    "How can I make my dua (supplication) more effective?",
    "What is the Islamic view on social media usage?",
    "How do I control my tongue and speech?",
    "What is the importance of seeking knowledge?",
    "How can I prepare for Ramadan?",
    "What does Islam say about justice and fairness?",
    "How should I deal with stress and burnout?",
    "What is the significance of Friday (Jumu'ah) prayer?",
    "How can I be a better friend?",
    "What are the signs of a hypocrite and how to avoid them?",
    "How do I deal with peer pressure?",
    "What is the importance of cleanliness and purity?",
    "How can I develop humility and avoid arrogance?",
    "I don't have a job, please help me through it",
    "I am sad and depressed in my life",
    "I am struggling financially and need assistance",
    "I feel overwhelmed and don't know where to turn",
    "I am facing significant personal challenges and need support",
    "I am feeling lonely and need companionship",
    "I am dealing with health issues and require help",
    "I am having trouble with my relationships and need guidance",
    "I am feeling lost and need direction in my life",
    "I am experiencing anxiety and stress and need coping strategies",
    "I am having trouble finding housing and need resources",
    "I am dealing with addiction and need treatment",
    "I am feeling hopeless and need motivation",
    "I am facing legal issues and need advice",
    "I am struggling with grief and loss and need emotional support",
    "I am feeling isolated and need social connection",
    "I am dealing with unemployment and need job search assistance",
    "I am having trouble with my education and need tutoring",
    "I am feeling burnt out and need a break or support",
    "I am experiencing discrimination and need advocacy",
    "I am dealing with a disability and need accommodations",
    "I am having trouble managing my time and need tools",
    "I am feeling angry and need anger management techniques",
    "I am facing creative blocks and need inspiration",
    "I am dealing with caregiving responsibilities and need respite",
    "I am having trouble adjusting to a new environment and need support",
    "I am feeling insecure and need to build confidence",
    "I am dealing with chronic pain and need management strategies",
    "I am having trouble managing my time and need tools",
    "I am feeling burnt out and need a break or support",
    "I am experiencing discrimination and need advocacy",
    "I am dealing with a disability and need accommodations",
    "I am having trouble managing my time and need tools",
    "I am feeling angry and need anger management techniques",
    "I am facing creative blocks and need inspiration",
    "I am dealing with caregiving responsibilities and need respite",
    "I am having trouble adjusting to a new environment and need support",
    "I am feeling insecure and need to build confidence",
    "I am dealing with chronic pain and need management strategies",
    "I am having trouble communicating effectively and need practice",
    "I am feeling disconnected from my community and need ways to connect",
    "I am struggling with sleep problems and need solutions",
    "I am dealing with trauma and need therapy",
    "I am having trouble making decisions and need clarity",
    "I am feeling unmotivated and need encouragement",
    "I am facing career changes and need guidance",
    "I am dealing with family conflicts and need mediation",
    "I am having trouble with technology and need technical support",
    "I am feeling misunderstood and need validation",
    "I am dealing with aging parents and need support",
    "I am having trouble setting boundaries and need strategies"
]

# =============================================================================
# GEMINI MODEL CONFIGURATION & SELECTION
# =============================================================================


GEMINI_MODELS = [
    {'id': 'gemini-2.0-flash-exp', 'name': 'Gemini 2.0 Flash Exp', 'input_tokens': 1048576, 'output_tokens': 65536},
    {'id': 'gemini-2.5-flash-preview', 'name': 'Gemini 2.5 Flash Preview', 'input_tokens': 1048576, 'output_tokens': 65536},
    {'id': 'gemini-2.5-pro-preview', 'name': 'Gemini 2.5 Pro Preview', 'input_tokens': 1048576, 'output_tokens': 65536},
    {'id': 'gemini-3-pro-preview', 'name': 'Gemini 3 Pro Preview', 'input_tokens': 1048576, 'output_tokens': 65536},
    {'id': 'gemini-flash-latest', 'name': 'Gemini Flash Latest', 'input_tokens': 1048576, 'output_tokens': 65536},
    {'id': 'gemini-pro-latest', 'name': 'Gemini Pro Latest', 'input_tokens': 1048576, 'output_tokens': 65536},
    {'id': 'gemini-2.5-flash-lite', 'name': 'Gemini 2.5 Flash Lite', 'input_tokens': 1048576, 'output_tokens': 65536},
    {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro', 'input_tokens': 2097152, 'output_tokens': 65536},
    {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash', 'input_tokens': 1048576, 'output_tokens': 65536},
]


def detect_serverless_environment() -> bool:
    """
    Detect if running in serverless environment (Vercel, AWS Lambda, etc.)
    
    Checks multiple environment variables for reliability:
    - VERCEL or VERCEL_ENV (Vercel)
    - AWS_LAMBDA_FUNCTION_NAME (AWS Lambda/Vercel Functions)
    - AWS_EXECUTION_ENV (AWS)
    - FUNCTION_NAME (Google Cloud Functions)
    - Filesystem write test (fallback)
    
    Returns:
        True if serverless, False if local development
    """
    # Check Vercel-specific variables
    if os.getenv("VERCEL") == "1":
        print("[DETECT] Serverless: VERCEL=1", file=sys.stdout, flush=True)
        return True
    
    if os.getenv("VERCEL_ENV"):
        print(f"[DETECT] Serverless: VERCEL_ENV={os.getenv('VERCEL_ENV')}", file=sys.stdout, flush=True)
        return True
    
    # Check AWS Lambda (Vercel uses AWS Lambda under the hood)
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        print("[DETECT] Serverless: AWS_LAMBDA_FUNCTION_NAME detected", file=sys.stdout, flush=True)
        return True
    
    if os.getenv("AWS_EXECUTION_ENV"):
        print("[DETECT] Serverless: AWS_EXECUTION_ENV detected", file=sys.stdout, flush=True)
        return True
    
    # Check Google Cloud Functions
    if os.getenv("FUNCTION_NAME"):
        print("[DETECT] Serverless: FUNCTION_NAME detected", file=sys.stdout, flush=True)
        return True
    
    # Fallback: Test filesystem writability
    try:
        test_file = "/tmp/.write_test"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        
        # If /tmp is writable but current directory is not, likely serverless
        try:
            local_test = "./.write_test"
            with open(local_test, "w") as f:
                f.write("test")
            os.remove(local_test)
            print("[DETECT] Local: Filesystem is writable", file=sys.stdout, flush=True)
            return False  # Local development
        except (OSError, PermissionError):
            print("[DETECT] Serverless: Filesystem read-only (except /tmp)", file=sys.stdout, flush=True)
            return True  # Serverless
    except Exception:
        pass