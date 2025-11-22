"""
Custom Keyword Extractor - No External Dependencies
Lightweight, domain-aware keyword extraction for Islamic Guidance AI

Features:
- No NLTK/spaCy dependencies
- Domain-specific stopwords and category boosting
- Conservative lemmatization
- Bigram detection
- Mental health, financial, relationship awareness
"""

import re
import math
from collections import Counter, defaultdict
from typing import List, Tuple, Optional, Iterable

# =============================================================================
# STOPWORDS CONFIGURATION
# =============================================================================

_DEFAULT_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "should", "can", "could", "may", "might", "must",
    "cannot", "i", "you", "he", "she", "it", "we", "they", "what", "which", "who", "when", "where",
    "why", "how", "am", "im", "this", "that", "as", "my", "me", "please", "thanks", "thank",
    "also", "so", "if", "its", "it's", "rt", "not", "dont", "cant", "wont", "won't", "thing", 
    "right", "help", "please", "search", "find", "finding", "looking", "look", "looking"
}

_DOMAIN_STOPWORDS = {
    "facing", "feeling", "having", "dealing", "experiencing", "struggling",
    "going", "getting", "trying", "feel", "helped", "helping", "through", "need",
    "needto", "needn't", "want", "wanted", "please", "pls"
}

# =============================================================================
# DOMAIN-SPECIFIC KEYWORD CATEGORIES (For Boosting)
# =============================================================================

MENTAL_HEALTH = {
    "depressed", "depression", "anxiety", "anxious", "stress", "stressed", 
    "overwhelmed", "suicidal", "hopeless", "grief", "sadness", "worry"
}

FINANCIAL = {
    "financial", "finance", "finances", "money", "debt", "bills", "rent", 
    "assistance", "support", "aid", "unemployment", "unemployed", "poverty"
}

RELATIONSHIP = {
    "relationship", "relationships", "partner", "marriage", "family", "friends", 
    "companionship", "lonely", "loneliness", "divorce", "conflict", "boundaries"
}

HEALTH = {
    "health", "illness", "sick", "medical", "pain", "injury", "chronic", 
    "addiction", "disease", "treatment"
}

JOB = {
    "job", "jobless", "unemployed", "employment", "work", "career", 
    "hiring", "jobsearch", "job-search", "workplace"
}

# =============================================================================
# TEXT PREPROCESSING
# =============================================================================

_SUFFIX_SAFE = (
    ("ies", "y"),
    ("sses", "ss"),
    ("ss", "ss"),
)

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")

_CONTRACTIONS = {
    "don't": "do not", "dont": "do not",
    "i'm": "i am", "im": "i am",
    "i've": "i have", "ive": "i have",
    "can't": "can not", "cant": "can not",
    "won't": "will not", "wont": "will not",
    "it's": "it is", "its": "it is",
    "i'd": "i would", "id": "i would",
    "i'll": "i will", "ill": "i will",
    "we're": "we are", "weve": "we have",
    "you're": "you are", "youre": "you are",
    "they're": "they are", "theyre": "they are",
}

def _apply_contractions(text: str) -> str:
    """Expand contractions in text."""
    t = text.lower()
    for k, v in _CONTRACTIONS.items():
        t = t.replace(k, " " + v + " ")
    t = re.sub(r"[''`]", "'", t)
    return t

def tokenize(text: str) -> List[str]:
    """
    Tokenize text into alphanumeric tokens.
    
    Args:
        text: Input text string
    
    Returns:
        List of lowercase tokens
    """
    if not text:
        return []
    text = _apply_contractions(text)
    tokens = _TOKEN_PATTERN.findall(text.lower())
    return tokens

def normalize_token(token: str) -> str:
    """Remove non-alphanumeric characters and lowercase."""
    return re.sub(r"[^a-z0-9]", "", token.lower())

