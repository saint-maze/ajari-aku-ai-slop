"""Unit tests for formatting and unit utilities."""

import unittest
from sysmon_cli.units import format_bytes, format_percent, render_progress_bar


class TestUnits(unittest.TestCase):
    """Test unit conversions, human formatting, and progress bar generation."""

    def test_format_bytes_standard(self):
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(512), "512 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 1024), "1.00 TB")

    def test_format_bytes_edge_cases(self):
        # Negative numbers
        self.assertEqual(format_bytes(-1024), "-1.00 KB")
        # None and invalid inputs
        self.assertEqual(format_bytes(None), "N/A")
        self.assertEqual(format_bytes("invalid"), "N/A")
        self.assertEqual(format_bytes(float("nan")), "N/A")
        self.assertEqual(format_bytes(float("inf")), "N/A")
        self.assertEqual(format_bytes(-float("inf")), "N/A")

    def test_format_percent(self):
        self.assertEqual(format_percent(0), "0.0%")
        self.assertEqual(format_percent(50.456, precision=1), "50.5%")
        self.assertEqual(format_percent(100, precision=0), "100%")
        self.assertEqual(format_percent(None), "N/A")
        self.assertEqual(format_percent("abc"), "N/A")
        self.assertEqual(format_percent(float("nan")), "N/A")
        self.assertEqual(format_percent(float("inf")), "N/A")

    def test_render_progress_bar(self):
        bar_0 = render_progress_bar(0, width=10, fill_char="#", empty_char="-")
        self.assertEqual(bar_0, "[----------]")

        bar_50 = render_progress_bar(50, width=10, fill_char="#", empty_char="-")
        self.assertEqual(bar_50, "[#####-----]")

        bar_100 = render_progress_bar(100, width=10, fill_char="#", empty_char="-")
        self.assertEqual(bar_100, "[##########]")

        # Boundary clamping
        bar_neg = render_progress_bar(-10, width=10, fill_char="#", empty_char="-")
        self.assertEqual(bar_neg, "[----------]")

        bar_over = render_progress_bar(150, width=10, fill_char="#", empty_char="-")
        self.assertEqual(bar_over, "[##########]")

        # NaN, Inf, and None
        bar_nan = render_progress_bar(float("nan"), width=10, fill_char="#", empty_char="-")
        self.assertEqual(bar_nan, "[----------]")

        bar_none = render_progress_bar(None, width=10, fill_char="#", empty_char="-")
        self.assertEqual(bar_none, "[----------]")

        bar_inf = render_progress_bar(float("inf"), width=10, fill_char="#", empty_char="-")
        self.assertEqual(bar_inf, "[----------]")

        # Zero and negative width
        self.assertEqual(render_progress_bar(50, width=0), "[]")
        self.assertEqual(render_progress_bar(50, width=-5), "[]")


if __name__ == "__main__":
    unittest.main()
