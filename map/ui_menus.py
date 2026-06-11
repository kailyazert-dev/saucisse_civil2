"""Fenêtres et menus de l'interface utilisateur du jeu."""
from __future__ import annotations
from typing import TYPE_CHECKING
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, KENNY

if TYPE_CHECKING:
    from map.map_base import BaseGameView


# ---------------------------------------------------------------------------
class StatsView(arcade.View):
    _TABS = ["Stats", "Quêtes"]

    def __init__(self, game_view: BaseGameView, tab: int = 0):
        super().__init__()
        self._game_view = game_view
        self._tab = tab

    def on_draw(self) -> None:
        self.clear()
        pad = 50
        cx  = WINDOW_WIDTH / 2

        arcade.draw_lrbt_rectangle_filled(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, (10, 10, 30, 255))
        arcade.draw_lrbt_rectangle_filled(pad, WINDOW_WIDTH - pad, pad, WINDOW_HEIGHT - pad, (25, 25, 50, 255))
        arcade.draw_lrbt_rectangle_outline(pad, WINDOW_WIDTH - pad, pad, WINDOW_HEIGHT - pad, arcade.color.WHITE, 2)

        player = self._game_view.player_sprite
        if player is None:
            return

        arcade.draw_text(player.nom, cx, WINDOW_HEIGHT - 90,
                         arcade.color.ORANGE, 18, anchor_x="center", font_name=KENNY)

        # Onglets
        tab_w, tab_h, tab_gap = 150, 34, 8
        total_w     = len(self._TABS) * tab_w + (len(self._TABS) - 1) * tab_gap
        tab_start_x = cx - total_w / 2
        tab_bottom  = WINDOW_HEIGHT - 148
        for i, name in enumerate(self._TABS):
            tx = tab_start_x + i * (tab_w + tab_gap)
            bg = (55, 55, 100) if i == self._tab else (30, 30, 60)
            arcade.draw_lrbt_rectangle_filled(tx, tx + tab_w, tab_bottom, tab_bottom + tab_h, bg)
            border = arcade.color.WHITE if i == self._tab else arcade.color.GRAY
            arcade.draw_lrbt_rectangle_outline(tx, tx + tab_w, tab_bottom, tab_bottom + tab_h, border, 1)
            color = arcade.color.WHITE if i == self._tab else arcade.color.GRAY
            arcade.draw_text(name, tx + tab_w / 2, tab_bottom + tab_h / 2,
                             color, 14, anchor_x="center", anchor_y="center",
                             bold=(i == self._tab), font_name=KENNY)

        sep_y = tab_bottom - 8
        arcade.draw_line(pad + 20, sep_y, WINDOW_WIDTH - pad - 20, sep_y, arcade.color.WHITE, 1)

        if self._tab == 0:
            self._draw_stats(player, sep_y - 20)
        else:
            self._draw_quests(sep_y - 20)

        arcade.draw_text("[← →] Changer d'onglet    [P] ou [Echap]  —  Fermer",
                         cx, pad + 16, arcade.color.GRAY, 12, anchor_x="center", font_name=KENNY)

    def _draw_stats(self, player, top_y: float) -> None:
        pad   = 50
        col_w = (WINDOW_WIDTH - 2 * pad) / 3
        sections = [
            ("Physique",  player.humain.get_stats_physique()),
            ("Intellect", player.humain.get_stats_intellect()),
            ("Sociale",   player.humain.get_stats_sociale()),
        ]
        for i, (title, stats) in enumerate(sections):
            col_cx = pad + col_w * i + col_w / 2
            arcade.draw_text(title, col_cx, top_y,
                             arcade.color.ORANGE, 16, anchor_x="center", bold=True, font_name=KENNY)
            y = top_y - 50
            for name, value in stats:
                bar_x = col_cx - 80
                bar_w, bar_h = 160, 14
                filled = int(bar_w * min(float(value), 1.0))
                arcade.draw_lrbt_rectangle_filled(bar_x, bar_x + bar_w, y, y + bar_h, (60, 60, 80))
                arcade.draw_lrbt_rectangle_filled(bar_x, bar_x + filled, y, y + bar_h, arcade.color.JADE)
                arcade.draw_text(name, bar_x, y + 18, arcade.color.WHITE, 13, font_name=KENNY)
                arcade.draw_text(f"{float(value):.2f}", bar_x + bar_w + 8, y + 2,
                                 arcade.color.WHITE, 11, font_name=KENNY)
                y -= 70

    def _draw_quests(self, top_y: float) -> None:
        pad    = 50
        cx     = WINDOW_WIDTH / 2
        text_w = WINDOW_WIDTH - 2 * pad - 40

        arc = self._game_view.quest_manager.arc
        if arc is None:
            arcade.draw_text("Aucune quête disponible.", cx, top_y - 40,
                             arcade.color.GRAY, 14, anchor_x="center", font_name=KENNY)
            return
        quest = next((q for q in arc.quests if q.status == "ec"), None)
        if quest is None:
            arcade.draw_text("Aucune quête en cours.", cx, top_y - 40,
                             arcade.color.GRAY, 14, anchor_x="center", font_name=KENNY)
            return

        arcade.draw_text(quest.title, pad + 20, top_y,
                         arcade.color.WHITE, 16, bold=True, font_name=KENNY)
        desc = arcade.Text(quest.description, pad + 20, top_y - 26,
                           arcade.color.GRAY, 12, font_name=KENNY,
                           width=text_w, multiline=True, anchor_y="top")
        desc.draw()
        y = top_y - 26 - desc.content_height - 16

        arcade.draw_text("Objectifs :", pad + 20, y, arcade.color.ORANGE, 14, bold=True, font_name=KENNY)
        y -= 28
        for obj in quest.objectives:
            done   = obj.status == "t"
            color  = arcade.color.JADE if done else arcade.color.WHITE
            prefix = "[x]" if done else "[ ]"
            name_t = arcade.Text(f"{prefix}  {obj.name}", pad + 30, y,
                                 color, 13, font_name=KENNY,
                                 width=text_w - 10, multiline=True, anchor_y="top")
            name_t.draw()
            y -= name_t.content_height + 4
            if obj.description:
                sub_t = arcade.Text(obj.description, pad + 60, y,
                                    arcade.color.GRAY, 11, font_name=KENNY,
                                    width=text_w - 40, multiline=True, anchor_y="top")
                sub_t.draw()
                y -= sub_t.content_height + 6

    def on_key_press(self, key, modifiers) -> None:
        if key in (arcade.key.P, arcade.key.ESCAPE):
            self.window.show_view(self._game_view)
        elif key == arcade.key.RIGHT:
            self._tab = (self._tab + 1) % len(self._TABS)
        elif key == arcade.key.LEFT:
            self._tab = (self._tab - 1) % len(self._TABS)


