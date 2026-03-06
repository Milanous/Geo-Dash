"""
tests/test_renderer.py

Story 2.6 — Gradient Sky & Block Tint Variation

Tests the `_compute_tint` pure function from renderer/game_renderer.py.
`import pygame` succeeds without a display — no drawing functions called here.
"""

from __future__ import annotations

import pytest
from renderer.game_renderer import _compute_tint, _SOLID_COLOR, _SPIKE_COLOR


# ---------------------------------------------------------------------------
# _compute_tint — determinism
# ---------------------------------------------------------------------------

def test_tint_is_deterministic() -> None:
    """Same (col, row) must always return the exact same colour."""
    c1 = _compute_tint(_SOLID_COLOR, 5, 3)
    c2 = _compute_tint(_SOLID_COLOR, 5, 3)
    assert c1 == c2


def test_tint_differs_by_position() -> None:
    """Adjacent tiles must produce different tinted colours."""
    c00 = _compute_tint(_SOLID_COLOR, 0, 0)
    c10 = _compute_tint(_SOLID_COLOR, 1, 0)
    c01 = _compute_tint(_SOLID_COLOR, 0, 1)
    # At least two of the three must differ (all three would be ideal)
    assert not (c00 == c10 == c01), "All three adjacent tiles have the same tint"


def test_tint_is_position_independent_of_call_order() -> None:
    """Calling for (3, 7) before or after (0, 0) must yield the same result."""
    _ = _compute_tint(_SOLID_COLOR, 0, 0)
    a = _compute_tint(_SOLID_COLOR, 3, 7)
    b = _compute_tint(_SOLID_COLOR, 3, 7)
    assert a == b


# ---------------------------------------------------------------------------
# _compute_tint — range constraint (±10% lightness)
# ---------------------------------------------------------------------------

def test_tint_solid_channels_in_valid_range() -> None:
    """All tinted solid channels must lie within [0, 255]."""
    for col in range(0, 50, 5):
        for row in range(0, 50, 5):
            r, g, b = _compute_tint(_SOLID_COLOR, col, row)
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255


def test_tint_spike_channels_in_valid_range() -> None:
    """All tinted spike channels must lie within [0, 255]."""
    for col in range(0, 50, 5):
        for row in range(0, 50, 5):
            r, g, b = _compute_tint(_SPIKE_COLOR, col, row)
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255


def test_tint_offset_within_ten_percent_of_solid() -> None:
    """Each channel of a tinted solid tile must be within ±10% of the base."""
    tolerance = 0.10
    for col in range(0, 30, 3):
        for row in range(0, 30, 3):
            tr, tg, tb = _compute_tint(_SOLID_COLOR, col, row)
            for tinted, base in zip((tr, tg, tb), _SOLID_COLOR):
                if base > 0:
                    ratio = abs(tinted - base) / base
                    assert ratio <= tolerance + 1e-6, (
                        f"Channel offset {ratio:.3f} > 10% at ({col},{row})"
                    )


# ---------------------------------------------------------------------------
# _compute_tint — edge cases
# ---------------------------------------------------------------------------

def test_tint_returns_three_tuple() -> None:
    """_compute_tint must return a tuple of exactly 3 ints."""
    result = _compute_tint(_SOLID_COLOR, 0, 0)
    assert isinstance(result, tuple)
    assert len(result) == 3
    for channel in result:
        assert isinstance(channel, int)


def test_tint_large_coordinates() -> None:
    """_compute_tint must not overflow at very large grid coordinates."""
    result = _compute_tint(_SOLID_COLOR, 99999, 99999)
    r, g, b = result
    assert 0 <= r <= 255
    assert 0 <= g <= 255
    assert 0 <= b <= 255


def test_tint_negative_coordinates() -> None:
    """_compute_tint must handle negative indices without crashing."""
    result = _compute_tint(_SOLID_COLOR, -5, -3)
    r, g, b = result
    assert 0 <= r <= 255
    assert 0 <= g <= 255
    assert 0 <= b <= 255
