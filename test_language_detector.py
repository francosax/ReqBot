"""
Unit Tests for Language Detector Module

Tests language detection functionality including:
- Detection accuracy across all 5 supported languages
- Confidence scoring
- Edge cases and error handling
- Individual detection strategies
- Fallback logic

Author: ReqBot Development Team
Version: 3.0.0
Date: 2025-11-18
"""

import pytest
from language_detector import LanguageDetector, detect_language


class TestLanguageDetectorBasics:
    """Test basic language detector functionality."""

    def test_initialization(self):
        """Test detector initialization with default threshold."""
        detector = LanguageDetector()
        assert detector.confidence_threshold == 0.5

    def test_initialization_custom_threshold(self):
        """Test detector initialization with custom threshold."""
        detector = LanguageDetector(confidence_threshold=0.7)
        assert detector.confidence_threshold == 0.7

    def test_supported_languages(self):
        """Test that all expected languages are supported."""
        detector = LanguageDetector()
        expected_langs = {'en', 'fr', 'de', 'it', 'es'}
        assert set(detector.SUPPORTED_LANGUAGES.keys()) == expected_langs

    def test_is_supported(self):
        """Test language support checking."""
        detector = LanguageDetector()
        assert detector.is_supported('en') is True
        assert detector.is_supported('fr') is True
        assert detector.is_supported('de') is True
        assert detector.is_supported('it') is True
        assert detector.is_supported('es') is True
        assert detector.is_supported('ru') is False
        assert detector.is_supported('zh') is False

    def test_get_language_name(self):
        """Test language name retrieval."""
        detector = LanguageDetector()
        assert detector.get_language_name('en') == 'English'
        assert detector.get_language_name('fr') == 'French'
        assert detector.get_language_name('de') == 'German'
        assert detector.get_language_name('it') == 'Italian'
        assert detector.get_language_name('es') == 'Spanish'
        assert detector.get_language_name('xx') == 'Unknown'


class TestLanguageDetection:
    """Test language detection accuracy."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance for testing."""
        return LanguageDetector(confidence_threshold=0.5)

    @pytest.fixture
    def test_texts(self):
        """Provide test texts in all supported languages."""
        return {
            'en': "The system shall ensure that all requirements are met. The security must be guaranteed.",
            'fr': "Le système doit garantir que toutes les exigences sont remplies. La sécurité devra être assurée.",
            'de': "Das System muss sicherstellen, dass alle Anforderungen erfüllt sind. Die Sicherheit soll gewährleistet werden.",
            'it': "Il sistema deve garantire che tutti i requisiti siano soddisfatti. La sicurezza deve essere garantita.",
            'es': "El sistema debe garantizar que todos los requisitos se cumplan. La seguridad debe estar garantizada."
        }

    def test_detect_english(self, detector, test_texts):
        """Test English language detection."""
        lang, conf = detector.detect(test_texts['en'])
        assert lang == 'en'
        assert conf > 0.5

    def test_detect_french(self, detector, test_texts):
        """Test French language detection."""
        lang, conf = detector.detect(test_texts['fr'])
        assert lang == 'fr'
        assert conf > 0.5

    def test_detect_german(self, detector, test_texts):
        """Test German language detection."""
        lang, conf = detector.detect(test_texts['de'])
        assert lang == 'de'
        assert conf > 0.5

    def test_detect_italian(self, detector, test_texts):
        """Test Italian language detection."""
        lang, conf = detector.detect(test_texts['it'])
        assert lang == 'it'
        assert conf > 0.5

    def test_detect_spanish(self, detector, test_texts):
        """Test Spanish language detection."""
        lang, conf = detector.detect(test_texts['es'])
        assert lang == 'es'
        assert conf > 0.5

    def test_all_languages_correctly_detected(self, detector, test_texts):
        """Test that all languages are correctly detected."""
        for expected_lang, text in test_texts.items():
            detected_lang, confidence = detector.detect(text)
            assert detected_lang == expected_lang, \
                f"Expected {expected_lang}, got {detected_lang} (confidence: {confidence})"
            assert confidence > 0.5, \
                f"Confidence too low for {expected_lang}: {confidence}"


