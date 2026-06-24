from __future__ import annotations
import math
import arcade
from assets.param_map import KENNY, WINDOW_WIDTH, WINDOW_HEIGHT
from character.equipment.weapon import FirearmWeapon, MeleeWeapon
from character.player.player import Player
from typing import TYPE_CHECKING
import utils.paths as paths

if TYPE_CHECKING:
    from world.zombie_mode import ZombieMode

# Constantes du panneau HUD droit
_PANEL_RIGHT = WINDOW_WIDTH - 15
_PANEL_W     = 248
_PANEL_LEFT  = _PANEL_RIGHT - _PANEL_W
_BAR_W, _BAR_H = 200, 16
_BAR_X       = WINDOW_WIDTH - _BAR_W - 20   # bord gauche de la barre de vie
_BAR_Y       = WINDOW_HEIGHT - 70            # bord bas de la barre de vie
_ICON_SIZE   = 40


class ZombieHUD:
    """Rendu visuel du mode zombie : sprite arme, arc mêlée, barre vie, kills, or, armes, crosshair."""

    def __init__(self, zombie_mode: "ZombieMode") -> None:
        self._zm = zombie_mode
        try:
            self._coin_tex = arcade.load_texture(
                paths.asset("assets/images/conssomables/coins.png"))
        except Exception:
            self._coin_tex = None

    # ---------------------------------------------------------------- world-space

    def draw_world(self) -> None:
        """Sprite arme à feu + animation arc mêlée (caméra world déjà activée)."""
        self._draw_player_firearm()
        self._draw_melee_arcs()

    def _draw_player_firearm(self) -> None:
        zm     = self._zm
        scene  = zm._scene
        player = scene.player_sprite
        weapon = player.weapon_feu
        if weapon is None:
            return
        world     = scene.camera_sprites.unproject((zm.mouse_x, zm.mouse_y))
        angle     = math.degrees(math.atan2(world.y - player.center_y, world.x - player.center_x))
        angle_rad = math.radians(angle)
        texture   = weapon.get_texture()
        if texture:
            size         = weapon.sprite_size or max(texture.width, texture.height)
            offset       = player.width / 2 + player.width / 3
            wx           = player.center_x + offset * math.cos(angle_rad)
            wy           = player.center_y + offset * math.sin(angle_rad)
            draw_texture = texture.flip_top_bottom() if world.x < player.center_x else texture
            arcade.draw_texture_rect(
                draw_texture,
                arcade.XYWH(wx, wy, size, size),
                angle=-angle,
                color=arcade.types.Color(255, 255, 255, 255),
            )
        else:
            barrel = player.width / 2 + 18
            tip_x  = player.center_x + barrel * math.cos(angle_rad)
            tip_y  = player.center_y + barrel * math.sin(angle_rad)
            arcade.draw_line(player.center_x, player.center_y, tip_x, tip_y, (70, 75, 85), 6)

    def _draw_melee_arcs(self) -> None:
        for arc in self._zm._melee_arcs:
            ratio     = max(0.0, arc["timer"] / arc["max_timer"])
            progress  = 1.0 - ratio
            cur_angle = arc["angle"] - arc["half_span"] + progress * arc["half_span"] * 2
            angle_rad = math.radians(cur_angle)
            r         = arc["radius"]
            wx        = arc["cx"] + r * math.cos(angle_rad)
            wy        = arc["cy"] + r * math.sin(angle_rad)
            alpha     = int(255 * ratio)

            texture    = arc.get("texture")
            ar, ag, ab = arc["arc_color"]
            if texture:
                size         = arc.get("sprite_size") or max(texture.width, texture.height)
                draw_texture = texture.flip_top_bottom() if math.cos(angle_rad) < 0 else texture
                arcade.draw_texture_rect(
                    draw_texture,
                    arcade.XYWH(wx, wy, size, size),
                    angle=-cur_angle,
                    color=arcade.types.Color(255, 255, 255, alpha),
                )
            else:
                perp_rad = math.radians(cur_angle + 90)
                arcade.draw_line(arc["cx"], arc["cy"], wx, wy, (190, 200, 210, alpha), 3)
                gd    = r * 0.3
                mid_x = arc["cx"] + gd * math.cos(angle_rad)
                mid_y = arc["cy"] + gd * math.sin(angle_rad)
                arcade.draw_line(
                    mid_x + 5 * math.cos(perp_rad), mid_y + 5 * math.sin(perp_rad),
                    mid_x - 5 * math.cos(perp_rad), mid_y - 5 * math.sin(perp_rad),
                    (150, 120, 60, alpha), 3)

            a0  = arc["angle"] - arc["half_span"]
            a1  = arc["angle"] + arc["half_span"]
            col = (ar, ag, ab, int(80 * ratio))
            a0r, a1r = math.radians(a0), math.radians(a1)
            arcade.draw_line(arc["cx"], arc["cy"],
                             arc["cx"] + r * math.cos(a0r), arc["cy"] + r * math.sin(a0r), col, 1)
            arcade.draw_line(arc["cx"], arc["cy"],
                             arc["cx"] + r * math.cos(a1r), arc["cy"] + r * math.sin(a1r), col, 1)
            arcade.draw_arc_outline(arc["cx"], arc["cy"], r, r, col, a0, a1, border_width=1)

    # ---------------------------------------------------------------- screen-space

    def draw_hud(self) -> None:
        """Barre vie + kills + cartes armes + crosshair (screen-space)."""
        self._draw_stats()
        self._draw_crosshair()

    def _draw_stats(self) -> None:
        scene  = self._zm._scene
        player = scene.player_sprite
        obj    = scene.quest_manager.get_kill_objective()

        # Kills (centre haut)
        if obj:
            arcade.draw_text(f"Zombies : {obj.counter} / {int(obj.validator)}",
                             WINDOW_WIDTH / 2, WINDOW_HEIGHT - 40,
                             arcade.color.RED, 20, anchor_x="center", bold=True, font_name=KENNY)

        # --- Barre de vie (même position qu'avant) ---
        ratio = max(0.0, player.health / Player.MAX_HEALTH)
        bar_color = (arcade.color.JADE   if ratio > 0.5
                     else arcade.color.ORANGE if ratio > 0.25
                     else arcade.color.RED)
        arcade.draw_text("Vie", _BAR_X - 40, _BAR_Y + _BAR_H / 2,
                         arcade.color.WHITE, 12, anchor_y="center", font_name=KENNY)
        arcade.draw_lrbt_rectangle_filled(_BAR_X, _BAR_X + _BAR_W, _BAR_Y, _BAR_Y + _BAR_H,
                                          (60, 10, 10))
        if ratio > 0:
            arcade.draw_lrbt_rectangle_filled(_BAR_X, _BAR_X + _BAR_W * ratio,
                                              _BAR_Y, _BAR_Y + _BAR_H, bar_color)
        arcade.draw_lrbt_rectangle_outline(_BAR_X, _BAR_X + _BAR_W, _BAR_Y, _BAR_Y + _BAR_H,
                                           arcade.color.WHITE, 1)
        arcade.draw_text(f"{player.health} / {Player.MAX_HEALTH}",
                         _BAR_X + _BAR_W + 8, _BAR_Y + _BAR_H / 2,
                         arcade.color.WHITE, 12, anchor_y="center", font_name=KENNY)

        # --- Or (sous la barre) ---
        gold_cy = _BAR_Y - 22
        if self._coin_tex:
            arcade.draw_texture_rect(
                self._coin_tex,
                arcade.XYWH(_PANEL_LEFT + 10, gold_cy, 20, 20))
        arcade.draw_text(f"Or : {player.gold}",
                         _PANEL_LEFT + 26, gold_cy,
                         (220, 180, 20), 13, anchor_y="center", bold=True, font_name=KENNY)

        # --- Armes (sous l'or) ---
        self._draw_weapon_compact(player.weapon_feu,   gold_cy - 48,  "Clic G")
        self._draw_weapon_compact(player.weapon_blanc, gold_cy - 106, "Clic D", icon_size=26)

    def _draw_weapon_compact(self, w, cy: float, label: str, icon_size: int = _ICON_SIZE) -> None:
        """Ligne compacte : icône + nom + dégâts, alignée sur le panneau droit."""
        row_h = 50
        arcade.draw_lrbt_rectangle_filled(
            _PANEL_LEFT, _PANEL_RIGHT, cy - row_h / 2, cy + row_h / 2, (35, 35, 65, 210))
        arcade.draw_lrbt_rectangle_outline(
            _PANEL_LEFT, _PANEL_RIGHT, cy - row_h / 2, cy + row_h / 2, arcade.color.WHITE, 1)

        # Icône arme
        texture = w.get_texture() if w else None
        icon_cx = _PANEL_LEFT + icon_size / 2 + 5
        if texture:
            arcade.draw_texture_rect(
                texture,
                arcade.XYWH(icon_cx, cy, icon_size, icon_size))
        else:
            arcade.draw_lrbt_rectangle_filled(
                _PANEL_LEFT + 5, _PANEL_LEFT + 5 + icon_size,
                cy - icon_size / 2, cy + icon_size / 2, (55, 55, 75))

        # Textes
        tx = _PANEL_LEFT + icon_size + 14
        if w is None:
            arcade.draw_text("— vide —", tx + 60, cy,
                             arcade.color.GRAY, 11,
                             anchor_x="center", anchor_y="center", font_name=KENNY)
            return

        arcade.draw_text(w.name, tx, cy + 10,
                         arcade.color.WHITE, 13, bold=True, anchor_y="center", font_name=KENNY)
        arcade.draw_text(label, _PANEL_RIGHT - 8, cy + 10,
                         arcade.color.LIGHT_GRAY, 9,
                         anchor_x="right", anchor_y="center", font_name=KENNY)
        arcade.draw_text(f"Dégâts : {w.damage_min:.1f} – {w.damage_max:.1f}", tx, cy - 9,
                         arcade.color.YELLOW, 10, anchor_y="center", font_name=KENNY)

    def _draw_crosshair(self) -> None:
        mx, my = self._zm.mouse_x, self._zm.mouse_y
        arcade.draw_line(mx - 12, my, mx + 12, my, arcade.color.RED, 2)
        arcade.draw_line(mx, my - 12, mx, my + 12, arcade.color.RED, 2)
        arcade.draw_circle_outline(mx, my, 7, arcade.color.RED, 1)
