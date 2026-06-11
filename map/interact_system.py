from __future__ import annotations
import arcade
from typing import TYPE_CHECKING
from assets.param_map import KENNY, WINDOW_HEIGHT

if TYPE_CHECKING:
    from map.map_base import BaseGameView


class InteractUI:
    _BOX_W    = 260
    _BOX_H    = 50
    _BOX_T_H  = 28
    _BOX_C_H  = 43
    _POP_BG   = (15, 15, 40, 215)
    _HINT_COL = (150, 180, 230)

    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view

    def draw_side_bar(self) -> None:
        gv = self.game_view
        if not gv.show_side_bar:
            return
        arc = gv.quest_manager.arc
        if arc is None:
            return
        quest = next((q for q in arc.quests if q.status == "ec"), None)
        if quest is None:
            return
        y = WINDOW_HEIGHT - 67
        arcade.draw_text(quest.title, 20, y, arcade.color.WHITE, 14, bold=True, font_name=KENNY)
        y -= 20
        for obj in quest.objectives:
            color = arcade.color.JADE if obj.status == "t" else arcade.color.WHITE
            arcade.draw_text(obj.name, 30, y, color, 12, bold=True, font_name=KENNY)
            y -= 20

    def draw_box(self) -> None:
        pass

    def draw_interact_box(self):
        arcade.get_window().use()
        player = self.game_view.player_sprite
        left = player.center_x + 25
        top  = player.center_y - 25
        w, h = self._BOX_W - 10, self._BOX_H
        self._draw_popup(left, top, w, h)
        return left, top

    def create_obstacles(self):
        gv = self.game_view
        obstacles = arcade.SpriteList()
        obstacles.extend(gv.pnj_sprite)
        obstacles.extend(gv.strategique_sprite)
        obstacles.extend(gv.objet_sprites)
        obstacles.extend(gv.scene["Meuble_H"])
        obstacles.extend(gv.scene["Mur"])
        return obstacles

    def get_r_corner_cord(self):
        arcade.get_window().use()
        player = self.game_view.player_sprite
        return player.center_x + 20, player.center_y - 55

    def _draw_popup(self, left: float, top: float, w: float, h: float) -> None:
        arcade.draw_lrbt_rectangle_filled(left, left + w, top - h, top, self._POP_BG)
        arcade.draw_lrbt_rectangle_outline(left, left + w, top - h, top, arcade.color.WHITE, 1)

    def _draw_box_rect(self, cx: float, cy: float, w: float, h: float) -> None:
        self._draw_popup(cx - w / 2, cy + h / 2, w, h)

    def interact_obj_prg(self) -> None:
        box_width  = self._BOX_W - 10
        box_height = self._BOX_H - 10
        gv     = self.game_view
        player = gv.player_sprite
        qm     = gv.quest_manager

        # Passe 1 : MapActionObject — priorité sur les UpStats quand un objectif est actif
        for objet in gv.objet_sprites:
            if type(objet).__name__ != "MapActionObject":
                continue
            if arcade.get_distance_between_sprites(player, objet) >= 68:
                continue
            if not objet.is_available(qm):
                continue
            left, top = self.get_r_corner_cord()
            gv.current_map_action = objet
            cx = left + box_width / 2
            self._draw_box_rect(cx, top, box_width, box_height)
            arcade.draw_text(objet.get_name(), cx, top + 9, arcade.color.JADE, 13,
                             anchor_x="center", anchor_y="center", font_name=KENNY)
            arcade.draw_text("[Entrée]", cx, top - 9, self._HINT_COL, 11,
                             anchor_x="center", anchor_y="center", font_name=KENNY)
            return

        # Passe 2 : UpStat / UpStatCollection
        for objet in gv.objet_sprites:
            if arcade.get_distance_between_sprites(player, objet) >= 68:
                continue
            left, top = self.get_r_corner_cord()

            if type(objet).__name__ == "UpStat":
                gv.current_objet = objet
                stat_name = objet.stat_cible
                player_level_stat = getattr(player.humain, stat_name)
                cx = left + box_width / 2
                self._draw_box_rect(cx, top, box_width, box_height)
                color = (
                    arcade.color.GRAY_BLUE if player_level_stat >= objet.stat_max
                    else arcade.color.RED if player_level_stat < objet.stat_min
                    else arcade.color.JADE
                )
                at_max     = player_level_stat >= objet.stat_max
                hint       = "Niveau max atteint" if at_max else "[Entrée]"
                hint_color = arcade.color.GRAY_BLUE if at_max else self._HINT_COL
                arcade.draw_text(objet.get_name(), cx, top + 9, color, 13,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)
                arcade.draw_text(hint, cx, top - 9, hint_color, 11,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)
                return

            if type(objet).__name__ == "UpStatCollection":
                gv.current_collection = objet
                box_width += 10
                cx = left + box_width / 2

                if not gv.open_collection:
                    self._draw_box_rect(cx, top, box_width, box_height)
                    arcade.draw_text(objet.get_name(), cx, top + 9, arcade.color.JADE, 13,
                                     anchor_x="center", anchor_y="center", font_name=KENNY)
                    arcade.draw_text("[Entrée]", cx, top - 9, self._HINT_COL, 11,
                                     anchor_x="center", anchor_y="center", font_name=KENNY)
                else:
                    upstats  = objet.get_all_upStats()
                    HEADER_H = 30
                    ITEM_H   = 28
                    FOOTER_H = 36
                    total_h  = HEADER_H + ITEM_H * len(upstats) + FOOTER_H
                    bx       = cx - box_width / 2
                    b_top    = top + box_height / 2
                    b_bot    = b_top - total_h

                    arcade.draw_lrbt_rectangle_filled(bx, bx + box_width, b_bot, b_top, self._POP_BG)
                    arcade.draw_lrbt_rectangle_outline(bx, bx + box_width, b_bot, b_top, arcade.color.WHITE, 1)

                    header_cy = b_top - HEADER_H / 2
                    arcade.draw_text(objet.get_name(), cx, header_cy, arcade.color.JADE, 13,
                                     anchor_x="center", anchor_y="center", font_name=KENNY)

                    sep1 = b_top - HEADER_H
                    arcade.draw_line(bx + 4, sep1, bx + box_width - 4, sep1, arcade.color.WHITE, 1)

                    for i, upstat in enumerate(upstats):
                        stat_name = upstat.stat_cible
                        player_level_stat = getattr(player.humain, stat_name)
                        color = (
                            arcade.color.GRAY_BLUE if player_level_stat >= upstat.stat_max
                            else arcade.color.RED if player_level_stat < upstat.stat_min
                            else arcade.color.JADE
                        )
                        item_cy = sep1 - ITEM_H / 2 - i * ITEM_H
                        if i == gv.current_index_upstat:
                            arcade.draw_lrbt_rectangle_filled(
                                bx + 1, bx + box_width - 1,
                                item_cy - ITEM_H / 2, item_cy + ITEM_H / 2,
                                (50, 50, 90),
                            )
                        label = f"> {upstat.get_name()}" if i == gv.current_index_upstat else upstat.get_name()
                        arcade.draw_text(label, cx, item_cy, color, 11,
                                         anchor_x="center", anchor_y="center", font_name=KENNY)

                    sep2 = sep1 - ITEM_H * len(upstats)
                    arcade.draw_line(bx + 4, sep2, bx + box_width - 4, sep2, arcade.color.WHITE, 1)

                    sel          = upstats[gv.current_index_upstat]
                    sel_stat_val = getattr(player.humain, sel.stat_cible)
                    sel_at_max   = sel_stat_val >= sel.stat_max
                    footer_cy    = sep2 - FOOTER_H / 2

                    arcade.draw_text("↑ ↓   Naviguer", cx, footer_cy + 9, self._HINT_COL, 10,
                                     anchor_x="center", anchor_y="center", font_name=KENNY)
                    if sel_at_max:
                        arcade.draw_text("Niveau max atteint", cx, footer_cy - 9, arcade.color.GRAY_BLUE, 10,
                                         anchor_x="center", anchor_y="center", font_name=KENNY)
                    else:
                        arcade.draw_text("[Entrée]   Utiliser", cx, footer_cy - 9, self._HINT_COL, 10,
                                         anchor_x="center", anchor_y="center", font_name=KENNY)
                return

    def interact_pnj_strateg(self) -> None:
        gv     = self.game_view
        player = gv.player_sprite
        for strategique in gv.strategique_sprite:
            dist = getattr(strategique, "interaction_distance", 50)
            if arcade.get_distance_between_sprites(player, strategique) < dist:
                gv.current_strategique = strategique
                w, h  = self._BOX_W - 10, self._BOX_H
                left  = strategique.center_x - w / 2
                top   = strategique.center_y + 60
                self._draw_popup(left, top, w, h)
                cx, cy = left + w / 2, top - h / 2
                arcade.draw_text(strategique.get_nom(), cx, cy + 9, arcade.color.ORANGE, 13,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)
                arcade.draw_text("[Entrée] Aller à PHL", cx, cy - 9, self._HINT_COL, 11,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)
                break

    def interact_pnj(self) -> None:
        gv     = self.game_view
        player = gv.player_sprite
        for pnj in gv.pnj_sprite:
            if arcade.get_distance_between_sprites(player, pnj) < 70:
                left, top = self.draw_interact_box()
                cx = left + (self._BOX_W - 10) / 2
                cy = top - self._BOX_H / 2
                arcade.draw_text(pnj.get_nom(), cx, cy + 9, arcade.color.ORANGE, 13,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)
                arcade.draw_text("[Entrée] Discuter", cx, cy - 9, self._HINT_COL, 11,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)
