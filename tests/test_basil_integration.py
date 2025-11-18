"""
Unit tests for BASIL integration module.

Tests the import/export functionality for BASIL-compatible SPDX 3.0.1 format.
"""

import pytest
import json
import pandas as pd
from pathlib import Path
import tempfile
import os

from basil_integration import (
    calculate_md5_hash,
    extract_requirement_id,
    create_basil_requirement,
    export_to_basil,
    import_from_basil,
    validate_basil_format,
    merge_basil_requirements,
    BASIL_TYPE_FILE,
    BASIL_PURPOSE_REQUIREMENT,
    BASIL_ANNOTATION_TYPE
)


@pytest.fixture
def sample_reqbot_dataframe():
    """Create a sample ReqBot requirements DataFrame for testing."""
    return pd.DataFrame({
        'Label Number': ['spec-Req#1-1', 'spec-Req#2-1', 'spec-Req#3-1'],
        'Description': [
            'The system shall provide secure user authentication',
            'The application must encrypt all data at rest',
            'Security protocols should comply with industry standards'
        ],
        'Page': [1, 2, 3],
        'Keyword': ['shall', 'must', 'should'],
        'Raw': [
            ['The', 'system', 'shall', 'provide', 'secure', 'user', 'authentication'],
            ['The', 'application', 'must', 'encrypt', 'all', 'data', 'at', 'rest'],
            ['Security', 'protocols', 'should', 'comply', 'with', 'industry', 'standards']
        ],
        'Note': [
            'spec-Req#1-1:The system shall provide secure user authentication',
            'spec-Req#2-1:The application must encrypt all data at rest',
            'spec-Req#3-1:Security protocols should comply with industry standards'
        ],
        'Priority': ['high', 'high', 'medium'],
        'Confidence': [0.95, 0.88, 0.72]
    })


@pytest.fixture
def sample_basil_json():
    """Create a sample BASIL JSON-LD structure for testing."""
    return {
        "@context": "https://spdx.github.io/spdx-3-model/context.jsonld",
        "type": "SpdxDocument",
        "spdxId": "spdx:document:basil:test",
        "name": "Test Requirements",
        "creationInfo": {
            "created": "2025-11-17T10:00:00",
            "createdBy": ["TestUser"],
            "specVersion": "3.0.1"
        },
        "element": [
            {
                "type": "software_File",
                "spdxId": "spdx:file:basil:software-requirement:1",
                "software_copyrightText": "",
                "software_primaryPurpose": "requirement",
                "name": "Test Requirement",
                "comment": "BASIL Software Requirement ID 1",
                "description": "This is a test requirement",
                "verifiedUsing": [
                    {
                        "type": "Hash",
                        "algorithm": "md5",
                        "hashValue": "abc123"
                    }
                ],
                "creationInfo": "_:creation_info_spdx:file:basil:software-requirement:1"
            },
            {
                "type": "Annotation",
                "annotationType": "other",
                "spdxId": "spdx:annotation:basil:software-requirement:1",
                "subject": "spdx:file:basil:software-requirement:1",
                "statement": json.dumps({
                    "id": 1,
                    "title": "Test Requirement",
                    "description": "This is a test requirement",
                    "status": "CRITICAL",
                    "created_by": "TestUser",
                    "version": "1",
                    "created_at": "2025-11-17 10:00",
                    "updated_at": "2025-11-17 10:00",
                    "__tablename__": "sw_requirements",
                    "reqbot_metadata": {
                        "page": 1,
                        "keyword": "shall",
                        "confidence": 0.9,
                        "priority": "high"
                    }
                }),
                "creationInfo": "_:creation_info_spdx:file:basil:software-requirement:1"
            }
        ]
    }


