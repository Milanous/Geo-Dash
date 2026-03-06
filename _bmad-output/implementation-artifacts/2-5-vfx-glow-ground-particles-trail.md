# Story 2.5: VFX — Glow, Ground Particles & Trail

Status: review

## Story

As a player,
I want visual effects around my character (glow, particles on landing, movement trail),
so that the game feels polished and satisfying.

## Acceptance Criteria

1. **Given** `renderer/vfx.py` exists with `VFXSystem` **When** `vfx_system.update(player_state, dt)` is called **Then** the trail deque records the last ~30 player positions ✅
2. **And** particles created by `on_land()` are updated (position, lifetime decreasing) ✅
3. **When** `vfx_system.draw(surface, camera_offset)` is called **Then** the trail is drawn as a gradient line white (head) → grey (tail) ✅
4. **And** active particles are drawn as small filled circles, fading as lifetime decreases ✅
5. **And** a soft glow/bloom halo is drawn using a semi-transparent SRCALPHA surface ✅
6. **When** `PlayerState.on_ground` transitions from `False` to `True` **Then** `on_land()` is called automatically, spawning ≥5 particles ✅
7. **And** `VFXSystem` never imports from `engine/player.py` directly ✅

## Tasks / Subtasks

- [x] Task 1 — `renderer/vfx.py` : VFXSystem avec import pygame paresseux (dans draw() seulement)
  - [x] 1.1 `_Particle` dataclass (world-space blocks, velocity, lifetime)
  - [x] 1.2 `update(player_state, dt)` — trail, détection atterrissage, expiry particules
  - [x] 1.3 `on_land(bx, by)` — burst de `_PARTICLE_COUNT=8` particules
  - [x] 1.4 `reset()` — clear trail + particules + `_was_on_ground=True`
  - [x] 1.5 `draw(surface, camera_offset_px)` — glow + trail gradient + particules
- [x] Task 2 — `ui/play_scene.py` : intégration VFXSystem
  - [x] 2.1 Import `VFXSystem`
  - [x] 2.2 `self._vfx = VFXSystem()` dans `__init__`
  - [x] 2.3 `self._vfx.reset()` lors du reset joueur dans `update()`
  - [x] 2.4 `self._vfx.update(self._player.state, dt)` à chaque step
  - [x] 2.5 `self._vfx.draw(surface, self._camera.x_offset)` à chaque frame
- [x] Task 3 — `tests/test_vfx.py` : 12 tests headless
  - [x] 3.1 Trail : vide à l'init, croît avec les updates, plafonné à maxlen=30
  - [x] 3.2 on_land : ≥5 particules, exactement _PARTICLE_COUNT=8
  - [x] 3.3 Transition atterrissage automatique (False→True)
  - [x] 3.4 Pas de particules si grounded en continu ou airborne en continu
  - [x] 3.5 Expiry : toutes les particules meurent après _PARTICLE_LIFETIME
  - [x] 3.6 reset() : nettoie trail + particules + prévient faux atterrissage
  - [x] 3.7 Guard : vfx.py n'importe pas engine.player

## Dev Notes

### Design decisions
- **Lazy pygame import** : `import pygame` est placé à l'intérieur de `draw()` et `_draw_glow()` uniquement. Le reste du module est headless-safe, permettant des tests unitaires sans display.
- **Particules en world-space** : positions en blocs, converties en pixels dans `draw()`. Évite les problèmes de drift avec le mouvement de caméra.
- **Glow dessiné en premier** (`draw()` avant `renderer.draw_player`) : le halo semi-transparent est visible sous le joueur. Dans l'implémentation actuelle, `vfx.draw()` est appelé APRÈS `renderer.draw()` dans PlayScene → glow s'affiche par-dessus (visuellement acceptable avec alpha=35 max).

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot — Amelia)

### Completion Notes List
- `renderer/vfx.py` créé ex-nihilo — 165 lignes
- `ui/play_scene.py` : import, init, reset, update, draw (5 modifications)
- `tests/test_vfx.py` créé — 12 tests headless tous passants

### File List
- `renderer/vfx.py` (nouveau)
- `ui/play_scene.py`
- `tests/test_vfx.py` (nouveau)

### Change Log
- 2026-03-05: Story 2.5 implémentée — 123 tests passing (111 → 123, +12)
