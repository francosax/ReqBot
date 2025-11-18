"""
Keyword Profiles Manager for ReqBot

Manages predefined and custom keyword sets for different industries and domains.
Allows users to quickly switch between keyword profiles optimized for different
types of requirements documents (aerospace, medical, automotive, software, etc.).

Features:
- Predefined industry profiles
- Custom profile creation and management
- Profile import/export (JSON)
- Profile persistence
"""

import json
import os
import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Configuration file location
PROFILES_CONFIG_FILE = "keyword_profiles.json"

# Default predefined profiles
DEFAULT_PROFILES = {
    "Generic": {
        "keywords": ["shall", "must", "should", "has to", "will", "ensures", "requires", "needs to"],
        "description": "General purpose requirements keywords suitable for most domains",
        "is_custom": False
    },
    "Aerospace": {
        "keywords": ["shall", "must", "will", "requires", "mandatory", "critical", "essential", "provisions"],
        "description": "Keywords optimized for aerospace and defense requirements (DO-178C, MIL-STD)",
        "is_custom": False
    },
    "Medical": {
        "keywords": ["shall", "must", "should", "mandatory", "essential", "required", "intended", "ensures"],
        "description": "Keywords for medical device requirements (FDA, IEC 62304)",
        "is_custom": False
    },
    "Automotive": {
        "keywords": ["shall", "must", "should", "requires", "mandatory", "safety-critical", "functional"],
        "description": "Keywords for automotive requirements (ISO 26262, ASPICE)",
        "is_custom": False
    },
    "Software": {
        "keywords": ["shall", "must", "should", "will", "needs to", "requires", "supports", "provides"],
        "description": "Keywords for software requirements specifications",
        "is_custom": False
    },
    "Safety": {
        "keywords": ["shall", "must", "mandatory", "critical", "safety", "hazard", "fail-safe", "prevents"],
        "description": "Keywords focused on safety-critical requirements",
        "is_custom": False
    }
}


@dataclass
class KeywordProfile:
    """Represents a keyword profile."""
    name: str
    keywords: List[str]
    description: str
    is_custom: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'keywords': self.keywords,
            'description': self.description,
            'is_custom': self.is_custom
        }

    @classmethod
    def from_dict(cls, name: str, data: Dict) -> 'KeywordProfile':
        """Create from dictionary."""
        return cls(
            name=name,
            keywords=data.get('keywords', []),
            description=data.get('description', ''),
            is_custom=data.get('is_custom', True)
        )


class KeywordProfilesManager:
    """
    Manages keyword profiles for requirement extraction.
    """

    def __init__(self, config_file: str = PROFILES_CONFIG_FILE):
        """
        Initialize the KeywordProfilesManager.

        Args:
            config_file: Path to JSON configuration file
        """
        self.config_file = config_file
        self.profiles: Dict[str, KeywordProfile] = {}
        self._load()

    def _load(self) -> None:
        """Load profiles from configuration file."""
        # Start with default profiles
        for name, data in DEFAULT_PROFILES.items():
            self.profiles[name] = KeywordProfile.from_dict(name, data)

        # Load custom profiles from file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    for name, data in loaded_data.items():
                        # Override defaults or add custom profiles
                        if data.get('is_custom', True):  # Only load custom profiles
                            self.profiles[name] = KeywordProfile.from_dict(name, data)
                logger.info(f"Loaded keyword profiles from {self.config_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse keyword profiles config: {e}")
            except Exception as e:
                logger.error(f"Error loading keyword profiles: {e}")
        else:
            logger.info(f"No custom profiles file found, using defaults only")

    def _save(self) -> bool:
        """
        Save custom profiles to configuration file.

        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            # Only save custom profiles
            custom_profiles = {
                name: profile.to_dict()
                for name, profile in self.profiles.items()
                if profile.is_custom
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(custom_profiles, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved keyword profiles to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save keyword profiles: {e}")
            return False

    def get_profile(self, name: str) -> Optional[KeywordProfile]:
        """
        Get a profile by name.

        Args:
            name: Profile name

        Returns:
            KeywordProfile if found, None otherwise
        """
        return self.profiles.get(name)

    def get_profile_names(self) -> List[str]:
        """
        Get list of all profile names.

        Returns:
            List of profile names sorted alphabetically
        """
        return sorted(self.profiles.keys())

    def get_keywords(self, profile_name: str) -> Set[str]:
        """
        Get keywords for a specific profile as a set.

        Args:
            profile_name: Name of the profile

        Returns:
            Set of keywords, empty set if profile not found
        """
        profile = self.get_profile(profile_name)
        if profile:
            return set(profile.keywords)
        return set()

    def add_profile(self, name: str, keywords: List[str], description: str = "") -> bool:
        """
        Add a new custom profile.

        Args:
            name: Profile name
            keywords: List of keywords
            description: Profile description

        Returns:
            bool: True if added successfully, False if name already exists
        """
        if name in self.profiles and not self.profiles[name].is_custom:
            logger.warning(f"Cannot override predefined profile: {name}")
            return False

        self.profiles[name] = KeywordProfile(
            name=name,
            keywords=keywords,
            description=description,
            is_custom=True
        )
        return self._save()

    def update_profile(self, name: str, keywords: List[str], description: str = "") -> bool:
        """
        Update an existing custom profile.

        Args:
            name: Profile name
            keywords: New list of keywords
            description: New description

        Returns:
            bool: True if updated successfully, False if profile doesn't exist or is not custom
        """
        if name not in self.profiles:
            logger.warning(f"Profile not found: {name}")
            return False

        if not self.profiles[name].is_custom:
            logger.warning(f"Cannot modify predefined profile: {name}")
            return False

        self.profiles[name].keywords = keywords
        self.profiles[name].description = description
        return self._save()

    def delete_profile(self, name: str) -> bool:
        """
        Delete a custom profile.

        Args:
            name: Profile name

        Returns:
            bool: True if deleted successfully, False if profile doesn't exist or is not custom
        """
        if name not in self.profiles:
            logger.warning(f"Profile not found: {name}")
            return False

        if not self.profiles[name].is_custom:
            logger.warning(f"Cannot delete predefined profile: {name}")
            return False

        del self.profiles[name]
        return self._save()

    def export_profile(self, name: str, output_path: str) -> bool:
        """
        Export a profile to a JSON file.

        Args:
            name: Profile name
            output_path: Path to save the profile

        Returns:
            bool: True if exported successfully
        """
        profile = self.get_profile(name)
        if not profile:
            logger.error(f"Profile not found: {name}")
            return False

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({name: profile.to_dict()}, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported profile '{name}' to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export profile: {e}")
            return False

    def import_profile(self, input_path: str) -> Optional[str]:
        """
        Import a profile from a JSON file.

        Args:
            input_path: Path to the profile file

        Returns:
            Profile name if imported successfully, None otherwise
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Expect a single profile in the file
            if not data or len(data) != 1:
                logger.error("Invalid profile file format")
                return None

            name, profile_data = next(iter(data.items()))
            profile_data['is_custom'] = True  # Imported profiles are custom

            self.profiles[name] = KeywordProfile.from_dict(name, profile_data)
            self._save()
            logger.info(f"Imported profile '{name}' from {input_path}")
            return name
        except Exception as e:
            logger.error(f"Failed to import profile: {e}")
            return None


# Singleton instance
_manager_instance: Optional[KeywordProfilesManager] = None


def get_profiles_manager() -> KeywordProfilesManager:
    """
    Get the singleton KeywordProfilesManager instance.

    Returns:
        KeywordProfilesManager instance
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = KeywordProfilesManager()
    return _manager_instance
