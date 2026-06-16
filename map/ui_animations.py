"""Animations d'écran réutilisables (fondu, transitions, etc.)."""
from __future__ import annotations
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT


# ---------------------------------------------------------------------------
class ScreenFade:
    """Fondu noir plein-écran. Même mécanique que HOME.py / PHL.py."""

    _SPEED     = 15   # alpha ajouté/retiré par frame
    _MAX_ALPHA = 180  # opacité maximale (0-255)

    def __init__(self, color: tuple[int, int, int] = (0, 0, 0)) -> None:
        self._color = color
        self._alpha = 0
        self._dir   = 0  # 0=idle, 1=assombrir, -1=éclaircir

    # ------------------------------------------------------------------
    def darken(self) -> None:
        self._dir = 1

    def lighten(self) -> None:
        self._dir = -1

    @property
    def is_active(self) -> bool:
        return self._alpha > 0 or self._dir != 0

    # ------------------------------------------------------------------
    def update(self) -> None:
        if self._dir == 1:
            self._alpha = min(self._MAX_ALPHA, self._alpha + self._SPEED)
            if self._alpha >= self._MAX_ALPHA:
                self._dir = 0
        elif self._dir == -1:
            self._alpha = max(0, self._alpha - self._SPEED)
            if self._alpha <= 0:
                self._dir = 0

    def draw(self) -> None:
        if self._alpha > 0:
            r, g, b = self._color
            arcade.draw_lrbt_rectangle_filled(
                0, WINDOW_WIDTH, 0, WINDOW_HEIGHT,
                (r, g, b, self._alpha),
            )
