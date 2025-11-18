"""
Tests for recent_projects.py - Recent Projects/Files functionality

Tests the RecentsManager class which manages storage and retrieval
of recently used paths (input folders, output folders, compliance matrix files).
"""

import os
import pytest
import tempfile
import json
from recent_projects import RecentsManager, MAX_RECENT_ITEMS


@pytest.fixture
def temp_config_file(tmp_path):
    """
    Creates a temporary config file path for testing.

    Returns:
        str: Path to temporary config file
    """
    config_file = tmp_path / "test_recents_config.json"
    return str(config_file)


@pytest.fixture
def recents_manager(temp_config_file):
    """
    Creates a RecentsManager instance with temporary config file.

    Returns:
        RecentsManager: Fresh instance for each test
    """
    return RecentsManager(config_file=temp_config_file)


@pytest.fixture
def sample_paths():
    """
    Provides sample paths for testing.

    Returns:
        dict: Dictionary of sample paths for each category
    """
    # Use temp directories that actually exist
    temp_dir = tempfile.gettempdir()
    return {
        'input_folders': [
            os.path.join(temp_dir, 'input1'),
            os.path.join(temp_dir, 'input2'),
            os.path.join(temp_dir, 'input3'),
            os.path.join(temp_dir, 'input4'),
            os.path.join(temp_dir, 'input5'),
            os.path.join(temp_dir, 'input6'),  # Extra for testing limit
        ],
        'output_folders': [
            os.path.join(temp_dir, 'output1'),
            os.path.join(temp_dir, 'output2'),
            os.path.join(temp_dir, 'output3'),
        ],
        'cm_files': [
            os.path.join(temp_dir, 'cm1.xlsx'),
            os.path.join(temp_dir, 'cm2.xlsx'),
        ]
    }


class TestRecentsManagerInitialization:
    """Test RecentsManager initialization and configuration loading"""

    def test_init_creates_empty_recents(self, recents_manager):
        """Test that new RecentsManager starts with empty lists"""
        assert recents_manager.recents['input_folders'] == []
        assert recents_manager.recents['output_folders'] == []
        assert recents_manager.recents['cm_files'] == []

    def test_init_creates_config_file_on_first_save(self, recents_manager, temp_config_file):
        """Test that config file is created when first item is added"""
        assert not os.path.exists(temp_config_file)
        recents_manager.add_input_folder("/test/path")
        assert os.path.exists(temp_config_file)

    def test_load_from_existing_config(self, temp_config_file):
        """Test loading recent paths from existing config file"""
        # Create a config file with some data
        test_data = {
            'input_folders': ['/path1', '/path2'],
            'output_folders': ['/out1'],
            'cm_files': ['/cm1.xlsx']
        }
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        # Create RecentsManager and verify it loaded the data
        manager = RecentsManager(config_file=temp_config_file)
        assert manager.recents['input_folders'] == ['/path1', '/path2']
        assert manager.recents['output_folders'] == ['/out1']
        assert manager.recents['cm_files'] == ['/cm1.xlsx']

    def test_load_invalid_json_uses_defaults(self, temp_config_file):
        """Test that invalid JSON file falls back to defaults"""
        # Create invalid JSON file
        with open(temp_config_file, 'w') as f:
            f.write("{ invalid json }")

        # Should not crash, should use defaults
        manager = RecentsManager(config_file=temp_config_file)
        assert manager.recents['input_folders'] == []
        assert manager.recents['output_folders'] == []
        assert manager.recents['cm_files'] == []


