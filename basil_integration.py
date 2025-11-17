"""
BASIL Integration Module

This module provides import/export functionality for ReqBot requirements to be compatible
with BASIL software component traceability matrices using SPDX 3.0.1 SBOM definitions.

BASIL exports/imports software requirements as JSON-LD format following SPDX 3.0.1 specification.
Each requirement is represented as:
- A software_File element with primaryPurpose="requirement"
- An Annotation element containing detailed requirement metadata as stringified JSON

Author: ReqBot Team
Date: 2025-11-17
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


# BASIL Integration Constants
BASIL_TYPE_FILE = "software_File"
BASIL_PURPOSE_REQUIREMENT = "requirement"
BASIL_ANNOTATION_TYPE = "Annotation"
BASIL_ANNOTATION_OTHER = "other"
BASIL_HASH_ALGORITHM = "md5"
BASIL_NAMESPACE_PREFIX = "spdx:file:basil:software-requirement:"
BASIL_ANNOTATION_PREFIX = "spdx:annotation:basil:software-requirement:"
BASIL_CREATION_INFO_PREFIX = "_:creation_info_spdx:file:basil:software-requirement:"

# ReqBot to BASIL status mapping
STATUS_MAPPING = {
    "high": "CRITICAL",
    "medium": "IN_PROGRESS",
    "low": "NEW",
    "security": "CRITICAL",
    "critical": "CRITICAL"
}

# Reverse mapping for import
REVERSE_STATUS_MAPPING = {
    "CRITICAL": "high",
    "IN_PROGRESS": "medium",
    "NEW": "low",
    "COMPLETED": "low",
    "APPROVED": "high",
    "REJECTED": "low"
}


def calculate_md5_hash(text: str) -> str:
    """
    Calculate MD5 hash of a text string.

    Args:
        text: Input text to hash

    Returns:
        MD5 hash as hexadecimal string
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def extract_requirement_id(label_number: str) -> int:
    """
    Extract numeric ID from ReqBot label number format.

    ReqBot format: "filename-Req#X-Y" where X is the ID

    Args:
        label_number: ReqBot label number string

    Returns:
        Extracted ID as integer, or 0 if extraction fails
    """
    try:
        # Format: filename-Req#X-Y -> extract X
        if "-Req#" in label_number:
            parts = label_number.split("-Req#")
            if len(parts) > 1:
                # Get the number before the next hyphen
                num_part = parts[1].split("-")[0]
                return int(num_part)
        return 0
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to extract ID from label {label_number}: {str(e)}")
        return 0


def create_basil_requirement(req_id: int, title: str, description: str,
                             priority: str = "low", page: int = 1,
                             keyword: str = "", confidence: float = 0.0,
                             created_by: str = "ReqBot",
                             version: str = "1") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Create BASIL-compatible requirement elements (File + Annotation).

    Args:
        req_id: Unique requirement ID
        title: Requirement title
        description: Requirement description
        priority: ReqBot priority level
        page: PDF page number
        keyword: Matching keyword
        confidence: Confidence score (0.0-1.0)
        created_by: Creator username
        version: Requirement version

    Returns:
        Tuple of (file_element, annotation_element) as dictionaries
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Map ReqBot priority to BASIL status
    status = STATUS_MAPPING.get(priority.lower(), "NEW")

    # Create the statement JSON with all requirement metadata
    statement_data = {
        "id": req_id,
        "title": title,
        "description": description,
        "status": status,
        "created_by": created_by,
        "version": version,
        "created_at": timestamp,
        "updated_at": timestamp,
        "__tablename__": "sw_requirements",
        # ReqBot-specific metadata
        "reqbot_metadata": {
            "page": page,
            "keyword": keyword,
            "confidence": confidence,
            "priority": priority
        }
    }

    statement_json = json.dumps(statement_data)

    # Calculate hash for verification
    hash_value = calculate_md5_hash(description)

    # Create SPDX IDs
    spdx_id = f"{BASIL_NAMESPACE_PREFIX}{req_id}"
    annotation_id = f"{BASIL_ANNOTATION_PREFIX}{req_id}"
    creation_info_id = f"{BASIL_CREATION_INFO_PREFIX}{req_id}"

    # Create File element (BASIL Software Requirement)
    file_element = {
        "type": BASIL_TYPE_FILE,
        "spdxId": spdx_id,
        "software_copyrightText": "",
        "software_primaryPurpose": BASIL_PURPOSE_REQUIREMENT,
        "name": title,
        "comment": f"BASIL Software Requirement ID {req_id}",
        "description": description,
        "verifiedUsing": [
            {
                "type": "Hash",
                "algorithm": BASIL_HASH_ALGORITHM,
                "hashValue": hash_value
            }
        ],
        "creationInfo": creation_info_id
    }

    # Create Annotation element with detailed metadata
    annotation_element = {
        "type": BASIL_ANNOTATION_TYPE,
        "annotationType": BASIL_ANNOTATION_OTHER,
        "spdxId": annotation_id,
        "subject": spdx_id,
        "statement": statement_json,
        "creationInfo": creation_info_id
    }

    return file_element, annotation_element


