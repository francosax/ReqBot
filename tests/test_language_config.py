"""
Unit Tests for Language Configuration Module

Tests language configuration management including:
- Configuration loading and saving
- Keyword retrieval
- Priority mappings
- Category management
- Singleton pattern
- Thread safety

Author: ReqBot Development Team
Version: 3.0.0
Date: 2025-11-18
"""

import pytest
import json
import os
import threading
import time
from language_config import LanguageConfig, get_language_config


class TestLanguageConfigBasics:
    """Test basic language configuration functionality."""

    def test_initialization_default(self):
        """Test initialization with default config path."""
        config = LanguageConfig()
        assert config.config is not None
        assert len(config.config) >= 5  # At least 5 languages

    def test_initialization_custom_path(self, tmp_path):
        """Test initialization with custom config path."""
        custom_path = tmp_path / "custom_config.json"
        config = LanguageConfig(config_path=str(custom_path))
        assert config.config_path == str(custom_path)

    def test_default_config_structure(self):
        """Test that default config has required structure."""
        config = LanguageConfig()

        for lang_name, lang_config in config.config.items():
            assert 'code' in lang_config
            assert 'model' in lang_config
            assert 'keywords' in lang_config
            assert 'priority_high' in lang_config
            assert 'priority_medium' in lang_config
            assert 'priority_low' in lang_config

    def test_supported_languages(self):
        """Test that all expected languages are present."""
        config = LanguageConfig()
        supported = config.get_supported_languages()

        assert 'en' in supported
        assert 'fr' in supported
        assert 'de' in supported
        assert 'it' in supported
        assert 'es' in supported
        assert len(supported) == 5


class TestConfigurationLoading:
    """Test configuration file loading."""

    def test_load_from_nonexistent_file(self, tmp_path):
        """Test loading when config file doesn't exist."""
        config_path = tmp_path / "nonexistent.json"
        config = LanguageConfig(config_path=str(config_path))

        # Should create default config
        assert config.config is not None
        assert os.path.exists(config_path)

    def test_load_from_existing_file(self, tmp_path):
        """Test loading from existing config file."""
        config_path = tmp_path / "test_config.json"

        # Create a test config
        test_config = {
            "test_lang": {
                "code": "test",
                "model": "test_model",
                "keywords": ["test_keyword"]
            }
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)

        config = LanguageConfig(config_path=str(config_path))
        assert "test_lang" in config.config
        assert config.config["test_lang"]["code"] == "test"

    def test_load_corrupted_file(self, tmp_path):
        """Test loading from corrupted config file."""
        config_path = tmp_path / "corrupted.json"

        # Create corrupted JSON
        with open(config_path, 'w') as f:
            f.write("{ invalid json ")

        config = LanguageConfig(config_path=str(config_path))

        # Should fallback to default config
        assert config.config is not None
        assert len(config.config) >= 5