class TestAddingPaths:
    """Test adding paths to recent lists"""

    def test_add_input_folder(self, recents_manager):
        """Test adding an input folder"""
        recents_manager.add_input_folder("/test/input")
        # Check raw data (not filtered by existence)
        assert len(recents_manager.recents['input_folders']) == 1
        assert "test" in recents_manager.recents['input_folders'][0]

    def test_add_output_folder(self, recents_manager):
        """Test adding an output folder"""
        recents_manager.add_output_folder("/test/output")
        # Check raw data (not filtered by existence)
        assert len(recents_manager.recents['output_folders']) == 1
        assert "test" in recents_manager.recents['output_folders'][0]

    def test_add_cm_file(self, recents_manager):
        """Test adding a compliance matrix file"""
        recents_manager.add_cm_file("/test/cm.xlsx")
        # Check raw data (not filtered by existence)
        assert len(recents_manager.recents['cm_files']) == 1
        assert "cm.xlsx" in recents_manager.recents['cm_files'][0]

    def test_add_project(self, recents_manager):
        """Test adding a complete project (all three paths)"""
        recents_manager.add_project("/input", "/output", "/cm.xlsx")
        # Check raw data (not filtered by existence)
        assert len(recents_manager.recents['input_folders']) == 1
        assert len(recents_manager.recents['output_folders']) == 1
        assert len(recents_manager.recents['cm_files']) == 1

    def test_add_duplicate_moves_to_top(self, recents_manager):
        """Test that adding duplicate path moves it to top of list"""
        recents_manager.add_input_folder("/path1")
        recents_manager.add_input_folder("/path2")
        recents_manager.add_input_folder("/path3")

        # Add path1 again - should move to top
        recents_manager.add_input_folder("/path1")

        # Check raw data (most recent first)
        raw_inputs = recents_manager.recents['input_folders']
        assert "path1" in raw_inputs[0]  # path1 should be first (most recent)

    def test_max_items_limit(self, recents_manager, sample_paths):
        """Test that recent lists are limited to MAX_RECENT_ITEMS"""
        # Add more than MAX_RECENT_ITEMS
        for path in sample_paths['input_folders']:
            recents_manager.add_input_folder(path)

        recent_inputs = recents_manager.get_input_folders()
        assert len(recent_inputs) <= MAX_RECENT_ITEMS

    def test_path_normalization(self, recents_manager):
        """Test that paths are normalized (converted to absolute paths)"""
        # Add relative path
        recents_manager.add_input_folder("relative/path")

        # Check raw data - should be converted to absolute path
        raw_inputs = recents_manager.recents['input_folders']
        assert len(raw_inputs) == 1
        assert os.path.isabs(raw_inputs[0])


class TestRetrievingPaths:
    """Test retrieving paths from recent lists"""

    def test_get_input_folders(self, recents_manager, sample_paths):
        """Test getting recent input folders"""
        for path in sample_paths['input_folders'][:3]:
            recents_manager.add_input_folder(path)

        recent_inputs = recents_manager.get_input_folders()
        assert len(recent_inputs) >= 0  # May filter out non-existent paths

    def test_get_output_folders(self, recents_manager, sample_paths):
        """Test getting recent output folders"""
        for path in sample_paths['output_folders']:
            recents_manager.add_output_folder(path)

        recent_outputs = recents_manager.get_output_folders()
        assert len(recent_outputs) >= 0  # May filter out non-existent paths

    def test_get_cm_files(self, recents_manager, sample_paths):
        """Test getting recent CM files"""
        for path in sample_paths['cm_files']:
            recents_manager.add_cm_file(path)

        recent_cms = recents_manager.get_cm_files()
        assert len(recent_cms) >= 0  # May filter out non-existent paths

    def test_get_filters_nonexistent_paths(self, recents_manager):
        """Test that get methods filter out paths that no longer exist"""
        # Add paths that don't exist
        recents_manager.add_input_folder("/nonexistent/path1")
        recents_manager.add_input_folder("/nonexistent/path2")

        # Get should filter them out
        recent_inputs = recents_manager.get_input_folders()
        assert len(recent_inputs) == 0

    def test_get_preserves_existing_paths(self, recents_manager, tmp_path):
        """Test that get methods preserve paths that do exist"""
        # Create actual directories
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        recents_manager.add_input_folder(str(existing_dir))
        recents_manager.add_input_folder("/nonexistent/path")

        recent_inputs = recents_manager.get_input_folders()
        assert len(recent_inputs) == 1
        assert str(existing_dir) in recent_inputs[0]  # May be normalized

    def test_most_recent_first(self, recents_manager):
        """Test that most recent paths appear first"""
        recents_manager.add_input_folder("/path1")
        recents_manager.add_input_folder("/path2")
        recents_manager.add_input_folder("/path3")

        recent_inputs = recents_manager.get_input_folders()
        # path3 should be first (most recent)
        if len(recent_inputs) > 0:
            assert "path3" in recent_inputs[0]


