import os
import sys

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