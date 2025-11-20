import os
import shutil
import logging
from datetime import datetime

from excel_writer import write_excel_file
from highlight_requirements import highlight_requirements
from pdf_analyzer import requirement_finder
from basil_integration import export_to_basil

# Security validation (Critical Security Fix)
from security.path_validator import (
    PathValidationError,
    validate_pdf_input,
    validate_excel_template,
    validate_directory,
    validate_output_path,
    sanitize_path_for_logging
)

# v3.0: Database services - Optional import
try:
    from database.services.document_service import DocumentService
    from database.services.requirement_service import RequirementService
    from database.models import Priority, ProcessingStatus
    DATABASE_AVAILABLE = True
except ImportError:
    # Database services not available
    DocumentService = None
    RequirementService = None
    Priority = None
    ProcessingStatus = None
    DATABASE_AVAILABLE = False

logger = logging.getLogger(__name__)


def requirement_bot(path_in, cm_path, words_to_find, path_out, confidence_threshold=0.5, project=None):
    """
    Main orchestration function for requirement extraction and processing.

    SECURITY UPDATE: Now includes comprehensive path validation to prevent
    path traversal attacks and ensure safe file system operations.

    Args:
        path_in: Path to input PDF file
        cm_path: Path to compliance matrix template
        words_to_find: Set of keywords to find
        path_out: Output directory path
        confidence_threshold: Minimum confidence threshold for requirements (default: 0.5)
        project: Optional Project object for database persistence (v3.0)

    Returns:
        DataFrame with extracted requirements

    Raises:
        PathValidationError: If any path validation fails
        FileNotFoundError: If required files are not found
        Exception: For other processing errors
    """
    # ========================= PATH VALIDATION (Security Fix) ===============================================
    # Validate input PDF path
    try:
        validated_pdf = validate_pdf_input(path_in)
        logger.info(f"Processing PDF: {sanitize_path_for_logging(str(validated_pdf))}")
    except PathValidationError as e:
        logger.error(f"PDF input validation failed: {str(e)}")
        raise

    # Validate compliance matrix path
    try:
        validated_cm = validate_excel_template(cm_path)
        logger.info(f"Using CM template: {sanitize_path_for_logging(str(validated_cm))}")
    except PathValidationError as e:
        logger.error(f"CM template validation failed: {str(e)}")
        raise

    # Validate output directory
    try:
        validated_output = validate_directory(path_out, must_exist=True, check_writable=True)
        logger.info(f"Output directory: {sanitize_path_for_logging(str(validated_output))}")
    except PathValidationError as e:
        logger.error(f"Output directory validation failed: {str(e)}")
        raise

    # ========================= FILE NAME PREPARATION ========================================================
    # Get current date for file naming
    current_date = datetime.today()
    formatted_date = current_date.strftime('%Y.%m.%d')

    filename_path, ext = os.path.splitext(str(validated_pdf))
    filename = os.path.basename(filename_path)

    # ========================= DATABASE OPERATIONS (v3.0) ==================================================
    # v3.0: Create or get document in database
    document = None
    if project and DATABASE_AVAILABLE and DocumentService:
        try:
            document, is_new = DocumentService.get_or_create_document(
                project_id=project.id,
                filename=os.path.basename(str(validated_pdf)),
                file_path=str(validated_pdf)
            )
            if document:
                if is_new:
                    logger.info(f"Created new document in database: {document.filename} (ID: {document.id})")
                else:
                    logger.info(f"Retrieved existing document from database: {document.filename} (ID: {document.id})")
        except Exception as e:
            logger.error(f"Failed to create/retrieve document in database: {str(e)}")
            # Continue processing even if database save fails

    # ========================= REQUIREMENT EXTRACTION =======================================================
    df = requirement_finder(str(validated_pdf), words_to_find, filename, confidence_threshold)

    # ========================= DATABASE SAVE (v3.0) ========================================================
    # v3.0: Save requirements to database
    if project and document and len(df) > 0 and DATABASE_AVAILABLE and RequirementService:
        try:
            logger.info(f"Saving {len(df)} requirements to database...")
            saved_count = 0
            for _, row in df.iterrows():
                # Map priority text to enum
                priority_map = {
                    'high': Priority.HIGH,
                    'medium': Priority.MEDIUM,
                    'low': Priority.LOW,
                    'security': Priority.SECURITY
                }
                priority_enum = priority_map.get(row.get('Priority', '').lower(), Priority.MEDIUM)

                # Create requirement
                req = RequirementService.create_requirement(
                    document_id=document.id,
                    project_id=project.id,
                    label_number=row['Label Number'],
                    description=row['Description'],
                    page_number=int(row['Page']),
                    keyword=row.get('Keyword'),
                    priority=priority_enum,
                    confidence_score=float(row.get('Confidence', 0.0)),
                    raw_text=str(row.get('Raw', ''))
                )
                if req:
                    saved_count += 1

            logger.info(f"Successfully saved {saved_count}/{len(df)} requirements to database")

            # Update document status to completed
            if DocumentService and ProcessingStatus:
                DocumentService.update_processing_status(
                    document_id=document.id,
                    status=ProcessingStatus.COMPLETED,
                    page_count=int(df['Page'].max()) if 'Page' in df.columns else None
                )
        except Exception as e:
            logger.error(f"Failed to save requirements to database: {str(e)}")
            # Continue processing even if database save fails

    # ========================= COMPLIANCE MATRIX GENERATION =================================================
    cm_with_extension = os.path.basename(str(validated_cm))
    cm_filename, cm_ext = os.path.splitext(cm_with_extension)
    new_cm_path = os.path.join(str(validated_output), formatted_date + '_Compliance Matrix_' + filename + cm_ext)

    # Validate output path before writing (Security Fix)
    try:
        validated_cm_output = validate_output_path(
            new_cm_path,
            allowed_extensions=['.xlsx', '.XLSX']
        )
        shutil.copy2(str(validated_cm), str(validated_cm_output))
        logger.info(f"Copied CM template to: {sanitize_path_for_logging(str(validated_cm_output))}")

        write_excel_file(df=df, excel_file=str(validated_cm_output))
        logger.info("Excel compliance matrix generated successfully")

    except PathValidationError as e:
        logger.error(f"Failed to validate CM output path: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate compliance matrix: {str(e)}")
        raise

    # ========================= BASIL SPDX 3.0.1 EXPORT ======================================================
    basil_output_path = os.path.join(str(validated_output), formatted_date + '_BASIL_Export_' + filename + '.jsonld')

    # Validate BASIL output path (Security Fix)
    try:
        validated_basil = validate_output_path(
            basil_output_path,
            allowed_extensions=['.jsonld', '.json']
        )

        export_success = export_to_basil(
            df=df,
            output_path=str(validated_basil),
            created_by='ReqBot',
            document_name=f'Requirements from {filename}'
        )
        if export_success:
            logger.info(f"BASIL export created: {sanitize_path_for_logging(str(validated_basil))}")
        else:
            logger.warning(f"BASIL export failed for {filename}")

    except PathValidationError as e:
        logger.error(f"BASIL output path validation failed: {str(e)}")
        # Continue processing even if BASIL export fails
    except Exception as e:
        logger.error(f"Error during BASIL export for {filename}: {str(e)}")
        # Continue processing even if BASIL export fails

    # ========================= PDF ANNOTATION ===============================================================
    out_pdf_path = os.path.join(str(validated_output), formatted_date + "_Tagged_" + filename + '.pdf')

    # Validate PDF output path before annotation (Security Fix)
    try:
        validated_pdf_output = validate_output_path(
            out_pdf_path,
            allowed_extensions=['.pdf', '.PDF']
        )

        highlight_requirements(
            filepath=str(validated_pdf),
            requirements_list=list(df['Raw']),
            note_list=list(df['Note']),
            page_list=list(df['Page']),
            out_pdf_name=str(validated_pdf_output)
        )
        logger.info(f"Annotated PDF created: {sanitize_path_for_logging(str(validated_pdf_output))}")

    except PathValidationError as e:
        logger.error(f"PDF output path validation failed: {str(e)}")
        # Continue - don't fail entire process if annotation fails
    except Exception as e:
        logger.error(f"Error during PDF annotation for {filename}: {str(e)}")
        # Continue - don't fail entire process if annotation fails

    # ====================================================================================================
    logger.info(f"Processing completed successfully for {filename}")
    return df