class TestUtilityFunctions:
    """Test utility functions for BASIL integration."""

    def test_calculate_md5_hash(self):
        """Test MD5 hash calculation."""
        text = "The system shall provide authentication"
        hash_value = calculate_md5_hash(text)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 32  # MD5 produces 32-character hex string
        # Hash should be consistent
        assert hash_value == calculate_md5_hash(text)

    def test_extract_requirement_id_valid(self):
        """Test extraction of requirement ID from label."""
        assert extract_requirement_id("spec-Req#42-1") == 42
        assert extract_requirement_id("document-Req#1-1") == 1
        assert extract_requirement_id("test-Req#999-5") == 999

    def test_extract_requirement_id_invalid(self):
        """Test extraction with invalid label formats."""
        assert extract_requirement_id("invalid-label") == 0
        assert extract_requirement_id("Req#abc") == 0
        assert extract_requirement_id("") == 0

    def test_create_basil_requirement(self):
        """Test creation of BASIL requirement elements."""
        file_elem, annotation_elem = create_basil_requirement(
            req_id=1,
            title="Test Requirement",
            description="This is a test",
            priority="high",
            page=5,
            keyword="shall",
            confidence=0.85
        )

        # Verify file element structure
        assert file_elem["type"] == BASIL_TYPE_FILE
        assert file_elem["software_primaryPurpose"] == BASIL_PURPOSE_REQUIREMENT
        assert file_elem["name"] == "Test Requirement"
        assert file_elem["description"] == "This is a test"
        assert "spdx:file:basil:software-requirement:1" in file_elem["spdxId"]

        # Verify annotation element structure
        assert annotation_elem["type"] == BASIL_ANNOTATION_TYPE
        assert annotation_elem["annotationType"] == "other"
        assert "spdx:annotation:basil:software-requirement:1" in annotation_elem["spdxId"]

        # Verify statement contains metadata
        statement = json.loads(annotation_elem["statement"])
        assert statement["id"] == 1
        assert statement["title"] == "Test Requirement"
        assert statement["description"] == "This is a test"
        assert statement["reqbot_metadata"]["page"] == 5
        assert statement["reqbot_metadata"]["keyword"] == "shall"
        assert statement["reqbot_metadata"]["confidence"] == 0.85
        assert statement["reqbot_metadata"]["priority"] == "high"


class TestExportFunctionality:
    """Test BASIL export functionality."""

    def test_export_to_basil_basic(self, sample_reqbot_dataframe, tmp_path):
        """Test basic export of requirements to BASIL format."""
        output_file = tmp_path / "test_export.jsonld"

        success = export_to_basil(
            sample_reqbot_dataframe,
            str(output_file),
            created_by="TestUser",
            document_name="Test Export"
        )

        assert success is True
        assert output_file.exists()

        # Load and verify structure
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert data["type"] == "SpdxDocument"
        assert data["name"] == "Test Export"
        assert "element" in data

        # Should have 3 requirements × 2 elements (file + annotation) = 6 elements
        assert len(data["element"]) == 6

    def test_export_to_basil_content(self, sample_reqbot_dataframe, tmp_path):
        """Test that exported content matches source requirements."""
        output_file = tmp_path / "test_export.jsonld"

        export_to_basil(
            sample_reqbot_dataframe,
            str(output_file)
        )

        with open(output_file, 'r') as f:
            data = json.load(f)

        # Find file elements
        files = [e for e in data["element"] if e.get("type") == BASIL_TYPE_FILE]
        assert len(files) == 3

        # Verify first requirement content
        first_file = files[0]
        assert "authentication" in first_file["description"].lower()
        assert first_file["software_primaryPurpose"] == BASIL_PURPOSE_REQUIREMENT

    def test_export_empty_dataframe(self, tmp_path):
        """Test export with empty DataFrame."""
        empty_df = pd.DataFrame()
        output_file = tmp_path / "empty_export.jsonld"

        success = export_to_basil(empty_df, str(output_file))

        assert success is True
        assert output_file.exists()

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert len(data["element"]) == 0

    def test_export_preserves_metadata(self, sample_reqbot_dataframe, tmp_path):
        """Test that export preserves all ReqBot metadata."""
        output_file = tmp_path / "metadata_export.jsonld"

        export_to_basil(sample_reqbot_dataframe, str(output_file))

        with open(output_file, 'r') as f:
            data = json.load(f)

        # Find annotations
        annotations = [e for e in data["element"] if e.get("type") == BASIL_ANNOTATION_TYPE]
        assert len(annotations) == 3

        # Check first annotation contains all metadata
        statement = json.loads(annotations[0]["statement"])
        assert "reqbot_metadata" in statement
        metadata = statement["reqbot_metadata"]

        assert "page" in metadata
        assert "keyword" in metadata
        assert "confidence" in metadata
        assert "priority" in metadata


