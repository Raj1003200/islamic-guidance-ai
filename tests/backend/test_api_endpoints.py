"""
Comprehensive Backend API Tests
Tests all FastAPI endpoints with valid and invalid inputs
"""
import pytest
import requests
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

class TestQuranSearchEndpoint:
    """Tests for /api/quran/search endpoint"""
    
    def test_search_with_valid_keyword(self):
        """Test searching with a valid keyword"""
        response = requests.get(f"{BASE_URL}/api/quran/search", params={"keyword": "patience"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check structure of first result
        if data:
            assert "text" in data[0]
            assert "surah" in data[0]
            assert "number" in data[0]
    
    def test_search_with_empty_keyword(self):
        """Test searching with empty keyword"""
        response = requests.get(f"{BASE_URL}/api/quran/search", params={"keyword": ""})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_with_special_characters(self):
        """Test searching with special characters"""
        response = requests.get(f"{BASE_URL}/api/quran/search", params={"keyword": "faith & hope"})
        assert response.status_code == 200
    
    def test_search_with_arabic_text(self):
        """Test searching with Arabic text"""
        response = requests.get(f"{BASE_URL}/api/quran/search", params={"keyword": "الله"})
        assert response.status_code == 200

class TestHadithSearchEndpoint:
    """Tests for /api/hadith/search endpoint"""
    
    def test_search_with_valid_topic_bukhari(self):
        """Test searching Sahih Bukhari"""
        response = requests.get(f"{BASE_URL}/api/hadith/search", 
                              params={"topic": "prayer", "book": "bukhari"})
        assert response.status_code == 200
        # Can be None or a hadith object
    
    def test_search_with_valid_topic_muslim(self):
        """Test searching Sahih Muslim"""
        response = requests.get(f"{BASE_URL}/api/hadith/search",
                              params={"topic": "faith", "book": "muslim"})
        assert response.status_code == 200
    
    def test_search_with_invalid_book(self):
        """Test with non-existent book"""
        response = requests.get(f"{BASE_URL}/api/hadith/search",
                              params={"topic": "prayer", "book": "nonexistent"})
        assert response.status_code == 200
        assert response.json() is None
    
    def test_search_with_empty_topic(self):
        """Test with empty topic"""
        response = requests.get(f"{BASE_URL}/api/hadith/search",
                              params={"topic": "", "book": "bukhari"})
        assert response.status_code == 200

class TestAPIKeyEndpoints:
    """Tests for API key management endpoints"""
    
    def test_get_api_key(self):
        """Test retrieving API key"""
        response = requests.get(f"{BASE_URL}/api/get-api-key")
        assert response.status_code == 200
        data = response.json()
        assert "apiKey" in data
        assert isinstance(data["apiKey"], str)
    
    # def test_save_api_key_valid(self):
    #     """Test saving a valid API key"""
    #     test_key = "test_api_key_12345"
    #     response = requests.post(f"{BASE_URL}/api/save-api-key",
    #                            json={"apiKey": test_key})
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["success"] is True
    
    # def test_save_api_key_empty(self):
    #     """Test saving an empty API key"""
    #     response = requests.post(f"{BASE_URL}/api/save-api-key",
    #                            json={"apiKey": ""})
    #     assert response.status_code == 400

class TestGuidanceEndpoint:
    """Tests for /api/guidance endpoint"""
    
    def test_guidance_with_valid_query(self):
        """Test with a valid question"""
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"query": "I am feeling anxious about my future career"},
                               timeout=30)
        # Can be 200, 429 (quota), or 503 (no API key)
        assert response.status_code in [200, 429, 503]
        if response.status_code == 200:
            data = response.json()
            # Should have either 'answer' or 'error'
            assert "answer" in data or "error" in data
    
    def test_guidance_with_short_query(self):
        """Test with too short query"""
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"query": "hello"})
        assert response.status_code == 400
    
    def test_guidance_with_empty_query(self):
        """Test with empty query"""
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"query": ""})
        assert response.status_code == 400
    
    def test_guidance_with_invalid_request(self):
        """Test with invalid JSON"""
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"test": "test"})
        # Should handle missing 'query' field
        assert response.status_code in [400, 422]

class TestStaticFiles:
    """Tests for static file serving"""
    
    def test_index_page(self):
        """Test main index page loads"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert "Islamic Guidance AI" in response.text
    
    def test_settings_page(self):
        """Test settings page loads"""
        response = requests.get(f"{BASE_URL}/settings.html")
        assert response.status_code == 200
        assert "Settings" in response.text
    
    def test_css_file(self):
        """Test CSS file loads"""
        response = requests.get(f"{BASE_URL}/styles.css")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/css")
