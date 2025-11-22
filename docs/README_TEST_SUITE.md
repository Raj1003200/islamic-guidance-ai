# Context Understanding Logic - QA Test Suite

## Overview
This test suite validates the "Context Understanding" logic of the Islamic Guidance Search Engine. It ensures that the system correctly processes user inputs, filters irrelevant queries, and provides appropriate Islamic guidance.

## Test Cases

### Test Case 1: Valid Problem
**Purpose**: Validate that the system correctly processes genuine problems and provides relevant Islamic guidance.

**Input**: 
```
"I have a lot of debt and I don't know how to pay it back."
```

**Expected Results**:
- ✅ HTTP Status: `200 OK`
- ✅ Extracted Keywords: `Quran="Debt"`, `Hadith="Debt"` (or related terms)
- ✅ Response contains actual Islamic advice
- ✅ Response includes Quran verses or Hadith references
- ✅ Response length > 50 characters (substantive advice)

**Validation Criteria**:
- Status code must be 200
- Response must contain meaningful guidance (not just acknowledgment)
- Keywords should be relevant to the problem domain

---

### Test Case 2: Emotional/Vague Problem
**Purpose**: Validate that the system can handle emotional and vague inputs by providing compassionate guidance.

**Input**: 
```
"I am feeling very lonely and depressed today."
```

**Expected Results**:
- ✅ HTTP Status: `200 OK`
- ✅ Extracted Keywords: `Quran="Comfort"`, `Hadith="Company"` (or related terms like "solace", "peace", "mercy")
- ✅ Response contains verses about Allah being near
- ✅ Response includes comfort-related themes: "Allah", "near", "close", "mercy", "compassion"

**Validation Criteria**:
- Status code must be 200
- Keywords should relate to comfort, companionship, or emotional support
- Response should contain at least one comfort-related theme
- Tone should be compassionate and supportive

---

### Test Case 3: Irrelevant Input (Filter Test)
**Purpose**: Validate that the system correctly filters out irrelevant queries that are not genuine Islamic guidance requests.

**Inputs**: 
```
1. "What is the capital of France?"
2. "Write a python script for me."
3. "How to make a cake?"
4. "What's the weather today?"
```

**Expected Results**:
- ✅ HTTP Status: `400 Bad Request` or `422 Unprocessable Entity`
- ✅ Error Message: "It looks like not a genuine problem" (or similar rejection message)
- ✅ No guidance provided
- ✅ All irrelevant inputs are filtered

**Validation Criteria**:
- Status code must be 400 or 422 for ALL irrelevant inputs
- Error message should clearly indicate rejection
- System should not attempt to provide Islamic guidance for non-Islamic queries

---

### Test Case 4: API Data Structure Validation
**Purpose**: Validate that the backend correctly parses and processes data from the external Quran API.

**Input**: 
```
"Heaven"
```

**External API Validation**:
- URL: `https://api.alquran.cloud/v1/search/Heaven/all/en`
- Expected JSON Structure:
  ```json
  {
    "code": 200,
    "data": {
      "matches": [...]
    }
  }
  ```

**Expected Results**:
- ✅ External API returns `code: 200`
- ✅ External API has `data.matches` array
- ✅ Backend successfully parses the API response
- ✅ Backend returns HTTP Status: `200 OK`
- ✅ Backend response includes Quran verses from the API

**Validation Criteria**:
- External API structure must match expected format
- Backend must successfully integrate external API data
- Backend response must include verse references

---

## Running the Tests

### Prerequisites
```bash
# Install required dependencies
pip install requests
```

### Configuration
Update the `BASE_URL` in the test script to match your API endpoint:
```python
BASE_URL = "http://localhost:3000"  # Update with your actual API URL
```

### Execution
```bash
# Run the complete test suite
python test_context_understanding.py
```

### Output
The test suite will:
1. Execute all 4 test cases sequentially
2. Display real-time progress in the console
3. Generate a summary report showing pass/fail status
4. Save a detailed JSON report to `test_report_context_understanding.json`

---

## Test Report Format

### Console Output
```
================================================================================
CONTEXT UNDERSTANDING LOGIC - QA TEST SUITE
================================================================================

Running Test Case 1: Valid Problem...
Running Test Case 2: Emotional/Vague Problem...
Running Test Case 3: Irrelevant Input Filter...
Running Test Case 4: API Data Structure Validation...

================================================================================
TEST EXECUTION REPORT
================================================================================

Total Tests: 4
Passed: 4 (100.0%)
Failed: 0 (0.0%)

1. Test Case 1: Valid Problem - Debt Issue
   Status: ✓ PASSED
   Expected: Status 200, Keywords related to 'Debt', Actual advice with references
   Actual: Status 200, Keywords: {...}, Advice length: 450
   Response Preview: In Islam, debt is a serious matter...

...
```

### JSON Report
A detailed JSON report is saved to `test_report_context_understanding.json` containing:
- Test suite metadata
- Timestamp
- Summary statistics
- Detailed results for each test case
- Full API responses
- Error details (if any)

---

## Interpreting Results

### ✓ PASSED
All validation criteria met. The feature is working as expected.

### ✗ FAILED
One or more validation criteria not met. Review the details section for:
- Actual vs. expected values
- Error messages
- Full API responses

### ⚠ WARNING
Test executed but with minor issues (currently not used, reserved for future enhancements).

---

## Troubleshooting

### Connection Errors
```
Request failed: Connection refused
```
**Solution**: Ensure the API server is running at the configured `BASE_URL`.

### Timeout Errors
```
Request failed: Timeout
```
**Solution**: 
- Increase timeout values in the test script
- Check API server performance
- Verify network connectivity

### Unexpected Status Codes
**Solution**: 
- Review API endpoint implementation
- Check request payload format
- Verify authentication (if required)

### Missing Keywords
**Solution**:
- Review keyword extraction logic
- Verify AI model is properly configured
- Check if the problem is being correctly interpreted

---

## Extending the Test Suite

### Adding New Test Cases
1. Create a new method in the `ContextUnderstandingTester` class:
   ```python
   def test_case_5_your_test(self) -> TestResult:
       """Your test description"""
       # Implementation
   ```

2. Add the test to `run_all_tests()`:
   ```python
   print("Running Test Case 5: Your Test...")
   self.test_case_5_your_test()
   ```

### Customizing Validation Logic
Modify the validation criteria in each test method to match your specific requirements.

---

## Best Practices

1. **Run tests after every major change** to the Context Understanding logic
2. **Review failed test details** carefully to identify root causes
3. **Keep the test suite updated** as new features are added
4. **Use the JSON report** for automated CI/CD integration
5. **Test edge cases** beyond the provided examples

---

## CI/CD Integration

### Example GitHub Actions Workflow
```yaml
name: QA Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install requests
      - name: Run tests
        run: python test_context_understanding.py
      - name: Upload test report
        uses: actions/upload-artifact@v2
        with:
          name: test-report
          path: test_report_context_understanding.json
```

---

## Support

For issues or questions about the test suite:
1. Review the test case documentation above
2. Check the troubleshooting section
3. Examine the detailed JSON report
4. Contact the QA team with specific error details

---

## Version History

- **v1.0** - Initial test suite with 4 core test cases
  - Valid Problem validation
  - Emotional/Vague Problem handling
  - Irrelevant Input filtering
  - API Data Structure validation
