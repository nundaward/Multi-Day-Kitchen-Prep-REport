"""Unit tests for the low-level char-gap word splitting, independent of any PDF."""

from app.parsing.column_split import Char, cluster_into_lines, split_line_into_words


def make_chars(specs, top=100.0):
    """specs: list of (text, x0, x1)."""
    return [Char(text=t, x0=x0, x1=x1, top=top) for t, x0, x1 in specs]


def test_split_line_into_words_normal_spacing():
    # "AB CD" with a real space char, ordinary small gaps throughout
    chars = make_chars(
        [
            ("A", 0.0, 5.0),
            ("B", 5.0, 10.0),
            (" ", 10.0, 12.0),
            ("C", 12.0, 17.0),
            ("D", 17.0, 22.0),
        ]
    )
    words = split_line_into_words(chars, gap_threshold=1.2)
    assert words == ["AB CD"]


def test_split_line_into_words_glued_number_no_space_char():
    # "San" immediately followed by "10" with NO space character between them,
    # but a visual gap (2.5pt) larger than the threshold -- the exact bug
    # described in the handoff doc.
    chars = make_chars(
        [
            ("S", 0.0, 5.0),
            ("a", 5.0, 10.0),
            ("n", 10.0, 15.0),
            ("1", 17.5, 22.0),  # gap of 2.5pt from previous char's x1=15.0
            ("0", 22.0, 27.0),
        ]
    )
    words = split_line_into_words(chars, gap_threshold=1.2)
    assert words == ["San", "10"]


def test_split_line_into_words_gap_below_threshold_does_not_split():
    chars = make_chars(
        [
            ("a", 0.0, 5.0),
            ("b", 5.6, 10.0),  # 0.6pt gap, clearly under the 1.2pt threshold
        ]
    )
    words = split_line_into_words(chars, gap_threshold=1.2)
    assert words == ["ab"]


def test_cluster_into_lines_groups_by_top_tolerance():
    chars = make_chars([("A", 0, 5), ("B", 5, 10)], top=100.0) + make_chars(
        [("C", 0, 5), ("D", 5, 10)], top=101.5
    ) + make_chars([("E", 0, 5)], top=110.0)

    lines = cluster_into_lines(chars, top_tolerance=2.5)
    assert len(lines) == 2
    assert [c.text for c in lines[0]] == ["A", "B", "C", "D"]
    assert [c.text for c in lines[1]] == ["E"]
