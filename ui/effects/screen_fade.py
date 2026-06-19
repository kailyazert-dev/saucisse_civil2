"""Effet de fondu écran (fade in/out)."""
from __future__ import annotations
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT


class ScreenFade:
    """Gère un fondu en entrée/sortie sur l'écran entier."""

    _SPEED     = 15
    _MAX_ALPHA = 255

    def __init__(self, color: tuple[int, int, int] = (0, 0, 0)) -> None:
        self._color = color
        self._alpha = 0
        self._dir   = 0   # 0=idle  1=assombrir  -1=éclaircir

    @property
    def is_active(self) -> bool:
        return self._dir != 0

    @property
    def alpha(self) -> int:
        return self._alpha

    def darken(self) -> None:
        self._dir = 1

    def lighten(self) -> None:
        self._dir = -1

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
                0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, (r, g, b, self._alpha))
