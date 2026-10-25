"""Tests for src/pdf_parser.py.

Tests that need a real PDF reader are skipped automatically if PyMuPDF is not installed.
"""

from pathlib import Path

import pytest

from src import pdf_parser
from src.pdf_parser import PDFParsingError, extract_text_from_pdf
from src.sample_pdf import build_simple_pdf

SAMPLE_PDF = Path(__file__).resolve().parent.parent / "sample_data" / "sample_resume.pdf"


def needs_pdf_library():
    if pdf_parser._pdf_lib is None:
        pytest.skip("PyMuPDF is not installed")


def test_empty_bytes_raises():
    with pytest.raises(PDFParsingError):
        extract_text_from_pdf(b"")


def test_non_bytes_input_raises_type_error():
    with pytest.raises(TypeError):
        extract_text_from_pdf("not bytes")
    with pytest.raises(TypeError):
        extract_text_from_pdf(None)


def test_plain_text_file_is_rejected():
    with pytest.raises(PDFParsingError):
        extract_text_from_pdf(b"This is just a text file, not a PDF.")


def test_oversized_file_is_rejected():
    too_big = b"%PDF-1.4\n" + b"0" * (pdf_parser.MAX_PDF_BYTES + 1)
    with pytest.raises(PDFParsingError):
        extract_text_from_pdf(too_big)


def test_corrupted_pdf_with_valid_header_raises():
    needs_pdf_library()
    with pytest.raises(PDFParsingError):
        extract_text_from_pdf(b"%PDF-1.4\nthis is garbage, not a real pdf structure")


def test_blank_pdf_without_text_raises():
    needs_pdf_library()
    with pytest.raises(PDFParsingError):
        extract_text_from_pdf(build_simple_pdf(""))


def test_valid_pdf_text_is_extracted():
    needs_pdf_library()
    text = extract_text_from_pdf(build_simple_pdf("Hello recruiter\nPython and SQL skills"))
    assert "Hello recruiter" in text
    assert "Python" in text


def test_bundled_sample_resume_pdf_is_readable():
    needs_pdf_library()
    text = extract_text_from_pdf(SAMPLE_PDF.read_bytes())
    assert "EDUCATION" in text
    assert "scikit-learn" in text


def test_clean_extracted_text_collapses_whitespace():
    assert pdf_parser.clean_extracted_text("a   b\n\n\n\nc \x00") == "a b\n\nc"
