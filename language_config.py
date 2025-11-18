"""
Language Configuration Management for Multi-lingual Requirement Extraction

This module manages language-specific configurations including:
- spaCy model mappings
- Requirement keywords per language
- Modal verb patterns
- Priority keyword mappings
- Category indicators

Configuration is stored in JSON format for easy modification without code changes.

Author: ReqBot Development Team
Version: 3.0.0
Date: 2025-11-18
"""

import json
import logging
import os
import threading
from typing import Dict, List, Set, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LanguageConfig:
    """
    Manages language-specific configurations for requirement extraction.

    This class provides access to:
    - spaCy model names per language
    - Requirement keywords (modal verbs)
    - Priority level mappings
    - Category indicators
    - Language-specific patterns

    Configuration can be loaded from JSON or use built-in defaults.
    """

    # Default configuration (used if config file not found)
    DEFAULT_CONFIG = {
        "english": {
            "code": "en",
            "model": "en_core_web_sm",
            "keywords": [
                "shall", "must", "should", "may", "will", "can",
                "has to", "have to", "need to", "ensure", "ensures",
                "ensuring", "scope", "recommended", "required"
            ],
            "modal_verbs": {
                "obligation": ["shall", "must", "has to", "have to", "need to", "required"],
                "recommendation": ["should", "ought to", "recommended"],
                "permission": ["may", "can", "could", "might"],
                "future": ["will", "shall"]
            },
            "priority_high": ["shall", "must", "has to", "have to", "required"],
            "priority_medium": ["should", "ought to", "need to", "recommended"],
            "priority_low": ["may", "can", "could", "might"],
            "security_keywords": ["security", "secure", "protection", "authentication",
                                 "authorization", "encryption", "confidentiality"],
            "categories": {
                "functional": ["function", "capability", "feature", "operation"],
                "performance": ["performance", "speed", "throughput", "latency", "response"],
                "safety": ["safety", "hazard", "risk", "fail-safe", "failure"],
                "security": ["security", "secure", "authentication", "authorization"],
                "interface": ["interface", "API", "connection", "integration"],
                "data": ["data", "database", "storage", "persistence"],
                "compliance": ["compliance", "standard", "regulation", "conform"]
            }
        },
        "french": {
            "code": "fr",
            "model": "fr_core_news_sm",
            "keywords": [
                "doit", "devra", "devrait", "peut", "pourra", "pourrait",
                "faut", "exigence", "exiger", "garantir", "assurer",
                "recommandé", "requis", "nécessaire"
            ],
            "modal_verbs": {
                "obligation": ["doit", "devra", "faut", "requis", "nécessaire"],
                "recommendation": ["devrait", "recommandé"],
                "permission": ["peut", "pourra", "pourrait"],
                "future": ["devra", "pourra"]
            },
            "priority_high": ["doit", "devra", "faut", "requis", "nécessaire"],
            "priority_medium": ["devrait", "recommandé"],
            "priority_low": ["peut", "pourra", "pourrait"],
            "security_keywords": ["sécurité", "sûreté", "protection", "authentification",
                                 "autorisation", "chiffrement", "confidentialité"],
            "categories": {
                "functional": ["fonction", "fonctionnalité", "caractéristique", "opération"],
                "performance": ["performance", "vitesse", "débit", "latence", "réponse"],
                "safety": ["sécurité", "sûreté", "risque", "défaillance"],
                "security": ["sécurité", "authentification", "autorisation"],
                "interface": ["interface", "API", "connexion", "intégration"],
                "data": ["données", "base de données", "stockage"],
                "compliance": ["conformité", "norme", "réglementation"]
            }
        },
        "german": {
            "code": "de",
            "model": "de_core_news_sm",
            "keywords": [
                "muss", "soll", "sollte", "kann", "könnte", "darf",
                "wird", "anforderung", "sicherstellen", "gewährleisten",
                "empfohlen", "erforderlich", "notwendig"
            ],
            "modal_verbs": {
                "obligation": ["muss", "muss...sein", "erforderlich", "notwendig"],
                "recommendation": ["soll", "sollte", "empfohlen"],
                "permission": ["kann", "könnte", "darf", "dürfte"],
                "future": ["wird"]
            },
            "priority_high": ["muss", "erforderlich", "notwendig"],
            "priority_medium": ["soll", "sollte", "empfohlen"],
            "priority_low": ["kann", "könnte", "darf"],
            "security_keywords": ["sicherheit", "schutz", "authentifizierung",
                                 "autorisierung", "verschlüsselung", "vertraulichkeit"],
            "categories": {
                "functional": ["funktion", "funktionalität", "merkmal", "betrieb"],
                "performance": ["leistung", "geschwindigkeit", "durchsatz", "latenz"],
                "safety": ["sicherheit", "gefahr", "risiko", "ausfallsicherheit"],
                "security": ["sicherheit", "authentifizierung", "autorisierung"],
                "interface": ["schnittstelle", "API", "verbindung", "integration"],
                "data": ["daten", "datenbank", "speicherung"],
                "compliance": ["konformität", "standard", "vorschrift"]
            }
        },
        "italian": {
            "code": "it",
            "model": "it_core_news_sm",
            "keywords": [
                "deve", "dovrà", "dovrebbe", "può", "potrebbe", "potrà",
                "requisito", "garantire", "assicurare", "raccomandato",
                "richiesto", "necessario"
            ],
            "modal_verbs": {
                "obligation": ["deve", "dovrà", "richiesto", "necessario"],
                "recommendation": ["dovrebbe", "raccomandato"],
                "permission": ["può", "potrebbe", "potrà"],
                "future": ["dovrà", "potrà"]
            },
            "priority_high": ["deve", "dovrà", "richiesto", "necessario"],
            "priority_medium": ["dovrebbe", "raccomandato"],
            "priority_low": ["può", "potrebbe", "potrà"],
            "security_keywords": ["sicurezza", "protezione", "autenticazione",
                                 "autorizzazione", "crittografia", "riservatezza"],
            "categories": {
                "functional": ["funzione", "funzionalità", "caratteristica", "operazione"],
                "performance": ["prestazione", "velocità", "throughput", "latenza"],
                "safety": ["sicurezza", "pericolo", "rischio", "fail-safe"],
                "security": ["sicurezza", "autenticazione", "autorizzazione"],
                "interface": ["interfaccia", "API", "connessione", "integrazione"],
                "data": ["dati", "database", "archiviazione"],
                "compliance": ["conformità", "standard", "regolamento"]
            }
        },
        "spanish": {
            "code": "es",
            "model": "es_core_news_sm",
            "keywords": [
                "debe", "deberá", "debería", "puede", "podría", "podrá",
                "requisito", "garantizar", "asegurar", "recomendado",
                "requerido", "necesario"
            ],
            "modal_verbs": {
                "obligation": ["debe", "deberá", "requerido", "necesario"],
                "recommendation": ["debería", "recomendado"],
                "permission": ["puede", "podría", "podrá"],
                "future": ["deberá", "podrá"]
            },
            "priority_high": ["debe", "deberá", "requerido", "necesario"],
            "priority_medium": ["debería", "recomendado"],
            "priority_low": ["puede", "podría", "podrá"],
            "security_keywords": ["seguridad", "protección", "autenticación",
                                 "autorización", "cifrado", "confidencialidad"],
            "categories": {
                "functional": ["función", "funcionalidad", "característica", "operación"],
                "performance": ["rendimiento", "velocidad", "throughput", "latencia"],
                "safety": ["seguridad", "peligro", "riesgo", "fail-safe"],
                "security": ["seguridad", "autenticación", "autorización"],
                "interface": ["interfaz", "API", "conexión", "integración"],
                "data": ["datos", "base de datos", "almacenamiento"],
                "compliance": ["cumplimiento", "estándar", "regulación"]
            }
        }
    }

    CONFIG_FILE = "language_keywords.json"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize language configuration.

        Args:
            config_path: Path to JSON configuration file (optional)
        """
        self.config_path = config_path or self.CONFIG_FILE
        self.config = self._load_config()
        logger.info(f"LanguageConfig initialized with {len(self.config)} languages")

    def _load_config(self) -> Dict:
        """Load configuration from file or use defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Loaded language config from {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading config file: {e}, using defaults")
                return self.DEFAULT_CONFIG
        else:
            logger.info("Config file not found, using default configuration")
            # Create default config file
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG

    def save_config(self, config: Optional[Dict] = None):
        """
        Save configuration to JSON file.

        Args:
            config: Configuration dict (uses current config if None)
        """
        config_to_save = config or self.config

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def get_language_config(self, lang_code: str) -> Optional[Dict]:
        """
        Get configuration for a specific language.

        Args:
            lang_code: ISO 639-1 language code (e.g., 'fr', 'de')

        Returns:
            Language configuration dict or None if not found
        """
        # Try direct code lookup
        for lang_name, lang_config in self.config.items():
            if lang_config.get('code') == lang_code:
                return lang_config

        # Try language name lookup (case-insensitive)
        lang_name = lang_code.lower()
        return self.config.get(lang_name)

    def get_model_name(self, lang_code: str) -> Optional[str]:
        """Get spaCy model name for language."""
        lang_config = self.get_language_config(lang_code)
        return lang_config.get('model') if lang_config else None

    def get_keywords(self, lang_code: str) -> Set[str]:
        """Get requirement keywords for language."""
        lang_config = self.get_language_config(lang_code)
        if lang_config:
            return set(lang_config.get('keywords', []))
        return set()

    def get_priority_keywords(self, lang_code: str, priority_level: str) -> Set[str]:
        """
        Get keywords for specific priority level.

        Args:
            lang_code: Language code
            priority_level: 'high', 'medium', or 'low'

        Returns:
            Set of keywords for that priority level
        """
        lang_config = self.get_language_config(lang_code)
        if lang_config:
            key = f'priority_{priority_level}'
            return set(lang_config.get(key, []))
        return set()

    def get_security_keywords(self, lang_code: str) -> Set[str]:
        """Get security-related keywords for language."""
        lang_config = self.get_language_config(lang_code)
        if lang_config:
            return set(lang_config.get('security_keywords', []))
        return set()

    def get_category_keywords(self, lang_code: str, category: str) -> Set[str]:
        """Get keywords for specific category."""
        lang_config = self.get_language_config(lang_code)
        if lang_config:
            categories = lang_config.get('categories', {})
            return set(categories.get(category, []))
        return set()

    def get_all_categories(self, lang_code: str) -> Dict[str, Set[str]]:
        """Get all category keyword mappings for language."""
        lang_config = self.get_language_config(lang_code)
        if lang_config:
            categories = lang_config.get('categories', {})
            return {cat: set(keywords) for cat, keywords in categories.items()}
        return {}

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return [cfg.get('code') for cfg in self.config.values() if 'code' in cfg]

    def is_language_supported(self, lang_code: str) -> bool:
        """Check if language is supported."""
        return lang_code in self.get_supported_languages()


# Singleton instance for global access
_config_instance: Optional[LanguageConfig] = None
_config_lock = threading.Lock()


def get_language_config() -> LanguageConfig:
    """
    Get singleton instance of LanguageConfig (thread-safe).

    Uses double-check locking pattern to ensure thread safety
    while minimizing lock overhead.

    Returns:
        LanguageConfig instance
    """
    global _config_instance
    if _config_instance is None:
        with _config_lock:
            # Double-check: another thread might have created instance
            if _config_instance is None:
                _config_instance = LanguageConfig()
    return _config_instance


if __name__ == '__main__':
    # Test the language configuration
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Language Configuration Test")
    print("=" * 60)

    config = LanguageConfig()

    print(f"\nSupported languages: {', '.join(config.get_supported_languages())}")

    for lang_code in config.get_supported_languages():
        print(f"\n{lang_code.upper()}:")
        print(f"  Model: {config.get_model_name(lang_code)}")
        print(f"  Keywords: {len(config.get_keywords(lang_code))} total")
        print(f"  High priority keywords: {config.get_priority_keywords(lang_code, 'high')}")
        print(f"  Security keywords: {len(config.get_security_keywords(lang_code))}")
        print(f"  Categories: {', '.join(config.get_all_categories(lang_code).keys())}")

    print("\n" + "=" * 60)
    print("Configuration saved to:", config.config_path)
    print("=" * 60)
