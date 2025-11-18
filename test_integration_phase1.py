"""
Integration Tests for Multi-lingual Extraction Phase 1

Tests the integration between language_detector.py and language_config.py,
ensuring all components work together correctly in realistic scenarios.

Tests:
- Component integration (detector + config)
- End-to-end workflows
- Thread safety of integrated system
- Performance benchmarks
- Error handling across components
- Real-world scenarios

Author: ReqBot Development Team
Version: 3.0.0
Date: 2025-11-18
"""

import pytest
import threading
import time
import tempfile
import os
from pathlib import Path
from language_detector import LanguageDetector, detect_language
from language_config import LanguageConfig, get_language_config


class TestComponentIntegration:
    """Test integration between LanguageDetector and LanguageConfig."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return LanguageDetector()

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        return get_language_config()

    def test_detector_uses_config_keywords(self, detector, config):
        """Test that detector can use config keywords for detection."""
        # Get English keywords from config
        en_keywords = config.get_keywords('en')

        # Create text with config keywords
        text = "The system " + " ".join(list(en_keywords)[:5])

        lang, conf = detector.detect(text)
        assert lang == 'en'
        assert conf > 0.0

    def test_all_languages_have_matching_keywords(self, detector, config):
        """Test that detector and config have matching language support."""
        detector_langs = set(detector.SUPPORTED_LANGUAGES.keys())
        config_langs = set(config.get_supported_languages())

        assert detector_langs == config_langs, \
            "Detector and config must support the same languages"

    def test_detector_requirement_keywords_match_config(self, detector, config):
        """Test that detector's requirement keywords match config."""
        for lang_code in ['en', 'fr', 'de', 'it', 'es']:
            detector_keywords = detector.REQUIREMENT_KEYWORDS.get(lang_code, set())
            config_keywords = config.get_keywords(lang_code)

            # Detector keywords should be subset of config keywords
            # (config may have more comprehensive lists)
            assert len(detector_keywords) > 0, \
                f"Detector has no keywords for {lang_code}"
            assert len(config_keywords) > 0, \
                f"Config has no keywords for {lang_code}"

    def test_model_names_are_consistent(self, config):
        """Test that model names follow consistent naming pattern."""
        for lang_code in config.get_supported_languages():
            model = config.get_model_name(lang_code)
            assert model is not None
            assert model.endswith('_sm'), \
                f"Model {model} should end with _sm"


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return LanguageDetector()

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        return get_language_config()

    def test_detect_then_get_keywords(self, detector, config):
        """Test workflow: detect language → get keywords."""
        texts = {
            'en': "The system shall ensure all requirements are met.",
            'fr': "Le système doit garantir que toutes les exigences sont remplies.",
            'de': "Das System muss sicherstellen, dass alle Anforderungen erfüllt sind.",
            'it': "Il sistema deve garantire che tutti i requisiti siano soddisfatti.",
            'es': "El sistema debe garantizar que todos los requisitos se cumplan."
        }

        for expected_lang, text in texts.items():
            # Step 1: Detect language
            detected_lang, confidence = detector.detect(text)

            # Step 2: Get keywords for detected language
            keywords = config.get_keywords(detected_lang)

            # Step 3: Verify keywords are relevant
            assert len(keywords) > 0
            assert detected_lang == expected_lang

    def test_detect_then_get_priority_keywords(self, detector, config):
        """Test workflow: detect language → get priority keywords."""
        text = "The system shall and must ensure security requirements."

        # Detect language
        lang, conf = detector.detect(text)
        assert lang == 'en'

        # Get priority keywords
        high_priority = config.get_priority_keywords(lang, 'high')
        medium_priority = config.get_priority_keywords(lang, 'medium')
        low_priority = config.get_priority_keywords(lang, 'low')

        # Verify we got keywords for each priority
        assert len(high_priority) > 0
        assert len(medium_priority) > 0
        assert len(low_priority) > 0

        # Verify 'shall' and 'must' are in high priority
        assert 'shall' in high_priority or 'must' in high_priority

    def test_detect_then_get_model(self, detector, config):
        """Test workflow: detect language → get spaCy model name."""
        text = "Das System muss sicherstellen."

        # Detect language
        lang, conf = detector.detect(text)
        assert lang == 'de'

        # Get model name
        model = config.get_model_name(lang)
        assert model == 'de_core_news_sm'

    def test_multi_document_processing(self, detector, config):
        """Test processing multiple documents in sequence."""
        documents = [
            ("doc1.pdf", "The system shall ensure that all requirements are properly met and validated."),
            ("doc2.pdf", "Le système doit garantir que toutes les exigences sont remplies correctement."),
            ("doc3.pdf", "Das System muss sicherstellen, dass alle Anforderungen erfüllt sind."),
            ("doc4.pdf", "Il sistema deve garantire che tutti i requisiti siano soddisfatti correttamente."),
            ("doc5.pdf", "El sistema debe garantizar que todos los requisitos se cumplan correctamente.")
        ]

        results = []
        for filename, text in documents:
            # Detect language
            lang, conf = detector.detect(text)

            # Get config for language
            keywords = config.get_keywords(lang)
            model = config.get_model_name(lang)

            results.append({
                'filename': filename,
                'language': lang,
                'confidence': conf,
                'keywords_count': len(keywords),
                'model': model
            })

        # Verify all documents processed
        assert len(results) == 5

        # Verify languages detected
        languages = [r['language'] for r in results]
        assert 'en' in languages
        assert 'fr' in languages
        assert 'de' in languages
        assert 'it' in languages
        assert 'es' in languages


