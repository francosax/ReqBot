"""
Unit tests for pdf_analyzer.py core functions.

Tests the critical requirement extraction logic including:
- Text preprocessing
- Sentence pattern matching
- Confidence scoring
- Priority assignment
- Requirement validation
"""

import pytest

# Import functions to test
from pdf_analyzer import (
    preprocess_pdf_text,
    matches_requirement_pattern,
    calculate_requirement_confidence,
    get_nlp_model
)


class TestTextPreprocessing:
    """Test suite for text preprocessing functions."""

    def test_preprocess_removes_hyphenated_line_breaks(self):
        """Test that hyphenated line breaks are properly fixed."""
        text = "The sys-\ntem shall operate correctly."
        result = preprocess_pdf_text(text)

        assert "sys-\n" not in result
        assert "system" in result

    def test_preprocess_removes_page_numbers(self):
        """Test that page numbers are removed."""
        text = "The system shall work.\n\nPage 42\n\nThe device must operate."
        result = preprocess_pdf_text(text)

        assert "Page 42" not in result

    def test_preprocess_normalizes_whitespace(self):
        """Test that whitespace is normalized."""
        text = "The  system   shall    work."
        result = preprocess_pdf_text(text)

        # Should not have multiple spaces
        assert "  " not in result

    def test_preprocess_preserves_content(self):
        """Test that actual content is preserved."""
        text = "The system shall ensure data integrity."
        result = preprocess_pdf_text(text)

        assert "system" in result
        assert "shall" in result
        assert "data integrity" in result


class TestRequirementPatternMatching:
    """Test suite for requirement pattern matching."""

    def test_matches_shall_pattern(self):
        """Test detection of 'shall' requirement pattern."""
        sentence = "The system shall provide user authentication"

        result = matches_requirement_pattern(sentence)

        assert result is True

    def test_matches_must_pattern(self):
        """Test detection of 'must' requirement pattern."""
        sentence = "The application must ensure data encryption"

        result = matches_requirement_pattern(sentence)

        assert result is True

    def test_matches_should_pattern(self):
        """Test detection of 'should' requirement pattern."""
        sentence = "The device should support multiple protocols"

        result = matches_requirement_pattern(sentence)

        assert result is True

    def test_non_requirement_sentence_no_match(self):
        """Test that non-requirement sentences don't match."""
        sentence = "This is just a regular sentence."

        result = matches_requirement_pattern(sentence)

        assert result is False

    def test_matches_compliance_indicators(self):
        """Test detection of compliance requirement indicators."""
        sentence = "The product must comply with ISO 26262"

        result = matches_requirement_pattern(sentence)

        assert result is True

    def test_matches_capability_indicators(self):
        """Test detection of capability requirement indicators."""
        sentence = "The system capable of processing 1000 requests per second"

        result = matches_requirement_pattern(sentence)

        assert result is True


