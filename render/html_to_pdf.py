#!/usr/bin/env python3
"""Convert EAC report HTML to PDF using WeasyPrint.

Pure Python, no browser dependency. Produces smaller PDFs (~250KB vs ~2MB).

Usage:
    python render/html_to_pdf.py output/domain/eac-audit-2026-05-25.html
    python render/html_to_pdf.py output/domain/eac-audit-2026-05-25.html --output report.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import weasyprint


def html_to_pdf(
    html_path: str | Path,
    pdf_path: str | Path | None = None,
) -> Path:
    html_path = Path(html_path).resolve()
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    if pdf_path is None:
        pdf_path = html_path.with_suffix(".pdf")
    else:
        pdf_path = Path(pdf_path).resolve()

    doc = weasyprint.HTML(filename=str(html_path))
    doc.write_pdf(str(pdf_path))

    print(f"PDF generated: {pdf_path} ({pdf_path.stat().st_size / 1024:.0f} KB)")
    return pdf_path


def main():
    parser = argparse.ArgumentParser(description="Convert EAC report HTML to PDF")
    parser.add_argument("html_path", help="Path to the HTML report file")
    parser.add_argument("--output", "-o", help="Output PDF path (default: same name with .pdf)")
    args = parser.parse_args()

    pdf_path = html_to_pdf(args.html_path, args.output)
    print(f"Done: {pdf_path}")


if __name__ == "__main__":
    main()
