"""
API Parsers for Quran and Hadith Data
Parses JSON responses from Quran and Hadith APIs
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import sys


@dataclass
class QuranVerse:
    """Represents a single Quran verse from search results"""
    number: int
    text: str
    surah_number: int
    surah_name_arabic: str
    surah_name_english: str
    surah_translation: str
    revelation_type: str
    verse_number_in_surah: int
    edition_name: str
    edition_language: str
    
    def __str__(self) -> str:
        return f"[{self.surah_name_english} {self.surah_number}:{self.verse_number_in_surah}] {self.text}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "number": self.number,
            "text": self.text,
            "surah": {
                "number": self.surah_number,
                "name_arabic": self.surah_name_arabic,
                "name_english": self.surah_name_english,
                "translation": self.surah_translation,
                "revelation_type": self.revelation_type
            },
            "verse_in_surah": self.verse_number_in_surah,
            "edition": {
                "name": self.edition_name,
                "language": self.edition_language
            }
        }


@dataclass
class Hadith:
    """Represents a single Hadith"""
    hadith_number: int
    arabic_number: int
    text: str
    collection_name: str
    book_reference: Optional[int] = None
    grades: Optional[List[str]] = None
    reference: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        return f"[{self.collection_name} #{self.hadith_number}] {self.text[:100]}..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "hadith_number": self.hadith_number,
            "arabic_number": self.arabic_number,
            "text": self.text,
            "collection": self.collection_name,
            "book_reference": self.book_reference,
            "grades": self.grades or [],
            "reference": self.reference
        }


class QuranAPIParser:
    """Parser for Quran API responses from api.alquran.cloud"""
    
    @staticmethod
    def parse_search_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Quran search API response
        
        Args:
            response_data: Raw JSON response from API
            
        Returns:
            Parsed data with verses and metadata
        """
        result = {
            "success": False,
            "code": response_data.get("code"),
            "status": response_data.get("status"),
            "total_matches": 0,
            "verses": [],
            "error": None
        }
        
        # Check if request was successful
        if response_data.get("code") != 200:
            result["error"] = f"API returned code {response_data.get('code')}"
            return result
        
        # Extract data
        data = response_data.get("data", {})
        result["total_matches"] = data.get("count", 0)
        
        # Parse matches
        matches = data.get("matches", [])
        for match in matches:
            try:
                verse = QuranAPIParser._parse_verse(match)
                result["verses"].append(verse)
            except Exception as e:
                # Log error but continue parsing other verses
                print(f"Error parsing verse: {e}", file=sys.stdout, flush=True)
                continue
        
        result["success"] = True
        return result
    
    @staticmethod
    def _parse_verse(match_data: Dict[str, Any]) -> QuranVerse:
        """Parse a single verse from match data"""
        surah = match_data.get("surah", {})
        edition = match_data.get("edition", {})
        
        return QuranVerse(
            number=match_data.get("number"),
            text=match_data.get("text", ""),
            surah_number=surah.get("number"),
            surah_name_arabic=surah.get("name", ""),
            surah_name_english=surah.get("englishName", ""),
            surah_translation=surah.get("englishNameTranslation", ""),
            revelation_type=surah.get("revelationType", ""),
            verse_number_in_surah=match_data.get("numberInSurah"),
            edition_name=edition.get("englishName", ""),
            edition_language=edition.get("language", "")
        )
    
    @staticmethod
    def get_top_verses(response_data: Dict[str, Any], limit: int = 5) -> List[QuranVerse]:
        """
        Get top N verses from search results
        
        Args:
            response_data: Raw JSON response from API
            limit: Maximum number of verses to return
            
        Returns:
            List of QuranVerse objects
        """
        parsed = QuranAPIParser.parse_search_response(response_data)
        return parsed["verses"][:limit]
    
    @staticmethod
    def format_verse_for_display(verse: QuranVerse) -> str:
        """
        Format a verse for user-friendly display
        
        Args:
            verse: QuranVerse object
            
        Returns:
            Formatted string
        """
        return f"""
[QURAN] {verse.surah_name_english}
   Chapter {verse.surah_number}, Verse {verse.verse_number_in_surah}
   Revelation: {verse.revelation_type}

"{verse.text}"
        """.strip()