class TestConfidenceScoring:
    """Test confidence score calculation."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance for testing."""
        return LanguageDetector()

    def test_confidence_range(self, detector):
        """Test that confidence scores are in valid range [0, 1]."""
        text = "The system shall ensure that all requirements are met."
        lang, conf = detector.detect(text)
        assert 0.0 <= conf <= 1.0

    def test_longer_text_higher_confidence(self, detector):
        """Test that longer texts generally have higher confidence."""
        short_text = "The system shall ensure requirements."
        long_text = "The system shall ensure that all requirements are met. " * 10

        _, short_conf = detector.detect(short_text)
        _, long_conf = detector.detect(long_text)

        # Longer text should generally have similar or higher confidence
        # (not strictly higher due to sampling)
        assert long_conf >= short_conf * 0.8  # Allow some variance

    def test_confidence_with_mixed_language(self, detector):
        """Test confidence with mixed language text."""
        mixed_text = "The system doit garantir the requirements."
        lang, conf = detector.detect(mixed_text)
        # Mixed language should still detect something, but confidence may vary
        assert lang in ['en', 'fr']  # Should detect English or French


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance for testing."""
        return LanguageDetector()

    def test_empty_string(self, detector):
        """Test detection with empty string."""
        lang, conf = detector.detect("")
        assert lang == 'en'  # Should default to English
        assert conf < 0.5  # Low confidence

    def test_very_short_text(self, detector):
        """Test detection with very short text."""
        lang, conf = detector.detect("Hi")
        assert lang == 'en'  # Should default to English
        assert conf < 0.5  # Low confidence

    def test_whitespace_only(self, detector):
        """Test detection with whitespace only."""
        lang, conf = detector.detect("   \n\t  ")
        assert lang == 'en'  # Should default to English
        assert conf < 0.5  # Low confidence

    def test_numbers_only(self, detector):
        """Test detection with numbers only."""
        lang, conf = detector.detect("123 456 789")
        assert lang == 'en'  # Should default to English

    def test_special_characters_only(self, detector):
        """Test detection with special characters only."""
        lang, conf = detector.detect("!@#$%^&*()")
        assert lang == 'en'  # Should default to English


class TestDetectionStrategies:
    """Test individual detection strategies."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance for testing."""
        return LanguageDetector()

    def test_special_char_detection_french(self, detector):
        """Test French accent detection."""
        text = "à é è ê ë î ï ô ù û ü ÿ œ"
        score = detector._score_special_chars(text.lower(), 'fr')
        assert score > 0.0

    def test_special_char_detection_german(self, detector):
        """Test German umlaut detection."""
        text = "ä ö ü ß"
        score = detector._score_special_chars(text.lower(), 'de')
        assert score > 0.0

    def test_special_char_detection_italian(self, detector):
        """Test Italian accent detection."""
        text = "à è é ì ò ù"
        score = detector._score_special_chars(text.lower(), 'it')
        assert score > 0.0

    def test_special_char_detection_spanish(self, detector):
        """Test Spanish accent detection."""
        text = "á é í ó ú ñ ü ¿ ¡"
        score = detector._score_special_chars(text.lower(), 'es')
        assert score > 0.0

    def test_common_words_english(self, detector):
        """Test English common word detection."""
        text = "the and of to a in that have it for"
        score = detector._score_common_words(text.lower(), 'en')
        assert score > 0.5  # Should match many common words

    def test_common_words_french(self, detector):
        """Test French common word detection."""
        text = "le de un et à il dans"
        score = detector._score_common_words(text.lower(), 'fr')
        assert score > 0.5

    def test_requirement_keywords_english(self, detector):
        """Test English requirement keyword detection."""
        text = "shall must should may will can" * 20  # Repeat for density
        score = detector._score_requirement_keywords(text.lower(), 'en')
        assert score > 0.0

    def test_requirement_keywords_french(self, detector):
        """Test French requirement keyword detection."""
        text = "doit devra devrait peut pourra" * 20
        score = detector._score_requirement_keywords(text.lower(), 'fr')
        assert score > 0.0

    def test_trigrams_english(self, detector):
        """Test English trigram detection."""
        text = "the and ing ion" * 10
        score = detector._score_trigrams(text.lower(), 'en')
        assert score > 0.0

    def test_trigrams_italian(self, detector):
        """Test Italian trigram detection."""
        text = "lla del che gli ell zio" * 10
        score = detector._score_trigrams(text.lower(), 'it')
        assert score > 0.0


class TestFallbackLogic:
    """Test fallback detection logic."""

    def test_manual_override(self):
        """Test manual language override."""
        detector = LanguageDetector()
        text = "This is English text"

        # Override to French
        lang, conf = detector.detect_with_fallback(text, manual_override='fr')
        assert lang == 'fr'
        assert conf == 1.0  # Manual override has full confidence

    def test_invalid_manual_override(self):
        """Test invalid manual language override."""
        detector = LanguageDetector()
        text = "This is English text"

        # Invalid override should be ignored
        lang, conf = detector.detect_with_fallback(text, manual_override='xx')
        assert lang == 'en'  # Should detect normally

    def test_low_confidence_fallback(self):
        """Test fallback to English on low confidence."""
        detector = LanguageDetector(confidence_threshold=0.9)  # Very high threshold
        text = "Some text"

        lang, conf = detector.detect_with_fallback(text)
        assert lang == 'en'  # Should fallback to English

    def test_no_fallback_high_confidence(self):
        """Test no fallback when confidence is sufficient."""
        detector = LanguageDetector(confidence_threshold=0.3)  # Low threshold
        text = "Le système doit garantir que toutes les exigences sont remplies."

        lang, conf = detector.detect_with_fallback(text)
        assert lang == 'fr'  # Should detect French
        assert conf >= 0.3


class TestConvenienceFunction:
    """Test the convenience detect_language() function."""

    def test_detect_language_function(self):
        """Test the standalone detect_language() function."""
        text = "The system shall ensure that all requirements are met."
        lang, conf = detect_language(text)
        assert lang == 'en'
        assert conf > 0.0

    def test_detect_language_custom_threshold(self):
        """Test detect_language() with custom threshold."""
        text = "Short"
        lang, conf = detect_language(text, confidence_threshold=0.9)
        # Should still work with high threshold
        assert lang in ['en', 'fr', 'de', 'it', 'es']


class TestSampleSizing:
    """Test sample size handling."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance for testing."""
        return LanguageDetector()

    def test_default_sample_size(self, detector):
        """Test that default sample size is used."""
        # Create a very long text
        long_text = "The system shall ensure requirements. " * 1000

        lang, conf = detector.detect(long_text)
        assert lang == 'en'
        # Should process efficiently regardless of length

    def test_custom_sample_size(self, detector):
        """Test detection with custom sample size."""
        text = "The system shall ensure requirements. " * 100

        # Use smaller sample
        lang, conf = detector.detect(text, sample_size=100)
        assert lang == 'en'

    def test_sample_size_smaller_than_text(self, detector):
        """Test that sample size limits processing."""
        text = "A" * 10000  # 10k characters

        # Small sample should still work
        lang, conf = detector.detect(text, sample_size=50)
        assert lang in ['en', 'fr', 'de', 'it', 'es']


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
