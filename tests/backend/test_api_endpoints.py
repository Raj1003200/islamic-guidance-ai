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
    
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"query": "I am feeling anxious about my future", "source": "internal"},
                               timeout=30)
        assert response.status_code in [200, 429, 503]
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data

    def test_guidance_with_valid_query_external(self):
        """Test with valid query and external source"""
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"query": "I want to learn about patience in Islam", "source": "external"},
                               timeout=30)
        assert response.status_code in [200, 429, 503]
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            # External should ideally have citations if found
            if "citations" in data:
                assert isinstance(data["citations"], list)

    def test_guidance_with_valid_query_both(self):
        """Test with valid query and both sources"""
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"query": "Tell me about the importance of prayer", "source": "both"},
                               timeout=30)
        assert response.status_code in [200, 429, 503]
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data

    def test_guidance_with_short_query(self):
        """Test with too short query"""
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"query": "hello", "source": "both"})
        assert response.status_code == 400
    
    def test_guidance_with_empty_query(self):
        """Test with empty query"""
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"query": "", "source": "both"})
        assert response.status_code == 400
    
    def test_guidance_with_invalid_request(self):
        """Test with invalid JSON"""
        response = requests.post(f"{BASE_URL}/api/guidance",
                               json={"test": "test"})
        # Should handle missing 'query' field
        assert response.status_code in [400, 422]

class TestSearchEndpoints:
    """Tests for direct search endpoints"""

    def test_quran_search(self):
        """Test /api/quran/search"""
        response = requests.get(f"{BASE_URL}/api/quran/search", params={"keyword": "patience"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_hadith_search(self):
        """Test /api/hadith/search"""
        response = requests.get(f"{BASE_URL}/api/hadith/search", params={"topic": "prayer", "book": "muslim"})
        assert response.status_code == 200
        # Can be dict or null


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