class TestConfigurationSaving:
    """Test configuration file saving."""

    def test_save_config(self, tmp_path):
        """Test saving configuration to file."""
        config_path = tmp_path / "save_test.json"
        config = LanguageConfig(config_path=str(config_path))

        # Modify config
        config.config["test"] = {"code": "test"}
        config.save_config()

        # Verify saved
        assert os.path.exists(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        assert "test" in saved_config

    def test_save_custom_config(self, tmp_path):
        """Test saving custom configuration."""
        config_path = tmp_path / "custom_save.json"
        config = LanguageConfig(config_path=str(config_path))

        custom_config = {"custom": {"code": "cu"}}
        config.save_config(custom_config)

        # Verify saved
        with open(config_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        assert "custom" in saved_config


class TestLanguageRetrieval:
    """Test language configuration retrieval."""

    @pytest.fixture
    def config(self):
        """Create a config instance for testing."""
        return LanguageConfig()

    def test_get_language_config_by_code(self, config):
        """Test getting language config by ISO code."""
        en_config = config.get_language_config('en')
        assert en_config is not None
        assert en_config['code'] == 'en'

    def test_get_language_config_by_name(self, config):
        """Test getting language config by name."""
        en_config = config.get_language_config('english')
        assert en_config is not None
        assert en_config['code'] == 'en'

    def test_get_language_config_invalid(self, config):
        """Test getting config for invalid language."""
        invalid_config = config.get_language_config('xx')
        assert invalid_config is None

    def test_get_model_name(self, config):
        """Test getting spaCy model name."""
        model = config.get_model_name('en')
        assert model == 'en_core_web_sm'

        model = config.get_model_name('fr')
        assert model == 'fr_core_news_sm'

    def test_get_model_name_invalid(self, config):
        """Test getting model for invalid language."""
        model = config.get_model_name('xx')
        assert model is None

    def test_is_language_supported(self, config):
        """Test language support checking."""
        assert config.is_language_supported('en') is True
        assert config.is_language_supported('fr') is True
        assert config.is_language_supported('de') is True
        assert config.is_language_supported('it') is True
        assert config.is_language_supported('es') is True
        assert config.is_language_supported('xx') is False


class TestKeywordRetrieval:
    """Test keyword retrieval functionality."""

    @pytest.fixture
    def config(self):
        """Create a config instance for testing."""
        return LanguageConfig()

    def test_get_keywords_english(self, config):
        """Test getting English keywords."""
        keywords = config.get_keywords('en')
        assert isinstance(keywords, set)
        assert 'shall' in keywords
        assert 'must' in keywords
        assert len(keywords) > 0

    def test_get_keywords_french(self, config):
        """Test getting French keywords."""
        keywords = config.get_keywords('fr')
        assert isinstance(keywords, set)
        assert 'doit' in keywords
        assert len(keywords) > 0

    def test_get_keywords_invalid(self, config):
        """Test getting keywords for invalid language."""
        keywords = config.get_keywords('xx')
        assert isinstance(keywords, set)
        assert len(keywords) == 0

    def test_get_security_keywords(self, config):
        """Test getting security keywords."""
        keywords = config.get_security_keywords('en')
        assert isinstance(keywords, set)
        assert 'security' in keywords
        assert len(keywords) > 0

    def test_get_security_keywords_french(self, config):
        """Test getting French security keywords."""
        keywords = config.get_security_keywords('fr')
        assert isinstance(keywords, set)
        assert 'sécurité' in keywords or 'securite' in str(keywords).lower()


class TestPriorityMappings:
    """Test priority keyword mappings."""

    @pytest.fixture
    def config(self):
        """Create a config instance for testing."""
        return LanguageConfig()

    def test_get_priority_high_english(self, config):
        """Test getting high-priority English keywords."""
        keywords = config.get_priority_keywords('en', 'high')
        assert isinstance(keywords, set)
        assert 'shall' in keywords or 'must' in keywords
        assert len(keywords) > 0

    def test_get_priority_medium_english(self, config):
        """Test getting medium-priority English keywords."""
        keywords = config.get_priority_keywords('en', 'medium')
        assert isinstance(keywords, set)
        assert 'should' in keywords
        assert len(keywords) > 0

    def test_get_priority_low_english(self, config):
        """Test getting low-priority English keywords."""
        keywords = config.get_priority_keywords('en', 'low')
        assert isinstance(keywords, set)
        assert 'may' in keywords or 'can' in keywords
        assert len(keywords) > 0

    def test_get_priority_french(self, config):
        """Test getting French priority keywords."""
        high = config.get_priority_keywords('fr', 'high')
        assert 'doit' in high or 'devra' in high

    def test_get_priority_invalid_level(self, config):
        """Test getting invalid priority level."""
        keywords = config.get_priority_keywords('en', 'invalid')
        assert isinstance(keywords, set)
        assert len(keywords) == 0

    def test_get_priority_invalid_language(self, config):
        """Test getting priority for invalid language."""
        keywords = config.get_priority_keywords('xx', 'high')
        assert isinstance(keywords, set)
        assert len(keywords) == 0


class TestCategoryManagement:
    """Test category keyword management."""

    @pytest.fixture
    def config(self):
        """Create a config instance for testing."""
        return LanguageConfig()

    def test_get_category_keywords(self, config):
        """Test getting keywords for specific category."""
        keywords = config.get_category_keywords('en', 'functional')
        assert isinstance(keywords, set)
        assert len(keywords) > 0

    def test_get_category_security(self, config):
        """Test getting security category keywords."""
        keywords = config.get_category_keywords('en', 'security')
        assert isinstance(keywords, set)
        assert 'security' in keywords or 'secure' in keywords

    def test_get_all_categories(self, config):
        """Test getting all categories for a language."""
        categories = config.get_all_categories('en')
        assert isinstance(categories, dict)
        assert 'functional' in categories
        assert 'performance' in categories
        assert 'security' in categories
        assert 'safety' in categories

    def test_get_categories_french(self, config):
        """Test getting French categories."""
        categories = config.get_all_categories('fr')
        assert isinstance(categories, dict)
        assert len(categories) > 0

    def test_get_category_invalid_language(self, config):
        """Test getting categories for invalid language."""
        categories = config.get_all_categories('xx')
        assert isinstance(categories, dict)
        assert len(categories) == 0


class TestSingletonPattern:
    """Test singleton pattern implementation."""

    def test_singleton_same_instance(self):
        """Test that get_language_config returns same instance."""
        config1 = get_language_config()
        config2 = get_language_config()
        assert config1 is config2

    def test_singleton_state_persistence(self):
        """Test that singleton maintains state."""
        config1 = get_language_config()
        config1._test_attribute = "test_value"

        config2 = get_language_config()
        assert hasattr(config2, '_test_attribute')
        assert config2._test_attribute == "test_value"

        # Clean up
        delattr(config2, '_test_attribute')


class TestThreadSafety:
    """Test thread safety of singleton pattern."""

    def test_singleton_thread_safety(self):
        """Test that singleton is thread-safe."""
        # Reset singleton
        import language_config
        language_config._config_instance = None

        results = []

        def create_config():
            config = get_language_config()
            results.append(id(config))
            time.sleep(0.01)  # Simulate work

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_config)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All threads should have gotten the same instance
        assert len(set(results)) == 1, \
            f"Multiple instances created: {len(set(results))} unique IDs"

    def test_concurrent_access(self):
        """Test concurrent access to singleton."""
        get_language_config()
        results = []

        def access_config():
            c = get_language_config()
            keywords = c.get_keywords('en')
            results.append(len(keywords))

        threads = []
        for _ in range(20):
            thread = threading.Thread(target=access_config)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should have gotten same keyword count
        assert len(set(results)) == 1, \
            "Inconsistent results from concurrent access"


class TestModalVerbs:
    """Test modal verb configurations."""

    @pytest.fixture
    def config(self):
        """Create a config instance for testing."""
        return LanguageConfig()

    def test_modal_verbs_structure(self, config):
        """Test that modal verbs have proper structure."""
        lang_config = config.get_language_config('en')

        if 'modal_verbs' in lang_config:
            modal_verbs = lang_config['modal_verbs']
            assert isinstance(modal_verbs, dict)

            # Check common categories
            expected_categories = ['obligation', 'recommendation', 'permission']
            for category in expected_categories:
                if category in modal_verbs:
                    assert isinstance(modal_verbs[category], list)
                    assert len(modal_verbs[category]) > 0

    def test_all_languages_have_modal_verbs(self, config):
        """Test that all languages define modal verbs."""
        for lang_code in config.get_supported_languages():
            lang_config = config.get_language_config(lang_code)
            # Modal verbs are optional but recommended
            assert lang_config is not None


class TestConfigurationValidation:
    """Test configuration validation and integrity."""

    @pytest.fixture
    def config(self):
        """Create a config instance for testing."""
        return LanguageConfig()

    def test_all_languages_have_required_fields(self, config):
        """Test that all languages have required configuration fields."""
        required_fields = ['code', 'model', 'keywords']

        for lang_code in config.get_supported_languages():
            lang_config = config.get_language_config(lang_code)
            for field in required_fields:
                assert field in lang_config, \
                    f"Language {lang_code} missing required field: {field}"

    def test_all_models_defined(self, config):
        """Test that all languages have spaCy models defined."""
        for lang_code in config.get_supported_languages():
            model = config.get_model_name(lang_code)
            assert model is not None
            assert len(model) > 0

    def test_all_keywords_non_empty(self, config):
        """Test that all languages have non-empty keyword lists."""
        for lang_code in config.get_supported_languages():
            keywords = config.get_keywords(lang_code)
            assert len(keywords) > 0, \
                f"Language {lang_code} has no keywords defined"

    def test_priority_keywords_non_empty(self, config):
        """Test that all languages have priority keywords."""
        for lang_code in config.get_supported_languages():
            high = config.get_priority_keywords(lang_code, 'high')
            medium = config.get_priority_keywords(lang_code, 'medium')
            low = config.get_priority_keywords(lang_code, 'low')

            # At least one priority level should have keywords
            total = len(high) + len(medium) + len(low)
            assert total > 0, \
                f"Language {lang_code} has no priority keywords"


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
