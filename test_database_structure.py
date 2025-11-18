#!/usr/bin/env python3
"""
Database Structure Validation Tests (No SQLAlchemy Required)

These tests validate the database backend structure without requiring
SQLAlchemy to be installed. They check:
- File structure
- Import statements
- Field naming consistency
- Code organization
"""

import re
import sys
from pathlib import Path


class DatabaseStructureValidator:
    """Validates database backend structure."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def log_pass(self, test_name):
        self.passed.append(f"✓ {test_name}")
        
    def log_error(self, test_name, message):
        self.errors.append(f"✗ {test_name}: {message}")
        
    def log_warning(self, test_name, message):
        self.warnings.append(f"⚠ {test_name}: {message}")
    
    def test_file_structure(self):
        """Test that all required files exist."""
        required_files = [
            'database/__init__.py',
            'database/models.py',
            'database/database.py',
            'database/services/project_service.py',
            'database/services/document_service.py',
            'database/services/requirement_service.py',
            'database/services/session_service.py',
            'config/database_config.py',
        ]
        
        for file_path in required_files:
            path = Path(file_path)
            if path.exists():
                self.log_pass(f"File exists: {file_path}")
            else:
                self.log_error(f"File exists: {file_path}", "File not found")
    
    def test_models_structure(self):
        """Test models.py structure."""
        models_path = Path('database/models.py')
        
        if not models_path.exists():
            self.log_error("Models structure", "models.py not found")
            return
            
        content = models_path.read_text()
        
        # Check for enum definitions
        required_enums = ['ProcessingStatus', 'Priority', 'SessionStatus', 'ChangeType']
        for enum_name in required_enums:
            if f"class {enum_name}(str, PyEnum):" in content:
                self.log_pass(f"Enum defined: {enum_name}")
            else:
                self.log_error(f"Enum defined: {enum_name}", "Enum not found")
        
        # Check for model classes
        required_models = ['Project', 'Document', 'Requirement', 
                          'RequirementHistory', 'ProcessingSession', 'KeywordProfile']
        for model_name in required_models:
            if f"class {model_name}(Base):" in content:
                self.log_pass(f"Model defined: {model_name}")
            else:
                self.log_error(f"Model defined: {model_name}", "Model not found")
        
        # Check that JSON fields use JSON type, not Text
        old_json_patterns = [
            r'metadata_json.*Text',
            r'snapshot_data_json.*Text',
            r'pdf_output_paths_json.*Text',
            r'warnings_json.*Text',
            r'errors_json.*Text',
            r'keywords_json.*Text',
        ]
        
        found_old_patterns = []
        for pattern in old_json_patterns:
            if re.search(pattern, content):
                found_old_patterns.append(pattern)
        
        if found_old_patterns:
            self.log_error("JSON field types", f"Found old *_json Text fields: {found_old_patterns}")
        else:
            self.log_pass("JSON field types: All migrated to JSON type")
        
        # Check for new JSON fields
        new_json_fields = [
            (r'metadata.*mapped_column\(JSON', 'metadata as JSON'),
            (r'snapshot_data.*mapped_column\(JSON', 'snapshot_data as JSON'),
            (r'pdf_output_paths.*mapped_column\(JSON', 'pdf_output_paths as JSON'),
            (r'warnings.*mapped_column\(JSON', 'warnings as JSON'),
            (r'errors.*mapped_column\(JSON', 'errors as JSON'),
            (r'keywords.*mapped_column\(JSON', 'keywords as JSON'),
        ]
        
        for pattern, field_name in new_json_fields:
            if re.search(pattern, content):
                self.log_pass(f"New JSON field: {field_name}")
            else:
                self.log_warning(f"New JSON field: {field_name}", "Pattern not found (might be OK)")
        
        # Check that json import is removed
        if re.search(r'^import json$', content, re.MULTILINE):
            self.log_error("JSON import", "Unnecessary 'import json' found (should be removed)")
        else:
            self.log_pass("JSON import removed")
        
        # Check that onupdate=func.now() is removed
        if 'onupdate=func.now()' in content:
            self.log_error("onupdate removal", "Found onupdate=func.now() (should be removed)")
        else:
            self.log_pass("onupdate=func.now() removed from all fields")
    
    def test_database_structure(self):
        """Test database.py structure."""
        db_path = Path('database/database.py')
        
        if not db_path.exists():
            self.log_error("Database structure", "database.py not found")
            return
            
        content = db_path.read_text()
        
        # Check for threading import
        if 'import threading' in content:
            self.log_pass("Threading import present")
        else:
            self.log_error("Threading import", "Missing 'import threading'")
        
        # Check for thread locks
        lock_patterns = [
            '_engine_lock',
            '_session_factory_lock',
            '_scoped_session_lock',
        ]
        
        for lock_name in lock_patterns:
            if lock_name in content:
                self.log_pass(f"Thread lock defined: {lock_name}")
            else:
                self.log_error(f"Thread lock defined: {lock_name}", "Lock not found")
        
        # Check for double-checked locking pattern
        if 'with _engine_lock:' in content:
            self.log_pass("Double-checked locking implemented")
        else:
            self.log_error("Double-checked locking", "Pattern not found")
        
        # Check for auto_initialize_database function
        if 'def auto_initialize_database()' in content:
            self.log_pass("auto_initialize_database() function exists")
        else:
            self.log_error("auto_initialize_database()", "Function not found")
        
        # Check for password sanitization
        if 'safe_url' in content and '***' in content:
            self.log_pass("Password sanitization implemented")
        else:
            self.log_error("Password sanitization", "Pattern not found")
    
    def test_service_layer_compatibility(self):
        """Test that service layer is compatible with new schema."""
        service_files = [
            'database/services/project_service.py',
            'database/services/document_service.py',
            'database/services/requirement_service.py',
            'database/services/session_service.py',
        ]
        
        for service_file in service_files:
            path = Path(service_file)
            if not path.exists():
                self.log_error(f"Service compatibility: {service_file}", "File not found")
                continue
                
            content = path.read_text()
            
            # Check that service doesn't reference old *_json field names
            old_field_patterns = [
                r'\.metadata_json',
                r'\.snapshot_data_json',
                r'\.pdf_output_paths_json',
                r'\.warnings_json',
                r'\.errors_json',
                r'\.keywords_json',
            ]
            
            found_old_fields = []
            for pattern in old_field_patterns:
                if re.search(pattern, content):
                    found_old_fields.append(pattern)
            
            if found_old_fields:
                self.log_error(f"Service compatibility: {service_file}", 
                             f"References old *_json fields: {found_old_fields}")
            else:
                self.log_pass(f"Service compatibility: {service_file}")
    
    def test_enum_imports(self):
        """Test that service files import enums correctly."""
        service_files = {
            'database/services/document_service.py': ['ProcessingStatus'],
            'database/services/requirement_service.py': ['Priority', 'ChangeType'],
            'database/services/session_service.py': ['SessionStatus'],
        }
        
        for service_file, required_enums in service_files.items():
            path = Path(service_file)
            if not path.exists():
                continue
                
            content = path.read_text()
            
            for enum_name in required_enums:
                if enum_name in content:
                    self.log_pass(f"Enum imported in {service_file}: {enum_name}")
                else:
                    self.log_warning(f"Enum imported in {service_file}: {enum_name}", 
                                   "Enum name not found in file")
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 70)
        print("Database Backend Structure Validation")
        print("=" * 70)
        print()
        
        self.test_file_structure()
        self.test_models_structure()
        self.test_database_structure()
        self.test_service_layer_compatibility()
        self.test_enum_imports()
        
        print("\n" + "=" * 70)
        print("Test Results Summary")
        print("=" * 70)
        
        print(f"\n✓ PASSED: {len(self.passed)}")
        for msg in self.passed:
            print(f"  {msg}")
        
        if self.warnings:
            print(f"\n⚠ WARNINGS: {len(self.warnings)}")
            for msg in self.warnings:
                print(f"  {msg}")
        
        if self.errors:
            print(f"\n✗ FAILED: {len(self.errors)}")
            for msg in self.errors:
                print(f"  {msg}")
        
        print("\n" + "=" * 70)
        print(f"Total: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors")
        print("=" * 70)
        
        return len(self.errors) == 0


if __name__ == '__main__':
    validator = DatabaseStructureValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)