def conservative_lemmatize(token: str) -> str:
    """
    Conservative lemmatization without external libraries.
    
    Rules:
    - Handle plural forms (ies -> y, sses -> ss, s -> '')
    - Handle -ing forms (running -> run)
    - Handle -ed forms (walked -> walk)
    - Handle -ly forms (quickly -> quick)
    - Preserve meaningful words (avoid over-stemming)
    
    Args:
        token: Word to lemmatize
    
    Returns:
        Lemmatized word
    """
    w = token
    
    # Safe suffix replacements
    for suf, rep in _SUFFIX_SAFE:
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            return w[:len(w)-len(suf)] + rep
    
    # Handle -ing (avoid stemming "something", "anything", "nothing")
    if w.endswith("ing") and len(w) > 5:
        if w.endswith("thing"):
            return w
        base = w[:-3]
        alt = base + "e"
        if len(alt) >= 4 and any(v in alt for v in "aeiou"):
            return alt
        if len(base) >= 4:
            return base
    
    # Handle -ed (avoid stemming "eed" endings like "need")
    if w.endswith("ed") and len(w) > 4:
        if w.endswith("eed"):
            return w
        base = w[:-2]
        if len(base) >= 3:
            return base
    
    # Handle -ly
    if w.endswith("ly") and len(w) > 4:
        base = w[:-2]
        if len(base) >= 4:
            return base
    
    # Handle plural -s (avoid double s like "stress")
    if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
        base = w[:-1]
        if len(base) >= 3:
            return base
    
    return w

def is_valid_token(token: str, min_length: int, stopwords: set) -> bool:
    """
    Check if token is valid for keyword extraction.
    
    Args:
        token: Token to validate
        min_length: Minimum length required
        stopwords: Set of stopwords to filter
    
    Returns:
        True if valid keyword candidate
    """
    if not token:
        return False
    if token in stopwords:
        return False
    if all(ch.isdigit() for ch in token):
        return False
    if len(token) < min_length:
        return False
    return True

