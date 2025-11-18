"""
Multi-lingual NLP Module for Requirement Extraction

This module manages spaCy models for multiple languages and provides
NLP processing capabilities for requirement extraction.

Key Features:
- Lazy loading and caching of spaCy models
- Thread-safe model access
- Fallback to English when models unavailable
- Sentence extraction using language-specific models
- Integration with language_detector and language_config

Supported Languages:
- English (en) - en_core_web_sm
- French (fr) - fr_core_news_sm
- German (de) - de_core_news_sm
- Italian (it) - it_core_news_sm
- Spanish (es) - es_core_news_sm

Author: ReqBot Development Team
Version: 3.0.0
Date: 2025-11-18
"""

import logging
import threading
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from language_config import get_language_config

logger = logging.getLogger(__name__)


@dataclass
class Sentence:
    """
    Represents a sentence extracted from text.

    Attributes:
        text: The sentence text
        start: Start character position in original text
        end: End character position in original text
        tokens: List of token strings
        word_count: Number of words/tokens in sentence
    """
    text: str
    start: int
    end: int
    tokens: List[str]
    word_count: int


class MultilingualNLP:
    """
    Manages spaCy NLP models for multiple languages.

    Provides lazy loading, caching, and thread-safe access to language models.
    Falls back to English model if specific language model is unavailable.
    """

    def __init__(self):
        """Initialize the multilingual NLP manager."""
        self._models: Dict[str, any] = {}
        self._model_lock = threading.Lock()
        self._config = get_language_config()
        self._load_attempts: Dict[str, bool] = {}  # Track failed load attempts

        logger.info("MultilingualNLP initialized")

    def get_model(self, lang_code: str):
        """
        Get spaCy model for specified language (lazy loading with caching).

        Args:
            lang_code: ISO 639-1 language code (en, fr, de, it, es)

        Returns:
            spaCy Language model or None if unavailable
        """
        # Check if already loaded
        if lang_code in self._models:
            return self._models[lang_code]

        # Check if we already tried and failed
        if lang_code in self._load_attempts and not self._load_attempts[lang_code]:
            logger.debug(f"Skipping {lang_code} model - previous load attempt failed")
            return None

        # Thread-safe model loading
        with self._model_lock:
            # Double-check after acquiring lock
            if lang_code in self._models:
                return self._models[lang_code]

            # Get model name from config
            model_name = self._config.get_model_name(lang_code)
            if not model_name:
                logger.warning(f"No model configured for language: {lang_code}")
                self._load_attempts[lang_code] = False
                return None

            # Try to load the model
            try:
                import spacy
                logger.info(f"Loading spaCy model: {model_name} for {lang_code}")
                model = spacy.load(model_name)
                self._models[lang_code] = model
                self._load_attempts[lang_code] = True
                logger.info(f"Successfully loaded model: {model_name}")
                return model

            except OSError as e:
                logger.warning(
                    f"Model {model_name} not found. "
                    f"Install with: python -m spacy download {model_name}"
                )
                self._load_attempts[lang_code] = False
                return None

            except Exception as e:
                logger.error(f"Error loading model {model_name}: {str(e)}")
                self._load_attempts[lang_code] = False
                return None

    def is_model_available(self, lang_code: str) -> bool:
        """
        Check if spaCy model is available for language.

        Args:
            lang_code: ISO 639-1 language code

        Returns:
            True if model is loaded or can be loaded, False otherwise
        """
        if lang_code in self._models:
            return True

        model = self.get_model(lang_code)
        return model is not None

    def get_available_languages(self) -> Set[str]:
        """
        Get set of languages with available spaCy models.

        Returns:
            Set of language codes with available models
        """
        available = set()

        for lang_code in self._config.get_supported_languages():
            if self.is_model_available(lang_code):
                available.add(lang_code)

        return available

    def extract_sentences(
        self,
        text: str,
        lang_code: str = 'en',
        min_words: int = 5,
        max_words: int = 100
    ) -> List[Sentence]:
        """
        Extract sentences from text using language-specific model.

        Args:
            text: Text to process
            lang_code: Language code for NLP model
            min_words: Minimum words per sentence (filter shorter)
            max_words: Maximum words per sentence (filter longer)

        Returns:
            List of Sentence objects
        """
        # Get model for language
        model = self.get_model(lang_code)

        if model is None:
            logger.warning(
                f"Model not available for {lang_code}, "
                f"falling back to English"
            )
            model = self.get_model('en')

            if model is None:
                logger.error("English model not available - cannot process text")
                return []

        # Process text with spaCy
        try:
            doc = model(text)
            sentences = []

            for sent in doc.sents:
                # Count tokens (exclude punctuation and spaces)
                tokens = [token.text for token in sent if not token.is_punct and not token.is_space]
                word_count = len(tokens)

                # Apply length filters
                if word_count < min_words:
                    logger.debug(f"Skipping short sentence ({word_count} words): {sent.text[:50]}...")
                    continue

                if word_count > max_words:
                    logger.debug(f"Skipping long sentence ({word_count} words): {sent.text[:50]}...")
                    continue

                # Create Sentence object
                sentence = Sentence(
                    text=sent.text.strip(),
                    start=sent.start_char,
                    end=sent.end_char,
                    tokens=tokens,
                    word_count=word_count
                )

                sentences.append(sentence)

            logger.debug(f"Extracted {len(sentences)} sentences from text ({len(text)} chars)")
            return sentences

        except Exception as e:
            logger.error(f"Error extracting sentences: {str(e)}")
            return []

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text before NLP processing.

        Handles common PDF extraction issues:
        - Hyphenated words across lines
        - Extra whitespace
        - Page numbers
        - Headers/footers patterns

        Args:
            text: Raw text from PDF

        Returns:
            Cleaned text
        """
        import re

        # Fix hyphenated words across line breaks
        # "require-\nment" -> "requirement"
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # Remove page numbers (various patterns)
        # "Page 1 of 10", "Page 1/10", "- 1 -", etc.
        text = re.sub(r'\bPage\s+\d+\s+of\s+\d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPage\s+\d+/\d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\s*-\s*\d+\s*-\s*\n', '\n', text)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double newline

        # Remove common header/footer artifacts
        text = re.sub(r'\bCONFIDENTIAL\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bDRAFT\b(?!\s+(?:shall|must|should))', '', text, flags=re.IGNORECASE)

        return text.strip()

    def check_sentence_quality(
        self,
        sentence: Sentence,
        keywords: Set[str],
        lang_code: str = 'en'
    ) -> Tuple[bool, float]:
        """
        Check if sentence is a valid requirement candidate.

        Evaluates:
        - Contains requirement keywords
        - Has reasonable length
        - Not a header/footer
        - Not a list item marker

        Args:
            sentence: Sentence object to evaluate
            keywords: Set of requirement keywords
            lang_code: Language code for language-specific checks

        Returns:
            Tuple of (is_valid, quality_score)
            quality_score ranges from 0.0 to 1.0
        """
        text_lower = sentence.text.lower()
        score = 0.0

        # Check 1: Contains requirement keyword (40 points)
        has_keyword = any(keyword in text_lower for keyword in keywords)
        if has_keyword:
            score += 0.4
        else:
            # No keyword = not a requirement
            return (False, 0.0)

        # Check 2: Reasonable length (20 points)
        if 10 <= sentence.word_count <= 50:
            score += 0.2
        elif 5 <= sentence.word_count <= 100:
            score += 0.1

        # Check 3: Not a header/title (20 points)
        # Headers are often short, all caps, or end with ':'
        if not sentence.text.isupper() and not sentence.text.endswith(':'):
            score += 0.2

        # Check 4: Not a list marker (10 points)
        # "a)", "1.", "•", etc.
        import re
        if not re.match(r'^\s*[\da-z][\).]\s', sentence.text):
            score += 0.1

        # Check 5: Contains verb or modal verb (10 points)
        # Modal verbs: shall, must, should, may, will, etc.
        modal_verbs = {
            'en': {'shall', 'must', 'should', 'may', 'will', 'can'},
            'fr': {'doit', 'devra', 'devrait', 'peut', 'pourra'},
            'de': {'muss', 'soll', 'sollte', 'kann', 'darf'},
            'it': {'deve', 'dovrebbe', 'può', 'dovrà'},
            'es': {'debe', 'debería', 'puede', 'deberá'}
        }

        lang_modals = modal_verbs.get(lang_code, modal_verbs['en'])
        if any(modal in text_lower for modal in lang_modals):
            score += 0.1

        # Sentence is valid if score >= 0.5
        is_valid = score >= 0.5

        return (is_valid, score)

    def get_loaded_models(self) -> Dict[str, str]:
        """
        Get dictionary of currently loaded models.

        Returns:
            Dict mapping language codes to model names
        """
        loaded = {}
        for lang_code, model in self._models.items():
            model_name = self._config.get_model_name(lang_code)
            loaded[lang_code] = model_name

        return loaded

    def unload_model(self, lang_code: str) -> bool:
        """
        Unload a specific language model to free memory.

        Args:
            lang_code: Language code of model to unload

        Returns:
            True if model was unloaded, False if not loaded
        """
        with self._model_lock:
            if lang_code in self._models:
                del self._models[lang_code]
                logger.info(f"Unloaded model for {lang_code}")
                return True
            return False

    def unload_all_models(self):
        """Unload all models to free memory."""
        with self._model_lock:
            count = len(self._models)
            self._models.clear()
            self._load_attempts.clear()
            logger.info(f"Unloaded {count} models")


# Singleton instance for global access
_nlp_instance: Optional[MultilingualNLP] = None
_nlp_lock = threading.Lock()


def get_nlp() -> MultilingualNLP:
    """
    Get singleton instance of MultilingualNLP (thread-safe).

    Returns:
        MultilingualNLP instance
    """
    global _nlp_instance
    if _nlp_instance is None:
        with _nlp_lock:
            # Double-check after acquiring lock
            if _nlp_instance is None:
                _nlp_instance = MultilingualNLP()
    return _nlp_instance


if __name__ == '__main__':
    # Test the multilingual NLP module
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )

    print("=" * 70)
    print("Multilingual NLP Test")
    print("=" * 70)
    print()

    nlp = get_nlp()

    # Test 1: Check available models
    print("1. Checking available models...")
    available = nlp.get_available_languages()
    if available:
        print(f"   Available languages: {', '.join(sorted(available))}")
    else:
        print("   ⚠ No spaCy models installed")
        print("   Install with: python -m spacy download en_core_web_sm")
    print()

    # Test 2: Try loading English model
    print("2. Loading English model...")
    model = nlp.get_model('en')
    if model:
        print(f"   ✓ English model loaded: {model.meta['name']}")
    else:
        print("   ✗ English model not available")
    print()

    # Test 3: Extract sentences (only if English model available)
    if model:
        print("3. Extracting sentences from test text...")
        test_text = """
        The system shall ensure that all requirements are met.
        The security must be guaranteed at all times.
        Users may customize the interface settings.
        Page 1 of 10
        This is a very short text.
        """

        sentences = nlp.extract_sentences(test_text, 'en', min_words=5, max_words=100)
        print(f"   Extracted {len(sentences)} sentences:")
        for i, sent in enumerate(sentences, 1):
            print(f"   {i}. ({sent.word_count} words) {sent.text[:60]}...")
        print()

        # Test 4: Check sentence quality
        print("4. Checking sentence quality...")
        config = get_language_config()
        keywords = config.get_keywords('en')

        for i, sent in enumerate(sentences, 1):
            is_valid, score = nlp.check_sentence_quality(sent, keywords, 'en')
            status = "✓ VALID" if is_valid else "✗ INVALID"
            print(f"   Sentence {i}: {status} (score: {score:.2f})")
        print()

    # Test 5: Singleton pattern
    print("5. Testing singleton pattern...")
    nlp2 = get_nlp()
    if nlp is nlp2:
        print("   ✓ Singleton pattern working (same instance)")
    else:
        print("   ✗ Singleton pattern failed (different instances)")
    print()

    # Test 6: Text preprocessing
    print("6. Testing text preprocessing...")
    messy_text = """
    The   system   shall    ensure
    require-
    ments   are   met.


    Page 1 of 10

    CONFIDENTIAL
    """
    clean_text = nlp.preprocess_text(messy_text)
    print(f"   Original: {repr(messy_text[:60])}")
    print(f"   Cleaned:  {repr(clean_text[:60])}")
    print()

    print("=" * 70)
    print("Test complete!")
    print("=" * 70)
