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
from ai.neuron import DX_MIN, DX_MAX, DY_MIN, DY_MAX
from ai.neuron import Neuron
from engine.camera import Camera
from engine.player import Player
from engine.world import TileType, World
from renderer.game_renderer import GameRenderer
from ui.scene import Scene
from ui import theme as T

# ── Replay-specific constants ─────────────────────────────────────────
_LIST_TOP = 110

_START_X: float = 5.0
_START_Y: float = 5.0

_NEURON_RADIUS: int = 14
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
_BOUNDS_COLOR = (120, 120, 140)
_BOUNDS_LINE_WIDTH: int = 1

_GEN_PATTERN = re.compile(r"^gen_(\d+)_best\.json$")

_DEFAULT_BRAINS_DIR: str = "data/brains"


class ReplayScene(Scene):
    """Best-agent replay: generation selector + single-brain simulation."""

    # Pause button layout (top-right corner)
    _PAUSE_BTN_W: int = 90
    _PAUSE_BTN_H: int = 32
    _PAUSE_BTN_MARGIN: int = 10

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

        # Pause state
        self._paused: bool = False

        # Search state
        self._search_active: bool = False
        self._search_text: str = ""

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
    # Search helpers
    # ------------------------------------------------------------------

    def _apply_search(self) -> None:
        """Jump to the generation matching the search text, or closest."""
        self._search_active = False
        if not self._search_text or not self._generations:
            self._search_text = ""
            return
        target = int(self._search_text)
        self._search_text = ""
        # Exact match first
        if target in self._generations:
            self._selected_idx = self._generations.index(target)
            return
        # Otherwise find the closest generation
        closest_idx = min(
            range(len(self._generations)),
            key=lambda i: abs(self._generations[i] - target),
        )
        self._selected_idx = closest_idx

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
                    if self._paused:
                        self._paused = False
                        continue
                    if self._brain is not None:
                        # If replaying → back to gen selector
                        self._brain = None
                        self._player = None
                        self._camera = None
                        self._renderer = None
                        self._current_gen = None
                        self._paused = False
                        return True
                    # If on selector → return to caller
                    if self._return_scene is not None:
                        self.next_scene = self._return_scene
                        return True
                    return False

                if event.key == pygame.K_p and self._brain is not None:
                    self._paused = not self._paused
                    continue

                if event.key == pygame.K_r and self._current_gen is not None:
                    self._paused = False
                    self._load_gen(self._current_gen)
                    return True

                # Selector mode
                if self._brain is None:
                    if self._search_active:
                        if event.key == pygame.K_ESCAPE:
                            self._search_active = False
                            self._search_text = ""
                            continue
                        elif event.key == pygame.K_RETURN:
                            self._apply_search()
                            continue
                        elif event.key == pygame.K_BACKSPACE:
                            self._search_text = self._search_text[:-1]
                            continue
                        elif event.unicode.isdigit():
                            self._search_text += event.unicode
                            continue
                        continue
                    if event.key == pygame.K_g:
                        self._search_active = True
                        self._search_text = ""
                        continue
                    if event.key == pygame.K_UP and self._selected_idx > 0:
                        self._selected_idx -= 1
                    elif (
                        event.key == pygame.K_DOWN
                        and self._selected_idx < len(self._generations) - 1
                    ):
                        self._selected_idx += 1
                    elif event.key == pygame.K_RETURN and self._generations:
                        self._load_gen(self._generations[self._selected_idx])

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._brain is not None and self._pause_btn_rect_hit(event.pos):
                    self._paused = not self._paused

        return True

    def update(self, dt: float) -> None:
        if self._brain is None or self._player is None or self._camera is None:
            return

        if self._paused:
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
        T.fill_bg(surface)
        sw = surface.get_width()
        sh = surface.get_height()

        if self._font is None:
            self._font = pygame.font.Font(None, T.FONT_BODY)
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, T.FONT_TITLE)
        if self._hint_font is None:
            self._hint_font = pygame.font.Font(None, T.FONT_HINT)

        # ── Header ─────────────────────────────────────────────────
        T.draw_header(surface, "REPLAY", "Sélection de génération", accent=T.PURPLE)

        # ── List panel ─────────────────────────────────────────────
        panel_x = sw // 2 - 220
        panel_w = 440
        list_area_top = _LIST_TOP
        list_area_bottom = sh - T.HINT_BAR_H - 10
        panel_h = list_area_bottom - list_area_top

        panel_rect = pygame.Rect(panel_x, list_area_top, panel_w, panel_h)
        T.draw_panel(surface, panel_rect)

        if not self._generations:
            empty = self._font.render("Aucun brain sauvegardé", True, T.TEXT_DIM)
            surface.blit(empty, (sw // 2 - empty.get_width() // 2, list_area_top + 30))
        else:
            inner_top = list_area_top + 10
            max_visible = (panel_h - 20) // T.LINE_H
            scroll = max(0, self._selected_idx - max_visible + 1)

            for vi, i in enumerate(range(scroll, min(scroll + max_visible, len(self._generations)))):
                gen = self._generations[i]
                y = inner_top + vi * T.LINE_H

                card_rect = pygame.Rect(panel_x + 10, y, panel_w - 20, T.LINE_H - 6)
                T.draw_card(surface, card_rect, selected=(i == self._selected_idx), accent=T.PURPLE)

                label = f"Génération {gen}"
                txt = self._font.render(label, True, T.TEXT)
                surface.blit(
                    txt,
                    (card_rect.x + 16, card_rect.y + (card_rect.height - txt.get_height()) // 2),
                )

                badge = self._hint_font.render(f"#{gen}", True, T.PURPLE)
                surface.blit(
                    badge,
                    (card_rect.right - badge.get_width() - 12,
                     card_rect.y + (card_rect.height - badge.get_height()) // 2),
                )

            if scroll > 0:
                up_surf = self._hint_font.render("▲", True, T.PURPLE)
                surface.blit(up_surf, (sw // 2 - up_surf.get_width() // 2, list_area_top + 2))
            if scroll + max_visible < len(self._generations):
                dn_surf = self._hint_font.render("▼", True, T.PURPLE)
                surface.blit(dn_surf, (sw // 2 - dn_surf.get_width() // 2, list_area_bottom - 14))

        # ── Search bar ──────────────────────────────────────────
        if self._search_active:
            search_w = 300
            search_h = 36
            search_x = sw // 2 - search_w // 2
            search_y = list_area_bottom - search_h - 8
            search_rect = pygame.Rect(search_x, search_y, search_w, search_h)
            pygame.draw.rect(surface, T.BG_INPUT_ACT, search_rect, border_radius=T.RADIUS_SM)
            pygame.draw.rect(surface, T.PURPLE, search_rect, width=2, border_radius=T.RADIUS_SM)

            prompt = f"Génération : {self._search_text}_"
            stxt = self._font.render(prompt, True, T.TEXT)
            surface.blit(
                stxt,
                (search_rect.x + 12,
                 search_rect.y + (search_rect.height - stxt.get_height()) // 2),
            )

        # ── Footer ────────────────────────────────────────────────
        if self._search_active:
            T.draw_footer(surface, "[Enter] Aller  [ESC] Annuler")
        else:
            T.draw_footer(surface, "[↑↓] Sélectionner  [G] Rechercher  [Enter] Lancer  [ESC] Retour")

    # ------------------------------------------------------------------
    # Replay drawing (game + debug overlay)
    # ------------------------------------------------------------------

    def _draw_replay(self, surface: pygame.Surface) -> None:
        assert self._renderer is not None
        assert self._player is not None
        assert self._camera is not None
        assert self._brain is not None

        self._renderer.draw(surface, self._world, self._player, self._camera)

        # Debug overlay: bounds frame + neuron dots + jump glow
        self._draw_bounds_frame(surface)
        self._draw_neuron_overlay(surface)

        # HUD hint
        if self._hint_font is None:
            self._hint_font = pygame.font.Font(None, T.FONT_HINT)
        hint = self._hint_font.render(
            f"Gen {self._current_gen}  |  [R] Restart  [P] Pause  [ESC] Retour",
            True, T.TEXT_DIM,
        )
        surface.blit(hint, (10, 10))

        # Pause button + overlay
        self._draw_pause_button(surface)
        if self._paused:
            self._draw_pause_overlay(surface)

    # ------------------------------------------------------------------
    # Pause UI
    # ------------------------------------------------------------------

    def _pause_btn_rect(self, surface: pygame.Surface) -> pygame.Rect:
        sw = surface.get_width()
        return pygame.Rect(
            sw - self._PAUSE_BTN_W - self._PAUSE_BTN_MARGIN,
            self._PAUSE_BTN_MARGIN,
            self._PAUSE_BTN_W,
            self._PAUSE_BTN_H,
        )

    def _pause_btn_rect_hit(self, pos: tuple[int, int]) -> bool:
        try:
            surface = pygame.display.get_surface()
            if surface is None:
                return False
            return self._pause_btn_rect(surface).collidepoint(pos)
        except pygame.error:
            return False

    def _draw_pause_button(self, surface: pygame.Surface) -> None:
        rect = self._pause_btn_rect(surface)
        label = "\u25b6 Play" if self._paused else "\u275a\u275a Pause"
        bg = T.BTN_PRI if not self._paused else T.GREEN

        pygame.draw.rect(surface, bg, rect, border_radius=T.RADIUS_SM)
        pygame.draw.rect(surface, T.BORDER_HI, rect, width=1, border_radius=T.RADIUS_SM)

        font = pygame.font.Font(None, T.FONT_HINT)
        txt = font.render(label, True, T.TEXT_TITLE)
        surface.blit(txt, (
            rect.x + (rect.width - txt.get_width()) // 2,
            rect.y + (rect.height - txt.get_height()) // 2,
        ))

    def _draw_pause_overlay(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        big_font = pygame.font.Font(None, 64)
        txt = big_font.render("PAUSE", True, T.PURPLE)
        surface.blit(txt, (sw // 2 - txt.get_width() // 2, sh // 2 - txt.get_height() // 2 - 20))

        hint_font = pygame.font.Font(None, T.FONT_SMALL)
        hint = hint_font.render("[P] Reprendre  |  [ESC] Retour", True, T.TEXT_SEC)
        surface.blit(hint, (sw // 2 - hint.get_width() // 2, sh // 2 + 30))

    def _draw_bounds_frame(self, surface: pygame.Surface) -> None:
        """Draw the allowed neuron placement zone as a thin rectangle."""
        assert self._player is not None
        assert self._camera is not None

        screen_h = surface.get_height()
        px = self._player.state.x
        py = self._player.state.y

        left = int(World.to_px(px + DX_MIN) - self._camera.x_offset)
        right = int(World.to_px(px + DX_MAX) - self._camera.x_offset)
        top = int(screen_h - World.to_px(py + DY_MAX))
        bottom = int(screen_h - World.to_px(py + DY_MIN))

        rect = pygame.Rect(left, top, right - left, bottom - top)
        pygame.draw.rect(surface, _BOUNDS_COLOR, rect, _BOUNDS_LINE_WIDTH)

    def _draw_neuron_overlay(self, surface: pygame.Surface) -> None:
        assert self._player is not None
        assert self._camera is not None
        assert self._brain is not None

        screen_h = surface.get_height()
        line_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        for net_idx, net in enumerate(self._brain.networks):
            net_color = _NETWORK_COLORS[net_idx % len(_NETWORK_COLORS)]

            # Compute screen positions + active state + type for each neuron
            positions: list[tuple[int, int]] = []
            actives: list[bool] = []
            neurons_ref: list[Neuron] = []
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
                neurons_ref.append(neuron)

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

            # Draw neuron shapes (circle=AIR, square=SOLID, triangle=SPIKE)
            for pos, active, nrn in zip(positions, actives, neurons_ref):
                dot_color = _NEURON_GREEN if active else _NEURON_RED
                sx, sy = pos
                r = _NEURON_RADIUS
                if nrn.type == TileType.AIR:
                    pygame.draw.circle(surface, dot_color, pos, r, 2)
                elif nrn.type == TileType.SOLID:
                    pygame.draw.rect(surface, dot_color,
                                     (sx - r, sy - r, r * 2, r * 2), 2)
                else:
                    # Triangle for all spike types
                    pts = [(sx, sy - r), (sx - r, sy + r), (sx + r, sy + r)]
                    pygame.draw.polygon(surface, dot_color, pts, 2)

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
