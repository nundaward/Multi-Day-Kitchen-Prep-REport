"""Kitchen report PDF parsing pipeline.

parse_pdf(path_or_file) -> (parsed_report, bread_summary_totals)
"""

import pdfplumber

from .column_split import page_to_reading_order_lines
from .dedupe_pages import dedupe_pages
from .line_classifier import parse_lines


def parse_pdf(file) -> tuple[dict, dict]:
    """Parse one kitchen report PDF (path or file-like object).

    Returns (parsed_report, bread_summary_totals) -- see line_classifier.parse_lines.
    """
    with pdfplumber.open(file) as pdf:
        pages_lines = [page_to_reading_order_lines(page) for page in pdf.pages]

    deduped_pages = dedupe_pages(pages_lines)
    all_lines = [line for page_lines in deduped_pages for line in page_lines]
    return parse_lines(all_lines)
