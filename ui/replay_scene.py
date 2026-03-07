"""
ui/replay_scene.py — Best-agent replay scene (Story 5.6).

Scans data/brains/ for gen_NNN_best.json files, lets the user pick a
generation, then replays the best brain at 60 FPS with neuron debug overlay.

Import rules: ui/ may import ai/, engine/, renderer/, pygame.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pygame

from ai.brain import Brain
from engine.camera import Camera
from engine.player import Player
from engine.world import TileType, World
from renderer.game_renderer import GameRenderer
from ui.scene import Scene

# ── Visual constants ──────────────────────────────────────────────────
_BG_COLOR = (15, 15, 25)
_TEXT_COLOR = (220, 220, 220)
_SELECTED_COLOR = (90, 60, 180)
_TITLE_COLOR = (255, 255, 255)
_SUBTITLE_COLOR = (180, 170, 210)
_HINT_COLOR = (140, 140, 160)
_ACCENT_COLOR = (160, 100, 255)       # Purple accent for replay theme
_PANEL_BG = (22, 18, 35)
_PANEL_BORDER = (50, 40, 80)
_ENTRY_BG = (28, 22, 42)
_LINE_HEIGHT = 44
_TITLE_Y = 30
_LIST_TOP = 120
_HINT_BAR_H = 50

_START_X: float = 5.0
_START_Y: float = 5.0

_NEURON_RADIUS: int = 4
_NEURON_GREEN = (0, 255, 0)
_NEURON_RED = (255, 0, 0)
_HUB_RADIUS: int = 7
_HUB_GLOW_RADIUS: int = 14
_HUB_OFF_COLOR = (80, 80, 80)
_NETWORK_COLORS = [
    (0, 201, 255),    # Cyan
    (255, 160, 0),    # Orange
    (200, 80, 255),   # Purple
    (255, 255, 0),    # Yellow
    (0, 255, 180),    # Teal
    (255, 80, 120),   # Pink
]
_NETWORK_LINE_ALPHA: int = 80
_NETWORK_LINE_WIDTH: int = 1
_JUMP_GLOW_COLOR = (255, 255, 100)
_JUMP_GLOW_RADIUS: int = 20
_JUMP_GLOW_DURATION: float = 0.1

_GEN_PATTERN = re.compile(r"^gen_(\d+)_best\.json$")

_DEFAULT_BRAINS_DIR: str = "data/brains"


class ReplayScene(Scene):
    """Best-agent replay: generation selector + single-brain simulation."""

    def __init__(
        self,
        world: World,
        return_scene: Scene | None = None,
        brains_dir: str = _DEFAULT_BRAINS_DIR,
        auto_gen: int | None = None,
    ) -> None:
        super().__init__()
        self._world = world
        self._return_scene = return_scene
        self._brains_dir = brains_dir
        self._generations = self._scan_generations()
        self._selected_idx: int = 0

        # Runtime state (set when a generation is selected)
        self._brain: Brain | None = None
        self._player: Player | None = None
        self._camera: Camera | None = None
        self._renderer: GameRenderer | None = None
        self._current_gen: int | None = None
        self._prev_should_jump: bool = False

        # Jump glow timer
        self._glow_timer: float = 0.0

        # Lazy fonts
        self._font: pygame.font.Font | None = None
        self._title_font: pygame.font.Font | None = None
        self._hint_font: pygame.font.Font | None = None

        # Auto-load a specific generation (e.g. when coming from training)
        if auto_gen is not None:
            self._load_gen(auto_gen)
            if auto_gen in self._generations:
                self._selected_idx = self._generations.index(auto_gen)

    # ------------------------------------------------------------------
    # Generation scanning
    # ------------------------------------------------------------------

    def _scan_generations(self) -> list[int]:
        """Return sorted list of generation numbers found in brains_dir."""
        folder = Path(self._brains_dir)
        if not folder.is_dir():
            return []
        gens: list[int] = []
        for f in folder.iterdir():
            m = _GEN_PATTERN.match(f.name)
            if m:
                gens.append(int(m.group(1)))
        gens.sort()
        return gens

    # ------------------------------------------------------------------
    # Brain loading
    # ------------------------------------------------------------------

    def _load_gen(self, gen_num: int) -> None:
        """Load brain for *gen_num* and reset player / camera."""
        path = Path(self._brains_dir) / f"gen_{gen_num:03d}_best.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._brain = Brain.from_json(data)
            self._player = Player(start_x=_START_X, start_y=_START_Y)
            self._camera = Camera()
            self._renderer = GameRenderer()
            self._current_gen = gen_num
            self._glow_timer = 0.0
            self._prev_should_jump = False
        except (ValueError, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading {path.name}: {e}")
            self._brain = None

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._brain is not None:
                        # If replaying → back to gen selector
                        self._brain = None
                        self._player = None
                        self._camera = None
                        self._renderer = None
                        self._current_gen = None
                        return True
                    # If on selector → return to caller
                    if self._return_scene is not None:
                        self.next_scene = self._return_scene
                        return True
                    return False

                if event.key == pygame.K_r and self._current_gen is not None:
                    self._load_gen(self._current_gen)
                    return True

                # Selector mode
                if self._brain is None:
                    if event.key == pygame.K_UP and self._selected_idx > 0:
                        self._selected_idx -= 1
                    elif (
                        event.key == pygame.K_DOWN
                        and self._selected_idx < len(self._generations) - 1
                    ):
                        self._selected_idx += 1
                    elif event.key == pygame.K_RETURN and self._generations:
                        self._load_gen(self._generations[self._selected_idx])

        return True

    def update(self, dt: float) -> None:
        if self._brain is None or self._player is None or self._camera is None:
            return

        if not self._player.alive or self._player.state.finished:
            return

        # Evaluate brain and trigger jump
        should = self._brain.should_jump(
            self._player.state.x, self._player.state.y, self._world,
        )

        # Trigger glow on rising edge (False -> True) regardless of on_ground
        if should and not self._prev_should_jump:
            self._glow_timer = _JUMP_GLOW_DURATION
        self._prev_should_jump = should

        if should and self._player.state.on_ground:
            self._player.jump()

        self._player.update(dt, self._world)
        self._camera.follow(self._player.state.x)

        # Tick glow timer
        if self._glow_timer > 0.0:
            self._glow_timer -= dt

    def draw(self, surface: pygame.Surface) -> None:
        if self._brain is None:
            self._draw_selector(surface)
        else:
            self._draw_replay(surface)

    # ------------------------------------------------------------------
    # Selector drawing
    # ------------------------------------------------------------------

    def _draw_selector(self, surface: pygame.Surface) -> None:
        surface.fill(_BG_COLOR)
        sw = surface.get_width()
        sh = surface.get_height()

        if self._font is None:
            self._font = pygame.font.Font(None, 28)
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, 44)
        if self._hint_font is None:
            self._hint_font = pygame.font.Font(None, 22)

        # ── Header ─────────────────────────────────────────────────
        title = self._title_font.render("REPLAY", True, _TITLE_COLOR)
        surface.blit(title, (sw // 2 - title.get_width() // 2, _TITLE_Y))

        # Accent line
        line_w = 100
        line_y = _TITLE_Y + title.get_height() + 8
        pygame.draw.line(
            surface, _ACCENT_COLOR,
            (sw // 2 - line_w // 2, line_y),
            (sw // 2 + line_w // 2, line_y), 2,
        )

        # Subtitle
        sub_font = pygame.font.Font(None, 24)
        sub_surf = sub_font.render("Sélection de génération", True, _SUBTITLE_COLOR)
        surface.blit(sub_surf, (sw // 2 - sub_surf.get_width() // 2, line_y + 10))

        # ── List panel ─────────────────────────────────────────────
        panel_x = sw // 2 - 220
        panel_w = 440
        list_area_top = _LIST_TOP
        list_area_bottom = sh - _HINT_BAR_H - 10
        panel_h = list_area_bottom - list_area_top

        panel_rect = pygame.Rect(panel_x, list_area_top, panel_w, panel_h)
        pygame.draw.rect(surface, _PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(surface, _PANEL_BORDER, panel_rect, width=1, border_radius=8)

        if not self._generations:
            empty = self._font.render("Aucun brain sauvegardé", True, _HINT_COLOR)
            surface.blit(empty, (sw // 2 - empty.get_width() // 2, list_area_top + 30))
        else:
            inner_top = list_area_top + 10
            max_visible = (panel_h - 20) // _LINE_HEIGHT
            scroll = max(0, self._selected_idx - max_visible + 1)

            for vi, i in enumerate(range(scroll, min(scroll + max_visible, len(self._generations)))):
                gen = self._generations[i]
                y = inner_top + vi * _LINE_HEIGHT

                card_rect = pygame.Rect(panel_x + 10, y, panel_w - 20, _LINE_HEIGHT - 6)

                if i == self._selected_idx:
                    pygame.draw.rect(surface, _SELECTED_COLOR, card_rect, border_radius=5)
                    # Left accent bar
                    pygame.draw.rect(
                        surface, _ACCENT_COLOR,
                        pygame.Rect(card_rect.x, card_rect.y, 3, card_rect.height),
                        border_radius=2,
                    )
                else:
                    pygame.draw.rect(surface, _ENTRY_BG, card_rect, border_radius=5)

                label = f"Génération {gen}"
                txt = self._font.render(label, True, _TEXT_COLOR)
                surface.blit(
                    txt,
                    (card_rect.x + 16, card_rect.y + (card_rect.height - txt.get_height()) // 2),
                )

                # Gen number badge (right side)
                badge = self._hint_font.render(f"#{gen}", True, _ACCENT_COLOR)
                surface.blit(
                    badge,
                    (card_rect.right - badge.get_width() - 12,
                     card_rect.y + (card_rect.height - badge.get_height()) // 2),
                )

            # Scroll indicators
            if scroll > 0:
                up_surf = self._hint_font.render("▲", True, _ACCENT_COLOR)
                surface.blit(up_surf, (sw // 2 - up_surf.get_width() // 2, list_area_top + 2))
            if scroll + max_visible < len(self._generations):
                dn_surf = self._hint_font.render("▼", True, _ACCENT_COLOR)
                surface.blit(dn_surf, (sw // 2 - dn_surf.get_width() // 2, list_area_bottom - 14))

        # ── Footer hint bar ───────────────────────────────────────
        footer_y = sh - _HINT_BAR_H
        pygame.draw.rect(surface, _PANEL_BG, (0, footer_y, sw, _HINT_BAR_H))
        pygame.draw.line(surface, _PANEL_BORDER, (0, footer_y), (sw, footer_y), 1)

        hint = self._hint_font.render(
            "[↑↓] Sélectionner  [Enter] Lancer  [ESC] Retour", True, _HINT_COLOR,
        )
        surface.blit(
            hint,
            (sw // 2 - hint.get_width() // 2,
             footer_y + (_HINT_BAR_H - hint.get_height()) // 2),
        )

    # ------------------------------------------------------------------
    # Replay drawing (game + debug overlay)
    # ------------------------------------------------------------------

    def _draw_replay(self, surface: pygame.Surface) -> None:
        assert self._renderer is not None
        assert self._player is not None
        assert self._camera is not None
        assert self._brain is not None

        self._renderer.draw(surface, self._world, self._player, self._camera)

        # Debug overlay: neuron dots + jump glow
        self._draw_neuron_overlay(surface)

        # HUD hint
        if self._hint_font is None:
            self._hint_font = pygame.font.Font(None, 22)
        hint = self._hint_font.render(
            f"Gen {self._current_gen}  |  [R] Restart  [ESC] Retour",
            True, _HINT_COLOR,
        )
        surface.blit(hint, (10, 10))

    def _draw_neuron_overlay(self, surface: pygame.Surface) -> None:
        assert self._player is not None
        assert self._camera is not None
        assert self._brain is not None

        screen_h = surface.get_height()
        line_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        for net_idx, net in enumerate(self._brain.networks):
            net_color = _NETWORK_COLORS[net_idx % len(_NETWORK_COLORS)]

            # Compute screen positions + active state for each neuron
            positions: list[tuple[int, int]] = []
            actives: list[bool] = []
            for neuron in net.neurons:
                sx = int(
                    World.to_px(self._player.state.x + neuron.dx)
                    - self._camera.x_offset
                )
                sy = int(screen_h - World.to_px(self._player.state.y + neuron.dy))
                positions.append((sx, sy))
                actives.append(neuron.is_active(
                    self._player.state.x, self._player.state.y, self._world,
                ))

            # Central hub = average position of all neurons in the network
            if positions:
                cx = sum(p[0] for p in positions) // len(positions)
                cy = sum(p[1] for p in positions) // len(positions)
            else:
                continue
            hub = (cx, cy)
            network_fires = all(actives)

            # Draw lines from each neuron to the central hub
            for pos, active in zip(positions, actives):
                line_color = (*(_NEURON_GREEN if active else _NEURON_RED), _NETWORK_LINE_ALPHA)
                pygame.draw.line(line_surf, line_color, pos, hub, _NETWORK_LINE_WIDTH)

            # Draw neuron dots
            for pos, active in zip(positions, actives):
                dot_color = _NEURON_GREEN if active else _NEURON_RED
                pygame.draw.circle(surface, net_color, pos, _NEURON_RADIUS + 2)
                pygame.draw.circle(surface, dot_color, pos, _NEURON_RADIUS)

            # Draw central hub — lights up in network color when firing
            if network_fires:
                glow_surf = pygame.Surface(
                    (_HUB_GLOW_RADIUS * 2, _HUB_GLOW_RADIUS * 2), pygame.SRCALPHA,
                )
                pygame.draw.circle(
                    glow_surf, (*net_color, 100),
                    (_HUB_GLOW_RADIUS, _HUB_GLOW_RADIUS), _HUB_GLOW_RADIUS,
                )
                surface.blit(glow_surf, (hub[0] - _HUB_GLOW_RADIUS, hub[1] - _HUB_GLOW_RADIUS))
                pygame.draw.circle(surface, net_color, hub, _HUB_RADIUS)
            else:
                pygame.draw.circle(surface, _HUB_OFF_COLOR, hub, _HUB_RADIUS)
            pygame.draw.circle(surface, net_color, hub, _HUB_RADIUS, 2)

        surface.blit(line_surf, (0, 0))

        # Jump glow
        if self._glow_timer > 0.0:
            player_sx = (
                World.to_px(self._player.state.x + 0.5) - self._camera.x_offset
            )
            player_sy = screen_h - World.to_px(self._player.state.y + 0.5)
            glow_surf = pygame.Surface(
                (_JUMP_GLOW_RADIUS * 2, _JUMP_GLOW_RADIUS * 2), pygame.SRCALPHA,
            )
            alpha = int(200 * (self._glow_timer / _JUMP_GLOW_DURATION))
            pygame.draw.circle(
                glow_surf,
                (*_JUMP_GLOW_COLOR, alpha),
                (_JUMP_GLOW_RADIUS, _JUMP_GLOW_RADIUS),
                _JUMP_GLOW_RADIUS,
                3,
            )
            surface.blit(
                glow_surf,
                (player_sx - _JUMP_GLOW_RADIUS, player_sy - _JUMP_GLOW_RADIUS),
            )
