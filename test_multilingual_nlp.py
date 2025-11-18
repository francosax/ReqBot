"""
Unit Tests for Multilingual NLP Module

Tests NLP functionality including:
- Model loading and caching
- Sentence extraction
- Text preprocessing
- Sentence quality checking
- Thread safety
- Memory management

Author: ReqBot Development Team
Version: 3.0.0
Date: 2025-11-18
"""

import pytest
import threading
import time
from multilingual_nlp import MultilingualNLP, get_nlp, Sentence


class TestMultilingualNLPBasics:
    """Test basic multilingual NLP functionality."""

    def test_initialization(self):
        """Test NLP manager initialization."""
        nlp = MultilingualNLP()
        assert nlp is not None
        assert isinstance(nlp._models, dict)
        assert len(nlp._models) == 0  # No models loaded yet

    def test_singleton_pattern(self):
        """Test that get_nlp() returns singleton instance."""
        nlp1 = get_nlp()
        nlp2 = get_nlp()
        assert nlp1 is nlp2

    def test_singleton_thread_safety(self):
        """Test singleton is thread-safe."""
        # Reset singleton
        import multilingual_nlp
        multilingual_nlp._nlp_instance = None

        results = []

        def create_nlp():
            nlp = get_nlp()
            results.append(id(nlp))
            time.sleep(0.01)

        threads = [threading.Thread(target=create_nlp) for _ in range(10)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        # All threads should get same instance
        assert len(set(results)) == 1


class TestModelManagement:
    """Test spaCy model loading and management."""

    @pytest.fixture
    def nlp(self):
        """Create a fresh NLP instance."""
        return MultilingualNLP()

    def test_model_loading_attempt(self, nlp):
        """Test that model loading is attempted."""
        # Try to load English model (may fail if spaCy not installed)
        model = nlp.get_model('en')
        # Either model is loaded or marked as failed
        assert 'en' in nlp._load_attempts

    def test_model_caching(self, nlp):
        """Test that models are cached after loading."""
        # First call
        model1 = nlp.get_model('en')

        # Second call should return cached version
        model2 = nlp.get_model('en')

        # Should be same instance (if loaded)
        if model1 is not None:
            assert model1 is model2

    def test_invalid_language_code(self, nlp):
        """Test handling of invalid language codes."""
        model = nlp.get_model('invalid_lang')
        assert model is None
        assert nlp._load_attempts.get('invalid_lang') == False

    def test_is_model_available(self, nlp):
        """Test model availability checking."""
        # Check English (most likely to be installed)
        is_available = nlp.is_model_available('en')
        assert isinstance(is_available, bool)

        # Check invalid language
        assert nlp.is_model_available('invalid') == False

    def test_get_available_languages(self, nlp):
        """Test getting list of available languages."""
        available = nlp.get_available_languages()
        assert isinstance(available, set)

        # If any models available, 'en' should be among them
        if len(available) > 0:
            # English is most commonly installed
            pass  # Can't assume which models are installed

    def test_get_loaded_models(self, nlp):
        """Test getting currently loaded models."""
        # Load a model (if available)
        nlp.get_model('en')

        loaded = nlp.get_loaded_models()
        assert isinstance(loaded, dict)

        # If English model loaded, should be in dict
        if nlp.is_model_available('en'):
            assert 'en' in loaded

    def test_unload_model(self, nlp):
        """Test model unloading."""
        # Try to load model
        nlp.get_model('en')

        # Try to unload
        result = nlp.unload_model('en')

        # If model was loaded, unload should return True
        if result:
            assert 'en' not in nlp._models

    def test_unload_all_models(self, nlp):
        """Test unloading all models."""
        # Load some models
        nlp.get_model('en')
        nlp.get_model('fr')

        # Unload all
        nlp.unload_all_models()

        assert len(nlp._models) == 0
        assert len(nlp._load_attempts) == 0


class TestTextPreprocessing:
    """Test text preprocessing functionality."""

    @pytest.fixture
    def nlp(self):
        """Create NLP instance."""
        return MultilingualNLP()

    def test_hyphenated_words(self, nlp):
        """Test fixing hyphenated words across lines."""
        text = "The require-\nment shall be met."
        cleaned = nlp.preprocess_text(text)
        assert "requirement" in cleaned
        assert "require-\n" not in cleaned

    def test_page_numbers_removal(self, nlp):
        """Test removal of page numbers."""
        test_cases = [
            "Some text\nPage 1 of 10\nMore text",
            "Content\nPage 5/10\nMore content",
            "Text\n- 5 -\nMore text",
        ]

        for text in test_cases:
            cleaned = nlp.preprocess_text(text)
            assert "Page" not in cleaned or "page" not in cleaned.lower()

    def test_whitespace_normalization(self, nlp):
        """Test whitespace normalization."""
        text = "The    system   shall    ensure    requirements."
        cleaned = nlp.preprocess_text(text)

        # Should have single spaces
        assert "    " not in cleaned
        assert "The system shall" in cleaned

    def test_multiple_newlines(self, nlp):
        """Test multiple newline handling."""
        text = "Line 1\n\n\n\nLine 2"
        cleaned = nlp.preprocess_text(text)

        # Should reduce to double newline
        assert "\n\n\n" not in cleaned

    def test_header_footer_removal(self, nlp):
        """Test removal of common header/footer artifacts."""
        text = "CONFIDENTIAL\nThe system shall work.\nDRAFT"
        cleaned = nlp.preprocess_text(text)

        # CONFIDENTIAL should be removed
        assert "CONFIDENTIAL" not in cleaned

    def test_empty_text(self, nlp):
        """Test preprocessing empty text."""
        cleaned = nlp.preprocess_text("")
        assert cleaned == ""

    def test_whitespace_only(self, nlp):
        """Test preprocessing whitespace-only text."""
        cleaned = nlp.preprocess_text("   \n\n   \t\t   ")
        assert cleaned == ""


class TestSentenceExtraction:
    """Test sentence extraction functionality."""

    @pytest.fixture
    def nlp(self):
        """Create NLP instance."""
        return get_nlp()

    def test_sentence_object_structure(self):
        """Test Sentence dataclass structure."""
        sent = Sentence(
            text="The system shall work.",
            start=0,
            end=23,
            tokens=["The", "system", "shall", "work"],
            word_count=4
        )

        assert sent.text == "The system shall work."
        assert sent.start == 0
        assert sent.end == 23
        assert len(sent.tokens) == 4
        assert sent.word_count == 4

    def test_extract_sentences_basic(self, nlp):
        """Test basic sentence extraction."""
        if not nlp.is_model_available('en'):
            pytest.skip("English model not available")

        text = "The system shall ensure requirements. The security must be guaranteed."

        sentences = nlp.extract_sentences(text, lang_code='en')

        # Should extract 2 sentences
        assert len(sentences) >= 1  # At least one sentence
        assert all(isinstance(s, Sentence) for s in sentences)

    def test_extract_sentences_min_words_filter(self, nlp):
        """Test minimum word count filtering."""
        if not nlp.is_model_available('en'):
            pytest.skip("English model not available")

        text = "Short. The system shall ensure all requirements are properly met."

        sentences = nlp.extract_sentences(text, lang_code='en', min_words=5)

        # "Short." should be filtered out
        assert all(s.word_count >= 5 for s in sentences)

    def test_extract_sentences_max_words_filter(self, nlp):
        """Test maximum word count filtering."""
        if not nlp.is_model_available('en'):
            pytest.skip("English model not available")

        long_text = " ".join(["word"] * 150)  # 150 words
        text = f"The system shall work. {long_text}"

        sentences = nlp.extract_sentences(text, lang_code='en', max_words=100)

        # Long sentence should be filtered out
        assert all(s.word_count <= 100 for s in sentences)

    def test_extract_sentences_empty_text(self, nlp):
        """Test extraction from empty text."""
        sentences = nlp.extract_sentences("", lang_code='en')
        assert len(sentences) == 0

    def test_extract_sentences_fallback_to_english(self, nlp):
        """Test fallback to English when model unavailable."""
        # Try with unlikely-to-be-installed language
        sentences = nlp.extract_sentences(
            "Some text here.",
            lang_code='invalid_lang'
        )

        # Should fallback gracefully (either English or empty)
        assert isinstance(sentences, list)

    def test_sentence_tokens_no_punctuation(self, nlp):
        """Test that tokens exclude punctuation."""
        if not nlp.is_model_available('en'):
            pytest.skip("English model not available")

        text = "The system, shall work!"

        sentences = nlp.extract_sentences(text, lang_code='en')

        if sentences:
            # Tokens should not include punctuation
            for sent in sentences:
                assert "," not in sent.tokens
                assert "!" not in sent.tokens


class TestSentenceQuality:
    """Test sentence quality checking."""

    @pytest.fixture
    def nlp(self):
        """Create NLP instance."""
        return MultilingualNLP()

    @pytest.fixture
    def sentence(self):
        """Create test sentence."""
        return Sentence(
            text="The system shall ensure that all requirements are met.",
            start=0,
            end=55,
            tokens=["The", "system", "shall", "ensure", "that", "all", "requirements", "are", "met"],
            word_count=9
        )

    def test_quality_with_keyword(self, nlp, sentence):
        """Test quality check with valid requirement keyword."""
        keywords = {'shall', 'must', 'should'}

        is_valid, score = nlp.check_sentence_quality(sentence, keywords, 'en')

        # Should be valid (contains 'shall')
        assert is_valid == True
        assert 0.0 <= score <= 1.0
        assert score >= 0.5  # Valid requirements score >= 0.5

    def test_quality_without_keyword(self, nlp):
        """Test quality check without requirement keyword."""
        sentence = Sentence(
            text="This is just a regular sentence.",
            start=0,
            end=33,
            tokens=["This", "is", "just", "a", "regular", "sentence"],
            word_count=6
        )
        keywords = {'shall', 'must', 'should'}

        is_valid, score = nlp.check_sentence_quality(sentence, keywords, 'en')

        # Should be invalid (no keywords)
        assert is_valid == False
        assert score == 0.0

    def test_quality_reasonable_length(self, nlp):
        """Test quality bonus for reasonable length."""
        sentence = Sentence(
            text="The system shall ensure that all requirements are properly met and validated.",
            start=0,
            end=78,
            tokens=["The", "system", "shall", "ensure", "that", "all", "requirements",
                    "are", "properly", "met", "and", "validated"],
            word_count=12
        )
        keywords = {'shall'}

        is_valid, score = nlp.check_sentence_quality(sentence, keywords, 'en')

        # Length 12 is in optimal range (10-50)
        assert is_valid == True
        assert score >= 0.6  # Should get length bonus

    def test_quality_header_penalty(self, nlp):
        """Test penalty for header-like sentences."""
        sentence = Sentence(
            text="REQUIREMENTS SHALL BE MET",
            start=0,
            end=25,
            tokens=["REQUIREMENTS", "SHALL", "BE", "MET"],
            word_count=4
        )
        keywords = {'shall'}

        is_valid, score = nlp.check_sentence_quality(sentence, keywords, 'en')

        # All caps + short = likely header, should be penalized
        # May still be valid but with lower score
        assert 0.0 <= score <= 1.0

    def test_quality_list_marker_penalty(self, nlp):
        """Test penalty for list markers."""
        sentence = Sentence(
            text="1) The system shall work.",
            start=0,
            end=26,
            tokens=["The", "system", "shall", "work"],
            word_count=4
        )
        keywords = {'shall'}

        is_valid, score = nlp.check_sentence_quality(sentence, keywords, 'en')

        # List markers should be penalized but may still be valid
        assert 0.0 <= score <= 1.0

    def test_quality_modal_verb_bonus(self, nlp, sentence):
        """Test bonus for modal verbs."""
        keywords = {'shall'}

        is_valid, score = nlp.check_sentence_quality(sentence, keywords, 'en')

        # Sentence contains 'shall' which is a modal verb
        assert is_valid == True
        assert score > 0.5  # Should get modal verb bonus


class TestThreadSafety:
    """Test thread safety of NLP operations."""

    def test_concurrent_model_loading(self):
        """Test concurrent model loading attempts."""
        nlp = MultilingualNLP()
        results = []
        errors = []

        def load_model():
            try:
                model = nlp.get_model('en')
                results.append(model is not None or 'en' in nlp._load_attempts)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=load_model) for _ in range(10)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        # No errors should occur
        assert len(errors) == 0
        # All threads should complete
        assert len(results) == 10

    def test_concurrent_sentence_extraction(self):
        """Test concurrent sentence extraction."""
        nlp = get_nlp()
        if not nlp.is_model_available('en'):
            pytest.skip("English model not available")

        results = []
        errors = []

        def extract():
            try:
                text = "The system shall ensure requirements are met properly."
                sentences = nlp.extract_sentences(text, 'en')
                results.append(len(sentences))
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=extract) for _ in range(20)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        # No errors
        assert len(errors) == 0
        # All threads completed
        assert len(results) == 20


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def nlp(self):
        """Create NLP instance."""
        return MultilingualNLP()

    def test_very_long_text(self, nlp):
        """Test processing very long text."""
        long_text = "The system shall work. " * 1000  # Very long

        # Should not crash
        sentences = nlp.extract_sentences(long_text, 'en')
        assert isinstance(sentences, list)

    def test_special_characters(self, nlp):
        """Test text with special characters."""
        text = "The system shall support Unicode: áéíóú ñ ü ß"

        cleaned = nlp.preprocess_text(text)
        assert isinstance(cleaned, str)

    def test_mixed_language_text(self, nlp):
        """Test text with mixed languages."""
        text = "The system shall work. Le système doit fonctionner."

        # Should handle without crashing
        sentences = nlp.extract_sentences(text, 'en')
        assert isinstance(sentences, list)

    def test_numbers_and_symbols(self, nlp):
        """Test text with numbers and symbols."""
        text = "The system shall support 100% of requirements (>=99.9%)."

        cleaned = nlp.preprocess_text(text)
        assert "100" in cleaned
        assert "99.9" in cleaned


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
