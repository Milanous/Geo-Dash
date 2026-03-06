"""
ui/scene.py — Abstract base class for all game scenes.

Import rules: no pygame at module level (use TYPE_CHECKING for type hints).
Scenes include: PlayScene, MenuScene, EditorScene.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


class Scene(ABC):
    """
    Abstract base class for a game scene.

    Lifecycle per frame (called by the main loop):
      1. handle_events() — process input, return False to quit
      2. update(dt)      — fixed-timestep physics/logic step
      3. draw(surface)   — render current frame

    Y-axis note: engine uses y=0=floor/up positive; renderer flips to screen coords.

    Attributes:
        next_scene: Set to another Scene to request a scene transition next frame.
                    The main loop checks this after handle_events() returns.
    """

    def __init__(self) -> None:
        self.next_scene: Scene | None = None

    @abstractmethod
    def handle_events(self) -> bool:
        """
        Process pending pygame events.

        Returns:
            False when the scene requests exit (ESC, QUIT), True otherwise.
        """

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Advance scene state by one physics timestep.

        Args:
            dt: Timestep in seconds (typically DT = 1/240).
        """

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """
        Render the scene to *surface*.

        Args:
            surface: The pygame display surface (800×600).
        """
