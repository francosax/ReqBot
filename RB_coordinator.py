import os
import shutil
from datetime import datetime

from CM_excel_writer import write_excel_file
from highlight_requirements import highlight_requirements
from pdf_analyzer import requirement_finder


def requirement_bot(path_in, cm_path, words_to_find, path_out):
    # Ottieni data corrente
    current_date = datetime.today()
    formatted_date = current_date.strftime('%Y.%m.%d')

    filename_path, ext = os.path.splitext(path_in)
    filename = os.path.basename(filename_path)
    # print(filename)
    #folder_path = os.path.dirname(filename_path)

    # ========================= ALGORITMO PER TROVARE I REQUISITI =====================================================
    df = requirement_finder(path_in, words_to_find, filename)

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
    # ========================= GESTIONE DEGLI HIGHLIGHT E NOTE DEL PDF ================================================
    out_pdf_name = os.path.join(path_out, formatted_date + "_Tagged_" + filename + '.pdf')
    highlight_requirements(filepath=path_in, requirements_list=list(df['Raw']),
                           note_list=list(df['Note']), page_list=list(df['Page']), out_pdf_name=out_pdf_name)
    # ==================================================================================================================
    return df

# path_in= r"C:/Users/Python/Desktop/Spec_pdf/2023_10_20_Lastenheft_Winder_PAG2_V04_sent.pdf"
# word_set = {'must', 'shall', 'should', 'has to', 'scope', 'recommended', 'ensuring', 'ensures', 'ensure'}
#
# cm_path= r"C:/Users/Python/Desktop/Compliance_Matrix_Template_rev001.xlsx"
# path_out= "C:/Users/Python/Desktop/Spec_pdf/"
#
# RequirementBot(path_in,cm_path,word_set,path_out)