class TestImportFunctionality:
    """Test BASIL import functionality."""

    def test_import_from_basil_basic(self, sample_basil_json, tmp_path):
        """Test basic import from BASIL format."""
        input_file = tmp_path / "test_import.jsonld"

        with open(input_file, 'w') as f:
            json.dump(sample_basil_json, f)

        df = import_from_basil(str(input_file))

        assert not df.empty
        assert len(df) == 1
        assert 'Label Number' in df.columns
        assert 'Description' in df.columns
        assert 'Priority' in df.columns
        assert 'Confidence' in df.columns

    def test_import_from_basil_content(self, sample_basil_json, tmp_path):
        """Test that imported content matches BASIL source."""
        input_file = tmp_path / "test_import.jsonld"

        with open(input_file, 'w') as f:
            json.dump(sample_basil_json, f)

        df = import_from_basil(str(input_file))

        # Verify imported data
        assert df.iloc[0]['Description'] == "This is a test requirement"
        assert df.iloc[0]['Priority'] == "high"  # Mapped from CRITICAL
        assert df.iloc[0]['Confidence'] == 0.9
        assert df.iloc[0]['Page'] == 1
        assert df.iloc[0]['Keyword'] == "shall"

    def test_import_missing_file(self):
        """Test import with non-existent file."""
        df = import_from_basil("nonexistent_file.jsonld")
        assert df.empty

    def test_import_invalid_json(self, tmp_path):
        """Test import with invalid JSON file."""
        input_file = tmp_path / "invalid.jsonld"

        with open(input_file, 'w') as f:
            f.write("This is not valid JSON")

        df = import_from_basil(str(input_file))
        assert df.empty

    def test_import_no_requirements(self, tmp_path):
        """Test import with document containing no requirements."""
        input_file = tmp_path / "no_reqs.jsonld"

        data = {
            "type": "SpdxDocument",
            "spdxId": "spdx:document:test",
            "name": "Empty Document",
            "creationInfo": {},
            "element": []
        }

        with open(input_file, 'w') as f:
            json.dump(data, f)

        df = import_from_basil(str(input_file))
        assert df.empty


class TestRoundTrip:
    """Test export-import round-trip to ensure data integrity."""

    def test_export_import_roundtrip(self, sample_reqbot_dataframe, tmp_path):
        """Test that data survives export-import round trip."""
        export_file = tmp_path / "roundtrip.jsonld"

        # Export
        export_success = export_to_basil(
            sample_reqbot_dataframe,
            str(export_file)
        )
        assert export_success

        # Import
        imported_df = import_from_basil(str(export_file))

        # Verify same number of requirements
        assert len(imported_df) == len(sample_reqbot_dataframe)

        # Verify descriptions match
        original_descriptions = set(sample_reqbot_dataframe['Description'])
        imported_descriptions = set(imported_df['Description'])
        assert original_descriptions == imported_descriptions

        # Verify priorities are preserved (considering mapping)
        for i in range(len(sample_reqbot_dataframe)):
            original_priority = sample_reqbot_dataframe.iloc[i]['Priority']
            imported_priority = imported_df.iloc[i]['Priority']
            # High should map to CRITICAL and back to high
            if original_priority == 'high':
                assert imported_priority == 'high'


class TestValidation:
    """Test BASIL format validation."""

    def test_validate_valid_format(self, sample_basil_json):
        """Test validation of valid BASIL format."""
        is_valid, message = validate_basil_format(sample_basil_json)

        assert is_valid is True
        assert "requirements found" in message.lower()

    def test_validate_invalid_type(self):
        """Test validation with wrong document type."""
        invalid_data = {
            "type": "InvalidType",
            "element": []
        }

        is_valid, message = validate_basil_format(invalid_data)
        assert is_valid is False
        assert "SpdxDocument" in message

    def test_validate_missing_elements(self):
        """Test validation with missing elements array."""
        invalid_data = {
            "type": "SpdxDocument"
        }

        is_valid, message = validate_basil_format(invalid_data)
        assert is_valid is False
        assert "element" in message.lower()

    def test_validate_no_requirements(self):
        """Test validation with no requirements in document."""
        data = {
            "type": "SpdxDocument",
            "element": [
                {"type": "OtherType", "name": "Not a requirement"}
            ]
        }

        is_valid, message = validate_basil_format(data)
        assert is_valid is False
        assert "no software requirements" in message.lower()


