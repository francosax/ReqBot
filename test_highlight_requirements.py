import os
import fitz
import tempfile
import pytest

from highlight_requirements import highlight_requirements

@pytest.fixture
def sample_pdf():
    # Create a temporary PDF with some text for testing
    doc = fitz.open() #"D:\\PycharmProjects\\RequirementBot\\V12_rel\\RB_1.2\\static\\pippo.pdf",filetype = "pdf")
    page = doc.new_page()
    text = "REQ-001: The system should allow user login.\nREQ-002: The system should allow user registration."
    rect = fitz.Rect(50, 50, 500, 100)
    page.insert_textbox(rect, text)
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    doc.save(path)
    doc.close()
    yield path
    os.remove(path)

def test_highlight_requirements_basic(sample_pdf):
    # Prepare
    # Get the text coordinates by extracting from the PDF
    doc = fitz.open(sample_pdf)
    page = doc[0]
    words = page.get_text("words")
    # "REQ-001:" "The" "system" "should" "allow" "user" "login."
    req1 = ["REQ-001:", "The", "system", "should", "allow", "user", "login."]
    req2 = ["REQ-002:", "The", "system", "should", "allow", "user", "registration."]

    # page_list = [1, 1] since both requirements are on the first page
    requirements_list = [req1, req2]
    note_list = ["Login requirement", "Registration requirement"]
    page_list = [1, 1]

    # Output file
    out_pdf = tempfile.mktemp(suffix=".pdf")
    try:
        # Act
        highlight_requirements(sample_pdf, requirements_list, note_list, page_list, out_pdf)

        # Assert: open the new PDF and check for highlights and annotations
        doc_out = fitz.open(out_pdf)
        page = doc_out[0]

        # There should be at least two highlight annotations
        highlights = [annot for annot in page.annots() if annot.type[0] == 8]  # 8: highlight
        # for annot in page.annots() or []:
        #     print("\n DEBUG: annot types", annot.type)
        notes = [annot.info.get("content") for annot in page.annots() if annot.type[0] == 0]  # 0: text/note

        assert len(highlights) >= 2, "Should have at least two highlights"
        assert len(notes) >= 2, "Should have at least two notes"
        doc_out.close()
    finally:
        if os.path.exists(out_pdf):
            os.remove(out_pdf)

def test_highlight_requirements_no_match(sample_pdf):
    requirements_list = [["Nonexistent", "requirement"]]
    note_list = ["Should not be found"]
    page_list = [1]
    out_pdf = tempfile.mktemp(suffix=".pdf")
    try:
        highlight_requirements(sample_pdf, requirements_list, note_list, page_list, out_pdf)
        # Assert: open the new PDF and check for NO highlights or notes
        doc_out = fitz.open(out_pdf)
        page = doc_out[0]

        highlights = [annot for annot in page.annots() if annot.type[0] == 8]
        notes = [annot for annot in page.annots() if annot.type[0] == 1]
        assert len(highlights) == 0, "Should have no highlights"
        assert len(notes) == 0, "Should have no notes"
        doc_out.close()
    finally:
        if os.path.exists(out_pdf):
            os.remove(out_pdf)