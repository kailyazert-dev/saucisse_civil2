from __future__ import annotations
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, KENNY


class LoadingView(arcade.View):
    """Affiche 'Chargement...' pendant un frame avant d'exécuter le setup de la map."""

    def __init__(self, setup_fn):
        super().__init__()
        self._setup_fn = setup_fn
        self._ready = False

    def on_draw(self) -> None:
        self.clear()
        arcade.draw_text(
            "Chargement...",
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
            arcade.color.WHITE, 28,
            anchor_x="center", anchor_y="center",
            font_name=KENNY,
        )

    def on_update(self, delta_time: float) -> None:
        if not self._ready:
            self._ready = True
        else:
            self._setup_fn()
