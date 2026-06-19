"""Popups et dialogues narratifs liés aux quêtes."""
from __future__ import annotations
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, KENNY


# ---------------------------------------------------------------------------
class CutscenePopup:
    """Popup de dialogue générique réutilisable pour n'importe quel PNJ."""

    _W, _H  = 640, 190
    _BTN_W  = 240
    _BTN_H  = 34

    def __init__(
        self,
        speaker: str,
        lines: list[str],
        speaker_color: tuple[int, int, int] = arcade.color.ORANGE,
    ) -> None:
        self._speaker       = speaker
        self._lines         = lines
        self._speaker_color = speaker_color
        self.active         = False
        self._step          = 0

    def open(self) -> None:
        self._step  = 0
        self.active = True

    def advance(self) -> bool:
        """Avance d'un cran. Retourne True si c'était la dernière ligne (popup fermée)."""
        if self._step < len(self._lines) - 1:
            self._step += 1
            return False
        self.active = False
        self._step  = 0
        return True

    def draw(self) -> None:
        if not self.active:
            return
        cx, cy = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        w, h   = self._W, self._H
        bx, bt = cx - w / 2, cy + h / 2

        arcade.draw_lrbt_rectangle_filled(bx, bx + w, bt - h, bt, (15, 15, 40, 245))
        arcade.draw_lrbt_rectangle_outline(bx, bx + w, bt - h, bt, arcade.color.WHITE, 2)

        arcade.draw_text(self._speaker, bx + 14, bt - 18,
                         self._speaker_color, 14, bold=True,
                         anchor_y="center", font_name=KENNY)
        arcade.draw_line(bx + 6, bt - 30, bx + w - 6, bt - 30, arcade.color.WHITE, 1)

        msg = arcade.Text(self._lines[self._step], cx, cy + 20,
                          arcade.color.WHITE, 15,
                          font_name=KENNY, width=int(w - 40),
                          multiline=True, anchor_x="center", anchor_y="center")
        msg.draw()

        is_last = self._step == len(self._lines) - 1
        btn_lbl = "Terminer  [Entrée]" if is_last else "Suivant  [Entrée]"
        btn_cx  = cx
        by      = bt - h + 14
        arcade.draw_lrbt_rectangle_filled(
            btn_cx - self._BTN_W / 2, btn_cx + self._BTN_W / 2,
            by, by + self._BTN_H, (50, 50, 110))
        arcade.draw_lrbt_rectangle_outline(
            btn_cx - self._BTN_W / 2, btn_cx + self._BTN_W / 2,
            by, by + self._BTN_H, arcade.color.WHITE, 1)
        arcade.draw_text(btn_lbl, btn_cx, by + self._BTN_H / 2,
                         arcade.color.WHITE, 13,
                         anchor_x="center", anchor_y="center", font_name=KENNY)
