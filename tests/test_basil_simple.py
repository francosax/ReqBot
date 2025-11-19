#!/usr/bin/env python3
"""
Simple test script for BASIL integration that doesn't require pandas.
Tests core utility functions and JSON structure generation.
"""

import json
import hashlib
import sys
from datetime import datetime

# Test utility functions without importing the full module


def calculate_md5_hash(text: str) -> str:
    """Calculate MD5 hash of a text string."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def extract_requirement_id(label_number: str) -> int:
    """Extract numeric ID from ReqBot label number format."""
    try:
        if "-Req#" in label_number:
            parts = label_number.split("-Req#")
            if len(parts) > 1:
                num_part = parts[1].split("-")[0]
                return int(num_part)
        return 0
    except (ValueError, IndexError) as e:
        print(f"Warning: Failed to extract ID from label {label_number}: {str(e)}")
        return 0


def create_basil_requirement_dict(req_id, title, description, priority="low"):
    """Create a BASIL requirement structure as dictionary."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Priority mapping
    status_map = {
        "high": "CRITICAL",
        "medium": "IN_PROGRESS",
        "low": "NEW",
        "security": "CRITICAL"
    }
    status = status_map.get(priority.lower(), "NEW")

    # Create statement data
    statement_data = {
        "id": req_id,
        "title": title,
        "description": description,
        "status": status,
        "created_by": "ReqBot-Test",
        "version": "1",
        "created_at": timestamp,
        "updated_at": timestamp,
        "__tablename__": "sw_requirements",
        "reqbot_metadata": {
            "page": 1,
            "keyword": "shall",
            "confidence": 0.9,
            "priority": priority
        }
    }

    statement_json = json.dumps(statement_data)
    hash_value = calculate_md5_hash(description)

    # SPDX IDs
    spdx_id = f"spdx:file:basil:software-requirement:{req_id}"
    annotation_id = f"spdx:annotation:basil:software-requirement:{req_id}"
    creation_info_id = f"_:creation_info_spdx:file:basil:software-requirement:{req_id}"

    # File element
    file_element = {
        "type": "software_File",
        "spdxId": spdx_id,
        "software_copyrightText": "",
        "software_primaryPurpose": "requirement",
        "name": title,
        "comment": f"BASIL Software Requirement ID {req_id}",
        "description": description,
        "verifiedUsing": [
            {
                "type": "Hash",
                "algorithm": "md5",
                "hashValue": hash_value
            }
        ],
        "creationInfo": creation_info_id
    }

    # Annotation element
    annotation_element = {
        "type": "Annotation",
        "annotationType": "other",
        "spdxId": annotation_id,
        "subject": spdx_id,
        "statement": statement_json,
        "creationInfo": creation_info_id
    }

    return file_element, annotation_element


def validate_basil_structure(data):
    """Validate BASIL/SPDX structure."""
    errors = []

    if not isinstance(data, dict):
        return False, ["Root element must be a dictionary"]

    if data.get("type") != "SpdxDocument":
        errors.append(f"Expected type 'SpdxDocument', got '{data.get('type')}'")

    if "element" not in data:
        errors.append("Missing 'element' array")

    elements = data.get("element", [])
    if not isinstance(elements, list):
        errors.append("'element' must be an array")

    # Count requirements
    req_count = 0
    for elem in elements:
        if elem.get("type") == "software_File":
            if elem.get("software_primaryPurpose") == "requirement":
                req_count += 1

    if errors:
        return False, errors

    return True, [f"Valid BASIL format with {req_count} requirements"]

# Run tests


