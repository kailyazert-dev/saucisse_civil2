from __future__ import annotations
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, KENNY


class ShopMenu:
    """Overlay boutique : navigation clavier, achat avec déduction d'or."""

    _W        = 480
    _ITEM_H   = 62
    _HEADER_H = 80
    _FOOTER_H = 46

    def __init__(self) -> None:
        self.active             = False
        self._items: list[dict] = []
        self._selected          = 0
        self._message           = ""
        self._message_timer     = 0.0
        self._message_ok        = True

    # ---------------------------------------------------------------- public

    def open(self, items: list[dict]) -> None:
        self._items    = items
        self._selected = 0
        self._message  = ""
        self.active    = True

    def close(self) -> None:
        self.active = False

    def update(self, delta_time: float) -> None:
        if self._message_timer > 0:
            self._message_timer = max(0.0, self._message_timer - delta_time)

    def handle_key(self, key: int, player) -> None:
        if key == arcade.key.ESCAPE:
            self.close()
            return
        if not self._items:
            return
        if key in (arcade.key.UP, arcade.key.Z):
            self._selected = (self._selected - 1) % len(self._items)
        elif key in (arcade.key.DOWN, arcade.key.S):
            self._selected = (self._selected + 1) % len(self._items)
        elif key in (arcade.key.E, arcade.key.RETURN):
            self._buy(player)

    # ---------------------------------------------------------------- draw

    def draw(self, player) -> None:
        if not self.active or not self._items:
            return

        n       = len(self._items)
        total_h = self._HEADER_H + n * self._ITEM_H + self._FOOTER_H
        cx      = WINDOW_WIDTH  / 2
        cy      = WINDOW_HEIGHT / 2
        px      = cx - self._W / 2
        py      = cy - total_h / 2

        # Fond semi-transparent global
        arcade.draw_lrbt_rectangle_filled(
            0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, (0, 0, 0, 140))

        # Panneau
        arcade.draw_lrbt_rectangle_filled(
            px, px + self._W, py, py + total_h, (18, 18, 45, 245))
        arcade.draw_lrbt_rectangle_outline(
            px, px + self._W, py, py + total_h, (220, 180, 20), 2)

        # En-tête
        arcade.draw_text("DISTRIBUTEUR", cx, py + total_h - 26,
                         (220, 180, 20), 18, anchor_x="center",
                         bold=True, font_name=KENNY)
        arcade.draw_text(f"Or disponible : {player.gold}", cx, py + total_h - 52,
                         arcade.color.WHITE, 12, anchor_x="center", font_name=KENNY)
        arcade.draw_line(px + 10, py + total_h - self._HEADER_H,
                         px + self._W - 10, py + total_h - self._HEADER_H,
                         (220, 180, 20), 1)

        # Articles
        for i, item in enumerate(self._items):
            iy       = py + total_h - self._HEADER_H - (i + 0.5) * self._ITEM_H
            selected = i == self._selected

            if selected:
                arcade.draw_lrbt_rectangle_filled(
                    px + 4, px + self._W - 4,
                    iy - self._ITEM_H / 2 + 2, iy + self._ITEM_H / 2 - 2,
                    (50, 50, 110, 180))

            can_afford  = player.gold >= item["prix"]
            name_color  = arcade.color.YELLOW if selected else arcade.color.WHITE
            price_color = (80, 220, 80) if can_afford else (220, 80, 80)

            arcade.draw_text(item["nom"], px + 16, iy + 10,
                             name_color, 13, bold=selected,
                             anchor_y="center", font_name=KENNY)
            arcade.draw_text(item.get("description", ""), px + 16, iy - 10,
                             arcade.color.LIGHT_GRAY, 10,
                             anchor_y="center", font_name=KENNY)
            arcade.draw_text(f"{item['prix']} or", px + self._W - 16, iy,
                             price_color, 13,
                             anchor_x="right", anchor_y="center", font_name=KENNY)

        # Pied de page
        arcade.draw_line(px + 10, py + self._FOOTER_H,
                         px + self._W - 10, py + self._FOOTER_H,
                         (80, 80, 120), 1)

        if self._message and self._message_timer > 0:
            color = (80, 220, 80) if self._message_ok else (220, 80, 80)
            arcade.draw_text(self._message, cx, py + self._FOOTER_H / 2,
                             color, 13, anchor_x="center",
                             anchor_y="center", bold=True, font_name=KENNY)
        else:
            arcade.draw_text("↑↓ Naviguer   E Acheter   ECHAP Fermer",
                             cx, py + self._FOOTER_H / 2,
                             arcade.color.LIGHT_GRAY, 10,
                             anchor_x="center", anchor_y="center", font_name=KENNY)

    # ---------------------------------------------------------------- private

    def _buy(self, player) -> None:
        item = self._items[self._selected]
        if player.gold < item["prix"]:
            self._message       = "Pas assez d'or !"
            self._message_ok    = False
            self._message_timer = 2.0
            return
        player.gold -= item["prix"]
        self._apply(item, player)
        self._message       = f"{item['nom']} acheté !"
        self._message_ok    = True
        self._message_timer = 2.0

    def _apply(self, item: dict, player) -> None:
        kind = item["type"]
        if kind == "soin":
            from character.player.player import Player
            max_hp = Player.MAX_HEALTH + getattr(player, "max_health_bonus", 0)
            player.health = min(max_hp, player.health + item["valeur"])
        elif kind == "arme":
            from character.equipment.weapon import Weapon
            weapon = Weapon.from_name(item["arme_id"])
            if item.get("slot", "feu") == "feu":
                player.weapon_feu = weapon
            else:
                player.weapon_blanc = weapon
        elif kind == "upgrade_arme":
            slot   = item.get("slot", "feu")
            weapon = player.weapon_feu if slot == "feu" else player.weapon_blanc
            if weapon:
                weapon.damage_min += item["valeur"]
                weapon.damage_max += item["valeur"]
        elif kind == "upgrade_perso":
            from character.player.player import Player
            player.max_health_bonus  = getattr(player, "max_health_bonus", 0) + item["valeur"]
            player.health            = min(player.health + item["valeur"],
                                          Player.MAX_HEALTH + player.max_health_bonus)