def bigrams(tokens: List[str]) -> List[Tuple[str, str]]:
    """Generate bigrams from token list."""
    return [(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]

# =============================================================================
# KEYWORD EXTRACTOR CLASS
# =============================================================================

class KeywordExtractorNoDeps:
    """
    Lightweight keyword extractor with no external dependencies.
    
    Features:
    - Domain-aware stopword filtering
    - Conservative lemmatization
    - Category-based keyword boosting
    - Bigram detection
    - TF-based scoring with length and category bonuses
    """
    
    def __init__(self,
                 custom_stopwords: Optional[Iterable[str]] = None,
                 min_word_length: int = 3,
                 max_keywords: int = 4):
        """
        Initialize keyword extractor.
        
        Args:
            custom_stopwords: Additional stopwords to filter
            min_word_length: Minimum word length to consider
            max_keywords: Maximum keywords to extract
        """
        base = set(_DEFAULT_STOPWORDS) | set(_DOMAIN_STOPWORDS)
        if custom_stopwords:
            base |= set(w.lower() for w in custom_stopwords)
        self.stopwords = base
        self.min_word_length = max(1, min_word_length)
        self.max_keywords = max(1, max_keywords)
    
    def _preprocess(self, text: str) -> Tuple[List[str], dict]:
        """
        Preprocess text: tokenize, normalize, track original forms.
        
        Args:
            text: Input text
        
        Returns:
            Tuple of (normalized_tokens, original_mapping)
        """
        toks = tokenize(text)
        normalized = []
        original_map = {}
        
        for t in toks:
            n = normalize_token(t)
            if not n:
                continue
            if n not in original_map:
                original_map[n] = t
            normalized.append(n)
        
        return normalized, original_map
    
    def _category_bonus(self, word: str) -> float:
        """
        Calculate category-based scoring bonus.
        
        Boosts keywords related to important domains:
        - Mental health: 3.0x
        - Job/Employment: 3.0x
        - Financial: 2.5x
        - Relationship: 2.0x
        - Health: 2.0x
        
        Args:
            word: Word to check
        
        Returns:
            Bonus multiplier (1.0 if no category match)
        """
        if word in MENTAL_HEALTH:
            return 3.0
        if word in JOB:
            return 3.0
        if word in FINANCIAL:
            return 2.5
        if word in RELATIONSHIP:
            return 2.0
        if word in HEALTH:
            return 2.0
        return 1.0
    
    def extract(self, text: str, method: str = "hybrid", top_k: Optional[int] = None) -> List[str]:
        """
        Extract keywords from text.
        
        Scoring algorithm:
        1. Term Frequency (TF) * 2.0
        2. Length bonus: log(len + 1) * 0.18
        3. Category multiplier (1.0 - 3.0x)
        4. Bigram co-occurrence bonus: 0.35 per occurrence
        5. Short word penalty: 0.5x for words <= 2 chars
        
        Args:
            text: Input text to extract keywords from
            method: Extraction method (currently only "hybrid" supported)
            top_k: Number of keywords to return (defaults to max_keywords)
        
        Returns:
            List of extracted keywords in original form
        """
        method = (method or "hybrid").lower()
        top_k = top_k or self.max_keywords
        
        normalized, original_map = self._preprocess(text)
        
        if not normalized:
            return []
        
        # Filter valid candidates and apply lemmatization
        candidates = []
        for t in normalized:
            if is_valid_token(t, self.min_word_length, self.stopwords):
                lem = conservative_lemmatize(t)
                if len(lem) >= self.min_word_length:
                    candidates.append(lem)
                else:
                    candidates.append(t)
        
        if not candidates:
            # Emergency fallback: return non-stopwords
            raw = [t for t in normalized if t not in self.stopwords]
            return [original_map.get(r, r) for r in raw[:top_k]]
        
        # Calculate term frequencies
        freq = Counter(candidates)
        scores = defaultdict(float)
        total_tokens = sum(freq.values()) if freq else 1
        
        # Base scoring: TF + length + category
        for w, count in freq.items():
            tf = count / total_tokens
            length_boost = math.log(len(w) + 1)
            cat = self._category_bonus(w)
            scores[w] = (tf * 2.0) + (length_boost * 0.18)
            scores[w] *= cat
        
        # Bigram co-occurrence bonus
        bg = bigrams([c for c in candidates])
        if bg:
            bg_freq = Counter(" ".join(pair) for pair in bg)
            for phrase, cnt in bg_freq.items():
                parts = phrase.split()
                for p in parts:
                    if p in scores:
                        scores[p] += 0.35 * (cnt / max(1, total_tokens))
        
        # Short word penalty
        for w in list(scores.keys()):
            if len(w) <= 2:
                scores[w] *= 0.5
        
        # Sort by score and select top keywords
        scored = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected = [w for w, _ in scored if w in freq][:top_k]
        
        # Fill remaining slots with most frequent words
        if len(selected) < top_k:
            for w, _ in freq.most_common():
                if w not in selected:
                    selected.append(w)
                if len(selected) >= top_k:
                    break
        
        # Map back to original forms
        output = []
        for w in selected:
            out = original_map.get(w, w)
            if out:
                output.append(out)
        
        # Remove duplicates while preserving order
        seen = set()
        final = []
        for tok in output:
            if tok not in seen:
                final.append(tok)
                seen.add(tok)
        
        return final[:top_k]
    
    def process_many(self, texts: Iterable[str], method: str = "hybrid", top_k: Optional[int] = None) -> List[List[str]]:
        """
        Extract keywords from multiple texts.
        
        Args:
            texts: Iterable of text strings
            method: Extraction method
            top_k: Number of keywords per text
        
        Returns:
            List of keyword lists (one per input text)
        """
        out = []
        for t in texts:
            out.append(self.extract(t, method=method, top_k=top_k))
        return out

# =============================================================================
# MODULE-LEVEL INSTANCE (For easy importing)
# =============================================================================

# Default instance with optimal settings for Islamic Guidance AI
default_extractor = KeywordExtractorNoDeps(min_word_length=3, max_keywords=3)

def extract_keywords(text: str, max_keywords: int = 3) -> List[str]:
    """
    Convenience function for quick keyword extraction.
    
    Args:
        text: Input text
        max_keywords: Number of keywords to extract
    
    Returns:
        List of extracted keywords
    """
    return default_extractor.extract(text, top_k=max_keywords)
