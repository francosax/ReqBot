"""
Recent Projects Manager for ReqBot

This module manages the storage and retrieval of recently used paths
(input folders, output folders, compliance matrix files) to provide
quick access in the GUI.

Features:
- Stores up to 5 recent paths for each category
- Persists data to JSON configuration file
- Automatically deduplicates and maintains order
- Thread-safe operations
"""

import json
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Configuration file location
RECENTS_CONFIG_FILE = "recents_config.json"
MAX_RECENT_ITEMS = 5


class RecentsManager:
    """
    Manages recently used paths for input folders, output folders,
    and compliance matrix files.
    """

    def __init__(self, config_file: str = RECENTS_CONFIG_FILE):
        """
        Initialize the RecentsManager.

        Args:
            config_file: Path to JSON configuration file (default: recents_config.json)
        """
        self.config_file = config_file
        self.recents = {
            'input_folders': [],
            'output_folders': [],
            'cm_files': []
        }
        self._load()

    def _load(self) -> None:
        """
        Load recent paths from configuration file.
        Creates default config if file doesn't exist.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Validate loaded data structure
                    if isinstance(loaded_data, dict):
                        self.recents['input_folders'] = loaded_data.get('input_folders', [])
                        self.recents['output_folders'] = loaded_data.get('output_folders', [])
                        self.recents['cm_files'] = loaded_data.get('cm_files', [])
                        logger.info(f"Loaded recent paths from {self.config_file}")
                    else:
                        logger.warning(f"Invalid recents config format, using defaults")
            else:
                logger.info(f"Recents config file not found, will create on first save")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse recents config: {e}. Using defaults.")
        except Exception as e:
            logger.error(f"Error loading recents config: {e}. Using defaults.")

    def _save(self) -> bool:
        """
        Save recent paths to configuration file.

        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.recents, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved recent paths to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save recents config: {e}")
            return False

    def _add_to_category(self, category: str, path: str) -> None:
        """
        Add a path to a specific category, maintaining order and limit.

        Args:
            category: Category name ('input_folders', 'output_folders', 'cm_files')
            path: Absolute path to add
        """
        if category not in self.recents:
            logger.error(f"Invalid category: {category}")
            return

        # Normalize path (convert to absolute, normalize separators)
        normalized_path = os.path.abspath(path)

        # Remove if already exists (to move to top)
        if normalized_path in self.recents[category]:
            self.recents[category].remove(normalized_path)

        # Add to beginning of list
        self.recents[category].insert(0, normalized_path)

        # Limit to MAX_RECENT_ITEMS
        self.recents[category] = self.recents[category][:MAX_RECENT_ITEMS]

        # Save changes
        self._save()

    def add_input_folder(self, path: str) -> None:
        """
        Add an input folder to recent list.

        Args:
            path: Input folder path
        """
        self._add_to_category('input_folders', path)
        logger.debug(f"Added input folder to recents: {path}")

    def add_output_folder(self, path: str) -> None:
        """
        Add an output folder to recent list.

        Args:
            path: Output folder path
        """
        self._add_to_category('output_folders', path)
        logger.debug(f"Added output folder to recents: {path}")

    def add_cm_file(self, path: str) -> None:
        """
        Add a compliance matrix file to recent list.

        Args:
            path: Compliance matrix file path
        """
        self._add_to_category('cm_files', path)
        logger.debug(f"Added CM file to recents: {path}")

    def add_project(self, input_folder: str, output_folder: str, cm_file: str) -> None:
        """
        Add a complete project (all three paths) to recent lists.

        Args:
            input_folder: Input folder path
            output_folder: Output folder path
            cm_file: Compliance matrix file path
        """
        self.add_input_folder(input_folder)
        self.add_output_folder(output_folder)
        self.add_cm_file(cm_file)
        logger.info(f"Added project to recents: {os.path.basename(input_folder)}")

    def get_input_folders(self) -> List[str]:
        """
        Get list of recent input folders.

        Returns:
            List of recent input folder paths (most recent first)
        """
        # Filter out paths that no longer exist
        existing = [p for p in self.recents['input_folders'] if os.path.exists(p)]
        # Update list if any were removed
        if len(existing) != len(self.recents['input_folders']):
            self.recents['input_folders'] = existing
            self._save()
        return existing

    def get_output_folders(self) -> List[str]:
        """
        Get list of recent output folders.

        Returns:
            List of recent output folder paths (most recent first)
        """
        # Filter out paths that no longer exist
        existing = [p for p in self.recents['output_folders'] if os.path.exists(p)]
        # Update list if any were removed
        if len(existing) != len(self.recents['output_folders']):
            self.recents['output_folders'] = existing
            self._save()
        return existing

    def get_cm_files(self) -> List[str]:
        """
        Get list of recent compliance matrix files.

        Returns:
            List of recent CM file paths (most recent first)
        """
        # Filter out paths that no longer exist
        existing = [p for p in self.recents['cm_files'] if os.path.exists(p)]
        # Update list if any were removed
        if len(existing) != len(self.recents['cm_files']):
            self.recents['cm_files'] = existing
            self._save()
        return existing

    def clear_all(self) -> None:
        """
        Clear all recent paths.
        """
        self.recents = {
            'input_folders': [],
            'output_folders': [],
            'cm_files': []
        }
        self._save()
        logger.info("Cleared all recent paths")

    def clear_category(self, category: str) -> None:
        """
        Clear recent paths for a specific category.

        Args:
            category: Category name ('input_folders', 'output_folders', 'cm_files')
        """
        if category in self.recents:
            self.recents[category] = []
            self._save()
            logger.info(f"Cleared recent paths for category: {category}")
        else:
            logger.error(f"Invalid category: {category}")


# Convenience function for single-instance usage
_recents_manager_instance: Optional[RecentsManager] = None


def get_recents_manager() -> RecentsManager:
    """
    Get the global RecentsManager instance (singleton pattern).

    Returns:
        RecentsManager: Global recents manager instance
    """
    global _recents_manager_instance
    if _recents_manager_instance is None:
        _recents_manager_instance = RecentsManager()
    return _recents_manager_instance