def export_to_basil(df: pd.DataFrame, output_path: str,
                    created_by: str = "ReqBot",
                    document_name: str = "ReqBot Requirements Export") -> bool:
    """
    Export ReqBot requirements DataFrame to BASIL JSON-LD format.

    Args:
        df: ReqBot requirements DataFrame with columns:
            - Label Number
            - Description
            - Page
            - Keyword
            - Priority
            - Confidence (optional)
        output_path: Path to output JSON-LD file
        created_by: Creator username for BASIL metadata
        document_name: Name of the SPDX document

    Returns:
        True if export successful, False otherwise
    """
    try:
        logger.info(f"Starting BASIL export for {len(df)} requirements")

        # Initialize SPDX document structure
        spdx_document = {
            "@context": "https://spdx.github.io/spdx-3-model/context.jsonld",
            "type": "SpdxDocument",
            "spdxId": "spdx:document:basil:reqbot-export",
            "name": document_name,
            "creationInfo": {
                "created": datetime.now().isoformat(),
                "createdBy": [created_by],
                "specVersion": "3.0.1"
            },
            "element": []
        }

        # Process each requirement
        for index, row in df.iterrows():
            # Extract requirement ID from label
            req_id = extract_requirement_id(row.get('Label Number', ''))
            if req_id == 0:
                req_id = index + 1  # Fallback to index-based ID

            title = row.get('Note', row.get('Description', ''))[:100]  # First 100 chars as title
            description = row.get('Description', '')
            priority = row.get('Priority', 'low')
            page = row.get('Page', 1)
            keyword = row.get('Keyword', '')
            confidence = row.get('Confidence', 0.0)

            # Create BASIL elements
            file_elem, annotation_elem = create_basil_requirement(
                req_id=req_id,
                title=title,
                description=description,
                priority=priority,
                page=page,
                keyword=keyword,
                confidence=confidence,
                created_by=created_by
            )

            # Add to document
            spdx_document["element"].append(file_elem)
            spdx_document["element"].append(annotation_elem)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(spdx_document, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully exported {len(df)} requirements to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to export to BASIL format: {str(e)}")
        return False


def import_from_basil(input_path: str) -> pd.DataFrame:
    """
    Import BASIL JSON-LD format to ReqBot requirements DataFrame.

    Args:
        input_path: Path to BASIL JSON-LD file

    Returns:
        Pandas DataFrame with ReqBot requirement columns:
        - Label Number
        - Description
        - Page
        - Keyword
        - Raw (empty list for imported requirements)
        - Note
        - Priority
        - Confidence
    """
    try:
        logger.info(f"Starting BASIL import from {input_path}")

        # Read JSON-LD file
        with open(input_path, 'r', encoding='utf-8') as f:
            spdx_document = json.load(f)

        # Extract elements
        elements = spdx_document.get("element", [])

        # Separate files and annotations
        files = {}
        annotations = {}

        for elem in elements:
            elem_type = elem.get("type", "")
            if elem_type == BASIL_TYPE_FILE:
                if elem.get("software_primaryPurpose") == BASIL_PURPOSE_REQUIREMENT:
                    spdx_id = elem.get("spdxId", "")
                    files[spdx_id] = elem
            elif elem_type == BASIL_ANNOTATION_TYPE:
                subject = elem.get("subject", "")
                annotations[subject] = elem

        logger.info(f"Found {len(files)} requirement files and {len(annotations)} annotations")

        # Build requirements list
        requirements = []

        for spdx_id, file_elem in files.items():
            # Get basic info from file element
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

            if req_id == 0 and BASIL_NAMESPACE_PREFIX in spdx_id:
                try:
                    req_id = int(spdx_id.split(BASIL_NAMESPACE_PREFIX)[-1])
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
                    status = statement_data.get("status", "NEW")
                    priority = REVERSE_STATUS_MAPPING.get(status, "low")

                    # Extract ReqBot-specific metadata if available
                    reqbot_meta = statement_data.get("reqbot_metadata", {})
                    if reqbot_meta:
                        page = reqbot_meta.get("page", 1)
                        keyword = reqbot_meta.get("keyword", "")
                        confidence = reqbot_meta.get("confidence", 0.0)
                        # Use original priority if available
                        priority = reqbot_meta.get("priority", priority)

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse annotation statement for {spdx_id}: {str(e)}")

            # Create ReqBot requirement entry
            label_number = f"BASIL-Req#{req_id}-1"
            note = f"{label_number}:{name}"

            requirements.append({
                'Label Number': label_number,
                'Description': description,
                'Page': page,
                'Keyword': keyword,
                'Raw': [],  # Empty for imported requirements
                'Note': note,
                'Priority': priority,
                'Confidence': confidence
            })

        # Create DataFrame
        df = pd.DataFrame(requirements)

        logger.info(f"Successfully imported {len(df)} requirements from BASIL format")
        return df

    except Exception as e:
        logger.error(f"Failed to import from BASIL format: {str(e)}")
        return pd.DataFrame()


def validate_basil_format(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that a JSON structure conforms to BASIL/SPDX 3.0.1 format.

    Args:
        data: Dictionary containing parsed JSON-LD data

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check root structure
        if not isinstance(data, dict):
            return False, "Root element must be a dictionary"

        if data.get("type") != "SpdxDocument":
            return False, f"Expected type 'SpdxDocument', got '{data.get('type')}'"

        # Check elements exist
        if "element" not in data:
            return False, "Missing 'element' array"

        elements = data.get("element", [])
        if not isinstance(elements, list):
            return False, "'element' must be an array"

        # Count requirement files
        req_count = 0
        for elem in elements:
            if elem.get("type") == BASIL_TYPE_FILE:
                if elem.get("software_primaryPurpose") == BASIL_PURPOSE_REQUIREMENT:
                    req_count += 1

        if req_count == 0:
            return False, "No software requirements found in document"

        logger.info(f"Validation successful: {req_count} requirements found")
        return True, f"Valid BASIL format with {req_count} requirements found"

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def merge_basil_requirements(existing_df: pd.DataFrame,
                             imported_df: pd.DataFrame,
                             merge_strategy: str = "append") -> pd.DataFrame:
    """
    Merge imported BASIL requirements with existing ReqBot requirements.

    Args:
        existing_df: Existing ReqBot requirements DataFrame
        imported_df: Imported BASIL requirements DataFrame
        merge_strategy: "append" (add all), "update" (update matching IDs),
                       "replace" (replace all)

    Returns:
        Merged DataFrame
    """
    if merge_strategy == "append":
        # Simply append all imported requirements
        result = pd.concat([existing_df, imported_df], ignore_index=True)
        logger.info(f"Appended {len(imported_df)} requirements to {len(existing_df)} existing")

    elif merge_strategy == "update":
        # Update existing requirements with matching IDs
        result = existing_df.copy()
        for _, imported_row in imported_df.iterrows():
            label = imported_row['Label Number']
            # Find matching requirement in existing
            mask = result['Label Number'] == label
            if mask.any():
                # Update existing row - use row index to avoid pandas list assignment issues
                idx = result[mask].index[0]
                for col in imported_df.columns:
                    result.at[idx, col] = imported_row[col]
                logger.debug(f"Updated requirement {label}")
            else:
                # Add new requirement
                result = pd.concat([result, imported_row.to_frame().T], ignore_index=True)
                logger.debug(f"Added new requirement {label}")
        logger.info(f"Updated/added {len(imported_df)} requirements")

    elif merge_strategy == "replace":
        # Replace all existing with imported
        result = imported_df.copy()
        logger.info(f"Replaced {len(existing_df)} requirements with {len(imported_df)} imported")

    else:
        logger.error(f"Unknown merge strategy: {merge_strategy}")
        result = existing_df.copy()

    return result


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    print("BASIL Integration Module - Example Usage\n")

    # Example 1: Create sample requirements and export
    print("=" * 60)
    print("Example 1: Export ReqBot requirements to BASIL format")
    print("=" * 60)

    sample_requirements = pd.DataFrame({
        'Label Number': ['test-Req#1-1', 'test-Req#2-1', 'test-Req#3-1'],
        'Description': [
            'The system shall provide user authentication',
            'The application must ensure data encryption',
            'Security protocols should be implemented'
        ],
        'Page': [1, 2, 3],
        'Keyword': ['shall', 'must', 'should'],
        'Raw': [[], [], []],
        'Note': [
            'test-Req#1-1:The system shall provide user authentication',
            'test-Req#2-1:The application must ensure data encryption',
            'test-Req#3-1:Security protocols should be implemented'
        ],
        'Priority': ['high', 'high', 'security'],
        'Confidence': [0.95, 0.88, 0.92]
    })

    export_success = export_to_basil(
        sample_requirements,
        'sample_basil_export.jsonld',
        created_by='ReqBot-Test',
        document_name='Sample Requirements Export'
    )

    if export_success:
        print("✓ Export successful: sample_basil_export.jsonld")
    else:
        print("✗ Export failed")

    # Example 2: Validate the exported file
    print("\n" + "=" * 60)
    print("Example 2: Validate BASIL format")
    print("=" * 60)

    try:
        with open('sample_basil_export.jsonld', 'r') as f:
            data = json.load(f)

        is_valid, message = validate_basil_format(data)
        if is_valid:
            print(f"✓ {message}")
        else:
            print(f"✗ Validation failed: {message}")
    except FileNotFoundError:
        print("✗ Export file not found")

    # Example 3: Import back from BASIL format
    print("\n" + "=" * 60)
    print("Example 3: Import from BASIL format")
    print("=" * 60)

    imported_df = import_from_basil('sample_basil_export.jsonld')

    if not imported_df.empty:
        print(f"✓ Import successful: {len(imported_df)} requirements imported")
        print("\nImported requirements:")
        print(imported_df[['Label Number', 'Description', 'Priority', 'Confidence']])
    else:
        print("✗ Import failed")

    print("\n" + "=" * 60)
    print("BASIL Integration Module ready for use")
    print("=" * 60)
