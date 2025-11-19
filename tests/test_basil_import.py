#!/usr/bin/env python3
"""
Test BASIL import and validation functionality.
"""

import json
import sys


def validate_basil_format(data):
    """Validate that a JSON structure conforms to BASIL/SPDX 3.0.1 format."""
    try:
        if not isinstance(data, dict):
            return False, "Root element must be a dictionary"

        if data.get("type") != "SpdxDocument":
            return False, f"Expected type 'SpdxDocument', got '{data.get('type')}'"

        if "element" not in data:
            return False, "Missing 'element' array"

        elements = data.get("element", [])
        if not isinstance(elements, list):
            return False, "'element' must be an array"

        # Count requirement files
        req_count = 0
        annotation_count = 0
        for elem in elements:
            if elem.get("type") == "software_File":
                if elem.get("software_primaryPurpose") == "requirement":
                    req_count += 1
            elif elem.get("type") == "Annotation":
                annotation_count += 1

        if req_count == 0:
            return False, "No software requirements found in document"

        return True, f"Valid BASIL format with {req_count} requirements and {annotation_count} annotations"

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def import_from_basil(input_path):
    """Import BASIL JSON-LD format (simplified version without pandas)."""
    try:
        print(f"Reading from: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            spdx_document = json.load(f)

        # Extract elements
        elements = spdx_document.get("element", [])

        # Separate files and annotations
        files = {}
        annotations = {}

        for elem in elements:
            elem_type = elem.get("type", "")
            if elem_type == "software_File":
                if elem.get("software_primaryPurpose") == "requirement":
                    spdx_id = elem.get("spdxId", "")
                    files[spdx_id] = elem
            elif elem_type == "Annotation":
                subject = elem.get("subject", "")
                annotations[subject] = elem

        print(f"Found {len(files)} requirement files")
        print(f"Found {len(annotations)} annotations")

        # Build requirements list
        requirements = []

        for spdx_id, file_elem in files.items():
            name = file_elem.get("name", "")
            description = file_elem.get("description", "")
            comment = file_elem.get("comment", "")

            # Extract ID from comment or spdxId
            req_id = 0
            if "ID" in comment:
                try:
                    req_id = int(comment.split("ID")[-1].strip())
                except ValueError:
                    pass

            # Get detailed metadata from annotation if available
            page = 1
            keyword = ""
            confidence = 0.0
            priority = "low"

            if spdx_id in annotations:
                annotation = annotations[spdx_id]
                statement = annotation.get("statement", "{}")

                try:
                    statement_data = json.loads(statement)

                    # Map BASIL status back to ReqBot priority
                    status_map = {
                        "CRITICAL": "high",
                        "IN_PROGRESS": "medium",
                        "NEW": "low",
                        "COMPLETED": "low",
                        "APPROVED": "high",
                        "REJECTED": "low"
                    }
                    status = statement_data.get("status", "NEW")
                    priority = status_map.get(status, "low")

                    # Extract ReqBot-specific metadata if available
                    reqbot_meta = statement_data.get("reqbot_metadata", {})
                    if reqbot_meta:
                        page = reqbot_meta.get("page", 1)
                        keyword = reqbot_meta.get("keyword", "")
                        confidence = reqbot_meta.get("confidence", 0.0)
                        priority = reqbot_meta.get("priority", priority)

                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse annotation for {spdx_id}: {str(e)}")

            # Create requirement entry
            label_number = f"BASIL-Req#{req_id}-1"

            requirements.append({
                'Label Number': label_number,
                'Description': description,
                'Page': page,
                'Keyword': keyword,
                'Priority': priority,
                'Confidence': confidence,
                'Name': name
            })

        return requirements

    except Exception as e:
        print(f"Error importing: {str(e)}")
        return []


def main():
    print("=" * 70)
    print("BASIL Import and Validation Test")
    print("=" * 70)
    print()

    input_file = "test_basil_export.jsonld"

    # Test 1: Validate Format
    print("Test 1: Validate BASIL Format")
    print("-" * 70)

    with open(input_file, 'r') as f:
        data = json.load(f)

    is_valid, message = validate_basil_format(data)

    if is_valid:
        print("✓ Validation: PASSED")
        print(f"  {message}")
    else:
        print("✗ Validation: FAILED")
        print(f"  {message}")
        return 1

    print()

    # Test 2: Import Requirements
    print("Test 2: Import Requirements")
    print("-" * 70)

    requirements = import_from_basil(input_file)

    if not requirements:
        print("✗ Import failed - no requirements returned")
        return 1

    print(f"✓ Successfully imported {len(requirements)} requirements")
    print()

    # Test 3: Verify Imported Data
    print("Test 3: Verify Imported Data")
    print("-" * 70)

    expected_requirements = [
        {
            'name': 'Authentication Requirement',
            'description': 'The system shall provide user authentication',
            'priority': 'high'
        },
        {
            'name': 'Encryption Requirement',
            'description': 'The application must encrypt all data at rest',
            'priority': 'high'
        },
        {
            'name': 'Security Requirement',
            'description': 'Security protocols should comply with standards',
            'priority': 'security'
        }
    ]

    all_matched = True
    for i, expected in enumerate(expected_requirements):
        if i >= len(requirements):
            print(f"✗ Requirement {i+1}: Missing")
            all_matched = False
            continue

        actual = requirements[i]

        # Check description
        if actual['Description'] == expected['description']:
            print(f"✓ Requirement {i+1}: Description matches")
        else:
            print(f"✗ Requirement {i+1}: Description mismatch")
            print(f"  Expected: {expected['description']}")
            print(f"  Got: {actual['Description']}")
            all_matched = False

        # Check priority
        if actual['Priority'] == expected['priority']:
            print(f"  Priority: {actual['Priority']} ✓")
        else:
            print(f"  Priority mismatch: expected {expected['priority']}, got {actual['Priority']} ✗")
            all_matched = False

        # Check metadata
        print(f"  Page: {actual['Page']}")
        print(f"  Keyword: {actual['Keyword']}")
        print(f"  Confidence: {actual['Confidence']}")

    print()

    if not all_matched:
        print("✗ Data verification FAILED")
        return 1

    print("✓ Data verification PASSED")
    print()

    # Test 4: Verify Round-trip Integrity
    print("Test 4: Verify Round-trip Integrity")
    print("-" * 70)

    # Original data from export
    original_descriptions = [
        "The system shall provide user authentication",
        "The application must encrypt all data at rest",
        "Security protocols should comply with standards"
    ]

    imported_descriptions = [req['Description'] for req in requirements]

    if set(original_descriptions) == set(imported_descriptions):
        print("✓ All descriptions preserved in round-trip")
    else:
        print("✗ Description mismatch in round-trip")
        print(f"  Original: {original_descriptions}")
        print(f"  Imported: {imported_descriptions}")
        return 1

    print("✓ Round-trip integrity verified")
    print()

    # Test 5: Invalid Format Handling
    print("Test 5: Invalid Format Handling")
    print("-" * 70)

    # Test with invalid document type
    invalid_data_1 = {"type": "InvalidType", "element": []}
    is_valid, message = validate_basil_format(invalid_data_1)
    assert not is_valid, "Should reject invalid document type"
    print(f"✓ Correctly rejects invalid type: {message}")

    # Test with missing elements
    invalid_data_2 = {"type": "SpdxDocument"}
    is_valid, message = validate_basil_format(invalid_data_2)
    assert not is_valid, "Should reject missing elements"
    print(f"✓ Correctly rejects missing elements: {message}")

    # Test with no requirements
    invalid_data_3 = {"type": "SpdxDocument", "element": [{"type": "OtherType"}]}
    is_valid, message = validate_basil_format(invalid_data_3)
    assert not is_valid, "Should reject document with no requirements"
    print(f"✓ Correctly rejects no requirements: {message}")

    print()

    # Summary
    print("=" * 70)
    print("All Import and Validation Tests Passed! ✓")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - Format validation: Working ✓")
    print("  - Requirements import: Working ✓")
    print("  - Data integrity: Working ✓")
    print("  - Round-trip preservation: Working ✓")
    print("  - Error handling: Working ✓")
    print()
    print(f"Successfully imported {len(requirements)} requirements from BASIL format")
    print()

    # Display imported requirements
    print("Imported Requirements:")
    print("-" * 70)
    for i, req in enumerate(requirements, 1):
        print(f"{i}. {req['Name']}")
        print(f"   Description: {req['Description']}")
        print(f"   Priority: {req['Priority']}, Page: {req['Page']}, Confidence: {req['Confidence']}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
