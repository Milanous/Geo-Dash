"""
tests/test_save_dialog.py — Headless tests for ui/save_dialog.py (Story 6.1).

All tests run WITHOUT a pygame display. SaveDialog must support headless
instantiation (lazy pygame resource init).
"""

from __future__ import annotations

import pygame
import pytest

from ui.save_dialog import SaveDialog


# ---------------------------------------------------------------------------
# Task 5.1 — SaveDialog instantiates without display
# ---------------------------------------------------------------------------

def test_save_dialog_instantiates_headless() -> None:
    """SaveDialog() must not crash without a pygame display."""
    dialog = SaveDialog()
    assert dialog is not None


# ---------------------------------------------------------------------------
# Task 5.2 — update(KEYDOWN Enter) returns typed name
# ---------------------------------------------------------------------------

def test_save_dialog_enter_returns_name() -> None:
    dialog = SaveDialog()
    dialog._text = "my_level"  # simulate typed text

    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0)
    result = dialog.update(event)
    assert result == "my_level"


# ---------------------------------------------------------------------------
# Task 5.3 — update(KEYDOWN ESC) returns False
# ---------------------------------------------------------------------------

def test_save_dialog_esc_returns_false() -> None:
    dialog = SaveDialog()

    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="", mod=0)
    result = dialog.update(event)
    assert result is False
