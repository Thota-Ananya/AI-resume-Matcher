"""Tiny dependency-free PDF writer.

Used to create ``sample_data/sample_resume.pdf`` and PDF fixtures for the tests.
Run ``python -m src.sample_pdf`` from the project root to regenerate the sample.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

_REPLACEMENTS = {"\u2022": "-", "\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'",
                 "\u201c": '"', "\u201d": '"'}


def _escape(line: str) -> bytes:
    for old, new in _REPLACEMENTS.items():
        line = line.replace(old, new)
    data = line.encode("latin-1", errors="replace")
    return data.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def build_simple_pdf(text: str, font_size: int = 10, wrap: int = 95, lines_per_page: int = 52) -> bytes:
    """Create a simple text PDF (Helvetica, US Letter). Empty text gives a blank page."""
    lines: list[str] = []
    for raw in text.splitlines():
        lines.extend(textwrap.wrap(raw, wrap) or [""])
    pages = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)] or [[]]

    leading = font_size + 3
    bodies: list[bytes] = [b"", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    kids = []
    for index, page_lines in enumerate(pages):
        page_obj, content_obj = 4 + 2 * index, 5 + 2 * index
        kids.append(f"{page_obj} 0 R")
        bodies.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_obj} 0 R >>".encode()
        )
        if page_lines:
            parts = [f"BT /F1 {font_size} Tf {leading} TL 54 738 Td".encode()]
            for line in page_lines:
                parts.append(b"(" + _escape(line) + b") Tj T*")
            parts.append(b"ET")
            stream = b"\n".join(parts)
        else:
            stream = b""
        bodies.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    bodies[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    bodies[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>".encode()

    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(bodies, start=1):
        offsets.append(len(output))
        output += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_position = len(output)
    output += f"xref\n0 {len(bodies) + 1}\n".encode() + b"0000000000 65535 f \n"
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n".encode()
    output += f"trailer\n<< /Size {len(bodies) + 1} /Root 1 0 R >>\nstartxref\n{xref_position}\n%%EOF\n".encode()
    return bytes(output)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent / "sample_data"
    source = (root / "sample_resume.txt").read_text(encoding="utf-8")
    target = root / "sample_resume.pdf"
    target.write_bytes(build_simple_pdf(source))
    print(f"Created {target}")
