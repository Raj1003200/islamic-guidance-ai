"""
Endpoint Health Check Script
Tests all API endpoints and displays status in colored console output
"""

import requests
import sys
import time
from typing import Dict, List, Tuple

# ANSI color codes for console output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")

def print_status(endpoint: str, status: str, message: str = "", response_time: float = 0):
    """Print endpoint status with color coding"""
    status_color = Colors.GREEN if status == "[OK]" else Colors.RED
    endpoint_display = f"{endpoint:<40}"
    status_display = f"{status_color}{status}{Colors.RESET}"
    time_display = f"{response_time:.3f}s" if response_time > 0 else ""
    
    print(f"{endpoint_display} {status_display:<20} {time_display}")
    if message:
        print(f"{'':40} {Colors.YELLOW}- {message}{Colors.RESET}")

def test_endpoint(base_url: str, endpoint: str, method: str = "GET", data: dict = None) -> Tuple[bool, str, float]:
    """
    Test a single endpoint
    
    Returns:
        (success, message, response_time)
    """
    url = f"{base_url}{endpoint}"
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return False, f"Unsupported method: {method}", 0
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            return True, f"Status {response.status_code}", response_time
        else:
            return False, f"Status {response.status_code}", response_time
            
    except requests.exceptions.Timeout:
        return False, "Timeout (>10s)", 0
    except requests.exceptions.ConnectionError:
        return False, "Connection refused", 0
    except Exception as e:
        return False, str(e)[:50], 0

def run_health_checks(base_url: str = "http://localhost:8000"):
    """Run comprehensive health checks on all endpoints"""
    
    print_header("ISLAMIC GUIDANCE AI - ENDPOINT HEALTH CHECK")
    print(f"{Colors.BOLD}Base URL:{Colors.RESET} {base_url}\n")
    
    # Define all endpoints to test
    endpoints = [
        # Basic endpoints
        ("GET", "/", "Root endpoint"),
        ("GET", "/api/health", "Health check"),
        
        # Search endpoints
        ("GET", "/api/quran/search?keyword=peace", "Quran search"),
        ("GET", "/api/hadith/search?topic=prayer&collections=eng-bukhari", "Hadith search"),
        ("GET", "/api/test-keywords?text=how to deal with anxiety", "Keyword extraction"),
        
        # Model management
        ("GET", "/api/models", "List Gemini models"),
        ("GET", "/api/get-api-key", "Get API key"),
        
        # Main guidance endpoint
        ("POST", "/api/guidance", "Guidance endpoint", {
            "query": "test query for health check",
            "source": "internal",
            "hadith_collection": ["eng-bukhari"]
        }),
        
        # Admin endpoints
        ("POST", "/api/admin/clear-cache", "Clear cache (admin)"),
    ]
    
    results = []
    total_tests = len(endpoints)
    passed_tests = 0
    
    print(f"{Colors.BOLD}Testing {total_tests} endpoints...{Colors.RESET}\n")
    
    for endpoint_info in endpoints:
        method = endpoint_info[0]
        endpoint = endpoint_info[1]
        description = endpoint_info[2]
        data = endpoint_info[3] if len(endpoint_info) > 3 else None
        
        success, message, response_time = test_endpoint(base_url, endpoint, method, data)
        
        status = "[OK]" if success else "[FAIL]"
        print_status(f"{description} ({method})", status, message, response_time)
        
        results.append((description, success))
        if success:
            passed_tests += 1
    
    # Print summary
    print_header("SUMMARY")
    
    success_rate = (passed_tests / total_tests) * 100
    color = Colors.GREEN if success_rate == 100 else (Colors.YELLOW if success_rate >= 70 else Colors.RED)
    
    print(f"{Colors.BOLD}Total Tests:{Colors.RESET} {total_tests}")
    print(f"{Colors.BOLD}Passed:{Colors.RESET} {color}{passed_tests}{Colors.RESET}")
    print(f"{Colors.BOLD}Failed:{Colors.RESET} {Colors.RED}{total_tests - passed_tests}{Colors.RESET}")
    print(f"{Colors.BOLD}Success Rate:{Colors.RESET} {color}{success_rate:.1f}%{Colors.RESET}\n")
    
    if passed_tests == total_tests:
        print(f"{Colors.GREEN}{Colors.BOLD}[SUCCESS] All endpoints are working correctly!{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}[ERROR] Some endpoints failed. Check the details above.{Colors.RESET}\n")
        return 1

def test_main(base_url="http://localhost:8000"):
    """Main entry point"""
    try:
        exit_code = run_health_checks(base_url)
        return exit_code
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Health check interrupted by user.{Colors.RESET}\n")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}Error running health checks: {e}{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    exit_code = test_main()
    print(f"\nExit code: {exit_code}")