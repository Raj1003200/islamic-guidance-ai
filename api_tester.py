"""
API Tester and Response Analyzer
Tests Quran and Hadith APIs and saves their JSON responses
"""

import requests
import json
import urllib.parse
from typing import Dict, Any, List
import os
import logging

# Configure basic logging for detailed API request tracing
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class APITester:
    """Test and analyze Quran and Hadith APIs"""
    
    def __init__(self):
        self.output_dir = "api_responses"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Hadith API endpoints
        self.hadith_apis = [
            {
                "name": "eng-abudawud",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-abudawud.json"
            },
            {
                "name": "eng-bukhari",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-bukhari.json"
            },
            {
                "name": "eng-dehlawi",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-dehlawi.json"
            },
            {
                "name": "eng-ibnmajah",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-ibnmajah.json"
            },
            {
                "name": "eng-malik",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-malik.json"
            },
            {
                "name": "eng-muslim",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-muslim.json"
            },
            {
                "name": "eng-nasai",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-nasai.json"
            },
            {
                "name": "eng-nawawi",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-nawawi.json"
            },
            {
                "name": "eng-qudsi",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-qudsi.json"
            },
            {
                "name": "eng-tirmidhi",
                "link": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-tirmidhi.json"
            }
        ]
    
    def test_quran_api(self, search_text: str = "Heaven") -> Dict[str, Any]:
        """
        Test Quran API with a search query
        
        Args:
            search_text: Text to search for in the Quran
            
        Returns:
            API response data
        """
        print(f"\n{'='*80}")
        print(f"Testing Quran API - Search: '{search_text}'")
        print(f"{'='*80}")
        
        # URL encode the search text
        encoded_text = urllib.parse.quote(search_text)
        url = f"https://api.alquran.cloud/v1/search/{encoded_text}/all/en"
        
        print(f"URL: {url}")
        logging.info(f"Sending GET request to Quran API: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            logging.info(f"Received response with status code {response.status_code} (elapsed: {response.elapsed.total_seconds():.2f}s)")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Save response to file
                filename = f"{self.output_dir}/quran_search_{search_text.replace(' ', '_')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"[OK] Response saved to: {filename}")
                logging.info(f"Response saved to: {filename}")
                
                # Analyze structure
                print("\n--- Response Structure Analysis ---")
                print(f"Top-level keys: {list(data.keys())}")
                
                if 'code' in data:
                    print(f"Code: {data['code']}")
                
                if 'data' in data:
                    print(f"Data keys: {list(data['data'].keys())}")
                    
                    if 'matches' in data['data']:
                        matches = data['data']['matches']
                        print(f"Number of matches: {len(matches)}")
                        
                        if matches:
                            print("\n--- First Match Structure ---")
                            first_match = matches[0]
                            print(f"Match keys: {list(first_match.keys())}")
                            print(f"Sample match:")
                            print(json.dumps(first_match, indent=2, ensure_ascii=False)[:500])
                
                return data
            else:
                print(f"[ERROR] Status code {response.status_code}")
                logging.error(f"Quran API returned status code {response.status_code}")
                return {"error": f"Status code {response.status_code}"}
                
        except Exception as e:
            print(f"[ERROR] Exception: {str(e)}")
            logging.error(f"Exception during Quran API request: {str(e)}")
            return {"error": str(e)}
    
    def test_hadith_api(self, api_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Test a single Hadith API endpoint
        
        Args:
            api_info: Dictionary with 'name' and 'link' keys
            
        Returns:
            API response data
        """
        name = api_info['name']
        url = api_info['link']
        
        print(f"\n{'='*80}")
        print(f"Testing Hadith API - {name}")
        print(f"{'='*80}")
        print(f"URL: {url}")
        logging.info(f"Sending GET request to Hadith API ({name}): {url}")
        
        try:
            response = requests.get(url, timeout=15)
            logging.info(f"Received response with status code {response.status_code} (elapsed: {response.elapsed.total_seconds():.2f}s)")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Save response to file
                filename = f"{self.output_dir}/hadith_{name}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"[OK] Response saved to: {filename}")
                logging.info(f"Response saved to: {filename}")
                
                # Analyze structure
                print("\n--- Response Structure Analysis ---")
                print(f"Top-level keys: {list(data.keys())}")
                
                # Analyze metadata
                if 'metadata' in data:
                    print(f"Metadata keys: {list(data['metadata'].keys())}")
                
                # Analyze hadiths
                if 'hadiths' in data:
                    hadiths = data['hadiths']
                    print(f"Number of hadiths: {len(hadiths)}")
                    
                    if hadiths:
                        print("\n--- First Hadith Structure ---")
                        first_hadith = hadiths[0]
                        print(f"Hadith keys: {list(first_hadith.keys())}")
                        print(f"Sample hadith:")
                        print(json.dumps(first_hadith, indent=2, ensure_ascii=False)[:500])
                
                return data
            else:
                print(f"[ERROR] Status code {response.status_code}")
                logging.error(f"Hadith API ({name}) returned status code {response.status_code}")
                return {"error": f"Status code {response.status_code}"}
                
        except Exception as e:
            print(f"[ERROR] Exception: {str(e)}")
            logging.error(f"Exception during Hadith API request ({name}): {str(e)}")
            return {"error": str(e)}
    
    def test_all_hadith_apis(self) -> Dict[str, Any]:
        """Test all Hadith API endpoints"""
        print(f"\n{'#'*80}")
        print("TESTING ALL HADITH APIs")
        print(f"{'#'*80}")
        
        results = {}
        
        for api_info in self.hadith_apis:
            result = self.test_hadith_api(api_info)
            results[api_info['name']] = {
                'success': 'error' not in result,
                'data': result
            }
        
        return results
    
    def test_quran_with_multiple_queries(self) -> Dict[str, Any]:
        """Test Quran API with multiple search queries"""
        print(f"\n{'#'*80}")
        print("TESTING QURAN API WITH MULTIPLE QUERIES")
        print(f"{'#'*80}")
        
        test_queries = [
            "Heaven",
            "Debt",
            "Comfort",
            "Patience",
            "This is a test"  # Multi-word query
        ]
        
        results = {}
        
        for query in test_queries:
            result = self.test_quran_api(query)
            results[query] = {
                'success': 'error' not in result,
                'data': result
            }
        
        return results
    
    def generate_summary_report(self):
        """Generate a summary report of all API tests"""
        print(f"\n{'#'*80}")
        print("API TESTING SUMMARY REPORT")
        print(f"{'#'*80}")
        
        # Count files in output directory
        files = os.listdir(self.output_dir)
        quran_files = [f for f in files if f.startswith('quran_')]
        hadith_files = [f for f in files if f.startswith('hadith_')]
        
        print(f"\nTotal API responses saved: {len(files)}")
        print(f"  - Quran API responses: {len(quran_files)}")
        print(f"  - Hadith API responses: {len(hadith_files)}")
        
        print(f"\nAll responses saved to: {os.path.abspath(self.output_dir)}/")
        
        print("\n--- Quran API Files ---")
        for f in quran_files:
            print(f"  [OK] {f}")
        
        print("\n--- Hadith API Files ---")
        for f in hadith_files:
            print(f"  [OK] {f}")


def main():
    """Main execution function"""
    tester = APITester()
    
    # Test Quran API with multiple queries
    print("Starting Quran API tests...")
    quran_results = tester.test_quran_with_multiple_queries()
    
    # Test all Hadith APIs
    print("\n\nStarting Hadith API tests...")
    hadith_results = tester.test_all_hadith_apis()
    
    # Generate summary report
    tester.generate_summary_report()
    
    print("\n" + "="*80)
    print("API TESTING COMPLETED")
    print("="*80)
    print("\nNext step: Review the JSON files in the 'api_responses' directory")
    print("to create appropriate parsers based on the response structures.")


if __name__ == "__main__":
    main()
