"""Utility functions for unit formatting and rendering."""

import math
from typing import Union


def format_bytes(num_bytes: Union[int, float], precision: int = 2) -> str:
    """Convert bytes into human-readable string (B, KB, MB, GB, TB, PB)."""
    if num_bytes is None:
        return "N/A"
    try:
        val = float(num_bytes)
        if math.isnan(val) or math.isinf(val):
            return "N/A"
    except (ValueError, TypeError):
        return "N/A"

    if val < 0:
        return f"-{format_bytes(-val, precision)}"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    while val >= 1024.0 and unit_index < len(units) - 1:
        val /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f"{int(val)} B"
    return f"{val:.{precision}f} {units[unit_index]}"


def format_percent(percent: Union[int, float], precision: int = 1) -> str:
    """Format float percentage into string."""
    if percent is None:
        return "N/A"
    try:
        val = float(percent)
        if math.isnan(val) or math.isinf(val):
            return "N/A"
        return f"{val:.{precision}f}%"
    except (ValueError, TypeError):
        return "N/A"


def render_progress_bar(
    percent: Union[int, float],
    width: int = 20,
    fill_char: str = "|",
    empty_char: str = " ",
) -> str:
    """Render a text progress bar: [||||||              ]."""
    if width <= 0:
        return "[]"
    if percent is None:
        return f"[{empty_char * width}]"
    try:
        val = float(percent)
        if math.isnan(val) or math.isinf(val):
            return f"[{empty_char * width}]"
        pct = max(0.0, min(100.0, val))
        filled_len = int(round(width * (pct / 100.0)))
    except (ValueError, TypeError):
        return f"[{empty_char * width}]"

    empty_len = max(0, width - filled_len)
    return f"[{fill_char * filled_len}{empty_char * empty_len}]"
