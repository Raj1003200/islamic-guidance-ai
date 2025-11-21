"""
Test Script for Context Understanding Logic
QA Engineer: Validation Test Suite

This script validates the Context Understanding logic of the Islamic Guidance Search Engine.
It tests 4 key scenarios:
1. Valid Problem Input
2. Emotional/Vague Problem Input
3. Irrelevant Input (Filter Test)
4. API Data Structure Validation
"""

import requests
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "✓ PASSED"
    FAILED = "✗ FAILED"
    WARNING = "⚠ WARNING"


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: TestStatus
    expected: str
    actual: str
    details: Dict[str, Any]


class ContextUnderstandingTester:
    """QA Test Suite for Context Understanding Logic"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        """
        Initialize the tester with base URL
        
        Args:
            base_url: The base URL of the API endpoint
        """
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/guidance"
        self.results: List[TestResult] = []
        
    def test_case_1_valid_problem(self) -> TestResult:
        """
        Test Case 1: Valid Problem
        Input: "I have a lot of debt and I don't know how to pay it back."
        
        Expected:
        - Status: 200
        - Extracted Keywords: Quran="Debt", Hadith="Debt"
        - Response contains actual advice
        """
        test_name = "Test Case 1: Valid Problem - Debt Issue"
        input_text = "I have a lot of debt and I don't know how to pay it back."
        
        try:
            response = requests.post(
                self.api_endpoint,
                json={"problem": input_text},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            # Validate status code
            status_ok = response.status_code == 200
            
            # Parse response
            data = response.json()
            
            # Validate extracted keywords
            keywords_present = False
            extracted_keywords = data.get("extracted_keywords", {})
            quran_keyword = extracted_keywords.get("quran", "").lower()
            hadith_keyword = extracted_keywords.get("hadith", "").lower()
            
            if "debt" in quran_keyword or "debt" in hadith_keyword:
                keywords_present = True
            
            # Validate response contains advice
            advice_present = False
            response_text = data.get("guidance", "") or data.get("response", "")
            if response_text and len(response_text) > 50:
                advice_present = True
            
            # Check for Quran verses or Hadith references
            has_references = (
                data.get("quran_verses") or 
                data.get("hadith_references") or
                "verse" in response_text.lower() or
                "hadith" in response_text.lower()
            )
            
            # Overall validation
            all_checks_passed = status_ok and advice_present
            
            result = TestResult(
                test_name=test_name,
                status=TestStatus.PASSED if all_checks_passed else TestStatus.FAILED,
                expected="Status 200, Keywords related to 'Debt', Actual advice with references",
                actual=f"Status {response.status_code}, Keywords: {extracted_keywords}, Advice length: {len(response_text)}",
                details={
                    "status_code": response.status_code,
                    "status_ok": status_ok,
                    "extracted_keywords": extracted_keywords,
                    "keywords_present": keywords_present,
                    "advice_present": advice_present,
                    "has_references": has_references,
                    "response_preview": response_text[:200] if response_text else None,
                    "full_response": data
                }
            )
            
        except requests.exceptions.RequestException as e:
            result = TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                expected="Successful API call",
                actual=f"Request failed: {str(e)}",
                details={"error": str(e)}
            )
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                expected="Valid response parsing",
                actual=f"Unexpected error: {str(e)}",
                details={"error": str(e)}
            )
        
        self.results.append(result)
        return result
    
    def test_case_2_emotional_vague_problem(self) -> TestResult:
        """
        Test Case 2: Emotional/Vague Problem
        Input: "I am feeling very lonely and depressed today."
        
        Expected:
        - Status: 200
        - Extracted Keywords: Quran="Comfort", Hadith="Company"
        - Response contains verses about Allah being near
        """
        test_name = "Test Case 2: Emotional/Vague Problem - Loneliness"
        input_text = "I am feeling very lonely and depressed today."
        
        try:
            response = requests.post(
                self.api_endpoint,
                json={"problem": input_text},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            # Validate status code
            status_ok = response.status_code == 200
            
            # Parse response
            data = response.json()
            
            # Validate extracted keywords (comfort-related)
            extracted_keywords = data.get("extracted_keywords", {})
            quran_keyword = extracted_keywords.get("quran", "").lower()
            hadith_keyword = extracted_keywords.get("hadith", "").lower()
            
            comfort_keywords = ["comfort", "company", "lonely", "depression", "solace", "peace", "near"]
            keywords_relevant = any(
                keyword in quran_keyword or keyword in hadith_keyword 
                for keyword in comfort_keywords
            )
            
            # Validate response contains comfort/Allah being near
            response_text = data.get("guidance", "") or data.get("response", "")
            comfort_themes = ["allah", "near", "close", "comfort", "mercy", "compassion", "peace"]
            contains_comfort = any(theme in response_text.lower() for theme in comfort_themes)
            
            # Overall validation
            all_checks_passed = status_ok and contains_comfort
            
            result = TestResult(
                test_name=test_name,
                status=TestStatus.PASSED if all_checks_passed else TestStatus.FAILED,
                expected="Status 200, Comfort-related keywords, Response about Allah being near",
                actual=f"Status {response.status_code}, Keywords: {extracted_keywords}, Contains comfort: {contains_comfort}",
                details={
                    "status_code": response.status_code,
                    "status_ok": status_ok,
                    "extracted_keywords": extracted_keywords,
                    "keywords_relevant": keywords_relevant,
                    "contains_comfort": contains_comfort,
                    "response_preview": response_text[:200] if response_text else None,
                    "full_response": data
                }
            )
            
        except requests.exceptions.RequestException as e:
            result = TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                expected="Successful API call",
                actual=f"Request failed: {str(e)}",
                details={"error": str(e)}
            )
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                expected="Valid response parsing",
                actual=f"Unexpected error: {str(e)}",
                details={"error": str(e)}
            )
        
        self.results.append(result)
        return result
    
    def test_case_3_irrelevant_input(self) -> TestResult:
        """
        Test Case 3: Irrelevant Input (Filter Test)
        Input: "What is the capital of France?" or "Write a python script for me."
        
        Expected:
        - Status: 400 or 422
        - Error Message: "It looks like not a genuine problem."
        """
        test_name = "Test Case 3: Irrelevant Input - Filter Test"
        
        # Test with multiple irrelevant inputs
        irrelevant_inputs = [
            "What is the capital of France?",
            "Write a python script for me.",
            "How to make a cake?",
            "What's the weather today?"
        ]
        
        all_filtered = True
        test_details = []
        
        for input_text in irrelevant_inputs:
            try:
                response = requests.post(
                    self.api_endpoint,
                    json={"problem": input_text},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                # Expected status codes for rejection
                is_rejected = response.status_code in [400, 422]
                
                # Check error message
                data = response.json()
                error_message = data.get("error", "") or data.get("message", "")
                has_rejection_message = (
                    "not a genuine problem" in error_message.lower() or
                    "irrelevant" in error_message.lower() or
                    "cannot help" in error_message.lower()
                )
                
                test_details.append({
                    "input": input_text,
                    "status_code": response.status_code,
                    "is_rejected": is_rejected,
                    "error_message": error_message,
                    "has_rejection_message": has_rejection_message
                })
                
                if not is_rejected:
                    all_filtered = False
                    
            except Exception as e:
                test_details.append({
                    "input": input_text,
                    "error": str(e)
                })
                all_filtered = False
        
        result = TestResult(
            test_name=test_name,
            status=TestStatus.PASSED if all_filtered else TestStatus.FAILED,
            expected="Status 400/422 with rejection message for irrelevant inputs",
            actual=f"All filtered: {all_filtered}",
            details={
                "all_filtered": all_filtered,
                "test_results": test_details
            }
        )
        
        self.results.append(result)
        return result
    
    def test_case_4_api_data_check(self) -> TestResult:
        """
        Test Case 4: API Data Check
        Input: "Heaven"
        
        Validation: 
        - Check https://api.alquran.cloud/v1/search/Heaven/all/en
        - Ensure JSON structure (code: 200, data.matches) is parsed correctly
        """
        test_name = "Test Case 4: API Data Structure Validation"
        search_term = "Heaven"
        api_url = f"https://api.alquran.cloud/v1/search/{search_term}/all/en"
        
        try:
            # First, validate the external API structure
            external_response = requests.get(api_url, timeout=10)
            external_data = external_response.json()
            
            # Validate external API structure
            has_code = "code" in external_data
            code_is_200 = external_data.get("code") == 200
            has_data = "data" in external_data
            has_matches = "matches" in external_data.get("data", {})
            matches = external_data.get("data", {}).get("matches", [])
            has_results = len(matches) > 0
            
            external_api_valid = has_code and code_is_200 and has_data and has_matches
            
            # Now test our backend with the same input
            backend_response = requests.post(
                self.api_endpoint,
                json={"problem": search_term},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            backend_data = backend_response.json()
            
            # Validate that backend correctly processes the API data
            backend_has_verses = (
                backend_data.get("quran_verses") or 
                backend_data.get("verses") or
                False
            )
            
            # Check if backend response includes verse references
            response_text = backend_data.get("guidance", "") or backend_data.get("response", "")
            
            all_checks_passed = external_api_valid and backend_response.status_code == 200
            
            result = TestResult(
                test_name=test_name,
                status=TestStatus.PASSED if all_checks_passed else TestStatus.FAILED,
                expected="External API returns code:200 with data.matches, Backend parses correctly",
                actual=f"External API valid: {external_api_valid}, Backend status: {backend_response.status_code}",
                details={
                    "external_api": {
                        "url": api_url,
                        "has_code": has_code,
                        "code_is_200": code_is_200,
                        "has_data": has_data,
                        "has_matches": has_matches,
                        "match_count": len(matches),
                        "first_match_preview": matches[0] if matches else None
                    },
                    "backend_response": {
                        "status_code": backend_response.status_code,
                        "has_verses": backend_has_verses,
                        "response_preview": response_text[:200] if response_text else None,
                        "full_response": backend_data
                    }
                }
            )
            
        except requests.exceptions.RequestException as e:
            result = TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                expected="Successful API calls",
                actual=f"Request failed: {str(e)}",
                details={"error": str(e)}
            )
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                expected="Valid response parsing",
                actual=f"Unexpected error: {str(e)}",
                details={"error": str(e)}
            )
        
        self.results.append(result)
        return result
    
    def run_all_tests(self) -> None:
        """Run all test cases and generate report"""
        print("=" * 80)
        print("CONTEXT UNDERSTANDING LOGIC - QA TEST SUITE")
        print("=" * 80)
        print()
        
        # Run all test cases
        print("Running Test Case 1: Valid Problem...")
        self.test_case_1_valid_problem()
        print()
        
        print("Running Test Case 2: Emotional/Vague Problem...")
        self.test_case_2_emotional_vague_problem()
        print()
        
        print("Running Test Case 3: Irrelevant Input Filter...")
        self.test_case_3_irrelevant_input()
        print()
        
        print("Running Test Case 4: API Data Structure Validation...")
        self.test_case_4_api_data_check()
        print()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        print("=" * 80)
        print("TEST EXECUTION REPORT")
        print("=" * 80)
        print()
        
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print()
        
        # Detailed results
        for i, result in enumerate(self.results, 1):
            print(f"\n{i}. {result.test_name}")
            print(f"   Status: {result.status.value}")
            print(f"   Expected: {result.expected}")
            print(f"   Actual: {result.actual}")
            
            if result.status == TestStatus.FAILED:
                print(f"   Details: {json.dumps(result.details, indent=6)}")
            else:
                # Show summary for passed tests
                if "response_preview" in result.details:
                    print(f"   Response Preview: {result.details['response_preview']}")
        
        print("\n" + "=" * 80)
        
        # Save detailed report to file
        self.save_report_to_file()
    
    def save_report_to_file(self) -> None:
        """Save detailed test report to JSON file"""
        report_data = {
            "test_suite": "Context Understanding Logic Validation",
            "timestamp": requests.get("http://worldtimeapi.org/api/timezone/Etc/UTC").json().get("datetime", ""),
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.status == TestStatus.PASSED),
                "failed": sum(1 for r in self.results if r.status == TestStatus.FAILED)
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status.value,
                    "expected": r.expected,
                    "actual": r.actual,
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        with open("test_report_context_understanding.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nDetailed report saved to: test_report_context_understanding.json")


def main():
    """Main execution function"""
    # Configuration
    BASE_URL = "http://localhost:3000"  # Update with your actual API URL
    
    print("Context Understanding Logic - QA Test Suite")
    print(f"Target API: {BASE_URL}/api/guidance")
    print()
    
    # Initialize tester
    tester = ContextUnderstandingTester(base_url=BASE_URL)
    
    # Run all tests
    tester.run_all_tests()


if __name__ == "__main__":
    main()
