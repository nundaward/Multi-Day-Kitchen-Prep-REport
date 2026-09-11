"""Detect and drop the repeated second pass through the report.

Both source PDFs in the reference reports had every station printed twice,
back-to-back (page N repeats verbatim at some later page). This scans each
page's reading-order lines for a station-header line, then truncates the
page list right before the *first* station header repeats -- i.e. keeps
pages up through the end of the first full pass only.
"""

from __future__ import annotations

from .line_classifier import STATION_HEADER


def first_station_header(lines: list[str]) -> str | None:
    for line in lines:
        m = STATION_HEADER.match(line.strip())
        if m:
            return m.group(1).strip()
    return None


def dedupe_pages(pages_lines: list[list[str]]) -> list[list[str]]:
    """Given per-page reading-order lines, drop pages from the repeated pass.

    pages_lines: one list of lines per page, in document order.
    Returns the subset of pages belonging to the first full pass.
    """
    headers = [first_station_header(lines) for lines in pages_lines]

    first_header = next((h for h in headers if h is not None), None)
    if first_header is None:
        return pages_lines

    first_index = headers.index(first_header)
    repeat_index = None
    for idx in range(first_index + 1, len(headers)):
        if headers[idx] == first_header:
            repeat_index = idx
            break

    if repeat_index is None:
        return pages_lines

    return pages_lines[:repeat_index]
