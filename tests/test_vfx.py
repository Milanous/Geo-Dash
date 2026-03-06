"""
tests/test_vfx.py

Story 2.5 — VFX: Glow, Ground Particles & Trail

Headless — never imports pygame.  VFXSystem uses lazy pygame imports inside
draw() only, so update()/on_land()/reset() are safe to call without a display.
"""

from __future__ import annotations

import pytest
from engine.physics import DT, PlayerState
from renderer.vfx import VFXSystem, _TRAIL_MAXLEN, _PARTICLE_COUNT, _PARTICLE_LIFETIME


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(on_ground: bool = True, x: float = 5.0, y: float = 0.0) -> PlayerState:
    return PlayerState(x=x, y=y, vy=0.0, on_ground=on_ground, angle=0.0)


# ---------------------------------------------------------------------------
# Trail
# ---------------------------------------------------------------------------

def test_trail_empty_at_init() -> None:
    """Trail must be empty before any update."""
    vfx = VFXSystem()
    assert vfx.trail_length == 0


def test_trail_grows_with_updates() -> None:
    """After N updates, trail must contain N entries (while N ≤ maxlen)."""
    vfx = VFXSystem()
    state = _make_state()
    for i in range(10):
        vfx.update(state, DT)
    assert vfx.trail_length == 10


def test_trail_capped_at_maxlen() -> None:
    """Trail must never exceed _TRAIL_MAXLEN entries."""
    vfx = VFXSystem()
    state = _make_state()
    for _ in range(_TRAIL_MAXLEN + 20):
        vfx.update(state, DT)
    assert vfx.trail_length == _TRAIL_MAXLEN


# ---------------------------------------------------------------------------
# on_land / particle spawning
# ---------------------------------------------------------------------------

def test_on_land_spawns_particles() -> None:
    """on_land() must create a burst of at least 5 particles."""
    vfx = VFXSystem()
    assert vfx.particle_count == 0
    vfx.on_land(5.0, 0.0)
    assert vfx.particle_count >= 5


def test_on_land_spawns_exact_particle_count() -> None:
    """on_land() must spawn exactly _PARTICLE_COUNT particles."""
    vfx = VFXSystem()
    vfx.on_land(0.0, 0.0)
    assert vfx.particle_count == _PARTICLE_COUNT


def test_landing_transition_auto_triggers_on_land() -> None:
    """Transition on_ground False→True must automatically call on_land."""
    vfx = VFXSystem()
    # First update: player is in the air
    vfx.update(_make_state(on_ground=False), DT)
    assert vfx.particle_count == 0
    # Second update: player lands
    vfx.update(_make_state(on_ground=True), DT)
    assert vfx.particle_count == _PARTICLE_COUNT


def test_no_spurious_particles_when_staying_grounded() -> None:
    """No particles must appear when the player stays on the ground."""
    vfx = VFXSystem()
    for _ in range(10):
        vfx.update(_make_state(on_ground=True), DT)
    assert vfx.particle_count == 0


def test_no_spurious_particles_when_staying_airborne() -> None:
    """No particles must appear while the player stays in the air."""
    vfx = VFXSystem()
    for _ in range(10):
        vfx.update(_make_state(on_ground=False), DT)
    assert vfx.particle_count == 0


# ---------------------------------------------------------------------------
# Particle lifetime / expiry
# ---------------------------------------------------------------------------

def test_particles_expire_over_time() -> None:
    """All particles must expire after _PARTICLE_LIFETIME seconds."""
    vfx = VFXSystem()
    vfx.on_land(5.0, 0.0)
    assert vfx.particle_count > 0

    # Advance time well past _PARTICLE_LIFETIME
    steps = int(_PARTICLE_LIFETIME / DT) + 10
    state = _make_state()
    for _ in range(steps):
        vfx.update(state, DT)

    assert vfx.particle_count == 0


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------

def test_reset_clears_trail_and_particles() -> None:
    """reset() must wipe the trail and all particles."""
    vfx = VFXSystem()
    state = _make_state()
    for _ in range(20):
        vfx.update(state, DT)
    vfx.on_land(5.0, 0.0)

    vfx.reset()

    assert vfx.trail_length == 0
    assert vfx.particle_count == 0


def test_reset_prevents_spurious_landing_on_next_update() -> None:
    """After reset(), a grounded update must NOT trigger a landing burst."""
    vfx = VFXSystem()
    # Player was airborne → reset → now on_ground
    vfx.update(_make_state(on_ground=False), DT)
    vfx.reset()
    vfx.update(_make_state(on_ground=True), DT)
    # _was_on_ground is reset to True, so no False→True transition
    assert vfx.particle_count == 0


# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------

def test_vfx_does_not_import_engine_player() -> None:
    """renderer.vfx must never import engine.player directly."""
    import renderer.vfx as vfx_mod
    assert not hasattr(vfx_mod, "Player"), (
        "renderer/vfx.py must not import Player from engine.player"
    )
