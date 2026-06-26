from __future__ import annotations
import os
from typing import TYPE_CHECKING
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, KENNY
if TYPE_CHECKING:
    from world.scene.base_scene import BaseScene


# ---------------------------------------------------------------------------
class StatsView(arcade.View):
    _TABS = ["Stats", "Quêtes", "Équipement"]

    def __init__(self, game_view: BaseScene, tab: int = 0):
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
        elif self._tab == 1:
            self._draw_quests(sep_y - 20)
        else:
            self._draw_equipment(player, sep_y - 20)

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

    def _draw_equipment(self, player, top_y: float) -> None:
        pad = 50
        cx  = WINDOW_WIDTH / 2
        w   = WINDOW_WIDTH - 2 * pad - 40

        weapon_feu   = getattr(player, "weapon_feu",   None)
        weapon_blanc = getattr(player, "weapon_blanc", None)
        if weapon_feu is None and weapon_blanc is None:
            weapon_feu = getattr(player, "weapon", None)

        arcade.draw_text("Équipement", pad + 20, top_y,
                         arcade.color.ORANGE, 16, bold=True, font_name=KENNY)
        arcade.draw_line(pad + 20, top_y - 10, pad + 20 + w, top_y - 10, (80, 80, 120), 1)

        if weapon_feu is None and weapon_blanc is None:
            arcade.draw_text("Aucune arme équipée", cx, top_y - 50,
                             arcade.color.GRAY, 14, anchor_x="center", font_name=KENNY)
            return

        card_w = min(w, 400)
        y = top_y - 28
        if weapon_feu is not None:
            self._draw_weapon_card(weapon_feu, pad + 20, y, card_w, label="Clic gauche")
            y -= 148
        if weapon_blanc is not None:
            self._draw_weapon_card(weapon_blanc, pad + 20, y, card_w, label="Clic droit", show_projectile=False)

    def _draw_weapon_card(self, weapon, card_x: float, card_y: float, card_w: float,
                          label: str = "", show_projectile: bool = True) -> None:
        card_h = 130
        arcade.draw_lrbt_rectangle_filled(
            card_x, card_x + card_w, card_y - card_h, card_y, (35, 35, 65, 220))
        arcade.draw_lrbt_rectangle_outline(
            card_x, card_x + card_w, card_y - card_h, card_y, arcade.color.WHITE, 1)

        img_margin = 10
        img_size   = card_h - 2 * img_margin
        img_x      = card_x + img_margin
        img_y      = card_y - card_h + img_margin
        img_cx     = img_x + img_size / 2
        img_cy     = img_y + img_size / 2

        if os.path.exists(weapon.image_path):
            tex = arcade.load_texture(weapon.image_path)
            arcade.draw_texture_rect(tex, arcade.LRBT(img_x, img_x + img_size, img_y, img_y + img_size))
        else:
            arcade.draw_lrbt_rectangle_filled(img_x, img_x + img_size, img_y, img_y + img_size, (50, 50, 80))
            arcade.draw_lrbt_rectangle_outline(img_x, img_x + img_size, img_y, img_y + img_size, arcade.color.GRAY, 1)
            arcade.draw_text("?", img_cx, img_cy, arcade.color.GRAY, 28,
                             anchor_x="center", anchor_y="center", font_name=KENNY)

        text_x = img_x + img_size + 12

        arcade.draw_text(weapon.name, text_x, card_y - 22,
                         arcade.color.WHITE, 18, bold=True, anchor_y="center", font_name=KENNY)
        if label:
            arcade.draw_text(f"[{label}]", card_x + card_w - 10, card_y - 22,
                             arcade.color.LIGHT_GRAY, 10,
                             anchor_x="right", anchor_y="center", font_name=KENNY)

        dmg_label_y = card_y - 52
        arcade.draw_text("Dégâts :", text_x, dmg_label_y,
                         arcade.color.GRAY, 12, anchor_y="center", font_name=KENNY)
        arcade.draw_text(f"{weapon.damage_min:.1f}  –  {weapon.damage_max:.1f}",
                         text_x + 84, dmg_label_y,
                         arcade.color.YELLOW, 14, anchor_y="center", font_name=KENNY)

        bar_x = text_x
        bar_y = card_y - 72
        bar_w = card_w - (text_x - card_x) - 16
        bar_h = 10
        fill_min = max(0.0, min(1.0, weapon.damage_min / 10.0))
        fill_max = max(0.0, min(1.0, weapon.damage_max / 10.0))
        arcade.draw_lrbt_rectangle_filled(bar_x, bar_x + bar_w, bar_y, bar_y + bar_h, (50, 50, 70))
        arcade.draw_lrbt_rectangle_filled(bar_x, bar_x + bar_w * fill_max, bar_y, bar_y + bar_h, (180, 60, 60))
        arcade.draw_lrbt_rectangle_filled(bar_x, bar_x + bar_w * fill_min, bar_y, bar_y + bar_h, (220, 100, 60))
        arcade.draw_lrbt_rectangle_outline(bar_x, bar_x + bar_w, bar_y, bar_y + bar_h, arcade.color.WHITE, 1)

        if show_projectile and hasattr(weapon, "bullet_color"):
            proj_label_y = card_y - 100
            arcade.draw_text("Projectile :", text_x, proj_label_y,
                             arcade.color.GRAY, 12, anchor_y="center", font_name=KENNY)
            swatch_x    = text_x + 92
            swatch_size = 16
            r, g, b = weapon.bullet_color
            arcade.draw_lrbt_rectangle_filled(
                swatch_x, swatch_x + swatch_size,
                proj_label_y - swatch_size / 2, proj_label_y + swatch_size / 2,
                (r, g, b, 255))
            arcade.draw_lrbt_rectangle_outline(
                swatch_x, swatch_x + swatch_size,
                proj_label_y - swatch_size / 2, proj_label_y + swatch_size / 2,
                arcade.color.WHITE, 1)

    def on_key_press(self, key, modifiers) -> None:
        if key in (arcade.key.P, arcade.key.ESCAPE):
            self.window.show_view(self._game_view)
        elif key == arcade.key.RIGHT:
            self._tab = (self._tab + 1) % len(self._TABS)
        elif key == arcade.key.LEFT:
            self._tab = (self._tab - 1) % len(self._TABS)