class HadithAPIParser:
    """Parser for Hadith API responses from hadith-api"""
    
    # Collection name mapping
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
    
    @staticmethod
    def parse_collection_response(response_data: Dict[str, Any], collection_id: str) -> Dict[str, Any]:
        """
        Parse Hadith collection API response
        
        Args:
            response_data: Raw JSON response from API
            collection_id: Collection identifier (e.g., 'eng-bukhari')
            
        Returns:
            Parsed data with hadiths and metadata
        """
        result = {
            "success": False,
            "collection_id": collection_id,
            "collection_name": HadithAPIParser.COLLECTION_NAMES.get(collection_id, collection_id),
            "total_hadiths": 0,
            "sections": {},
            "hadiths": [],
            "error": None
        }
        
        try:
            # Extract metadata
            metadata = response_data.get("metadata", {})
            result["collection_name"] = metadata.get("name", result["collection_name"])
            result["sections"] = metadata.get("sections", {})
            
            # Extract hadiths
            hadiths_data = response_data.get("hadiths", [])
            result["total_hadiths"] = len(hadiths_data)
            
            # Parse hadiths
            for hadith_data in hadiths_data:
                try:
                    hadith = HadithAPIParser._parse_hadith(hadith_data, result["collection_name"])
                    result["hadiths"].append(hadith)
                except Exception as e:
                    print(f"Error parsing hadith: {e}", file=sys.stdout, flush=True)
                    continue
            
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def _parse_hadith(hadith_data: Dict[str, Any], collection_name: str) -> Hadith:
        """Parse a single hadith from data"""
        reference = hadith_data.get("reference", {})
        
        return Hadith(
            hadith_number=hadith_data.get("hadithnumber", 0),
            arabic_number=hadith_data.get("arabicnumber", 0),
            text=hadith_data.get("text", ""),
            collection_name=collection_name,
            book_reference=reference.get("book") if isinstance(reference, dict) else None,
            grades=hadith_data.get("grades", []),
            reference=reference
        )
    
    @staticmethod
    def search_hadiths_by_keyword(
        response_data: Dict[str, Any],
        collection_id: str,
        keyword: str,
        limit: int = 10
    ) -> List[Hadith]:
        """
        Search hadiths by keyword in text
        
        Args:
            response_data: Raw JSON response from API
            collection_id: Collection identifier
            keyword: Keyword to search for
            limit: Maximum number of results
            
        Returns:
            List of matching Hadith objects
        """
        parsed = HadithAPIParser.parse_collection_response(response_data, collection_id)
        
        if not parsed["success"]:
            return []
        
        keyword_lower = keyword.lower()
        matching_hadiths = []
        
        for hadith in parsed["hadiths"]:
            if keyword_lower in hadith.text.lower():
                matching_hadiths.append(hadith)
                if len(matching_hadiths) >= limit:
                    break
        
        return matching_hadiths
    
    @staticmethod
    def get_hadith_by_number(
        response_data: Dict[str, Any],
        collection_id: str,
        hadith_number: int
    ) -> Optional[Hadith]:
        """
        Get a specific hadith by its number
        
        Args:
            response_data: Raw JSON response from API
            collection_id: Collection identifier
            hadith_number: Hadith number to find
            
        Returns:
            Hadith object or None if not found
        """
        parsed = HadithAPIParser.parse_collection_response(response_data, collection_id)
        
        if not parsed["success"]:
            return None
        
        for hadith in parsed["hadiths"]:
            if hadith.hadith_number == hadith_number:
                return hadith
        
        return None
    
    @staticmethod
    def format_hadith_for_display(hadith: Hadith) -> str:
        """
        Format a hadith for user-friendly display
        
        Args:
            hadith: Hadith object
            
        Returns:
            Formatted string
        """
        grades_str = f"\nGrades: {', '.join(hadith.grades)}" if hadith.grades else ""
        book_ref = f" - Book {hadith.book_reference}" if hadith.book_reference else ""
        
        return f"""
[HADITH] {hadith.collection_name}
   Hadith #{hadith.hadith_number}{book_ref}{grades_str}

"{hadith.text}"
        """.strip()


