"""
Pytest configuration and fixtures
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def base_url():
    """Base URL for API tests"""
    return "http://127.0.0.1:8000"

@pytest.fixture(scope="session")
def sample_quran_keywords():
    """Sample keywords for Quran search tests"""
    return ["patience", "faith", "mercy", "guidance", "prayer"]

@pytest.fixture(scope="session")
def sample_hadith_topics():
    """Sample topics for Hadith search tests"""
    return ["prayer", "faith", "charity", "kindness", "patience"]

@pytest.fixture(scope="session")
def hadith_books():
    """Available Hadith books"""
    return ["bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah"]