# ---------------------------------------------------------------------------
class Menu:
    _OPTIONS = ["Reprendre", "Sauvegarder", "Réinitialiser", "Quitter"]
    _W, _H   = 320, 290

    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view
        self.selected  = 0

    def draw(self) -> None:
        if not self.game_view.show_menu:
            return
        cx, cy = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        arcade.draw_lrbt_rectangle_filled(
            cx - self._W / 2, cx + self._W / 2,
            cy - self._H / 2, cy + self._H / 2, (15, 15, 15, 210))
        arcade.draw_lrbt_rectangle_outline(
            cx - self._W / 2, cx + self._W / 2,
            cy - self._H / 2, cy + self._H / 2, arcade.color.WHITE, 2)
        arcade.draw_text("MENU", cx, cy + self._H / 2 - 35,
                         arcade.color.WHITE, 22, anchor_x="center", bold=True, font_name=KENNY)
        for i, opt in enumerate(self._OPTIONS):
            color = arcade.color.YELLOW if i == self.selected else arcade.color.WHITE
            arcade.draw_text(opt, cx, cy + 50 - i * 55,
                             color, 17, anchor_x="center", font_name=KENNY)

    def handle_key(self, key) -> None:
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self._OPTIONS)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self._OPTIONS)
        elif key == arcade.key.ENTER:
            self._confirm()

    def _confirm(self) -> None:
        opt = self._OPTIONS[self.selected]
        if opt == "Reprendre":
            self.game_view.show_menu = False
        elif opt == "Sauvegarder":
            self.game_view.character_manager.save_player()
            self.game_view.quest_manager.save_progress()
        elif opt == "Réinitialiser":
            self.game_view.character_manager.reset()
            self.game_view.quest_manager.reset()
            self.game_view.show_menu = False
            self.game_view.manager.switch_map("home")
        elif opt == "Quitter":
            arcade.exit()


# ---------------------------------------------------------------------------
class QuestNotif:
    _FADE_IN  = 0.35
    _HOLD     = 2.2
    _FADE_OUT = 0.55

    def __init__(self):
        self._queue:        list[dict] = []
        self._current_text: str        = ""
        self._current_type: str        = ""
        self._state:        str        = "idle"
        self._timer:        float      = 0.0
        self._alpha:        int        = 0

    def update(self, delta_time: float, pending: list) -> None:
        while pending:
            self._queue.append(pending.pop(0))

        if self._state == "idle":
            if self._queue:
                n = self._queue.pop(0)
                self._current_text = n["text"]
                self._current_type = n["type"]
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
        cx  = WINDOW_WIDTH / 2
        cy  = WINDOW_HEIGHT * 0.68
        if self._current_type == "quest":
            r, g, b, size = 255, 172, 28, 24
        else:
            r, g, b, size = 0, 168, 107, 19
        bg_alpha = int(self._alpha * 0.72)
        arcade.draw_lrbt_rectangle_filled(cx - 220, cx + 220,
                                          cy - 14, cy + size + 14,
                                          (0, 0, 0, bg_alpha))
        arcade.draw_text(self._current_text, cx, cy + size / 2,
                         (r, g, b, self._alpha), size,
                         anchor_x="center", anchor_y="center",
                         bold=True, font_name=KENNY)


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