class IslamicDataAggregator:
    """Aggregates and manages Quran and Hadith data"""
    
    def __init__(self):
        self.quran_parser = QuranAPIParser()
        self.hadith_parser = HadithAPIParser()
    
    def search_quran(self, search_term: str, quran_response: Dict[str, Any], limit: int = 5) -> Dict[str, Any]:
        """
        Search Quran and return formatted results
        
        Args:
            search_term: Search query
            quran_response: Raw API response
            limit: Maximum results
            
        Returns:
            Formatted search results
        """
        parsed = self.quran_parser.parse_search_response(quran_response)
        
        return {
            "search_term": search_term,
            "total_found": parsed["total_matches"],
            "verses_returned": len(parsed["verses"][:limit]),
            "verses": [v.to_dict() for v in parsed["verses"][:limit]],
            "formatted_verses": [
                self.quran_parser.format_verse_for_display(v)
                for v in parsed["verses"][:limit]
            ]
        }
    
    def search_hadith(
        self,
        keyword: str,
        hadith_response: Dict[str, Any],
        collection_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search Hadith collection and return formatted results
        
        Args:
            keyword: Search keyword
            hadith_response: Raw API response
            collection_id: Collection identifier
            limit: Maximum results
            
        Returns:
            Formatted search results
        """
        matching_hadiths = self.hadith_parser.search_hadiths_by_keyword(
            hadith_response,
            collection_id,
            keyword,
            limit
        )
        
        return {
            "keyword": keyword,
            "collection": self.hadith_parser.COLLECTION_NAMES.get(collection_id, collection_id),
            "total_found": len(matching_hadiths),
            "hadiths": [h.to_dict() for h in matching_hadiths],
            "formatted_hadiths": [
                self.hadith_parser.format_hadith_for_display(h)
                for h in matching_hadiths
            ]
        }
    
    def get_guidance_package(
        self,
        quran_search_term: str,
        hadith_keyword: str,
        quran_response: Dict[str, Any],
        hadith_responses: Dict[str, Dict[str, Any]],
        quran_limit: int = 3,
        hadith_limit: int = 2
    ) -> Dict[str, Any]:
        """
        Get a complete guidance package with Quran verses and Hadiths
        
        Args:
            quran_search_term: Quran search term
            hadith_keyword: Hadith search keyword
            quran_response: Quran API response
            hadith_responses: Dict of hadith collection responses
            quran_limit: Max Quran verses
            hadith_limit: Max hadiths per collection
            
        Returns:
            Complete guidance package
        """
        # Get Quran verses
        quran_results = self.search_quran(quran_search_term, quran_response, quran_limit)
        
        # Get Hadiths from multiple collections
        hadith_results = {}
        for collection_id, response in hadith_responses.items():
            hadiths = self.hadith_parser.search_hadiths_by_keyword(
                response,
                collection_id,
                hadith_keyword,
                hadith_limit
            )
            if hadiths:
                hadith_results[collection_id] = {
                    "collection_name": self.hadith_parser.COLLECTION_NAMES.get(collection_id, collection_id),
                    "hadiths": [h.to_dict() for h in hadiths],
                    "formatted": [self.hadith_parser.format_hadith_for_display(h) for h in hadiths]
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "quran": quran_results,
            "hadith": hadith_results,
            "summary": {
                "quran_verses": len(quran_results["verses"]),
                "hadith_collections": len(hadith_results),
                "total_hadiths": sum(len(r["hadiths"]) for r in hadith_results.values())
            }
        }


# Example usage and testing
if __name__ == "__main__":
    import json
    import sys
    
    # Set console encoding to UTF-8 for Windows
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    print("="*80, file=sys.stdout, flush=True)
    print("ISLAMIC DATA PARSERS - DEMONSTRATION", file=sys.stdout, flush=True)
    print("="*80, file=sys.stdout, flush=True)
    
    # Example: Parse Quran response
    print("\n1. Quran API Parser Example", file=sys.stdout, flush=True)
    print("-" * 40, file=sys.stdout, flush=True)
    
    try:
        with open("api_responses/quran_search_Heaven.json", "r", encoding="utf-8") as f:
            quran_data = json.load(f)
        
        parser = QuranAPIParser()
        top_verses = parser.get_top_verses(quran_data, limit=3)
        
        print(f"Found {len(top_verses)} verses:", file=sys.stdout, flush=True)
        for verse in top_verses:
            formatted = parser.format_verse_for_display(verse)
            # Handle encoding errors for Windows console
            try:
                print(f"\n{formatted}", file=sys.stdout, flush=True)
            except UnicodeEncodeError:
                print(f"\n{formatted.encode('ascii', 'replace').decode('ascii')}", file=sys.stdout, flush=True)
    except FileNotFoundError:
        print("Quran response file not found", file=sys.stdout, flush=True)
    
    # Example: Parse Hadith response
    print("\n\n2. Hadith API Parser Example", file=sys.stdout, flush=True)
    print("-" * 40, file=sys.stdout, flush=True)
    
    try:
        with open("api_responses/hadith_eng-bukhari.json", "r", encoding="utf-8") as f:
            hadith_data = json.load(f)
        
        hadith_parser = HadithAPIParser()
        matching_hadiths = hadith_parser.search_hadiths_by_keyword(
            hadith_data,
            "eng-bukhari",
            "faith",
            limit=2
        )
        
        print(f"Found {len(matching_hadiths)} hadiths about 'faith':", file=sys.stdout, flush=True)
        for hadith in matching_hadiths:
            formatted = hadith_parser.format_hadith_for_display(hadith)
            # Handle encoding errors for Windows console
            try:
                print(f"\n{formatted}", file=sys.stdout, flush=True)
            except UnicodeEncodeError:
                print(f"\n{formatted.encode('ascii', 'replace').decode('ascii')}", file=sys.stdout, flush=True)
    except FileNotFoundError:
        print("Hadith response file not found", file=sys.stdout, flush=True)
    
    print("\n" + "="*80, file=sys.stdout, flush=True)
    print("PARSERS READY FOR USE", file=sys.stdout, flush=True)
    print("="*80, file=sys.stdout, flush=True)

