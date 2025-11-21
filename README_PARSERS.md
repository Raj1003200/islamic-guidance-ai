# API Parsers Documentation

## Overview

This document provides comprehensive documentation for the Quran and Hadith API parsers. These parsers are designed to process JSON responses from external Islamic text APIs and convert them into structured, usable data for the Muslim Guide AI application.

## Table of Contents

1. [Architecture](#architecture)
2. [Data Models](#data-models)
3. [Parser Classes](#parser-classes)
4. [Usage Examples](#usage-examples)
5. [API Response Structures](#api-response-structures)
6. [Error Handling](#error-handling)
7. [Integration Guide](#integration-guide)

---

## Architecture

The parser system consists of three main components:

```
api_parsers.py
├── Data Models (QuranVerse, Hadith)
├── QuranAPIParser
├── HadithAPIParser
└── IslamicDataAggregator
```

### Design Principles

- **Separation of Concerns**: Each parser handles one API type
- **Type Safety**: Uses dataclasses for structured data
- **Error Resilience**: Continues parsing even if individual items fail
- **Flexibility**: Supports multiple Hadith collections
- **Ease of Use**: High-level aggregator for common workflows

---

## Data Models

### QuranVerse

Represents a single verse from the Quran.

```python
@dataclass
class QuranVerse:
    number: int                      # Absolute verse number in Quran
    text: str                        # English translation text
    surah_number: int                # Chapter number (1-114)
    surah_name_arabic: str           # Arabic name of chapter
    surah_name_english: str          # English name of chapter
    surah_translation: str           # English translation of chapter name
    revelation_type: str             # "Meccan" or "Medinan"
    verse_number_in_surah: int       # Verse number within the chapter
    edition_name: str                # Translation edition name
    edition_language: str            # Language code (e.g., "en")
```

**Methods:**
- `__str__()`: Returns formatted string representation
- `to_dict()`: Converts to dictionary for JSON serialization

### Hadith

Represents a single Hadith narration.

```python
@dataclass
class Hadith:
    hadith_number: int               # Hadith number in collection
    arabic_number: int               # Arabic numbering system number
    text: str                        # Full Hadith text
    collection_name: str             # Collection name (e.g., "Sahih al-Bukhari")
    book_reference: Optional[int]    # Book number within collection
    grades: Optional[List[str]]      # Authentication grades
    reference: Optional[Dict]        # Additional reference data
```

**Methods:**
- `__str__()`: Returns formatted string representation
- `to_dict()`: Converts to dictionary for JSON serialization

---

## Parser Classes

### QuranAPIParser

Parses responses from the Quran API (`api.alquran.cloud`).

#### Methods

##### `parse_search_response(response_data: Dict) -> Dict`

Parses a complete search response from the Quran API.

**Parameters:**
- `response_data`: Raw JSON response from API

**Returns:**
```python
{
    "success": bool,
    "code": int,
    "status": str,
    "total_matches": int,
    "verses": List[QuranVerse],
    "error": Optional[str]
}
```

**Example:**
```python
parser = QuranAPIParser()
result = parser.parse_search_response(api_response)

if result["success"]:
    print(f"Found {result['total_matches']} verses")
    for verse in result["verses"]:
        print(verse)
```

##### `get_top_verses(response_data: Dict, limit: int = 5) -> List[QuranVerse]`

Extracts the top N verses from search results.

**Parameters:**
- `response_data`: Raw JSON response
- `limit`: Maximum number of verses to return (default: 5)

**Returns:** List of `QuranVerse` objects

**Example:**
```python
top_verses = QuranAPIParser.get_top_verses(api_response, limit=3)
for verse in top_verses:
    print(f"{verse.surah_name_english} {verse.verse_number_in_surah}")
```

##### `format_verse_for_display(verse: QuranVerse) -> str`

Formats a verse for user-friendly display.

**Parameters:**
- `verse`: QuranVerse object

**Returns:** Formatted string

**Example Output:**
```
[QURAN] Al-Baqara
   Chapter 2, Verse 255
   Revelation: Medinan

"Allah - there is no deity except Him, the Ever-Living, the Sustainer..."
```

---

### HadithAPIParser

Parses responses from the Hadith API (`hadith-api`).

#### Supported Collections

```python
COLLECTION_NAMES = {
    "eng-abudawud": "Sunan Abu Dawud",
    "eng-bukhari": "Sahih al-Bukhari",
    "eng-dehlawi": "Musnad Ahmad ibn Hanbal",
    "eng-ibnmajah": "Sunan Ibn Majah",
    "eng-malik": "Muwatta Malik",
    "eng-muslim": "Sahih Muslim",
    "eng-nasai": "Sunan an-Nasa'i",
    "eng-nawawi": "40 Hadith Nawawi",
    "eng-qudsi": "40 Hadith Qudsi",
    "eng-tirmidhi": "Jami` at-Tirmidhi"
}
```

#### Methods

##### `parse_collection_response(response_data: Dict, collection_id: str) -> Dict`

Parses a complete Hadith collection response.

**Parameters:**
- `response_data`: Raw JSON response
- `collection_id`: Collection identifier (e.g., "eng-bukhari")

**Returns:**
```python
{
    "success": bool,
    "collection_id": str,
    "collection_name": str,
    "total_hadiths": int,
    "sections": Dict,
    "hadiths": List[Hadith],
    "error": Optional[str]
}
```

##### `search_hadiths_by_keyword(response_data: Dict, collection_id: str, keyword: str, limit: int = 10) -> List[Hadith]`

Searches for Hadiths containing a specific keyword.

**Parameters:**
- `response_data`: Raw JSON response
- `collection_id`: Collection identifier
- `keyword`: Search term (case-insensitive)
- `limit`: Maximum results (default: 10)

**Returns:** List of matching `Hadith` objects

**Example:**
```python
parser = HadithAPIParser()
hadiths = parser.search_hadiths_by_keyword(
    bukhari_data,
    "eng-bukhari",
    "prayer",
    limit=5
)

for hadith in hadiths:
    print(f"Hadith #{hadith.hadith_number}: {hadith.text[:100]}...")
```

##### `get_hadith_by_number(response_data: Dict, collection_id: str, hadith_number: int) -> Optional[Hadith]`

Retrieves a specific Hadith by its number.

**Parameters:**
- `response_data`: Raw JSON response
- `collection_id`: Collection identifier
- `hadith_number`: Hadith number to find

**Returns:** `Hadith` object or `None` if not found

##### `format_hadith_for_display(hadith: Hadith) -> str`

Formats a Hadith for user-friendly display.

**Example Output:**
```
[HADITH] Sahih al-Bukhari
   Hadith #123 - Book 5
   Grades: Sahih

"Narrated Abu Huraira: The Prophet said..."
```

---

### IslamicDataAggregator

High-level class that combines Quran and Hadith parsers for common workflows.

#### Methods

##### `search_quran(search_term: str, quran_response: Dict, limit: int = 5) -> Dict`

Searches Quran and returns formatted results.

**Returns:**
```python
{
    "search_term": str,
    "total_found": int,
    "verses_returned": int,
    "verses": List[Dict],           # Verse dictionaries
    "formatted_verses": List[str]   # Pre-formatted strings
}
```

##### `search_hadith(keyword: str, hadith_response: Dict, collection_id: str, limit: int = 5) -> Dict`

Searches Hadith collection and returns formatted results.

**Returns:**
```python
{
    "keyword": str,
    "collection": str,
    "total_found": int,
    "hadiths": List[Dict],          # Hadith dictionaries
    "formatted_hadiths": List[str]  # Pre-formatted strings
}
```

##### `get_guidance_package(quran_search_term: str, hadith_keyword: str, quran_response: Dict, hadith_responses: Dict, quran_limit: int = 3, hadith_limit: int = 2) -> Dict`

Creates a complete guidance package with Quran verses and Hadiths from multiple collections.

**Parameters:**
- `quran_search_term`: Search term for Quran
- `hadith_keyword`: Keyword for Hadith search
- `quran_response`: Quran API response
- `hadith_responses`: Dictionary of collection_id -> response
- `quran_limit`: Max Quran verses
- `hadith_limit`: Max Hadiths per collection

**Returns:**
```python
{
    "timestamp": str,
    "quran": {...},                 # Quran search results
    "hadith": {...},                # Hadith results by collection
    "summary": {
        "quran_verses": int,
        "hadith_collections": int,
        "total_hadiths": int
    }
}
```

**Example:**
```python
aggregator = IslamicDataAggregator()

guidance = aggregator.get_guidance_package(
    quran_search_term="patience",
    hadith_keyword="patience",
    quran_response=quran_api_response,
    hadith_responses={
        "eng-bukhari": bukhari_response,
        "eng-muslim": muslim_response
    },
    quran_limit=3,
    hadith_limit=2
)

print(f"Found {guidance['summary']['quran_verses']} verses")
print(f"Found {guidance['summary']['total_hadiths']} hadiths")
```

---

## Usage Examples

### Basic Quran Parsing

```python
import json
from api_parsers import QuranAPIParser

# Load API response
with open("api_responses/quran_search_Heaven.json", "r", encoding="utf-8") as f:
    quran_data = json.load(f)

# Parse response
parser = QuranAPIParser()
result = parser.parse_search_response(quran_data)

# Display results
if result["success"]:
    print(f"Found {result['total_matches']} verses about Heaven")
    
    for verse in result["verses"][:5]:
        print(f"\n{parser.format_verse_for_display(verse)}")
```

### Basic Hadith Parsing

```python
import json
from api_parsers import HadithAPIParser

# Load API response
with open("api_responses/hadith_eng-bukhari.json", "r", encoding="utf-8") as f:
    hadith_data = json.load(f)

# Search for keyword
parser = HadithAPIParser()
hadiths = parser.search_hadiths_by_keyword(
    hadith_data,
    "eng-bukhari",
    "charity",
    limit=3
)

# Display results
print(f"Found {len(hadiths)} hadiths about charity")
for hadith in hadiths:
    print(f"\n{parser.format_hadith_for_display(hadith)}")
```

### Complete Guidance Package

```python
import json
from api_parsers import IslamicDataAggregator

# Load responses
with open("api_responses/quran_search_Patience.json", "r") as f:
    quran_data = json.load(f)

with open("api_responses/hadith_eng-bukhari.json", "r") as f:
    bukhari_data = json.load(f)

with open("api_responses/hadith_eng-muslim.json", "r") as f:
    muslim_data = json.load(f)

# Create guidance package
aggregator = IslamicDataAggregator()
guidance = aggregator.get_guidance_package(
    quran_search_term="patience",
    hadith_keyword="patience",
    quran_response=quran_data,
    hadith_responses={
        "eng-bukhari": bukhari_data,
        "eng-muslim": muslim_data
    }
)

# Display summary
print(f"Guidance Package Created at {guidance['timestamp']}")
print(f"Quran Verses: {guidance['summary']['quran_verses']}")
print(f"Hadith Collections: {guidance['summary']['hadith_collections']}")
print(f"Total Hadiths: {guidance['summary']['total_hadiths']}")

# Display formatted content
for formatted_verse in guidance['quran']['formatted_verses']:
    print(f"\n{formatted_verse}")

for collection_id, collection_data in guidance['hadith'].items():
    print(f"\n=== {collection_data['collection_name']} ===")
    for formatted_hadith in collection_data['formatted']:
        print(f"\n{formatted_hadith}")
```

---

## API Response Structures

### Quran API Response

**Endpoint:** `https://api.alquran.cloud/v1/search/{text}/all/en`

**Structure:**
```json
{
  "code": 200,
  "status": "OK",
  "data": {
    "count": 10,
    "matches": [
      {
        "number": 33,
        "text": "Then He said to Adam...",
        "edition": {
          "identifier": "en.asad",
          "language": "en",
          "name": "Muhammad Asad",
          "englishName": "Muhammad Asad",
          "type": "translation"
        },
        "surah": {
          "number": 2,
          "name": "سُورَةُ البَقَرَةِ",
          "englishName": "Al-Baqara",
          "englishNameTranslation": "The Cow",
          "revelationType": "Medinan"
        },
        "numberInSurah": 33
      }
    ]
  }
}
```

### Hadith API Response

**Endpoint:** `https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{collection-id}.json`

**Structure:**
```json
{
  "metadata": {
    "name": "Sahih al Bukhari",
    "sections": {
      "1": "Revelation",
      "2": "Belief"
    },
    "section_details": {...}
  },
  "hadiths": [
    {
      "hadithnumber": 1,
      "arabicnumber": 1,
      "text": "Narrated 'Umar bin Al-Khattab...",
      "grades": ["Sahih"],
      "reference": {
        "book": 1,
        "hadith": 1
      }
    }
  ]
}
```

---

## Error Handling

### Parser Error Handling

All parsers implement robust error handling:

1. **Individual Item Failures**: If one verse or Hadith fails to parse, the parser continues with the remaining items
2. **API Errors**: Returns structured error information in the result dictionary
3. **Missing Data**: Uses default values or `None` for optional fields
4. **Encoding Issues**: Handles Unicode characters gracefully

### Example Error Handling

```python
result = parser.parse_search_response(api_response)

if not result["success"]:
    print(f"Error: {result['error']}")
    print(f"API Code: {result['code']}")
else:
    # Process successful result
    for verse in result["verses"]:
        try:
            print(verse)
        except Exception as e:
            print(f"Error displaying verse: {e}")
```

---

## Integration Guide

### Step 1: Fetch API Data

```python
import requests
import urllib.parse

# Fetch Quran data
search_term = "patience"
encoded_term = urllib.parse.quote(search_term)
quran_url = f"https://api.alquran.cloud/v1/search/{encoded_term}/all/en"
quran_response = requests.get(quran_url).json()

# Fetch Hadith data
hadith_url = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-bukhari.json"
hadith_response = requests.get(hadith_url).json()
```

### Step 2: Parse Data

```python
from api_parsers import QuranAPIParser, HadithAPIParser

# Parse Quran
quran_parser = QuranAPIParser()
quran_result = quran_parser.parse_search_response(quran_response)

# Parse Hadith
hadith_parser = HadithAPIParser()
hadith_result = hadith_parser.parse_collection_response(hadith_response, "eng-bukhari")
```

### Step 3: Use Parsed Data

```python
# Get top verses
top_verses = quran_result["verses"][:3]

# Search Hadiths
matching_hadiths = hadith_parser.search_hadiths_by_keyword(
    hadith_response,
    "eng-bukhari",
    "patience",
    limit=3
)

# Format for display
for verse in top_verses:
    print(quran_parser.format_verse_for_display(verse))

for hadith in matching_hadiths:
    print(hadith_parser.format_hadith_for_display(hadith))
```

### Step 4: Store or Return Data

```python
# Convert to JSON-serializable format
guidance_data = {
    "quran_verses": [v.to_dict() for v in top_verses],
    "hadiths": [h.to_dict() for h in matching_hadiths]
}

# Save to file
import json
with open("guidance_output.json", "w", encoding="utf-8") as f:
    json.dump(guidance_data, f, indent=2, ensure_ascii=False)

# Or return in API response
return {
    "status": "success",
    "data": guidance_data
}
```

---

## Testing

Run the parser demonstration:

```bash
python api_parsers.py
```

This will:
1. Load sample Quran and Hadith responses
2. Parse the data
3. Display formatted results
4. Verify all parsers are working correctly

---

## Notes

- **Encoding**: All parsers handle UTF-8 encoding properly
- **Performance**: Parsers are optimized for speed and can handle large collections
- **Extensibility**: Easy to add new Hadith collections or customize formatting
- **Type Safety**: Uses Python type hints for better IDE support and error checking

---

## Support

For issues or questions about the parsers, refer to:
- API response samples in `api_responses/` directory
- Test script: `api_tester.py`
- Main parser file: `api_parsers.py`
