"""Shared data types for the kitchen report parser.

ParsedReport shape (plain dicts, for JSON serialization):
  { station: { shift_label: [ {"name": str, "qty": int}, ... ] } }
"""

ParsedReport = dict[str, dict[str, list[dict]]]