class TestMergeStrategies:
    """Test merging of imported requirements with existing ones."""

    def test_merge_append_strategy(self):
        """Test append merge strategy."""
        existing_df = pd.DataFrame({
            'Label Number': ['existing-Req#1-1'],
            'Description': ['Existing requirement'],
            'Page': [1],
            'Keyword': ['shall'],
            'Raw': [[]],
            'Note': ['existing-Req#1-1:Existing requirement'],
            'Priority': ['high'],
            'Confidence': [0.9]
        })

        imported_df = pd.DataFrame({
            'Label Number': ['imported-Req#1-1'],
            'Description': ['Imported requirement'],
            'Page': [2],
            'Keyword': ['must'],
            'Raw': [[]],
            'Note': ['imported-Req#1-1:Imported requirement'],
            'Priority': ['medium'],
            'Confidence': [0.8]
        })

        merged = merge_basil_requirements(existing_df, imported_df, merge_strategy="append")

        assert len(merged) == 2
        assert 'Existing requirement' in merged['Description'].values
        assert 'Imported requirement' in merged['Description'].values

    def test_merge_replace_strategy(self):
        """Test replace merge strategy."""
        existing_df = pd.DataFrame({
            'Label Number': ['existing-Req#1-1'],
            'Description': ['Existing requirement'],
            'Page': [1],
            'Keyword': ['shall'],
            'Raw': [[]],
            'Note': ['existing-Req#1-1:Existing requirement'],
            'Priority': ['high'],
            'Confidence': [0.9]
        })

        imported_df = pd.DataFrame({
            'Label Number': ['imported-Req#1-1'],
            'Description': ['Imported requirement'],
            'Page': [2],
            'Keyword': ['must'],
            'Raw': [[]],
            'Note': ['imported-Req#1-1:Imported requirement'],
            'Priority': ['medium'],
            'Confidence': [0.8]
        })

        merged = merge_basil_requirements(existing_df, imported_df, merge_strategy="replace")

        assert len(merged) == 1
        assert merged.iloc[0]['Description'] == 'Imported requirement'

    def test_merge_update_strategy(self):
        """Test update merge strategy."""
        existing_df = pd.DataFrame({
            'Label Number': ['test-Req#1-1', 'test-Req#2-1'],
            'Description': ['Old description 1', 'Keep this one'],
            'Page': [1, 2],
            'Keyword': ['shall', 'must'],
            'Raw': [[], []],
            'Note': ['test-Req#1-1:Old description 1', 'test-Req#2-1:Keep this one'],
            'Priority': ['low', 'high'],
            'Confidence': [0.5, 0.9]
        })

        imported_df = pd.DataFrame({
            'Label Number': ['test-Req#1-1', 'test-Req#3-1'],
            'Description': ['New description 1', 'New requirement 3'],
            'Page': [1, 3],
            'Keyword': ['shall', 'should'],
            'Raw': [[], []],
            'Note': ['test-Req#1-1:New description 1', 'test-Req#3-1:New requirement 3'],
            'Priority': ['high', 'medium'],
            'Confidence': [0.95, 0.7]
        })

        merged = merge_basil_requirements(existing_df, imported_df, merge_strategy="update")

        # Should have 3 total: updated #1, kept #2, added #3
        assert len(merged) == 3

        # Requirement #1 should be updated
        req1 = merged[merged['Label Number'] == 'test-Req#1-1'].iloc[0]
        assert req1['Description'] == 'New description 1'
        assert req1['Priority'] == 'high'

        # Requirement #2 should be unchanged
        req2 = merged[merged['Label Number'] == 'test-Req#2-1'].iloc[0]
        assert req2['Description'] == 'Keep this one'

        # Requirement #3 should be added
        req3 = merged[merged['Label Number'] == 'test-Req#3-1'].iloc[0]
        assert req3['Description'] == 'New requirement 3'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
