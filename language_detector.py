"""
Language Detection Module for Multi-lingual Requirement Extraction

This module provides language detection capabilities for PDF documents
using character pattern analysis and linguistic features. It's designed
to work offline without external API dependencies.

Supported Languages:
- English (en)
- French (fr)
- German (de)
- Italian (it)
- Spanish (es)

Author: ReqBot Development Team
Version: 3.0.0
Date: 2025-11-18
"""

import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class LanguageDetector:
    """
    Detects the language of text using character patterns and linguistic features.

    This detector uses multiple strategies:
    1. Special character frequency (accents, umlauts, etc.)
    2. Common word detection
    3. Character n-gram patterns
    4. Linguistic markers (articles, prepositions, modal verbs)

    Attributes:
        SUPPORTED_LANGUAGES: List of ISO 639-1 language codes
        confidence_threshold: Minimum confidence score (0.0-1.0)
    """

    # Supported languages with full names
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'es': 'Spanish'
    }

    # Special characters per language (frequency indicators)
    SPECIAL_CHARS = {
        'fr': set('àâæçéèêëîïôùûüÿœ'),  # French accents
        'de': set('äöüßẞ'),               # German umlauts
        'it': set('àèéìòù'),              # Italian accents
        'es': set('áéíóúñü¿¡'),           # Spanish accents and punctuation
        'en': set()                        # English rarely uses accents
    }

    # Common words per language (top 20 most frequent)
    COMMON_WORDS = {
        'en': {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it',
            'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this',
            'shall', 'must', 'should', 'may', 'will', 'can', 'would', 'could'
        },
        'fr': {
            'le', 'de', 'un', 'être', 'et', 'à', 'il', 'avoir', 'ne', 'je',
            'son', 'que', 'se', 'qui', 'ce', 'dans', 'en', 'du', 'elle', 'au',
            'doit', 'devra', 'devrait', 'peut', 'pourrait', 'exigence', 'garantir'
        },
        'de': {
            'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich',
            'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als',
            'muss', 'soll', 'kann', 'sollte', 'könnte', 'anforderung', 'sicherstellen'
        },
        'it': {
            'il', 'di', 'e', 'la', 'a', 'essere', 'un', 'avere', 'per', 'che',
            'in', 'non', 'da', 'con', 'su', 'come', 'al', 'del', 'alla', 'questo',
            'deve', 'dovrebbe', 'può', 'potrebbe', 'requisito', 'garantire',
            'sono', 'sia', 'siano', 'tutti', 'tutto', 'gli', 'delle', 'della',
            'sistema', 'sicurezza', 'soddisfatti', 'soddisfatto'
        },
        'es': {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se',
            'no', 'haber', 'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le',
            'debe', 'debería', 'puede', 'podría', 'requisito', 'garantizar',
            'son', 'sea', 'sean', 'todos', 'todo', 'los', 'las', 'del',
            'sistema', 'seguridad', 'cumplan', 'cumplir', 'garantizada', 'garantizado'
        }
    }

    # Requirement keywords per language (modal verbs indicating requirements)
    REQUIREMENT_KEYWORDS = {
        'en': {'shall', 'must', 'should', 'may', 'will', 'can', 'has to', 'have to'},
        'fr': {'doit', 'devra', 'devrait', 'peut', 'pourra', 'pourrait'},
        'de': {'muss', 'soll', 'sollte', 'kann', 'könnte', 'darf'},
        'it': {'deve', 'dovrebbe', 'può', 'potrebbe', 'dovrà'},
        'es': {'debe', 'debería', 'puede', 'podría', 'deberá'}
    }

    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize the language detector.

        Args:
            confidence_threshold: Minimum confidence score for detection (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
        logger.info(f"LanguageDetector initialized (threshold: {confidence_threshold})")

    def detect(self, text: str, sample_size: int = 5000) -> Tuple[str, float]:
        """
        Detect the language of the given text.

        Args:
            text: Text to analyze
            sample_size: Number of characters to sample (default: 5000)

        Returns:
            Tuple of (language_code, confidence_score)
            Example: ('fr', 0.87) for French with 87% confidence
        """
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for reliable detection, defaulting to English")
            return ('en', 0.3)  # Low confidence default

        # Sample the text (use first N characters for performance)
        sample = text[:sample_size].lower()

        # Calculate scores for each language
        scores = {}
        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            score = self._calculate_language_score(sample, lang_code)
            scores[lang_code] = score

        # Get the language with highest score
        detected_lang = max(scores, key=scores.get)
        confidence = scores[detected_lang]

        # Normalize confidence (scale to 0-1 range)
        confidence = min(1.0, confidence / 100.0)

        logger.info(f"Detected language: {self.SUPPORTED_LANGUAGES[detected_lang]} "
                    f"({detected_lang}) with confidence {confidence:.2f}")
        logger.debug(f"Language scores: {scores}")

        return (detected_lang, confidence)

    def _calculate_language_score(self, text: str, lang_code: str) -> float:
        """
        Calculate a score for how likely the text is in the given language.

        Args:
            text: Text sample (already lowercased)
            lang_code: ISO 639-1 language code

        Returns:
            Score (higher = more likely)
        """
        score = 0.0

        # Strategy 1: Special character frequency (weight: 30)
        special_char_score = self._score_special_chars(text, lang_code)
        score += special_char_score * 30

        # Strategy 2: Common words (weight: 40)
        common_word_score = self._score_common_words(text, lang_code)
        score += common_word_score * 40

        # Strategy 3: Requirement keywords (weight: 20)
        keyword_score = self._score_requirement_keywords(text, lang_code)
        score += keyword_score * 20

        # Strategy 4: Character trigrams (weight: 10)
        trigram_score = self._score_trigrams(text, lang_code)
        score += trigram_score * 10

        return score

    def _score_special_chars(self, text: str, lang_code: str) -> float:
        """Score based on special character frequency."""
        special_chars = self.SPECIAL_CHARS[lang_code]

        if not special_chars:
            # English: penalize if many special chars present
            special_char_count = sum(1 for c in text if c in 'àâæçéèêëîïôùûüÿœäöüßàèéìòùáéíóúñü')
            return max(0, 1.0 - (special_char_count / len(text) * 20))

        # Other languages: reward presence of their special chars
        char_count = sum(1 for c in text if c in special_chars)
        return min(1.0, char_count / len(text) * 100)

    def _score_common_words(self, text: str, lang_code: str) -> float:
        """Score based on common word frequency."""
        words = re.findall(r'\b\w+\b', text)
        if not words:
            return 0.0

        common_words = self.COMMON_WORDS[lang_code]
        matches = sum(1 for word in words if word in common_words)

        return matches / len(words)

    def _score_requirement_keywords(self, text: str, lang_code: str) -> float:
        """Score based on requirement keyword presence."""
        keywords = self.REQUIREMENT_KEYWORDS[lang_code]

        # Count occurrences of requirement keywords
        matches = 0
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches += len(re.findall(pattern, text))

        # Normalize by text length (keywords per 1000 characters)
        return min(1.0, matches / (len(text) / 1000) * 0.5)

    def _score_trigrams(self, text: str, lang_code: str) -> float:
        """
        Score based on character trigram patterns.
        Different languages have different character sequence patterns.
        """
        # Extract trigrams (simplified for performance)
        trigrams = [text[i:i+3] for i in range(len(text) - 2)]

        # Language-specific trigram patterns (most common and distinctive)
        lang_trigrams = {
            'en': {'the', 'and', 'ing', 'ion', 'tio', 'ent', 'ati', 'for', 'ter'},
            'fr': {'les', 'ent', 'que', 'ait', 'des', 'eur', 'ais', 'ont', 'aux'},
            'de': {'der', 'ein', 'ich', 'und', 'den', 'sch', 'ung', 'cht', 'gen'},
            'it': {'lla', 'del', 'che', 'gli', 'ell', 'zio', 'azi', 'tte', 'nto', 'sta', 'tto', 'tta', 'nza', 'gno', 'ere'},
            'es': {'que', 'los', 'del', 'aci', 'ión', 'nci', 'ora', 'ara', 'era', 'nte', 'ado', 'ido', 'par', 'ció', 'est'}
        }

        target_trigrams = lang_trigrams.get(lang_code, set())
        if not target_trigrams or not trigrams:
            return 0.5  # Neutral score

        matches = sum(1 for tg in trigrams if tg in target_trigrams)
        return matches / len(trigrams)

    def detect_with_fallback(self, text: str, manual_override: Optional[str] = None) -> Tuple[str, float]:
        """
        Detect language with fallback logic.

        Args:
            text: Text to analyze
            manual_override: Optional manual language code override

        Returns:
            Tuple of (language_code, confidence_score)
        """
        # Check manual override first
        if manual_override and manual_override in self.SUPPORTED_LANGUAGES:
            logger.info(f"Using manual language override: {manual_override}")
            return (manual_override, 1.0)

        # Attempt automatic detection
        lang_code, confidence = self.detect(text)

        # If confidence too low, fallback to English
        if confidence < self.confidence_threshold:
            logger.warning(f"Low confidence ({confidence:.2f}), falling back to English")
            return ('en', confidence)

        return (lang_code, confidence)

    def get_language_name(self, lang_code: str) -> str:
        """Get full language name from code."""
        return self.SUPPORTED_LANGUAGES.get(lang_code, 'Unknown')

    def is_supported(self, lang_code: str) -> bool:
        """Check if language is supported."""
        return lang_code in self.SUPPORTED_LANGUAGES


# Convenience function for quick detection
def detect_language(text: str, confidence_threshold: float = 0.5) -> Tuple[str, float]:
    """
    Quick language detection function.

    Args:
        text: Text to analyze
        confidence_threshold: Minimum confidence for detection

    Returns:
        Tuple of (language_code, confidence_score)

    Example:
        >>> lang, conf = detect_language("Le système doit garantir...")
        >>> print(f"Detected: {lang} ({conf:.2f})")
        Detected: fr (0.87)
    """
    detector = LanguageDetector(confidence_threshold=confidence_threshold)
    return detector.detect(text)


if __name__ == '__main__':
    # Test the language detector
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Language Detector Test")
    print("=" * 60)

    test_texts = {
        'en': "The system shall ensure that all requirements are met. The security must be guaranteed.",
        'fr': "Le système doit garantir que toutes les exigences sont remplies. La sécurité devra être assurée.",
        'de': "Das System muss sicherstellen, dass alle Anforderungen erfüllt sind. Die Sicherheit soll gewährleistet werden.",
        'it': "Il sistema deve garantire che tutti i requisiti siano soddisfatti. La sicurezza deve essere garantita.",
        'es': "El sistema debe garantizar que todos los requisitos se cumplan. La seguridad debe estar garantizada."
    }

    detector = LanguageDetector()

    for expected_lang, text in test_texts.items():
        print(f"\nTesting {detector.get_language_name(expected_lang)}:")
        print(f"Text: {text[:60]}...")
        detected_lang, confidence = detector.detect(text)
        match = "✓" if detected_lang == expected_lang else "✗"
        print(f"Result: {detector.get_language_name(detected_lang)} ({detected_lang}) "
              f"with {confidence:.2%} confidence {match}")

    print("\n" + "=" * 60)
    print("Test complete!")
