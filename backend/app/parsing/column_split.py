"""Reconstruct correct reading-order lines from a two-column "snake" layout page.

Kitchen report pages lay each station's shift data out in two print columns.
Reading top-to-bottom/left-to-right in raw document order interleaves rows
from both columns. This module splits characters by x-position into left/right
halves, clusters them into visual lines, and joins characters into words using
a horizontal-gap threshold (since some item/quantity pairs have no literal
space character between them, e.g. "San10").
"""

from dataclasses import dataclass

GAP_THRESHOLD = 1.2  # pt; gap between chars beyond which a new "word" starts
LINE_TOP_TOLERANCE = 2.5  # pt; chars within this vertical band are one line


@dataclass
class Char:
    text: str
    x0: float
    x1: float
    top: float


def chars_from_page(page) -> list[Char]:
    """Extract pdfplumber page.chars into our lightweight Char records."""
    return [
        Char(text=c["text"], x0=c["x0"], x1=c["x1"], top=c["top"])
        for c in page.chars
    ]


def split_columns(chars: list[Char], page_width: float) -> tuple[list[Char], list[Char]]:
    mid_x = page_width / 2
    left = [c for c in chars if c.x0 < mid_x]
    right = [c for c in chars if c.x0 >= mid_x]
    return left, right


def cluster_into_lines(chars: list[Char], top_tolerance: float = LINE_TOP_TOLERANCE) -> list[list[Char]]:
    """Group chars into visual rows by proximity of their 'top' coordinate."""
    if not chars:
        return []

    ordered = sorted(chars, key=lambda c: (c.top, c.x0))
    lines: list[list[Char]] = []
    current: list[Char] = [ordered[0]]
    current_top = ordered[0].top

    for c in ordered[1:]:
        if abs(c.top - current_top) <= top_tolerance:
            current.append(c)
        else:
            lines.append(current)
            current = [c]
            current_top = c.top
    lines.append(current)

    # within each line, chars must read left-to-right; sort by top first so
    # that if two visually-distinct rows land in the same tolerance bucket
    # (both close to the bucket's anchor top), rows don't get interleaved by
    # column position
    for line in lines:
        line.sort(key=lambda c: (c.top, c.x0))

    return lines


def split_line_into_words(line: list[Char], gap_threshold: float = GAP_THRESHOLD) -> list[str]:
    """Split a line of chars into words based on horizontal gaps.

    A new word starts whenever the gap between the end of the previous char
    and the start of the next exceeds gap_threshold -- this is what catches
    glued item-name/quantity pairs like "San10" (no literal space) using the
    same visual gap that separates ordinary words.
    """
    if not line:
        return []

    words: list[str] = []
    current = line[0].text
    prev_x1 = line[0].x1

    for c in line[1:]:
        gap = c.x0 - prev_x1
        if gap > gap_threshold:
            words.append(current)
            current = c.text
        else:
            current += c.text
        prev_x1 = c.x1

    words.append(current)
    return words


def page_to_reading_order_lines(page) -> list[str]:
    """Full pipeline: page -> ordered list of text lines in reading order."""
    chars = chars_from_page(page)
    left_chars, right_chars = split_columns(chars, page.width)

    left_lines = cluster_into_lines(left_chars)
    right_lines = cluster_into_lines(right_chars)

    result: list[str] = []
    for line in left_lines + right_lines:
        words = split_line_into_words(line)
        text = " ".join(words).strip()
        if text:
            result.append(text)
    return result
