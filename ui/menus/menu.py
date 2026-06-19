from __future__ import annotations
from typing import TYPE_CHECKING
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, KENNY
if TYPE_CHECKING:
    from world.scene.base_scene import BaseScene


# ---------------------------------------------------------------------------
class Menu:
    _OPTIONS = [
        "Reprendre",
        "Sauvegarder",
        "Charger une sauvegarde",
        "Retour à la maison",
        "Réinitialiser",
        "Quitter",
    ]
    _W, _H       = 360, 360
    _SUB_W, _SUB_H = 440, 360
    _NOM_W, _NOM_H = 390, 220
    _MAX_VIS     = 7

    def __init__(self, game_view: BaseScene):
        self.game_view     = game_view
        self.selected      = 0
        self._feedback:    str        = ""
        self._sub:         str | None = None   # None | "save_list" | "load_list" | "save_name" | "confirm_delete"
        self._saves:       list       = []
        self._slot_idx:    int        = 0
        self._scroll:      int        = 0
        self._name_input:  str        = ""
        self._delete_name: str        = ""
        self._prev_sub:    str        = ""

    # ------------------------------------------------------------------ public

    def reset(self) -> None:
        self.selected     = 0
        self._sub         = None
        self._feedback    = ""
        self._saves       = []
        self._slot_idx    = 0
        self._scroll      = 0
        self._name_input  = ""
        self._delete_name = ""
        self._prev_sub    = ""

    def has_sub(self) -> bool:
        return self._sub is not None

    def on_text(self, char: str) -> None:
        if self._sub == "save_name" and len(self._name_input) < 28:
            self._name_input += char

    # ------------------------------------------------------------------ draw

    def draw(self) -> None:
        if not self.game_view.show_menu:
            return
        if self._sub == "save_list":
            self._draw_slot_panel("Sauvegarder", show_new=True)
        elif self._sub == "load_list":
            self._draw_slot_panel("Charger une sauvegarde", show_new=False)
        elif self._sub == "save_name":
            self._draw_save_name()
        elif self._sub == "confirm_delete":
            self._draw_confirm_delete()
        else:
            self._draw_main()

    def _draw_main(self) -> None:
        cx, cy  = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        n       = len(self._OPTIONS)
        spacing = 42
        top_y   = cy + (n - 1) / 2 * spacing

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
            arcade.draw_text(opt, cx, top_y - i * spacing,
                             color, 15, anchor_x="center", font_name=KENNY)

        if self._feedback:
            arcade.draw_text(self._feedback, cx, cy - self._H / 2 + 22,
                             arcade.color.JADE, 12, anchor_x="center", font_name=KENNY)

    def _draw_slot_panel(self, title: str, show_new: bool) -> None:
        cx, cy = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        w, h   = self._SUB_W, self._SUB_H
        bx     = cx - w / 2
        top    = cy + h / 2

        arcade.draw_lrbt_rectangle_filled(bx, bx + w, top - h, top, (15, 15, 15, 220))
        arcade.draw_lrbt_rectangle_outline(bx, bx + w, top - h, top, arcade.color.WHITE, 2)
        arcade.draw_text(title, cx, top - 30,
                         arcade.color.WHITE, 17, anchor_x="center", bold=True, font_name=KENNY)
        arcade.draw_line(bx + 12, top - 52, bx + w - 12, top - 52, arcade.color.WHITE, 1)

        items = []
        if show_new:
            items.append({"name": "Nouvelle sauvegarde", "date": "", "new": True})
        for s in self._saves:
            items.append({"name": s["name"], "date": s.get("date", ""), "new": False})

        if not items:
            arcade.draw_text("Aucune sauvegarde disponible.",
                             cx, cy, arcade.color.GRAY, 13,
                             anchor_x="center", anchor_y="center", font_name=KENNY)
        else:
            row_h    = 34
            list_top = top - 88
            vis_n    = min(self._MAX_VIS, len(items))
            for v in range(vis_n):
                idx = self._scroll + v
                if idx >= len(items):
                    break
                item   = items[idx]
                y_row  = list_top - v * row_h + row_h / 2
                is_sel = idx == self._slot_idx
                if is_sel:
                    arcade.draw_lrbt_rectangle_filled(
                        bx + 8, bx + w - 8,
                        y_row - row_h / 2 + 2, y_row + row_h / 2 - 2,
                        (50, 50, 110, 200))
                prefix     = "→" if is_sel else "  "
                name_color = arcade.color.YELLOW if is_sel else arcade.color.WHITE
                if item["new"]:
                    name_color = arcade.color.JADE if is_sel else (100, 200, 130)
                arcade.draw_text(f"{prefix}  {item['name']}", bx + 14, y_row,
                                 name_color, 13, anchor_y="center", font_name=KENNY)
                if item.get("date"):
                    arcade.draw_text(item["date"], bx + w - 14, y_row,
                                     arcade.color.GRAY, 11,
                                     anchor_x="right", anchor_y="center", font_name=KENNY)

            if self._scroll > 0:
                arcade.draw_text("▲", cx, list_top + 14,
                                 arcade.color.GRAY, 11, anchor_x="center", font_name=KENNY)
            if self._scroll + vis_n < len(items):
                arcade.draw_text("▼", cx, list_top - vis_n * row_h + 26,
                                 arcade.color.GRAY, 11, anchor_x="center", font_name=KENNY)

        arcade.draw_line(bx + 12, top - h + 50, bx + w - 12, top - h + 50, arcade.color.WHITE, 1)
        arcade.draw_text("[↑↓] Naviguer    [Entrée] Sélectionner",
                         cx, top - h + 36,
                         arcade.color.GRAY, 10, anchor_x="center", font_name=KENNY)
        arcade.draw_text("[Suppr] Effacer    [Echap] Retour",
                         cx, top - h + 22,
                         arcade.color.GRAY, 10, anchor_x="center", font_name=KENNY)

    def _draw_save_name(self) -> None:
        cx, cy = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        w, h   = self._NOM_W, self._NOM_H
        bx     = cx - w / 2
        top    = cy + h / 2

        arcade.draw_lrbt_rectangle_filled(bx, bx + w, top - h, top, (15, 15, 15, 220))
        arcade.draw_lrbt_rectangle_outline(bx, bx + w, top - h, top, arcade.color.WHITE, 2)
        arcade.draw_text("Nom de la sauvegarde", cx, top - 30,
                         arcade.color.WHITE, 15, anchor_x="center", bold=True, font_name=KENNY)
        arcade.draw_line(bx + 12, top - 52, bx + w - 12, top - 52, arcade.color.WHITE, 1)

        input_y = cy + 12
        arcade.draw_lrbt_rectangle_filled(bx + 20, bx + w - 20,
                                           input_y - 22, input_y + 22, (28, 28, 58))
        arcade.draw_lrbt_rectangle_outline(bx + 20, bx + w - 20,
                                            input_y - 22, input_y + 22, arcade.color.WHITE, 1)
        arcade.draw_text(self._name_input + "▌", bx + 30, input_y,
                         arcade.color.WHITE, 14, anchor_y="center", font_name=KENNY)

        arcade.draw_line(bx + 12, top - h + 44, bx + w - 12, top - h + 44, arcade.color.WHITE, 1)
        arcade.draw_text("[Entrée] Confirmer    [Echap] Retour",
                         cx, top - h + 26,
                         arcade.color.GRAY, 10, anchor_x="center", font_name=KENNY)

    def _draw_confirm_delete(self) -> None:
        cx, cy = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        w, h   = 370, 190
        bx     = cx - w / 2
        top    = cy + h / 2

        arcade.draw_lrbt_rectangle_filled(bx, bx + w, top - h, top, (35, 8, 8, 235))
        arcade.draw_lrbt_rectangle_outline(bx, bx + w, top - h, top, arcade.color.RED, 2)
        arcade.draw_text("Supprimer cette sauvegarde ?", cx, top - 28,
                         arcade.color.WHITE, 15, anchor_x="center", bold=True, font_name=KENNY)
        arcade.draw_line(bx + 12, top - 50, bx + w - 12, top - 50, (180, 40, 40), 1)

        arcade.draw_text(f'"{self._delete_name}"', cx, cy + 10,
                         arcade.color.YELLOW, 14, anchor_x="center", anchor_y="center",
                         font_name=KENNY)
        arcade.draw_text("Cette action est irréversible.", cx, cy - 16,
                         arcade.color.GRAY, 11, anchor_x="center", font_name=KENNY)

        arcade.draw_line(bx + 12, top - h + 44, bx + w - 12, top - h + 44, (180, 40, 40), 1)
        arcade.draw_text("[Entrée] Supprimer    [Echap] Annuler",
                         cx, top - h + 26,
                         arcade.color.GRAY, 10, anchor_x="center", font_name=KENNY)

    # ------------------------------------------------------------------ key handling

    def handle_key(self, key) -> None:
        if self._sub is None:
            self._handle_main(key)
        elif self._sub in ("save_list", "load_list"):
            self._handle_slot_list(key)
        elif self._sub == "save_name":
            self._handle_save_name(key)
        elif self._sub == "confirm_delete":
            self._handle_confirm_delete(key)

    def _handle_main(self, key) -> None:
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self._OPTIONS)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self._OPTIONS)
        elif key == arcade.key.ENTER:
            self._confirm_main()

    def _confirm_main(self) -> None:
        opt = self._OPTIONS[self.selected]
        gv  = self.game_view
        if opt == "Reprendre":
            gv.show_menu = False
            self._feedback = ""
        elif opt == "Sauvegarder":
            self._saves    = gv.character_manager.get_all_saves()
            self._slot_idx = 0
            self._scroll   = 0
            self._sub      = "save_list"
        elif opt == "Charger une sauvegarde":
            self._saves    = gv.character_manager.get_all_saves()
            self._slot_idx = 0
            self._scroll   = 0
            self._sub      = "load_list"
        elif opt == "Retour à la maison":
            gv.character_manager.save_player()
            gv.quest_manager.save_progress()
            gv.show_menu = False
            self._feedback = ""
            gv.manager.switch_map("home")
        elif opt == "Réinitialiser":
            gv.character_manager.reset()
            gv.quest_manager.reset()
            gv.show_menu = False
            self._feedback = ""
            gv.manager.switch_map("home")
        elif opt == "Quitter":
            arcade.exit()

    def _handle_slot_list(self, key) -> None:
        for_save = (self._sub == "save_list")
        n_extra  = 1 if for_save else 0
        n        = n_extra + len(self._saves)
        if n == 0:
            if key == arcade.key.ESCAPE:
                self._sub = None
            return
        if key == arcade.key.UP:
            self._slot_idx = (self._slot_idx - 1) % n
            self._clamp_scroll(n)
        elif key == arcade.key.DOWN:
            self._slot_idx = (self._slot_idx + 1) % n
            self._clamp_scroll(n)
        elif key == arcade.key.ENTER:
            if for_save:
                if self._slot_idx == 0:
                    self._name_input = ""
                else:
                    self._name_input = self._saves[self._slot_idx - 1]["name"]
                self._sub = "save_name"
            else:
                slot     = self._saves[self._slot_idx]
                map_name = self.game_view.character_manager.load_slot(slot)
                self.game_view.show_menu = False
                self.reset()
                self.game_view.manager.switch_map(map_name)
        elif key == arcade.key.DELETE:
            save_idx = self._slot_idx - n_extra
            if save_idx >= 0 and save_idx < len(self._saves):
                self._delete_name = self._saves[save_idx]["name"]
                self._prev_sub    = self._sub
                self._sub         = "confirm_delete"
        elif key == arcade.key.ESCAPE:
            self._sub = None

    def _handle_save_name(self, key) -> None:
        if key == arcade.key.BACKSPACE:
            self._name_input = self._name_input[:-1]
        elif key == arcade.key.ENTER:
            name = self._name_input.strip()
            if name:
                gv = self.game_view
                gv.character_manager.save_slot(name, self._current_map_name())
                self._feedback = f"Sauvegardé : {name}"
                self._sub      = None
        elif key == arcade.key.ESCAPE:
            self._sub = "save_list"

    def _handle_confirm_delete(self, key) -> None:
        if key == arcade.key.ENTER:
            self.game_view.character_manager.delete_slot(self._delete_name)
            self._saves    = self.game_view.character_manager.get_all_saves()
            self._slot_idx = min(self._slot_idx, len(self._saves) - 1 + (1 if self._prev_sub == "save_list" else 0))
            self._slot_idx = max(0, self._slot_idx)
            self._clamp_scroll(len(self._saves) + (1 if self._prev_sub == "save_list" else 0))
            self._sub = self._prev_sub
        elif key == arcade.key.ESCAPE:
            self._sub = self._prev_sub

    def _clamp_scroll(self, n: int) -> None:
        vis = min(self._MAX_VIS, n)
        if self._slot_idx < self._scroll:
            self._scroll = self._slot_idx
        elif self._slot_idx >= self._scroll + vis:
            self._scroll = self._slot_idx - vis + 1

    def _current_map_name(self) -> str:
        cls = type(self.game_view).__name__.lower()
        if "home" in cls:
            return "home"
        if "tma" in cls:
            return "tma"
        if "phl" in cls:
            return "phl"
        return "home"
