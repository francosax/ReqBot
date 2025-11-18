import os
import shutil
import logging
from datetime import datetime

from excel_writer import write_excel_file
from highlight_requirements import highlight_requirements
from pdf_analyzer import requirement_finder
from basil_integration import export_to_basil

# v3.0: Database services
from database.services.document_service import DocumentService
from database.services.requirement_service import RequirementService
from database.models import Priority

logger = logging.getLogger(__name__)


def requirement_bot(path_in, cm_path, words_to_find, path_out, confidence_threshold=0.5, project=None):
    """
    Main orchestration function for requirement extraction and processing.

    Args:
        path_in: Path to input PDF file
        cm_path: Path to compliance matrix template
        words_to_find: Set of keywords to find
        path_out: Output directory path
        confidence_threshold: Minimum confidence threshold for requirements (default: 0.5)
        project: Optional Project object for database persistence (v3.0)

    Returns:
        DataFrame with extracted requirements
    """
    # Ottieni data corrente
    current_date = datetime.today()
    formatted_date = current_date.strftime('%Y.%m.%d')

    filename_path, ext = os.path.splitext(path_in)
    filename = os.path.basename(filename_path)
    # print(filename)
    #folder_path = os.path.dirname(filename_path)

    # v3.0: Create or get document in database
    document = None
    if project:
        try:
            document, is_new = DocumentService.get_or_create_document(
                project_id=project.id,
                filename=os.path.basename(path_in),
                file_path=path_in
            )
            if document:
                if is_new:
                    logger.info(f"Created new document in database: {document.filename} (ID: {document.id})")
                else:
                    logger.info(f"Retrieved existing document from database: {document.filename} (ID: {document.id})")
        except Exception as e:
            logger.error(f"Failed to create/retrieve document in database: {str(e)}")
            # Continue processing even if database save fails

    # ========================= ALGORITMO PER TROVARE I REQUISITI =====================================================
    df = requirement_finder(path_in, words_to_find, filename, confidence_threshold)

    # v3.0: Save requirements to database
    if project and document and len(df) > 0:
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
            DocumentService.update_processing_status(
                document_id=document.id,
                status='completed',
                page_count=int(df['Page'].max()) if 'Page' in df.columns else None
            )
        except Exception as e:
            logger.error(f"Failed to save requirements to database: {str(e)}")
            # Continue processing even if database save fails

    # ==================================================================================================================
    # ========================= GESTIONE DELLA COMPLIANCE MATRIX ======================================================

    path_cm = cm_path
    cm_with_extension = os.path.basename(path_cm)
    cm_filename, cm_ext = os.path.splitext(cm_with_extension)
    # cm_folder_path = os.path.dirname(path_cm)
    new_cm = os.path.join(path_out, formatted_date + '_Compliance Matrix_' + filename + cm_ext)
    shutil.copy2(path_cm, new_cm)

    write_excel_file(df=df, excel_file=new_cm)

    # ==================================================================================================================
    # ========================= GESTIONE EXPORT BASIL SPDX 3.0.1 ======================================================
    basil_output = os.path.join(path_out, formatted_date + '_BASIL_Export_' + filename + '.jsonld')
    try:
        export_success = export_to_basil(
            df=df,
            output_path=basil_output,
            created_by='ReqBot',
            document_name=f'Requirements from {filename}'
        )
        if export_success:
            logger.info(f"BASIL export created: {basil_output}")
        else:
            logger.warning(f"BASIL export failed for {filename}")
    except Exception as e:
        logger.error(f"Error during BASIL export for {filename}: {str(e)}")
        # Continue processing even if BASIL export fails

    # ==================================================================================================================
    # ========================= GESTIONE DEGLI HIGHLIGHT E NOTE DEL PDF ================================================
    out_pdf_name = os.path.join(path_out, formatted_date + "_Tagged_" + filename + '.pdf')
    highlight_requirements(filepath=path_in, requirements_list=list(df['Raw']),
                           note_list=list(df['Note']), page_list=list(df['Page']), out_pdf_name=out_pdf_name)
    # ==================================================================================================================
    return df

# path_in= r"C:/Users/Python/Desktop/Spec_pdf/2023_10_20_Last.pdf"
# word_set = {'must', 'shall', 'should', 'has to', 'scope', 'recommended', 'ensuring', 'ensures', 'ensure'}
#
# cm_path= r"C:/Users/Python/Desktop/Compliance_Matrix_Template_rev001.xlsx"
# path_out= "C:/Users/Python/Desktop/Spec_pdf/"
#
# RequirementBot(path_in,cm_path,word_set,path_out)
