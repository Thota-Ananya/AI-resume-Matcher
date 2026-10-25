"""Extract text from PDF resumes (in memory only - nothing is written to disk)."""

from __future__ import annotations

import re

try:  # PyMuPDF >= 1.24 exposes "pymupdf"; older versions only expose "fitz".
    import pymupdf as _pdf_lib
except ImportError:  # pragma: no cover - depends on the installed version
    try:
        import fitz as _pdf_lib
    except ImportError:  # pragma: no cover
        _pdf_lib = None

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB upload limit
MAX_PAGES = 30  # a resume should never need more than this


class PDFParsingError(Exception):
    """Raised when a PDF cannot be read or contains no usable text."""


def clean_extracted_text(text: str) -> str:
    """Normalise whitespace in text extracted from a PDF."""
    text = text.replace("\x00", " ").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Return the text contained in a PDF given as raw bytes.

    Raises:
        TypeError: if ``pdf_bytes`` is not bytes-like.
        PDFParsingError: if the file is empty, too large, not a valid PDF,
            password protected, or contains no extractable text (for example
            a scanned image).
    """
    if not isinstance(pdf_bytes, (bytes, bytearray)):
        raise TypeError("pdf_bytes must be bytes.")
    if len(pdf_bytes) == 0:
        raise PDFParsingError("The uploaded file is empty.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise PDFParsingError("The PDF is larger than 10 MB. Please upload a smaller file.")
    if b"%PDF" not in bytes(pdf_bytes[:1024]):
        raise PDFParsingError("This file does not look like a valid PDF.")
    if _pdf_lib is None:
        raise PDFParsingError(
            "PyMuPDF is not installed. Run: pip install -r requirements.txt"
        )

    try:
        document = _pdf_lib.open(stream=bytes(pdf_bytes), filetype="pdf")
    except Exception as exc:  # PyMuPDF raises several different error types
        raise PDFParsingError("The PDF is corrupted or could not be opened.") from exc

    try:
        if document.needs_pass:
            raise PDFParsingError("The PDF is password protected. Please remove the password.")
        if document.page_count == 0:
            raise PDFParsingError("The PDF has no pages.")

        pages = []
        for page_number in range(min(document.page_count, MAX_PAGES)):
            pages.append(document.load_page(page_number).get_text("text"))
    except PDFParsingError:
        raise
    except Exception as exc:
        raise PDFParsingError("Could not read the text from this PDF.") from exc
    finally:
        document.close()

    text = clean_extracted_text("\n".join(pages))
    if not text:
        raise PDFParsingError(
            "No text could be extracted. The PDF may be a scanned image; "
            "please upload a text-based PDF."
        )
    return text
