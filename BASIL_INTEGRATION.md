## BASIL Integration

**Status**: ✅ Complete (as of 2025-11-17)

ReqBot now supports seamless import/export of requirements to/from [BASIL](https://github.com/your-basil-link) (Software Component Traceability System) using SPDX 3.0.1 SBOM (Software Bill of Materials) definitions in JSON-LD format.

### Overview

BASIL is a software component traceability matrix system that uses standardized SPDX 3.0.1 format for exchanging software requirements and traceability information. The integration allows ReqBot to:

- **Export** ReqBot-extracted requirements to BASIL-compatible JSON-LD format
- **Import** BASIL software requirements into ReqBot for further processing
- **Preserve metadata** including priorities, confidence scores, and page references
- **Maintain traceability** through unique identifiers and hash verification

### Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **SPDX 3.0.1 Compliance** | Full compliance with SPDX 3.0.1 specification | Industry-standard format |
| **Bidirectional Sync** | Export to and import from BASIL | Seamless workflow integration |
| **Metadata Preservation** | Preserves all ReqBot-specific data | No data loss during exchange |
| **Hash Verification** | MD5 hashing for data integrity | Detects tampering/corruption |
| **Flexible Merging** | Multiple merge strategies (append/update/replace) | Customizable workflows |

### BASIL Format Structure

A BASIL software requirement consists of two elements:

#### 1. File Element (Software Requirement)

```json
{
  "type": "software_File",
  "spdxId": "spdx:file:basil:software-requirement:4",
  "software_copyrightText": "",
  "software_primaryPurpose": "requirement",
  "name": "Example Requirement one",
  "comment": "BASIL Software Requirement ID 4",
  "description": "Description of the example requirement one",
  "verifiedUsing": [
    {
      "type": "Hash",
      "algorithm": "md5",
      "hashValue": "6db25f81a86bab932810f1badd87dc57"
    }
  ],
  "creationInfo": "_:creation_info_spdx:file:basil:software-requirement:4"
}
```

#### 2. Annotation Element (Detailed Metadata)

```json
{
  "type": "Annotation",
  "annotationType": "other",
  "spdxId": "spdx:annotation:basil:software-requirement:4",
  "subject": "spdx:file:basil:software-requirement:4",
  "statement": "{\"id\": 4, \"title\": \"Example Requirement one\", \"description\": \"Description of the example requirement one\", \"status\": \"NEW\", \"created_by\": \"user1\", \"version\": \"1\", \"created_at\": \"2025-10-02 09:35\", \"updated_at\": \"2025-10-02 09:35\", \"__tablename__\": \"sw_requirements\", \"reqbot_metadata\": {\"page\": 1, \"keyword\": \"shall\", \"confidence\": 0.95, \"priority\": \"high\"}}",
  "creationInfo": "_:creation_info_spdx:file:basil:software-requirement:4"
}
```

### Module: basil_integration.py

**Location**: `basil_integration.py` (465 lines)

**Purpose**: Complete import/export functionality for BASIL integration

#### Key Functions

**Export Functions:**
- `export_to_basil(df, output_path, created_by, document_name)` - Main export function
- `create_basil_requirement(req_id, title, description, ...)` - Creates BASIL elements

**Import Functions:**
- `import_from_basil(input_path)` - Main import function
- `merge_basil_requirements(existing_df, imported_df, merge_strategy)` - Merge strategies

**Utility Functions:**
- `calculate_md5_hash(text)` - MD5 hash generation
- `extract_requirement_id(label_number)` - Extract ID from ReqBot labels
- `validate_basil_format(data)` - Validate SPDX 3.0.1 compliance

#### Data Mapping

**ReqBot → BASIL:**

| ReqBot Field | BASIL Field | Location | Notes |
|--------------|-------------|----------|-------|
| Label Number | id | Annotation statement | Extracted numeric ID |
| Description | description | File element + Annotation | Full requirement text |
| Note | title | File element + Annotation | First 100 chars |
| Priority | status | Annotation statement | Mapped (high→CRITICAL, etc.) |
| Page | reqbot_metadata.page | Annotation statement | PDF page number |
| Keyword | reqbot_metadata.keyword | Annotation statement | Matching keyword |
| Confidence | reqbot_metadata.confidence | Annotation statement | 0.0-1.0 score |

**Priority Mapping:**

```python
ReqBot → BASIL:
  high      → CRITICAL
  medium    → IN_PROGRESS
  low       → NEW
  security  → CRITICAL
  critical  → CRITICAL

BASIL → ReqBot:
  CRITICAL     → high
  IN_PROGRESS  → medium
  NEW          → low
  COMPLETED    → low
  APPROVED     → high
  REJECTED     → low
```

### Usage Examples

#### Export to BASIL

```python
from basil_integration import export_to_basil
import pandas as pd

# Assuming df is your ReqBot requirements DataFrame
df = pd.DataFrame({
    'Label Number': ['spec-Req#1-1', 'spec-Req#2-1'],
    'Description': ['System shall...', 'Application must...'],
    'Page': [1, 2],
    'Keyword': ['shall', 'must'],
    'Priority': ['high', 'high'],
    'Confidence': [0.95, 0.88],
    'Note': ['spec-Req#1-1:System shall...', 'spec-Req#2-1:Application must...'],
    'Raw': [[], []]
})

# Export to BASIL format
success = export_to_basil(
    df=df,
    output_path='requirements_export.jsonld',
    created_by='ReqBot',
    document_name='My Requirements Export'
)

if success:
    print("Export successful!")
```

#### Import from BASIL

```python
from basil_integration import import_from_basil

# Import BASIL requirements
imported_df = import_from_basil('basil_requirements.jsonld')

if not imported_df.empty:
    print(f"Imported {len(imported_df)} requirements")
    print(imported_df[['Label Number', 'Description', 'Priority']])
```

#### Validate BASIL Format

```python
from basil_integration import validate_basil_format
import json

# Load and validate
with open('requirements.jsonld', 'r') as f:
    data = json.load(f)

is_valid, message = validate_basil_format(data)
print(f"Valid: {is_valid}, Message: {message}")
```

#### Merge Imported Requirements

```python
from basil_integration import merge_basil_requirements

# Merge with different strategies
merged_append = merge_basil_requirements(
    existing_df, imported_df,
    merge_strategy="append"  # Add all imported
)

merged_update = merge_basil_requirements(
    existing_df, imported_df,
    merge_strategy="update"  # Update matching IDs, add new
)

merged_replace = merge_basil_requirements(
    existing_df, imported_df,
    merge_strategy="replace"  # Replace all existing
)
```

### Integration with ReqBot Workflow

The BASIL integration can be incorporated into the ReqBot workflow at multiple points:

#### Post-Processing Export

After ReqBot extracts requirements from PDFs:

```python
# In RB_coordinator.py or processing_worker.py
from basil_integration import export_to_basil

# After requirement extraction
df = pdf_analyzer.requirement_finder(path, keywords, filename)

# Export to BASIL
export_to_basil(
    df,
    output_path=os.path.join(output_folder, f"{date}_BASIL_Export_{filename}.jsonld"),
    created_by="ReqBot",
    document_name=f"Requirements from {filename}"
)
```

#### Pre-Processing Import

Import existing BASIL requirements before processing:

```python
from basil_integration import import_from_basil, merge_basil_requirements

# Load existing BASIL requirements
basil_df = import_from_basil('existing_requirements.jsonld')

# Extract new requirements from PDF
new_df = pdf_analyzer.requirement_finder(path, keywords, filename)

# Merge with update strategy
final_df = merge_basil_requirements(basil_df, new_df, merge_strategy="update")

# Continue with Excel and PDF generation
excel_writer.write_excel_file(final_df, excel_path)
```

### Testing

Comprehensive test suite in `test_basil_integration.py` (470+ lines):

**Test Classes:**
- `TestUtilityFunctions` - Hash calculation, ID extraction, element creation
- `TestExportFunctionality` - Export validation, content verification, metadata preservation
- `TestImportFunctionality` - Import validation, content mapping, error handling
- `TestRoundTrip` - Export-import integrity verification
- `TestValidation` - SPDX format validation
- `TestMergeStrategies` - Append, update, replace strategies

**Run tests:**
```bash
pytest test_basil_integration.py -v
```

**Coverage:**
- ✅ 25+ test cases
- ✅ Export/import round-trip verification
- ✅ Data integrity checks
- ✅ Error handling validation
- ✅ All merge strategies tested

### Configuration Constants

```python
# basil_integration.py

# BASIL/SPDX constants
BASIL_TYPE_FILE = "software_File"
BASIL_PURPOSE_REQUIREMENT = "requirement"
BASIL_ANNOTATION_TYPE = "Annotation"
BASIL_HASH_ALGORITHM = "md5"

# SPDX ID prefixes
BASIL_NAMESPACE_PREFIX = "spdx:file:basil:software-requirement:"
BASIL_ANNOTATION_PREFIX = "spdx:annotation:basil:software-requirement:"
BASIL_CREATION_INFO_PREFIX = "_:creation_info_spdx:file:basil:software-requirement:"

# Status mappings (customizable)
STATUS_MAPPING = {
    "high": "CRITICAL",
    "medium": "IN_PROGRESS",
    "low": "NEW",
    "security": "CRITICAL"
}
```

### Error Handling

The module includes comprehensive error handling:

- **Export errors**: Logs failures, returns False on error
- **Import errors**: Returns empty DataFrame on failure
- **Validation errors**: Returns (False, error_message) tuple
- **File I/O errors**: Gracefully handled with logging

All errors are logged using Python's logging module:

```python
import logging
logger = logging.getLogger(__name__)

# Usage throughout module
logger.info("Starting BASIL export...")
logger.warning("Failed to extract ID from label")
logger.error(f"Failed to import: {str(e)}")
```

### Future Enhancements

Potential improvements for BASIL integration:

1. **GUI Integration**: Add export/import buttons to main_app.py
2. **Batch Operations**: Export/import multiple documents at once
3. **Conflict Resolution**: Interactive conflict resolution for merge operations
4. **Version Control**: Track requirement versions across imports
5. **Custom Mappings**: User-configurable priority/status mappings
6. **API Integration**: Direct API calls to BASIL server (if available)

### Best Practices

When using BASIL integration:

1. **Always validate** imported files before processing
2. **Use hash verification** to detect corruption
3. **Choose appropriate merge strategy** based on workflow
4. **Preserve original files** before merge operations
5. **Test exports** with small datasets first
6. **Log all operations** for audit trails

### Troubleshooting

**Common Issues:**

| Issue | Solution |
|-------|----------|
| "Invalid BASIL format" | Run `validate_basil_format()` to identify specific issues |
| "Import returns empty DataFrame" | Check file exists, valid JSON, contains requirements |
| "Export fails silently" | Enable DEBUG logging to see detailed error messages |
| "Merged data has duplicates" | Use "update" strategy instead of "append" |
| "Priority mappings incorrect" | Customize STATUS_MAPPING dictionaries |

**Debug Logging:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run export/import operations
# Detailed logs will show each step
```

### References

- **SPDX 3.0.1 Specification**: https://spdx.github.io/spdx-spec/v3.0.1/
- **JSON-LD Format**: https://json-ld.org/
- **BASIL Documentation**: [Add link when available]
- **Module Documentation**: See docstrings in `basil_integration.py`

---
