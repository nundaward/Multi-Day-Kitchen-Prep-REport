"""Builds a synthetic kitchen-report PDF that exercises every parsing quirk
from the handoff doc, since no real sample PDF was available when this was
written:

  - two-column "snake" layout (station header/shift 1 in the left column,
    shift 2 starting in the right column of the same page)
  - glued item-name/quantity pairs with no literal space character but a
    real positional gap (drawn as two separate text-show operators)
  - a "Shift 3" / "Blank" pair that must NOT change the active shift, so a
    later overflow item still attributes to the previous shift
  - a BREAD SUMMARY day-total section for cross-checking
  - the whole report duplicated as a second pass, to exercise page dedup

Re-verify this fixture's assumptions (e.g. exact BREAD SUMMARY line format,
whether headers can span both columns) against a real report once one is
available -- see the NOTE in app/parsing/line_classifier.py.
"""

import io

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas as rl_canvas

FONT = "Helvetica"
SIZE = 10

LEFT_X = 50
RIGHT_X = 330  # page width is 612 -> mid_x = 306, so this is safely in the right half


def _draw_tokens(c, x, y, tokens):
    """tokens: list of (text, gap_before_pt). Draws tokens left to right as
    separate text-show calls, simulating a positional gap with no literal
    space character between them."""
    cur_x = x
    for text, gap in tokens:
        cur_x += gap
        c.drawString(cur_x, y, text)
        cur_x += c.stringWidth(text, FONT, SIZE)


def _draw_glued_item(c, x, y, name, qty, gap=2.5):
    _draw_tokens(c, x, y, [(name, 0), (str(qty), gap)])


def build_sandwich_station_pdf() -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=LETTER)
    c.setFont(FONT, SIZE)

    # --- Page 1: header + Shift 1 (left column), Shift 2 start + Blank Shift 3 (right column)
    c.drawString(LEFT_X, 750, "Sandwich Station 9/14/2026")
    c.drawString(LEFT_X, 700, "Shift 1")
    _draw_glued_item(c, LEFT_X, 650, "Turkey Club", 5)
    _draw_glued_item(c, LEFT_X, 600, "Turkey Club", 3)  # second order block, should sum to 8

    c.drawString(RIGHT_X, 750, "Shift 2")
    _draw_glued_item(c, RIGHT_X, 700, "Ham Swiss", 4)
    c.drawString(RIGHT_X, 650, "Shift 3")
    c.drawString(RIGHT_X, 600, "Blank")  # must NOT change current_shift away from Shift 2
    c.showPage()

    # --- Page 2: overflow item (still Shift 2), then a real Shift 4
    c.setFont(FONT, SIZE)
    _draw_glued_item(c, LEFT_X, 750, "Ham Swiss", 2)  # overflow -> should add to Shift 2 (4+2=6)

    c.drawString(RIGHT_X, 750, "Shift 4")
    _draw_glued_item(c, RIGHT_X, 700, "Club Wrap", 7)
    c.showPage()

    # --- Page 3: Bread Summary day totals (ground truth for cross-check)
    c.setFont(FONT, SIZE)
    c.drawString(LEFT_X, 750, "BREAD SUMMARY")
    c.drawString(LEFT_X, 700, "Turkey Club: 8")
    c.drawString(LEFT_X, 650, "Ham Swiss: 6")
    c.drawString(LEFT_X, 600, "Club Wrap: 7")
    c.showPage()

    # --- Page 4+: duplicate pass (should be discarded entirely by dedupe_pages)
    c.setFont(FONT, SIZE)
    c.drawString(LEFT_X, 750, "Sandwich Station 9/14/2026")
    c.drawString(LEFT_X, 700, "Shift 1")
    _draw_glued_item(c, LEFT_X, 650, "Turkey Club", 5)
    _draw_glued_item(c, LEFT_X, 600, "Turkey Club", 3)
    c.showPage()

    c.save()
    return buf.getvalue()


def build_bold_item_station_pdf() -> bytes:
    """A simpler, non-Sandwich station using the "Name: 12 All Day" bold-item
    format, split across a Shift 1 (left column) / Shift 2 (right column)
    on a single page -- exercises column split + BOLD_ITEM independent of
    the sandwich accumulation / Blank-shift / dedupe machinery."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=LETTER)
    c.setFont(FONT, SIZE)

    c.drawString(LEFT_X, 750, "Salad Station 9/14/2026")
    c.drawString(LEFT_X, 700, "Shift 1")
    c.drawString(LEFT_X, 650, "Caesar Salad: 12 All Day")
    c.drawString(LEFT_X, 600, "Caesar Salad: 12 All Day")  # exact duplicate print, should collapse

    c.drawString(RIGHT_X, 750, "Shift 2")
    c.drawString(RIGHT_X, 700, "Cobb Salad: 9 All Day")
    c.showPage()

    c.save()
    return buf.getvalue()
