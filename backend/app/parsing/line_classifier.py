"""State-machine walk over reading-order lines -> ParsedReport.

Implements the algorithm from the handoff doc (section 3):
- tracks current station / current shift as it walks lines top to bottom
- most stations: bold "Name: 12 All Day" lines, recorded once per station+shift
  (exact duplicate name+qty pairs collapse naturally since we key by name)
- Sandwich Station: "Name 12 <optional note>" lines, summed across order
  blocks within the same station+shift
- "Shift N" immediately followed by "Blank" is a no-op: it does NOT change
  current_shift, so shift-overflow items keep attributing to the prior shift
- a BREAD SUMMARY section (when present) is captured separately as a
  day-total cross-check, not folded into shift-level totals

NOTE: the exact BREAD_SUMMARY_ITEM line format was not available from a real
sample PDF at the time this was written -- it's implemented as "best guess"
supporting both a bold "Name: 12" style and a plain trailing-integer style.
Re-verify/adjust against a real report once one is available (see
backend/tests/test_parsing.py for the synthetic fixture standing in for now).
"""

from __future__ import annotations

import re

SANDWICH_STATION = "Sandwich Station"

STATION_HEADER = re.compile(r"^(.+?)\s+\d{1,2}/\d{1,2}/\d{4}$")
SHIFT_LINE = re.compile(r"^Shift\s+(\d+)$")
BOLD_ITEM = re.compile(r"^(.+?):\s*(\d+)\s*All Day\s*$")
SANDWICH_ITEM = re.compile(r"^(.+?)\s+(\d+)(?:\s+.*)?$")
BREAD_SUMMARY_BOLD_ITEM = re.compile(r"^(.+?):\s*(\d+)\s*$")
BREAD_SUMMARY_PLAIN_ITEM = re.compile(r"^(.+?)\s+(\d+)\s*$")

BREAD_SUMMARY_HEADER = "BREAD SUMMARY"
SUB_ORDER_NOISE_PREFIXES = (
    "ORDER ",
    "Total Rolls",
    "Total Wraps",
    "Total Croissants",
)


def parse_lines(lines: list[str]) -> tuple[dict, dict]:
    """Walk reading-order lines and return (parsed_report, bread_summary_totals).

    parsed_report: { station: { shift_label: [ {"name", "qty"}, ... ] } }
    bread_summary_totals: { item_name: qty } -- day-total cross-check figures,
      or {} if the report has no BREAD SUMMARY section.
    """
    acc: dict[str, dict[str, dict[str, int]]] = {}
    bread_acc: dict[str, int] = {}

    current_station: str | None = None
    current_shift: str | None = None
    in_bread_summary = False

    n = len(lines)
    i = 0
    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        station_match = STATION_HEADER.match(line)
        if station_match:
            current_station = station_match.group(1).strip()
            current_shift = None
            in_bread_summary = False
            i += 1
            continue

        if line == BREAD_SUMMARY_HEADER:
            in_bread_summary = True
            i += 1
            continue

        shift_match = SHIFT_LINE.match(line)
        if shift_match:
            next_nonblank = lines[i + 1].strip() if i + 1 < n else ""
            if next_nonblank == "Blank":
                i += 2  # no-op: keep attributing to the previously active shift
                continue
            current_shift = f"Shift {shift_match.group(1)}"
            in_bread_summary = False
            i += 1
            continue

        if any(line.startswith(p) for p in SUB_ORDER_NOISE_PREFIXES):
            i += 1
            continue

        if in_bread_summary:
            m = BREAD_SUMMARY_BOLD_ITEM.match(line) or BREAD_SUMMARY_PLAIN_ITEM.match(line)
            if m:
                name = m.group(1).strip()
                qty = int(m.group(2))
                bread_acc[name] = qty
            i += 1
            continue

        if current_station is None:
            i += 1
            continue

        bold_match = BOLD_ITEM.match(line)
        if bold_match:
            name = bold_match.group(1).strip()
            qty = int(bold_match.group(2))
            shift_key = current_shift or "Unassigned"
            acc.setdefault(current_station, {}).setdefault(shift_key, {})
            acc[current_station][shift_key][name] = qty
            i += 1
            continue

        if current_station == SANDWICH_STATION:
            sandwich_match = SANDWICH_ITEM.match(line)
            if sandwich_match:
                name = sandwich_match.group(1).strip()
                qty = int(sandwich_match.group(2))
                shift_key = current_shift or "Unassigned"
                acc.setdefault(current_station, {}).setdefault(shift_key, {})
                bucket = acc[current_station][shift_key]
                bucket[name] = bucket.get(name, 0) + qty
                i += 1
                continue

        i += 1

    report = {
        station: {
            shift: [{"name": name, "qty": qty} for name, qty in items.items()]
            for shift, items in shifts.items()
        }
        for station, shifts in acc.items()
    }
    return report, bread_acc