def main():
    print("=" * 70)
    print("BASIL Integration - Simple Functionality Test")
    print("=" * 70)
    print()

    # Test 1: MD5 Hash Calculation
    print("Test 1: MD5 Hash Calculation")
    print("-" * 70)
    test_text = "The system shall provide user authentication"
    hash_result = calculate_md5_hash(test_text)
    print(f"Text: {test_text}")
    print(f"MD5 Hash: {hash_result}")
    print(f"Hash length: {len(hash_result)} characters")
    assert len(hash_result) == 32, "MD5 hash should be 32 characters"
    assert hash_result == calculate_md5_hash(test_text), "Hash should be consistent"
    print("✓ PASSED\n")

    # Test 2: Requirement ID Extraction
    print("Test 2: Requirement ID Extraction")
    print("-" * 70)
    test_cases = [
        ("spec-Req#42-1", 42),
        ("document-Req#1-1", 1),
        ("test-Req#999-5", 999),
        ("invalid-label", 0),
        ("Req#abc", 0)
    ]

    all_passed = True
    for label, expected_id in test_cases:
        result = extract_requirement_id(label)
        status = "✓" if result == expected_id else "✗"
        print(f"{status} extract_requirement_id('{label}') = {result} (expected {expected_id})")
        if result != expected_id:
            all_passed = False

    if all_passed:
        print("✓ PASSED\n")
    else:
        print("✗ FAILED\n")
        return 1

    # Test 3: Create BASIL Requirement Structure
    print("Test 3: Create BASIL Requirement Structure")
    print("-" * 70)
    file_elem, annotation_elem = create_basil_requirement_dict(
        req_id=1,
        title="Test Requirement",
        description="The system shall provide secure authentication",
        priority="high"
    )

    # Validate file element
    assert file_elem["type"] == "software_File", "File type should be 'software_File'"
    assert file_elem["software_primaryPurpose"] == "requirement", "Purpose should be 'requirement'"
    assert file_elem["name"] == "Test Requirement", "Name should match"
    assert "spdx:file:basil:software-requirement:1" in file_elem["spdxId"], "SPDX ID should be correct"
    print(f"✓ File element type: {file_elem['type']}")
    print(f"✓ Primary purpose: {file_elem['software_primaryPurpose']}")
    print(f"✓ SPDX ID: {file_elem['spdxId']}")

    # Validate annotation element
    assert annotation_elem["type"] == "Annotation", "Annotation type should be 'Annotation'"
    assert annotation_elem["annotationType"] == "other", "Annotation type should be 'other'"
    print(f"✓ Annotation type: {annotation_elem['type']}")

    # Validate statement JSON
    statement = json.loads(annotation_elem["statement"])
    assert statement["id"] == 1, "ID should match"
    assert statement["status"] == "CRITICAL", "Status should be mapped to CRITICAL for 'high'"
    assert "reqbot_metadata" in statement, "Should contain reqbot_metadata"
    assert statement["reqbot_metadata"]["priority"] == "high", "Original priority should be preserved"
    print(f"✓ Statement ID: {statement['id']}")
    print(f"✓ Mapped status: {statement['status']} (from priority 'high')")
    print(f"✓ Metadata preserved: {list(statement['reqbot_metadata'].keys())}")
    print("✓ PASSED\n")

    # Test 4: Create Complete SPDX Document
    print("Test 4: Create Complete SPDX Document")
    print("-" * 70)

    # Create sample requirements
    requirements = [
        (1, "Authentication Requirement", "The system shall provide user authentication", "high"),
        (2, "Encryption Requirement", "The application must encrypt all data at rest", "high"),
        (3, "Security Requirement", "Security protocols should comply with standards", "security")
    ]

    # Build SPDX document
    spdx_document = {
        "@context": "https://spdx.github.io/spdx-3-model/context.jsonld",
        "type": "SpdxDocument",
        "spdxId": "spdx:document:basil:test",
        "name": "Test Requirements Export",
        "creationInfo": {
            "created": datetime.now().isoformat(),
            "createdBy": ["ReqBot-Test"],
            "specVersion": "3.0.1"
        },
        "element": []
    }

    for req_id, title, description, priority in requirements:
        file_elem, annotation_elem = create_basil_requirement_dict(
            req_id, title, description, priority
        )
        spdx_document["element"].append(file_elem)
        spdx_document["element"].append(annotation_elem)

    print(f"✓ Created SPDX document with {len(requirements)} requirements")
    print(f"✓ Total elements: {len(spdx_document['element'])} (files + annotations)")

    # Save to file
    output_file = "test_basil_export.jsonld"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(spdx_document, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved to: {output_file}")
    print("✓ PASSED\n")

    # Test 5: Validate BASIL Format
    print("Test 5: Validate BASIL Format")
    print("-" * 70)

    is_valid, messages = validate_basil_structure(spdx_document)
    print(f"Validation result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    for msg in messages:
        print(f"  {msg}")

    if not is_valid:
        print("✗ FAILED\n")
        return 1
    print("✓ PASSED\n")

    # Test 6: Read and Validate Exported File
    print("Test 6: Read and Validate Exported File")
    print("-" * 70)

    with open(output_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)

    is_valid, messages = validate_basil_structure(loaded_data)
    assert is_valid, "Loaded document should be valid"
    print("✓ Successfully loaded from file")
    print(f"✓ Document type: {loaded_data['type']}")
    print(f"✓ Document name: {loaded_data['name']}")
    print(f"✓ Elements count: {len(loaded_data['element'])}")

    # Find requirements
    files = [e for e in loaded_data["element"] if e.get("type") == "software_File"]
    annotations = [e for e in loaded_data["element"] if e.get("type") == "Annotation"]

    print(f"✓ Found {len(files)} requirement files")
    print(f"✓ Found {len(annotations)} annotations")
    assert len(files) == 3, "Should have 3 requirement files"
    assert len(annotations) == 3, "Should have 3 annotations"
    print("✓ PASSED\n")

    # Test 7: Verify Round-trip Data Integrity
    print("Test 7: Verify Round-trip Data Integrity")
    print("-" * 70)

    # Check that data in annotations matches original requirements
    for i, (req_id, title, description, priority) in enumerate(requirements):
        annotation = annotations[i]
        statement = json.loads(annotation["statement"])

        assert statement["id"] == req_id, f"ID should match for requirement {i}"
        assert statement["title"] == title, f"Title should match for requirement {i}"
        assert statement["description"] == description, f"Description should match for requirement {i}"

        # Verify metadata
        metadata = statement["reqbot_metadata"]
        assert metadata["priority"] == priority, f"Priority should match for requirement {i}"

        print(f"✓ Requirement {req_id}: Data integrity verified")

    print("✓ PASSED\n")

    # Test 8: Verify Hash Consistency
    print("Test 8: Verify Hash Consistency")
    print("-" * 70)

    for i, file_elem in enumerate(files):
        description = file_elem["description"]
        stored_hash = file_elem["verifiedUsing"][0]["hashValue"]
        calculated_hash = calculate_md5_hash(description)

        assert stored_hash == calculated_hash, f"Hash mismatch for requirement {i}"
        print(f"✓ Requirement {i+1}: Hash verified ({calculated_hash[:16]}...)")

    print("✓ PASSED\n")

    # Summary
    print("=" * 70)
    print("All Tests Passed! ✓")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - MD5 hashing: Working")
    print("  - ID extraction: Working")
    print("  - BASIL structure creation: Working")
    print("  - SPDX document creation: Working")
    print("  - Format validation: Working")
    print("  - File I/O: Working")
    print("  - Data integrity: Working")
    print("  - Hash verification: Working")
    print()
    print(f"Generated test file: {output_file}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
