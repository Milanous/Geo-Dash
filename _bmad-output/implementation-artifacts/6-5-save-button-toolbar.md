# Story 6.5: Save Button in Editor Toolbar

Status: done

## Story

As a level designer,
I want a visible SAVE button in the editor toolbar,
so that I can save my level without needing to know the keyboard shortcut.

## Acceptance Criteria

1. **Given** the editor is open **When** I look at the toolbar at the bottom **Then** I see a "SAVE [S]" button after the PLAY button
2. **When** I click the SAVE button and no level name is set yet **Then** a `SaveDialog` opens (same behaviour as pressing `S`)
3. **When** I click the SAVE button and a level name is already set **Then** the level saves directly and the "Saved!" flash appears (same as pressing `S`)
4. **When** `Shift+Click` on the SAVE button **Then** the save-as dialog opens (same as `Shift+S`)
5. **And** the button uses a distinct recognisable colour (orange/amber palette) that differs from PLAY and tile-selector buttons
6. **And** existing keyboard shortcuts `S` / `Shift+S` continue to work unchanged
7. **And** all existing tests pass (no regressions)
8. **And** `tests/test_editor_scene.py` contains at least one test verifying the SAVE button hit-test triggers save logic

## Tasks / Subtasks

- [ ] Task 1 — `renderer/editor_renderer.py`: Add SAVE button to toolbar
  - [ ] 1.1 Add `_BTN_SAVE_IDX: int = 4` (new index after PLAY at index 3)
  - [ ] 1.2 Add colour constants `_BTN_SAVE` (e.g. `(200, 140, 40)`) and `_BTN_SAVE_HOT` (e.g. `(240, 180, 60)`)
  - [ ] 1.3 In `_draw_toolbar()`: draw the SAVE button at index 4 with label `"SAVE [S]"` using `_BTN_SAVE` colour
  - [ ] 1.4 Expose `BTN_SAVE_IDX` as class attribute on `EditorRenderer`
  - [ ] 1.5 Update `toolbar_btn_rect` docstring to mention index 4=SAVE

- [ ] Task 2 — `ui/editor_scene.py`: Handle SAVE button click
  - [ ] 2.1 In `_handle_toolbar_click()`: add an `elif` for the SAVE button rect
  - [ ] 2.2 If `Shift` held (`pygame.key.get_mods() & pygame.KMOD_SHIFT`): open `SaveDialog(initial_text=self._level_name or "")`
  - [ ] 2.3 Else if `_level_name is None`: open `SaveDialog()`
  - [ ] 2.4 Else: call `self._do_save()`
  - [ ] 2.5 Update class docstring to mention `SAVE [S] btn` in the toolbar section

- [ ] Task 3 — `tests/test_editor_scene.py`: Add SAVE button test
  - [ ] 3.1 Test: `EditorRenderer.BTN_SAVE_IDX` exists and equals 4
  - [ ] 3.2 Test: `toolbar_btn_rect(BTN_SAVE_IDX, 600)` returns a valid `pygame.Rect`

## Dev Notes

### Architecture Constraints

| Module | Can import | Cannot import |
|---|---|---|
| `renderer/` | `engine/`, `pygame` | `ai/`, `editor/` |
| `ui/` | all except `ai/simulation.py` | — |

[Source: architecture.md#Règles d'import]

### Existing Code to Modify

1. **`renderer/editor_renderer.py`** — Button index constants are at module level (`_BTN_SOLID_IDX=0`, `_BTN_SPIKE_IDX=1`, `_BTN_FINISH_IDX=2`, `_BTN_PLAY_IDX=3`). Add `_BTN_SAVE_IDX=4`. The `_draw_toolbar()` method draws buttons sequentially — add the SAVE button block after the PLAY-TEST button block. Class attributes `BTN_*_IDX` are mirrored at line ~281 — add `BTN_SAVE_IDX` there too.

2. **`ui/editor_scene.py`** — `_handle_toolbar_click()` at line ~268 does hit-testing by btn rect. Add an `elif` branch for the save rect. Reuse the same logic as the `K_s` handler (lines 128-140): check shift mod, check `_level_name`, open dialog or call `_do_save()`.

### Testing Notes

- Tests must remain headless (no `pygame.display` init). The existing pattern in `tests/test_editor_scene.py` uses `pygame.init()` with mocking — follow that pattern.
- `EditorRenderer.toolbar_btn_rect()` is already a `@staticmethod` that can be called without a display.

### Cross-Story Dependencies

- Story 6.1 (done): `SaveDialog`, `_do_save()`, `_level_name`, `_save_flash` — all already exist. This story only adds the visual button + click handler.

### References

- [Source: renderer/editor_renderer.py — `_draw_toolbar()`, `_btn_rect()`, `BTN_*_IDX` constants]
- [Source: ui/editor_scene.py — `_handle_toolbar_click()`, `K_s` handling block, `_do_save()`]
- [Source: architecture.md#Règles d'import]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
