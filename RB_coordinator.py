import os
import shutil
import logging
from datetime import datetime

from excel_writer import write_excel_file
from highlight_requirements import highlight_requirements
from pdf_analyzer import requirement_finder
from basil_integration import export_to_basil

logger = logging.getLogger(__name__)


def requirement_bot(path_in, cm_path, words_to_find, path_out, confidence_threshold=0.5):
    """
    Main orchestration function for requirement extraction and processing.

    Args:
        path_in: Path to input PDF file
        cm_path: Path to compliance matrix template
        words_to_find: Set of keywords to find
        path_out: Output directory path
        confidence_threshold: Minimum confidence threshold for requirements (default: 0.5)

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

    # ========================= ALGORITMO PER TROVARE I REQUISITI =====================================================
    df = requirement_finder(path_in, words_to_find, filename, confidence_threshold)

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