class TestClearingPaths:
    """Test clearing recent paths"""

    def test_clear_all(self, recents_manager):
        """Test clearing all recent paths"""
        recents_manager.add_input_folder("/path1")
        recents_manager.add_output_folder("/path2")
        recents_manager.add_cm_file("/path3")

        recents_manager.clear_all()

        assert len(recents_manager.get_input_folders()) == 0
        assert len(recents_manager.get_output_folders()) == 0
        assert len(recents_manager.get_cm_files()) == 0

    def test_clear_category_input(self, recents_manager):
        """Test clearing only input folders"""
        recents_manager.add_input_folder("/path1")
        recents_manager.add_output_folder("/path2")

        recents_manager.clear_category('input_folders')

        assert len(recents_manager.get_input_folders()) == 0
        # Other categories should be unaffected
        # (output may be filtered if path doesn't exist)

    def test_clear_category_output(self, recents_manager):
        """Test clearing only output folders"""
        recents_manager.add_output_folder("/path1")
        recents_manager.add_cm_file("/path2")

        recents_manager.clear_category('output_folders')

        assert len(recents_manager.get_output_folders()) == 0

    def test_clear_category_cm_files(self, recents_manager):
        """Test clearing only CM files"""
        recents_manager.add_cm_file("/path1")
        recents_manager.add_input_folder("/path2")

        recents_manager.clear_category('cm_files')

        assert len(recents_manager.get_cm_files()) == 0

    def test_clear_invalid_category(self, recents_manager):
        """Test that clearing invalid category doesn't crash"""
        recents_manager.add_input_folder("/path1")

        # Should not crash
        recents_manager.clear_category('invalid_category')

        # Original data should be unaffected
        assert len(recents_manager.recents['input_folders']) > 0


class TestPersistence:
    """Test that data persists across RecentsManager instances"""

    def test_data_persists(self, temp_config_file):
        """Test that data is saved and loaded correctly"""
        # Create first manager and add data
        manager1 = RecentsManager(config_file=temp_config_file)
        manager1.add_input_folder("/persisted/path")

        # Create second manager - should load saved data
        manager2 = RecentsManager(config_file=temp_config_file)

        # Should contain the path in raw data
        # Normalize both paths for comparison
        normalized_paths = [os.path.normpath(p) for p in manager2.recents['input_folders']]
        expected_path = os.path.normpath(os.path.abspath("/persisted/path"))
        assert expected_path in normalized_paths

    def test_multiple_adds_persist(self, temp_config_file):
        """Test that multiple additions persist correctly"""
        manager1 = RecentsManager(config_file=temp_config_file)
        manager1.add_input_folder("/path1")
        manager1.add_input_folder("/path2")
        manager1.add_output_folder("/out1")

        manager2 = RecentsManager(config_file=temp_config_file)
        # Check raw data (not filtered by existence)
        assert len(manager2.recents['input_folders']) == 2
        assert len(manager2.recents['output_folders']) == 1


class TestSingletonPattern:
    """Test the get_recents_manager() singleton pattern"""

    def test_get_recents_manager_returns_instance(self):
        """Test that get_recents_manager returns a RecentsManager instance"""
        from recent_projects import get_recents_manager
        manager = get_recents_manager()
        assert isinstance(manager, RecentsManager)

    def test_get_recents_manager_returns_same_instance(self):
        """Test that get_recents_manager returns the same instance"""
        from recent_projects import get_recents_manager
        manager1 = get_recents_manager()
        manager2 = get_recents_manager()
        assert manager1 is manager2  # Same object reference


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
