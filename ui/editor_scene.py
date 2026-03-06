"""
ui/editor_scene.py — Level editor scene: integrates Editor, EditorCamera,
EditorRenderer and level_io into a full interactive scene.

Import rules: may import editor/, engine/, renderer/, pygame.
[Source: architecture.md#Règles d'import]
"""

from __future__ import annotations

import pygame

from editor.editor import Editor
from editor.editor_camera import EditorCamera
from editor.level_io import load_level, load_level_name, sanitise_name, save_level
from engine.world import TileType
from renderer.editor_renderer import EditorRenderer
from ui.save_dialog import SaveDialog
from ui.scene import Scene

# Screen height assumed for event handling before the first draw() call
_DEFAULT_SCREEN_H = 600


class EditorScene(Scene):
    """
    Full level-editor scene.

    Key bindings:
      Left click  → place selected tile
      Right click → erase tile
      Middle drag → pan camera
      Arrow keys  → pan camera (via EditorCamera.step)
      P           → play-test current level (switches to PlayScene)
      S           → save level (dialog if first save; direct + flash otherwise)
      Shift+S     → save-as dialog (always)
      ESC         → quit (or cancel save dialog)

    Toolbar (drawn at bottom by EditorRenderer):
      SOLID button  → select SOLID tile type
      SPIKE button  → select SPIKE tile type
      PLAY [P] btn  → same as P key
      SAVE [S] btn  → same as S key (shift+click → save-as)
    """

    def __init__(
        self,
        level_path: str | None = None,
        return_scene: Scene | None = None,
    ) -> None:
        super().__init__()
        self._editor = Editor()
        self._camera = EditorCamera()
        self._renderer = EditorRenderer()
        self._return_scene: Scene | None = return_scene

        # Level name (None → first save triggers dialog)
        self._level_name: str | None = None

        # Load a level if a path was provided
        if level_path is not None:
            world = load_level(level_path)
            self._editor = Editor.__new__(Editor)
            self._editor._world = world
            self._editor._selected = TileType.SOLID
            self._editor._erase_mode = False
            self._level_name = load_level_name(level_path)

        # Cursor in block coordinates (updated from mouse position)
        self._cursor_bx: int = 0
        self._cursor_by: int = 0

        # Middle-mouse drag state
        self._mid_drag_last: tuple[int, int] | None = None

        # Current screen height — updated on each draw() call
        self._screen_h: int = _DEFAULT_SCREEN_H

        # Save flash timer (> 0 → show "Saved!" label)
        self._save_flash: float = 0.0

        # Cached font for the save flash label
        self._save_font: pygame.font.Font | None = None

        # Save dialog (None when not open)
        self._save_dialog: SaveDialog | None = None

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def handle_events(self) -> bool:
        """
        Process pending pygame events.

        Returns:
            False when ESC or QUIT is received; True otherwise.
        """
        screen_h = self._screen_h

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # ── Save dialog modal — intercept all events ──────────────
            if self._save_dialog is not None:
                result = self._save_dialog.update(event)
                if result is False:
                    # ESC → cancel dialog
                    self._save_dialog = None
                elif isinstance(result, str):
                    # Enter → save with the typed name
                    self._save_dialog = None
                    self._level_name = result if result.strip() else "untitled"
                    self._do_save()
                continue  # swallow all events while dialog is open

            # ── Keyboard ──────────────────────────────────────────────
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._return_scene is not None:
                        self.next_scene = self._return_scene
                        return True
                    return False

                if event.key == pygame.K_p:
                    self._start_playtest()
                    return True

                if event.key == pygame.K_s:
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_SHIFT:
                        # Shift+S → always open save-as dialog
                        self._save_dialog = SaveDialog(
                            initial_text=self._level_name or ""
                        )
                    elif self._level_name is None:
                        # First save → open dialog
                        self._save_dialog = SaveDialog()
                    else:
                        # Name known → direct save + flash
                        self._do_save()

            # ── Mouse motion — update cursor & handle mid drag ────────
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                bx, by = self._camera.screen_to_world(mx, my, screen_h)
                self._cursor_bx, self._cursor_by = int(bx), int(by)

                # Middle-button drag → pan
                if self._mid_drag_last is not None:
                    lx, ly = self._mid_drag_last
                    self._camera.pan_pixels(lx - mx, ly - my)
                    self._mid_drag_last = (mx, my)

                # Continuous left-click drag → keep placing
                if event.buttons[0]:
                    if not self._click_on_toolbar(my, screen_h):
                        self._editor.place_tile(self._cursor_bx, self._cursor_by)

                # Continuous right-click drag → keep erasing
                if event.buttons[2]:
                    if not self._click_on_toolbar(my, screen_h):
                        self._editor.erase_tile(self._cursor_bx, self._cursor_by)

            # ── Mouse button down ─────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                bx, by = self._camera.screen_to_world(mx, my, screen_h)
                self._cursor_bx, self._cursor_by = int(bx), int(by)

                if event.button == 1:   # Left click
                    if self._click_on_toolbar(my, screen_h):
                        self._handle_toolbar_click(mx, screen_h)
                    else:
                        self._editor.place_tile(self._cursor_bx, self._cursor_by)

                elif event.button == 3:  # Right click
                    if not self._click_on_toolbar(my, screen_h):
                        self._editor.erase_tile(self._cursor_bx, self._cursor_by)

                elif event.button == 2:  # Middle click — start drag
                    self._mid_drag_last = (mx, my)

            # ── Mouse button up ───────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    self._mid_drag_last = None

        return True

    def update(self, dt: float) -> None:
        """Advance camera pan, flash timer, and dialog cursor blink."""
        # Decrement save flash timer
        if self._save_flash > 0:
            self._save_flash -= dt
            if self._save_flash < 0:
                self._save_flash = 0.0

        # Advance dialog cursor blink and skip camera update if dialog is open
        if self._save_dialog is not None:
            self._save_dialog.tick(dt)
            return

        keys_pressed = pygame.key.get_pressed()
        keys: dict[str, bool] = {
            "left":  bool(keys_pressed[pygame.K_LEFT]),
            "right": bool(keys_pressed[pygame.K_RIGHT]),
            "up":    bool(keys_pressed[pygame.K_UP]),
            "down":  bool(keys_pressed[pygame.K_DOWN]),
        }
        self._camera.step(dt, keys)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the editor frame."""
        self._screen_h = surface.get_height()
        self._renderer.draw(
            surface,
            self._editor.world,
            self._camera,
            self._cursor_bx,
            self._cursor_by,
            self._editor.selected_tile_type,
            self._editor.erase_mode,
        )

        # Flash "Saved!" label (top-right)
        if self._save_flash > 0:
            if self._save_font is None:
                self._save_font = pygame.font.Font(None, 24)
            label = self._save_font.render("Saved!", True, (50, 220, 80))
            surface.blit(label, (surface.get_width() - label.get_width() - 10, 10))

        # Save dialog overlay (drawn last — on top)
        if self._save_dialog is not None:
            self._save_dialog.draw(surface)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _start_playtest(self) -> None:
        """Switch to PlayScene with the current world, configured to return here."""
        from ui.play_scene import PlayScene  # local import to avoid cycle at load time
        play = PlayScene(world=self._editor.world, return_scene=self)
        self.next_scene = play

    def _do_save(self) -> None:
        """Save the current level to disk using ``_level_name`` and trigger flash."""
        if self._level_name is None:
            return
            
        safe_name = sanitise_name(self._level_name)
        if safe_name == "untitled":
            # Si le nom est vide ou non alphanumérique, on fixe le nom affiché à untitled
            self._level_name = "untitled"
            
        filename = safe_name + ".json"
        path = "data/levels/" + filename
        try:
            save_level(path, self._editor.world, name=self._level_name)
            self._save_flash = 1.5
        except OSError:
            pass  # Silently ignore save errors in editor (no crash)

    @staticmethod
    def _click_on_toolbar(my: int, screen_h: int) -> bool:
        """Return True if screen-Y coordinate *my* is in the toolbar area."""
        return my >= screen_h - EditorRenderer.TOOLBAR_HEIGHT

    def _handle_toolbar_click(self, mx: int, screen_h: int) -> None:
        """Handle a click in the toolbar area."""
        solid_rect  = EditorRenderer.toolbar_btn_rect(EditorRenderer.BTN_SOLID_IDX,  screen_h)
        spike_rect  = EditorRenderer.toolbar_btn_rect(EditorRenderer.BTN_SPIKE_IDX,  screen_h)
        finish_rect = EditorRenderer.toolbar_btn_rect(EditorRenderer.BTN_FINISH_IDX, screen_h)
        delete_rect = EditorRenderer.toolbar_btn_rect(EditorRenderer.BTN_DELETE_IDX, screen_h)
        play_rect   = EditorRenderer.toolbar_btn_rect(EditorRenderer.BTN_PLAY_IDX,   screen_h)
        save_rect   = EditorRenderer.toolbar_btn_rect(EditorRenderer.BTN_SAVE_IDX,   screen_h)

        if solid_rect.left <= mx <= solid_rect.right:
            self._editor.set_selected_tile_type(TileType.SOLID)
        elif spike_rect.left <= mx <= spike_rect.right:
            self._editor.set_selected_tile_type(TileType.SPIKE)
        elif finish_rect.left <= mx <= finish_rect.right:
            self._editor.set_selected_tile_type(TileType.FINISH)
        elif delete_rect.left <= mx <= delete_rect.right:
            self._editor.set_erase_mode(True)
        elif play_rect.left <= mx <= play_rect.right:
            self._start_playtest()
        elif save_rect.left <= mx <= save_rect.right:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                self._save_dialog = SaveDialog(
                    initial_text=self._level_name or ""
                )
            elif self._level_name is None:
                self._save_dialog = SaveDialog()
            else:
                self._do_save()
