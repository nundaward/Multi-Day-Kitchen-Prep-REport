import io

from app.parsing import parse_pdf

from .fixtures import build_bold_item_station_pdf, build_sandwich_station_pdf


def test_sandwich_station_full_pipeline():
    pdf_bytes = build_sandwich_station_pdf()
    report, bread_summary = parse_pdf(io.BytesIO(pdf_bytes))

    station = report["Sandwich Station"]

    # Shift 1: two order blocks of the same item should sum (5 + 3 = 8)
    assert station["Shift 1"] == [{"name": "Turkey Club", "qty": 8}]

    # Shift 2: "Shift 3" immediately followed by "Blank" must not move the
    # active shift, so the overflow item on page 2 still lands in Shift 2
    # (4 + 2 = 6), and Shift 4 (a real, non-blank shift change) gets its own item.
    assert station["Shift 2"] == [{"name": "Ham Swiss", "qty": 6}]
    assert station["Shift 4"] == [{"name": "Club Wrap", "qty": 7}]

    # No stray "Shift 3" bucket should exist at all -- it was a no-op.
    assert "Shift 3" not in station

    # The duplicated second pass (page 4) must be discarded by page-dedupe,
    # so totals must NOT be doubled (e.g. Turkey Club must be 8, not 16).
    all_qtys = {item["name"]: item["qty"] for shift in station.values() for item in shift}
    assert all_qtys == {"Turkey Club": 8, "Ham Swiss": 6, "Club Wrap": 7}

    # Cross-check against the Bread Summary ground-truth totals (doc section 2.5).
    assert bread_summary == {"Turkey Club": 8, "Ham Swiss": 6, "Club Wrap": 7}
    for name, total in bread_summary.items():
        summed = sum(
            item["qty"]
            for shift_items in station.values()
            for item in shift_items
            if item["name"] == name
        )
        assert summed == total, f"{name}: shift-summed qty {summed} != Bread Summary {total}"


def test_bold_item_station_and_column_split():
    pdf_bytes = build_bold_item_station_pdf()
    report, _ = parse_pdf(io.BytesIO(pdf_bytes))

    station = report["Salad Station"]

    # Exact duplicate bold-item line should collapse to one entry, not two.
    assert station["Shift 1"] == [{"name": "Caesar Salad", "qty": 12}]

    # Right-column shift assignment must be read after the full left column,
    # not interleaved by raw top-to-bottom document order.
    assert station["Shift 2"] == [{"name": "Cobb Salad", "qty": 9}]