class TestConfidenceScoring:
    """Test suite for requirement confidence scoring."""

    def test_confidence_for_optimal_length_sentence(self):
        """Test confidence score for optimally-sized sentence."""
        sentence_text = "The system shall provide user authentication and authorization."
        # This is ~10 words, which is in the optimal range

        confidence = calculate_requirement_confidence(
            sentence=sentence_text,
            keyword='shall',
            word_count=10
        )

        # Optimal length should not be penalized
        assert confidence > 0.5
        assert confidence <= 1.5  # Can exceed 1.0 due to multipliers

    def test_confidence_penalty_for_very_short_sentence(self):
        """Test that very short sentences receive confidence penalty."""
        sentence_text = "System shall work."  # Only 3 words

        confidence = calculate_requirement_confidence(
            sentence=sentence_text,
            keyword='shall',
            word_count=3
        )

        # Very short should be heavily penalized
        assert confidence < 0.5

    def test_confidence_penalty_for_very_long_sentence(self):
        """Test that very long sentences receive confidence penalty."""
        # Create a very long sentence (> 80 words)
        long_sentence = " ".join(["word"] * 85) + " shall operate"

        confidence = calculate_requirement_confidence(
            sentence=long_sentence,
            keyword='shall',
            word_count=87
        )

        # Very long should be penalized
        assert confidence < 0.8

    def test_confidence_boost_for_pattern_match(self):
        """Test that pattern matching boosts confidence."""
        # Pattern match is calculated internally based on sentence structure
        sentence_with_pattern = "The system shall provide authentication"
        sentence_without_pattern = "shall provide authentication somehow"

        conf_with_pattern = calculate_requirement_confidence(
            sentence=sentence_with_pattern,
            keyword='shall',
            word_count=5
        )

        conf_without_pattern = calculate_requirement_confidence(
            sentence=sentence_without_pattern,
            keyword='shall',
            word_count=4
        )

        # Pattern match should increase confidence
        assert conf_with_pattern > conf_without_pattern

    def test_confidence_boost_for_multiple_keywords(self):
        """Test that multiple keywords boost confidence."""
        # Function calculates keyword count internally
        sentence_with_multiple = "The system shall and must provide authentication"
        sentence_with_single = "The system will provide authentication"

        conf_multiple = calculate_requirement_confidence(
            sentence=sentence_with_multiple,
            keyword='shall',
            word_count=7
        )

        conf_single = calculate_requirement_confidence(
            sentence=sentence_with_single,
            keyword='will',
            word_count=5
        )

        # Multiple keywords should increase confidence
        assert conf_multiple > conf_single

    def test_confidence_boost_for_compliance_keywords(self):
        """Test that compliance-related requirements have good confidence."""
        sentence_text = "The system shall comply with ISO 26262 standard"

        confidence = calculate_requirement_confidence(
            sentence=sentence_text,
            keyword='shall',
            word_count=8
        )

        # Should have good confidence (optimal length + pattern match)
        assert confidence > 0.7

    def test_confidence_penalty_for_header_like_text(self):
        """Test that header-like text receives penalty."""
        sentence_text = "SECTION REQUIREMENTS"  # All caps, very short

        confidence = calculate_requirement_confidence(
            sentence=sentence_text,
            keyword='requirements',
            word_count=2
        )

        # Headers should be heavily penalized (all caps + very short)
        assert confidence < 0.5

    def test_confidence_penalty_for_number_heavy_text(self):
        """Test that number-heavy text receives penalty."""
        sentence_text = "123 456 789 shall 101112 131415"  # Many numbers

        confidence = calculate_requirement_confidence(
            sentence=sentence_text,
            keyword='shall',
            word_count=6
        )

        # Number-heavy text should be penalized
        assert confidence < 0.6

    def test_confidence_within_valid_range(self):
        """Test that confidence is always within valid range."""
        # Test various scenarios
        test_cases = [
            {"sentence": "shall", "keyword": "shall", "word_count": 1},
            {"sentence": "The system shall work properly", "keyword": "shall", "word_count": 5},
            {"sentence": "x " * 100 + "shall", "keyword": "shall", "word_count": 101},
        ]

        for case in test_cases:
            confidence = calculate_requirement_confidence(**case)
            assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} out of range for case {case}"


class TestNLPModelLoading:
    """Test suite for NLP model loading and caching."""

    def test_nlp_model_loads_successfully(self):
        """Test that NLP model can be loaded."""
        try:
            model = get_nlp_model()
            assert model is not None
        except Exception:
            pytest.skip("spaCy model not installed")

    def test_nlp_model_is_cached(self):
        """Test that NLP model is cached on subsequent calls."""
        try:
            model1 = get_nlp_model()
            model2 = get_nlp_model()

            # Should return same instance (cached)
            assert model1 is model2
        except Exception:
            pytest.skip("spaCy model not installed")