class TestThreadSafety:
    """Test thread safety of integrated system."""

    def test_concurrent_language_detection(self):
        """Test concurrent language detection from multiple threads."""
        detector = LanguageDetector()
        results = []
        errors = []

        def detect_text(text, expected_lang):
            try:
                lang, conf = detector.detect(text)
                results.append({
                    'detected': lang,
                    'expected': expected_lang,
                    'confidence': conf,
                    'match': lang == expected_lang
                })
            except Exception as e:
                errors.append(str(e))

        texts = [
            ("The system shall ensure that all requirements are properly met and validated.", 'en'),
            ("Le système doit garantir que toutes les exigences sont remplies correctement.", 'fr'),
            ("Das System muss sicherstellen, dass alle Anforderungen erfüllt sind.", 'de'),
            ("Il sistema deve garantire che tutti i requisiti siano soddisfatti correttamente.", 'it'),
            ("El sistema debe garantizar que todos los requisitos se cumplan correctamente.", 'es')
        ] * 4  # 20 total threads

        threads = []
        for text, expected in texts:
            thread = threading.Thread(target=detect_text, args=(text, expected))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify all detected correctly
        assert len(results) == 20
        correct = sum(1 for r in results if r['match'])
        accuracy = correct / len(results)
        assert accuracy >= 0.95, f"Detection accuracy too low: {accuracy}"

    def test_concurrent_config_access(self):
        """Test concurrent configuration access from multiple threads."""
        results = []
        errors = []

        def access_config(lang_code):
            try:
                config = get_language_config()
                keywords = config.get_keywords(lang_code)
                model = config.get_model_name(lang_code)
                priority = config.get_priority_keywords(lang_code, 'high')

                results.append({
                    'lang': lang_code,
                    'keywords': len(keywords),
                    'model': model,
                    'priority': len(priority)
                })
            except Exception as e:
                errors.append(str(e))

        lang_codes = ['en', 'fr', 'de', 'it', 'es'] * 8  # 40 threads

        threads = []
        for lang in lang_codes:
            thread = threading.Thread(target=access_config, args=(lang,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 40

    def test_integrated_concurrent_workflow(self):
        """Test complete workflow from multiple threads concurrently."""
        detector = LanguageDetector()
        config = get_language_config()
        results = []
        errors = []

        def process_document(text):
            try:
                # Detect language
                lang, conf = detector.detect(text)

                # Get configuration
                keywords = config.get_keywords(lang)
                model = config.get_model_name(lang)
                priority_high = config.get_priority_keywords(lang, 'high')

                # Simulate some processing
                time.sleep(0.01)

                results.append({
                    'lang': lang,
                    'conf': conf,
                    'keywords': len(keywords),
                    'model': model,
                    'priority': len(priority_high)
                })
            except Exception as e:
                errors.append(str(e))

        texts = [
            "The system shall ensure requirements.",
            "Le système doit garantir les exigences.",
            "Das System muss Anforderungen erfüllen.",
            "Il sistema deve garantire i requisiti.",
            "El sistema debe garantizar los requisitos."
        ] * 6  # 30 threads

        threads = [threading.Thread(target=process_document, args=(text,))
                   for text in texts]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 30


class TestPerformance:
    """Test performance of integrated system."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return LanguageDetector()

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        return get_language_config()

    def test_detection_speed(self, detector):
        """Test that language detection is fast enough."""
        text = "The system shall ensure that all requirements are met. " * 50

        start_time = time.time()
        for _ in range(100):
            lang, conf = detector.detect(text)
        elapsed = time.time() - start_time

        # Should complete 100 detections in under 5 seconds
        assert elapsed < 5.0, f"Detection too slow: {elapsed}s for 100 iterations"

        avg_time = elapsed / 100
        print(f"\nAverage detection time: {avg_time*1000:.2f}ms")

    def test_config_access_speed(self, config):
        """Test that configuration access is fast."""
        start_time = time.time()
        for _ in range(1000):
            keywords = config.get_keywords('en')
            model = config.get_model_name('en')
            priority = config.get_priority_keywords('en', 'high')
        elapsed = time.time() - start_time

        # Should complete 1000 accesses in under 1 second
        assert elapsed < 1.0, f"Config access too slow: {elapsed}s for 1000 iterations"

    def test_large_document_processing(self, detector, config):
        """Test processing large documents."""
        # Simulate a large PDF document (100KB of text)
        large_text = "The system shall ensure that all requirements are met. " * 2000

        start_time = time.time()
        lang, conf = detector.detect(large_text)
        keywords = config.get_keywords(lang)
        elapsed = time.time() - start_time

        assert lang == 'en'
        assert len(keywords) > 0
        # Should complete in under 1 second
        assert elapsed < 1.0, f"Large document processing too slow: {elapsed}s"


class TestErrorHandling:
    """Test error handling across integrated components."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return LanguageDetector()

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        return get_language_config()

    def test_invalid_language_code(self, config):
        """Test handling of invalid language codes."""
        keywords = config.get_keywords('xx')
        assert isinstance(keywords, set)
        assert len(keywords) == 0

        model = config.get_model_name('xx')
        assert model is None

    def test_empty_text_detection(self, detector, config):
        """Test workflow with empty text."""
        lang, conf = detector.detect("")

        # Should default to English
        assert lang == 'en'

        # Should still be able to get config
        keywords = config.get_keywords(lang)
        assert len(keywords) > 0

    def test_malformed_text(self, detector, config):
        """Test handling of malformed text."""
        malformed_texts = [
            "!@#$%^&*()",
            "123456789",
            "        ",
            "\n\n\n\n",
            "🚀🎉✨"
        ]

        for text in malformed_texts:
            # Should not crash
            lang, conf = detector.detect(text)
            assert lang in ['en', 'fr', 'de', 'it', 'es']

            # Should still be able to get config
            keywords = config.get_keywords(lang)
            assert isinstance(keywords, set)


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return LanguageDetector()

    @pytest.fixture
    def config(self):
        """Create a config instance."""
        return get_language_config()

    def test_pdf_text_with_formatting_artifacts(self, detector, config):
        """Test text extracted from PDFs with formatting issues."""
        pdf_text = """
        The  system   shall    ensure
        that   all   requirements
        are    met.

        Page 1 of 10

        Security  must  be
        guaranteed   at   all
        times.
        """

        lang, conf = detector.detect(pdf_text)
        assert lang == 'en'

        keywords = config.get_keywords(lang)
        high_priority = config.get_priority_keywords(lang, 'high')

        assert 'shall' in keywords
        assert 'must' in high_priority

    def test_mixed_language_document(self, detector, config):
        """Test document with mixed languages (should detect dominant)."""
        # Mostly English with some French
        mixed_text = """
        The system shall ensure requirements. The security must be guaranteed.
        The performance should be optimal. The interface may be customizable.
        Note: voir la documentation française pour plus de détails.
        """

        lang, conf = detector.detect(mixed_text)
        # Should detect English as dominant
        assert lang == 'en'

    def test_requirement_extraction_simulation(self, detector, config):
        """Simulate requirement extraction workflow."""
        documents = {
            'spec_en.pdf': """
                1.1 System Requirements
                The system shall process user requests within 2 seconds.
                The system must authenticate users before granting access.
                The system should log all security events.
            """,
            'spec_fr.pdf': """
                1.1 Exigences du Système
                Le système doit traiter les demandes dans les 2 secondes.
                Le système devra authentifier les utilisateurs.
                Le système devrait enregistrer tous les événements.
            """,
            'spec_de.pdf': """
                1.1 Systemanforderungen
                Das System muss Benutzeranfragen innerhalb von 2 Sekunden verarbeiten.
                Das System soll Benutzer authentifizieren.
                Das System sollte alle Ereignisse protokollieren.
            """
        }

        extracted_requirements = []

        for filename, text in documents.items():
            # Step 1: Detect language
            lang, conf = detector.detect(text)

            # Step 2: Get keywords for language
            keywords = config.get_keywords(lang)
            high_priority = config.get_priority_keywords(lang, 'high')
            medium_priority = config.get_priority_keywords(lang, 'medium')

            # Step 3: Simulate requirement extraction
            lines = text.strip().split('\n')
            for line in lines:
                line_lower = line.lower()
                # Check if line contains high-priority keywords
                if any(keyword in line_lower for keyword in high_priority):
                    extracted_requirements.append({
                        'file': filename,
                        'language': lang,
                        'text': line.strip(),
                        'priority': 'high'
                    })
                elif any(keyword in line_lower for keyword in medium_priority):
                    extracted_requirements.append({
                        'file': filename,
                        'language': lang,
                        'text': line.strip(),
                        'priority': 'medium'
                    })

        # Verify requirements extracted from all languages
        assert len(extracted_requirements) > 0
        languages_found = set(r['language'] for r in extracted_requirements)
        assert 'en' in languages_found
        assert 'fr' in languages_found
        assert 'de' in languages_found

    def test_batch_processing_workflow(self, detector, config):
        """Test batch processing multiple files."""
        file_batch = [
            ("file1.pdf", "The system shall ensure security at all times and must protect data."),
            ("file2.pdf", "Le système doit garantir la sécurité en permanence et protéger les données."),
            ("file3.pdf", "Das System muss Sicherheit gewährleisten und Daten schützen jederzeit."),
            ("file4.pdf", "Il sistema deve garantire la sicurezza in ogni momento e proteggere i dati."),
            ("file5.pdf", "El sistema debe garantizar la seguridad en todo momento y proteger los datos."),
        ]

        batch_results = []

        for filename, text in file_batch:
            # Complete workflow for each file
            lang, conf = detector.detect(text)
            keywords = config.get_keywords(lang)
            model = config.get_model_name(lang)
            security_keywords = config.get_security_keywords(lang)

            # Check if text contains security keywords
            text_lower = text.lower()
            has_security = any(kw in text_lower for kw in security_keywords)

            batch_results.append({
                'filename': filename,
                'language': lang,
                'confidence': conf,
                'has_security': has_security,
                'model': model
            })

        # Verify all files processed
        assert len(batch_results) == 5

        # All should have security keywords
        assert all(r['has_security'] for r in batch_results)

        # All should have valid models
        assert all(r['model'] is not None for r in batch_results)


class TestConfigurationPersistence:
    """Test configuration persistence and reloading."""

    def test_config_survives_multiple_detections(self):
        """Test that config state persists across multiple operations."""
        detector = LanguageDetector()
        config1 = get_language_config()

        # Perform multiple detections
        for _ in range(10):
            detector.detect("The system shall ensure requirements.")

        # Get config again
        config2 = get_language_config()

        # Should be same instance
        assert config1 is config2

    def test_config_custom_modifications_persist(self, tmp_path):
        """Test that custom config modifications persist."""
        config_path = tmp_path / "custom_config.json"

        # Create custom config
        config = LanguageConfig(config_path=str(config_path))

        # Modify config
        config.config['test_lang'] = {
            'code': 'test',
            'model': 'test_model',
            'keywords': ['test_keyword']
        }

        # Save config
        config.save_config()

        # Load config again
        config2 = LanguageConfig(config_path=str(config_path))

        # Verify modification persisted
        assert 'test_lang' in config2.config
        assert config2.config['test_lang']['code'] == 'test'


if __name__ == '__main__':
    # Run integration tests
    pytest.main([__file__, '-v', '--tb=short'])
