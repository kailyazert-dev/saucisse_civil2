from __future__ import annotations
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, KENNY


# ---------------------------------------------------------------------------
class DeathMenu:
    _OPTIONS = ["Recommencer au début", "Apparaître à la maison"]
    _W, _H   = 380, 200

    def __init__(self):
        self.selected = 0
        self.active   = False

    def draw(self) -> None:
        if not self.active:
            return
        cx, cy = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        arcade.draw_lrbt_rectangle_filled(
            cx - self._W / 2, cx + self._W / 2,
            cy - self._H / 2, cy + self._H / 2, (20, 0, 0, 240))
        arcade.draw_lrbt_rectangle_outline(
            cx - self._W / 2, cx + self._W / 2,
            cy - self._H / 2, cy + self._H / 2, arcade.color.RED, 2)
        arcade.draw_text("Vous êtes mort", cx, cy + 70,
                         arcade.color.RED, 20, anchor_x="center",
                         bold=True, font_name=KENNY)
        for i, opt in enumerate(self._OPTIONS):
            color = arcade.color.YELLOW if i == self.selected else arcade.color.WHITE
            arcade.draw_text(opt, cx, cy + 20 - i * 50,
                             color, 15, anchor_x="center", font_name=KENNY)

    def handle_key(self, key) -> str | None:
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self._OPTIONS)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self._OPTIONS)
        elif key == arcade.key.ENTER:
            return self._OPTIONS[self.selected]
        return None
