"""Notifications de quêtes et objectifs affichées en jeu."""
from __future__ import annotations
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, KENNY


# ---------------------------------------------------------------------------
class QuestNotif:
    _FADE_IN  = 0.35
    _HOLD     = 2.2
    _FADE_OUT = 0.55

    def __init__(self):
        self._queue:             list[dict]  = []
        self._current_text:      str         = ""
        self._current_type:      str         = ""
        self._current_title:     str         = ""
        self._current_objectives: list[str]  = []
        self._state:             str         = "idle"
        self._timer:             float       = 0.0
        self._alpha:             int         = 0

    @property
    def is_idle(self) -> bool:
        return self._state == "idle"

    @property
    def current_type(self) -> str:
        return self._current_type

    def update(self, delta_time: float, pending: list) -> None:
        while pending:
            self._queue.append(pending.pop(0))

        if self._state == "idle":
            if self._queue:
                n = self._queue.pop(0)
                self._current_text       = n["text"]
                self._current_type       = n["type"]
                self._current_title      = n.get("title", "")
                self._current_objectives = n.get("objectives", [])
                self._state = "fade_in"
                self._timer = 0.0
                self._alpha = 0
            return

        self._timer += delta_time
        if self._state == "fade_in":
            self._alpha = min(255, int(255 * self._timer / self._FADE_IN))
            if self._timer >= self._FADE_IN:
                self._alpha, self._state, self._timer = 255, "hold", 0.0
        elif self._state == "hold":
            if self._timer >= self._HOLD:
                self._state, self._timer = "fade_out", 0.0
        elif self._state == "fade_out":
            self._alpha = max(0, int(255 * (1.0 - self._timer / self._FADE_OUT)))
            if self._timer >= self._FADE_OUT:
                self._alpha, self._state, self._timer = 0, "idle", 0.0

    def draw(self) -> None:
        if self._state == "idle" or self._alpha == 0:
            return

        cx       = WINDOW_WIDTH / 2
        anchor_y = WINDOW_HEIGHT * 0.68

        if self._current_type in ("quest", "new_quest", "new_arc"):
            hr, hg, hb = 255, 172, 28
        else:
            hr, hg, hb = 0, 168, 107

        H_PAD   = 20
        V_PAD   = 10
        H_SIZE  = 22
        T_SIZE  = 17
        O_SIZE  = 13

        bg_alpha = int(self._alpha * 0.72)

        def _w(text: str, size: int) -> float:
            return arcade.Text(text, 0, 0, arcade.color.WHITE, size,
                               font_name=KENNY).content_width + 2 * H_PAD

        # Construit la liste des boîtes : (kind, width, height)
        specs = []

        w1 = _w(self._current_text, H_SIZE)
        specs.append(("header", w1, H_SIZE + 2 * V_PAD))

        if self._current_title:
            title_display = f"[v] {self._current_title}" if self._current_type == "objective" else self._current_title
            w2 = _w(title_display, T_SIZE)
            specs.append(("title", w2, T_SIZE + 2 * V_PAD))

        if self._current_type == "new_quest" and self._current_objectives:
            w3 = max(_w(f"[] {n}", O_SIZE) for n in self._current_objectives)
            h3 = (V_PAD
                  + len(self._current_objectives) * O_SIZE
                  + (len(self._current_objectives) - 1)
                  + V_PAD)
            specs.append(("objectives", w3, h3))

        # Centre la pile verticalement autour de anchor_y
        total_h = sum(s[2] for s in specs) + (len(specs) - 1)
        top = anchor_y + total_h / 2

        for kind, w, h in specs:
            bot = top - h
            mid = (top + bot) / 2
            arcade.draw_lrbt_rectangle_filled(cx - w / 2, cx + w / 2, bot, top,
                                              (0, 0, 0, bg_alpha))
            if kind == "header":
                arcade.draw_text(self._current_text, cx, mid,
                                 (hr, hg, hb, self._alpha), H_SIZE,
                                 anchor_x="center", anchor_y="center",
                                 bold=True, font_name=KENNY)
            elif kind == "title":
                title_display = f"[v] {self._current_title}" if self._current_type == "objective" else self._current_title
                arcade.draw_text(title_display, cx, mid,
                                 (hr, hg, hb, self._alpha), T_SIZE,
                                 anchor_x="center", anchor_y="center",
                                 bold=True, font_name=KENNY)
            elif kind == "objectives":
                y = top - V_PAD - O_SIZE / 2
                for name in self._current_objectives:
                    arcade.draw_text(f"[] {name}", cx, y,
                                     (255, 255, 255, int(self._alpha * 0.85)), O_SIZE,
                                     anchor_x="center", anchor_y="center",
                                     bold=False, font_name=KENNY)
                    y -= O_SIZE
            top = bot