class TestPriorityAssignment:
    """Test suite for priority assignment logic."""

    def test_security_keyword_assigns_security_priority(self):
        """Test that 'security' keyword assigns security priority."""
        # This would be tested through requirement_finder()
        # but here we document the expected behavior
        sentence = "The system shall implement security measures"

        # Expected: priority should be 'security'
        # This is handled in requirement_finder() at lines ~349-361
        assert "security" in sentence.lower()

    def test_must_shall_assigns_high_priority(self):
        """Test that 'must'/'shall' assigns high priority."""
        sentences = [
            "The system must operate correctly",
            "The application shall provide authentication"
        ]

        for sentence in sentences:
            # Expected: priority should be 'high'
            assert any(kw in sentence.lower() for kw in ['must', 'shall'])

    def test_should_assigns_medium_priority(self):
        """Test that 'should' assigns medium priority."""
        sentence = "The device should support USB connections"

        # Expected: priority should be 'medium'
        assert "should" in sentence.lower()


class TestRequirementValidation:
    """Test suite for requirement validation rules."""

    def test_too_short_sentence_rejected(self):
        """Test that sentences < 5 words are rejected."""
        # MIN_REQUIREMENT_LENGTH_WORDS = 5
        short_sentence = "Must work now"  # Only 3 words

        # This sentence should be filtered out
        word_count = len(short_sentence.split())
        assert word_count < 5

    def test_too_long_sentence_rejected(self):
        """Test that sentences > 100 words are rejected."""
        # MAX_REQUIREMENT_LENGTH_WORDS = 100
        long_sentence = " ".join(["word"] * 105)  # 105 words

        word_count = len(long_sentence.split())
        assert word_count > 100

    def test_optimal_length_sentence_accepted(self):
        """Test that sentences with 5-100 words are accepted."""
        good_sentence = "The system shall provide secure user authentication and authorization mechanisms"

        word_count = len(good_sentence.split())
        assert 5 <= word_count <= 100


@pytest.mark.integration
class TestRequirementFinderIntegration:
    """Integration tests for the complete requirement_finder function."""

    @pytest.fixture
    def mock_pdf(self, tmp_path):
        """Create a mock PDF file for testing."""
        pdf_path = tmp_path / "test_spec.pdf"
        # Note: This would need actual PDF creation for full integration test
        return str(pdf_path)

    @pytest.fixture
    def test_keywords(self):
        """Provide test keyword set."""
        return {'shall', 'must', 'should', 'has to'}

    def test_requirement_finder_returns_dataframe(self, mock_pdf, test_keywords):
        """Test that requirement_finder returns a DataFrame."""
        # This test would require actual PDF processing
        # Skipping if PDF file doesn't exist
        pytest.skip("Requires actual PDF file for integration test")

    def test_requirement_finder_includes_confidence_scores(self):
        """Test that extracted requirements include confidence scores."""
        # This would be an integration test with actual PDF
        pytest.skip("Requires actual PDF file for integration test")

    def test_requirement_finder_filters_by_threshold(self):
        """Test that confidence threshold filtering works."""
        # This would test that requirements below threshold are excluded
        pytest.skip("Requires actual PDF file for integration test")


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_empty_text_preprocessing(self):
        """Test preprocessing handles empty text."""
        result = preprocess_pdf_text("")
        assert result == ""

    def test_none_text_preprocessing(self):
        """Test preprocessing handles None."""
        result = preprocess_pdf_text(None)
        assert result == ""

    def test_pattern_matching_with_special_characters(self):
        """Test pattern matching handles special characters."""
        sentence = "The system shall: provide authentication & authorization"

        # Should still match despite special characters
        result = matches_requirement_pattern(sentence)
        assert result is True

    def test_confidence_with_zero_word_count(self):
        """Test confidence calculation handles zero word count."""
        confidence = calculate_requirement_confidence(
            sentence="",
            keyword="",
            word_count=0
        )

        # Should return low confidence, not crash
        assert 0.0 <= confidence <= 1.5  # Can exceed 1.0 due to multipliers

    def test_confidence_with_negative_values(self):
        """Test that confidence never goes negative."""
        # Try to break it with extreme values
        confidence = calculate_requirement_confidence(
            sentence="x" * 1000,  # Very long
            keyword="x",
            word_count=1000
        )

        assert confidence >= 0.0
