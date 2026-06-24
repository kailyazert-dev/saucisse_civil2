from __future__ import annotations
import math
import arcade
from assets.param_map import KENNY, WINDOW_WIDTH, WINDOW_HEIGHT
from character.enemies.zombie_manager import ZombieManager
from character.equipment.weapon import FirearmWeapon, MeleeWeapon
from character.player.player import Player
from ui.menus.death_menu import DeathMenu
from ui.menus.stats_view import StatsView
from typing import TYPE_CHECKING
import utils.paths as paths

if TYPE_CHECKING:
    from world.scene.base_scene import BaseScene

_ZOMBIE_MUSIC_PATH = "assets/song/zombie.mp3"
_music_cache: arcade.Sound | None = None
_FIRE_INTERVAL_DEFAULT = 0.2


class ZombieMode:
    """Encapsule l'état et la logique du mode zombie : spawn, tir, dégâts, mort et HUD.

    Usage :
        self.zombie_mode = ZombieMode(self)
        self.zombie_mode.setup(walls, spawn_points)           # PhlScene
        self.zombie_mode.setup(walls, spawn_points,
                               always_active=True)            # MercScene
    """

    def __init__(self, scene: "BaseScene") -> None:
        self._scene         = scene
        self.zombie_manager: ZombieManager | None = None
        self._combat_walls: arcade.SpriteList | None = None
        self._zombie_spawn  = (574, 50)
        self._death_alpha   = 0
        self._death_dir     = 0
        self._death_menu: DeathMenu | None = None
        self.mouse_x        = WINDOW_WIDTH  // 2
        self.mouse_y        = WINDOW_HEIGHT // 2
        self._music: arcade.Sound | None = None
        self._music_player  = None
        self._was_active    = False
        self._mouse_held_left    = False
        self._mouse_held_right   = False
        self._fire_timer_left    = 0.0
        self._fire_timer_right   = 0.0
        self._pending_melee_kills = 0
        self._melee_arcs: list[dict] = []

    # ---------------------------------------------------------------- setup

    def set_spawn_points(self, points: list) -> None:
        if self.zombie_manager:
            self.zombie_manager.set_spawn_points(points)

    def setup(self, walls: arcade.SpriteList, spawn_points: list,
              always_active: bool = False) -> None:
        """Configure le ZombieManager, le DeathMenu, les points de spawn et la musique."""
        self._combat_walls = walls
        self._zombie_spawn = spawn_points[0] if spawn_points else (574, 50)
        self._death_menu   = DeathMenu()

        scene = self._scene
        self.zombie_manager = ZombieManager(scene.quest_manager, scene.player_sprite)
        if always_active:
            self.zombie_manager.is_active = lambda: True
        self.zombie_manager.setup_walls(walls)
        self.zombie_manager.set_spawn_points(spawn_points)

        if always_active:
            self._start_music()

    # ---------------------------------------------------------------- music

    def _start_music(self) -> None:
        global _music_cache
        if self._music_player is not None:
            return
        if _music_cache is None:
            try:
                _music_cache = arcade.load_sound(paths.asset(_ZOMBIE_MUSIC_PATH))
            except Exception:
                return
        try:
            self._music_player = _music_cache.play(loop=True)
        except Exception:
            pass

    def stop_music(self) -> None:
        if _music_cache and self._music_player is not None:
            try:
                _music_cache.stop(self._music_player)
            except Exception:
                pass
            self._music_player = None

    # ---------------------------------------------------------------- properties

    def is_active(self) -> bool:
        """Vrai si le ZombieManager considère le mode zombie actif."""
        return self.zombie_manager is not None and self.zombie_manager.is_active()

    @property
    def dying(self) -> bool:
        """Vrai si le fondu de mort est en cours ou le menu de mort est affiché."""
        return self._death_dir != 0 or (
            self._death_menu is not None and self._death_menu.active)

    @property
    def zombies(self) -> arcade.SpriteList:
        return self.zombie_manager.zombies if self.zombie_manager else arcade.SpriteList()

    @property
    def combat_walls(self) -> arcade.SpriteList:
        return self._combat_walls or arcade.SpriteList()

    # ---------------------------------------------------------------- update

    def update(self, delta_time: float) -> int:
        """Met à jour le mode zombie. Retourne le nombre de kills (0 pendant la mort)."""
        active = self.is_active()
        if active and not self._was_active:
            self._start_music()
        elif not active and self._was_active:
            self.stop_music()
        self._was_active = active

        if self.dying:
            self._mouse_held_left  = False
            self._mouse_held_right = False
            self._update_death_fade(delta_time)
            return 0

        if active:
            player = self._scene.player_sprite
            if self._mouse_held_left:
                self._fire_timer_left -= delta_time
                if self._fire_timer_left <= 0.0:
                    w = player.weapon_feu
                    self._fire_timer_left = w.fire_interval if w else _FIRE_INTERVAL_DEFAULT
                    self._attack_left()
            if self._mouse_held_right:
                self._fire_timer_right -= delta_time
                if self._fire_timer_right <= 0.0:
                    w = player.weapon_blanc
                    self._fire_timer_right = w.fire_interval if w else _FIRE_INTERVAL_DEFAULT
                    self._attack_right()

        self._melee_arcs = [a for a in self._melee_arcs if a["timer"] > 0]
        for arc in self._melee_arcs:
            arc["timer"] -= delta_time

        kills = self.zombie_manager.update(delta_time) + self._pending_melee_kills
        self._pending_melee_kills = 0
        player = self._scene.player_sprite
        self.zombie_manager.check_player_damage(player, delta_time)

        if player.health <= 0:
            self._death_dir = 1

        return kills

    def _update_death_fade(self, delta_time: float) -> None:
        _SPEED = 5
        if self._death_dir == 1:
            self._death_alpha = min(255, self._death_alpha + _SPEED)
            if self._death_alpha >= 255:
                self._death_dir = 0
                self._death_menu.active = True
        elif self._death_dir == -1:
            self._death_alpha = max(0, self._death_alpha - _SPEED)
            if self._death_alpha <= 0:
                self._death_dir = 0

    def _do_death_reset(self) -> None:
        scene = self._scene
        obj = scene.quest_manager.get_kill_objective()
        if obj:
            obj.counter = 0
            scene.quest_manager.save_progress()
        player             = scene.player_sprite
        player.health          = Player.MAX_HEALTH
        player.damage_cooldown = 0.0
        player.center_x, player.center_y = self._zombie_spawn
        self.zombie_manager.reset()

    # ---------------------------------------------------------------- draw

    def _draw_player_firearm(self) -> None:
        """Dessine le sprite de l'arme à feu pointé vers le curseur (world-space)."""
        player = self._scene.player_sprite
        weapon = player.weapon_feu
        if weapon is None:
            return
        world    = self._scene.camera_sprites.unproject((self.mouse_x, self.mouse_y))
        angle    = math.degrees(math.atan2(
            world.y - player.center_y, world.x - player.center_x))
        angle_rad = math.radians(angle)
        texture = weapon.get_texture()
        if texture:
            size   = weapon.sprite_size or max(texture.width, texture.height)
            offset = player.width / 2 + size / 2
            wx = player.center_x + offset * math.cos(angle_rad)
            wy = player.center_y + offset * math.sin(angle_rad)
            arcade.draw_texture_rect(
                texture,
                arcade.XYWH(wx, wy, size, size),
                angle=angle + 180,
                color=arcade.types.Color(255, 255, 255, 255),
            )
        else:
            barrel = player.width / 2 + 18
            tip_x  = player.center_x + barrel * math.cos(angle_rad)
            tip_y  = player.center_y + barrel * math.sin(angle_rad)
            arcade.draw_line(player.center_x, player.center_y, tip_x, tip_y, (70, 75, 85), 6)
            arcade.draw_line(wx, wy, tip_x, tip_y, (150, 155, 165), 3)

    def draw_world(self) -> None:
        """Dessine zombies, balles et animation de frappe (world-space, caméra déjà activée)."""
        self._draw_player_firearm()
        self.zombie_manager.draw()
        for arc in self._melee_arcs:
            ratio     = max(0.0, arc["timer"] / arc["max_timer"])
            progress  = 1.0 - ratio
            cur_angle = arc["angle"] - arc["half_span"] + progress * arc["half_span"] * 2
            angle_rad = math.radians(cur_angle)
            r  = arc["radius"]
            wx = arc["cx"] + r * math.cos(angle_rad)
            wy = arc["cy"] + r * math.sin(angle_rad)
            alpha = int(255 * ratio)

            texture  = arc.get("texture")
            ar, ag, ab = arc["arc_color"]
            if texture:
                size = arc.get("sprite_size") or max(texture.width, texture.height)
                arcade.draw_texture_rect(
                    texture,
                    arcade.XYWH(wx, wy, size, size),
                    angle=cur_angle - 90,
                    color=arcade.types.Color(255, 255, 255, alpha),
                )
            else:
                perp_rad = math.radians(cur_angle + 90)
                # Lame du centre du joueur jusqu'au bord du rayon
                arcade.draw_line(
                    arc["cx"], arc["cy"], wx, wy,
                    (190, 200, 210, alpha), 3)
                # Garde à 30 % du rayon
                gd = r * 0.3
                mid_x = arc["cx"] + gd * math.cos(angle_rad)
                mid_y = arc["cy"] + gd * math.sin(angle_rad)
                gx1 = mid_x + 5 * math.cos(perp_rad)
                gy1 = mid_y + 5 * math.sin(perp_rad)
                gx2 = mid_x - 5 * math.cos(perp_rad)
                gy2 = mid_y - 5 * math.sin(perp_rad)
                arcade.draw_line(gx1, gy1, gx2, gy2, (150, 120, 60, alpha), 3)

            a0    = arc["angle"] - arc["half_span"]
            a1    = arc["angle"] + arc["half_span"]
            col   = (ar, ag, ab, int(80 * ratio))
            a0r   = math.radians(a0)
            a1r   = math.radians(a1)
            arcade.draw_line(
                arc["cx"], arc["cy"],
                arc["cx"] + r * math.cos(a0r), arc["cy"] + r * math.sin(a0r),
                col, 1)
            arcade.draw_line(
                arc["cx"], arc["cy"],
                arc["cx"] + r * math.cos(a1r), arc["cy"] + r * math.sin(a1r),
                col, 1)
            arcade.draw_arc_outline(
                arc["cx"], arc["cy"], r, r,
                col, a0, a1, border_width=1)

    def draw_hud(self) -> None:
        """HUD zombie complet : indicateurs, overlay de mort et menu de mort."""
        self._draw_zombie_hud()
        self.draw_death_overlay()

    def draw_death_overlay(self) -> None:
        """Fondu et menu de mort uniquement. Peut être appelé indépendamment de is_active()."""
        if self._death_alpha > 0:
            arcade.draw_lrbt_rectangle_filled(
                0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, (0, 0, 0, self._death_alpha))
        if self._death_menu:
            self._death_menu.draw()

    def _draw_zombie_hud(self) -> None:
        obj = self._scene.quest_manager.get_kill_objective()
        if obj:
            arcade.draw_text(f"Zombies : {obj.counter} / {int(obj.validator)}",
                             WINDOW_WIDTH / 2, WINDOW_HEIGHT - 40,
                             arcade.color.RED, 20, anchor_x="center",
                             bold=True, font_name=KENNY)

        BAR_W, BAR_H = 200, 16
        bx     = WINDOW_WIDTH - BAR_W - 20
        by     = WINDOW_HEIGHT - 70
        player = self._scene.player_sprite
        ratio  = max(0.0, player.health / Player.MAX_HEALTH)
        bar_color = (arcade.color.JADE   if ratio > 0.5
                     else arcade.color.ORANGE if ratio > 0.25
                     else arcade.color.RED)
        arcade.draw_text("Vie", bx - 40, by + BAR_H / 2,
                         arcade.color.WHITE, 12, anchor_y="center", font_name=KENNY)
        arcade.draw_lrbt_rectangle_filled(bx, bx + BAR_W, by, by + BAR_H, (60, 10, 10))
        if ratio > 0:
            arcade.draw_lrbt_rectangle_filled(bx, bx + BAR_W * ratio, by, by + BAR_H, bar_color)
        arcade.draw_lrbt_rectangle_outline(bx, bx + BAR_W, by, by + BAR_H, arcade.color.WHITE, 1)
        arcade.draw_text(f"{player.health} / {Player.MAX_HEALTH}",
                         bx + BAR_W + 8, by + BAR_H / 2,
                         arcade.color.WHITE, 12, anchor_y="center", font_name=KENNY)

        _CW, _CH = 210, 88
        cx_card = bx - 40
        self._draw_weapon_card(player.weapon_feu,   cx_card, by - 14,            "Clic G")
        self._draw_weapon_card(player.weapon_blanc, cx_card, by - 14 - _CH - 6,  "Clic D")

    def _draw_weapon_card(self, w, cx: float, cy: float, label: str) -> None:
        """Dessine une carte arme avec nom, dégâts et info spécifique au type."""
        cw, ch, bar_w = 210, 88, 178
        arcade.draw_lrbt_rectangle_filled(cx, cx + cw, cy - ch, cy, (35, 35, 65, 220))
        arcade.draw_lrbt_rectangle_outline(cx, cx + cw, cy - ch, cy, arcade.color.WHITE, 1)
        arcade.draw_text(label, cx + 8, cy - 9,
                         arcade.color.LIGHT_GRAY, 9, anchor_y="center", font_name=KENNY)
        if w is None:
            arcade.draw_text("— vide —", cx + cw / 2, cy - ch / 2,
                             arcade.color.GRAY, 11, anchor_x="center",
                             anchor_y="center", font_name=KENNY)
            return
        arcade.draw_text(w.name, cx + 12, cy - 22,
                         arcade.color.WHITE, 13, bold=True,
                         anchor_y="center", font_name=KENNY)
        dmg_y = cy - 42
        arcade.draw_text("Dégâts :", cx + 12, dmg_y,
                         arcade.color.GRAY, 10, anchor_y="center", font_name=KENNY)
        arcade.draw_text(f"{w.damage_min:.1f} – {w.damage_max:.1f}",
                         cx + 85, dmg_y,
                         arcade.color.YELLOW, 11, anchor_y="center", font_name=KENNY)
        bry      = cy - 58
        fill_min = max(0.0, min(1.0, w.damage_min / 10.0))
        fill_max = max(0.0, min(1.0, w.damage_max / 10.0))
        arcade.draw_lrbt_rectangle_filled(cx + 12, cx + 12 + bar_w, bry, bry + 7, (50, 50, 70))
        arcade.draw_lrbt_rectangle_filled(cx + 12, cx + 12 + bar_w * fill_max, bry, bry + 7, (180, 60, 60))
        arcade.draw_lrbt_rectangle_filled(cx + 12, cx + 12 + bar_w * fill_min, bry, bry + 7, (220, 100, 60))
        arcade.draw_lrbt_rectangle_outline(cx + 12, cx + 12 + bar_w, bry, bry + 7, arcade.color.WHITE, 1)
        info_y = cy - 76
        if isinstance(w, FirearmWeapon):
            arcade.draw_text("Projectile :", cx + 12, info_y,
                             arcade.color.GRAY, 10, anchor_y="center", font_name=KENNY)
            r, g, b = w.bullet_color
            sw = 12
            arcade.draw_lrbt_rectangle_filled(
                cx + 90, cx + 90 + sw, info_y - sw / 2, info_y + sw / 2, (r, g, b))
            arcade.draw_lrbt_rectangle_outline(
                cx + 90, cx + 90 + sw, info_y - sw / 2, info_y + sw / 2, arcade.color.WHITE, 1)
        elif isinstance(w, MeleeWeapon):
            arcade.draw_text("Rayon :", cx + 12, info_y,
                             arcade.color.GRAY, 10, anchor_y="center", font_name=KENNY)
            arcade.draw_text(f"{int(w.attack_radius)} px", cx + 85, info_y,
                             arcade.color.YELLOW, 11, anchor_y="center", font_name=KENNY)

        mx, my = self.mouse_x, self.mouse_y
        arcade.draw_line(mx - 12, my, mx + 12, my, arcade.color.RED, 2)
        arcade.draw_line(mx, my - 12, mx, my + 12, arcade.color.RED, 2)
        arcade.draw_circle_outline(mx, my, 7, arcade.color.RED, 1)

    # ---------------------------------------------------------------- input

    def on_key_press(self, key: int) -> bool:
        """Gère les touches du mode zombie. Retourne True si la touche a été consommée."""
        scene = self._scene

        if self._death_menu and self._death_menu.active:
            choice = self._death_menu.handle_key(key)
            if choice == "Recommencer au début":
                self._death_menu.active = False
                self._do_death_reset()
                self._death_dir = -1
            elif choice == "Apparaître à la maison":
                self._death_menu.active = False
                self._do_death_reset()
                self._death_alpha = 255
                self._death_dir   = -1
                self.stop_music()
                scene.character_manager.save_player()
                scene.manager.switch_map("home")
            return True

        if self.is_active():
            scene.input_handler._handle_movement_keys(key)
            if key == arcade.key.P and not scene.show_menu:
                scene.window.show_view(StatsView(scene))
            elif key == arcade.key.ESCAPE:
                if scene.show_menu and scene.menu.has_sub():
                    scene.menu.handle_key(key)
                else:
                    scene.show_menu = not scene.show_menu
                    scene.menu.reset()
            elif scene.show_menu:
                scene.menu.handle_key(key)
            return True

        return False

    def _attack_left(self) -> None:
        """Clic gauche : délègue à weapon_feu.use()."""
        scene  = self._scene
        player = scene.player_sprite
        weapon = player.weapon_feu
        if weapon is None:
            return
        world = scene.camera_sprites.unproject((self.mouse_x, self.mouse_y))
        weapon.use(player, self.zombie_manager, world.x, world.y)

    def _attack_right(self) -> None:
        """Clic droit : délègue à weapon_blanc.use(), stocke l'arc retourné."""
        scene  = self._scene
        player = scene.player_sprite
        weapon = player.weapon_blanc
        if weapon is None:
            return
        world = scene.camera_sprites.unproject((self.mouse_x, self.mouse_y))
        kills, arc = weapon.use(player, self.zombie_manager, world.x, world.y)
        self._pending_melee_kills += kills
        if arc:
            self._melee_arcs.append(arc)

    def on_mouse_press(self, x: float, y: float, button: int) -> bool:
        """Attaque immédiate + activation du maintien (gauche = feu, droit = blanc)."""
        if not self.is_active():
            return False
        self.mouse_x, self.mouse_y = x, y
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._mouse_held_left = True
            w = self._scene.player_sprite.weapon_feu
            self._fire_timer_left = w.fire_interval if w else _FIRE_INTERVAL_DEFAULT
            self._attack_left()
            return True
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self._mouse_held_right = True
            if self._fire_timer_right <= 0.0:
                w = self._scene.player_sprite.weapon_blanc
                self._fire_timer_right = w.fire_interval if w else _FIRE_INTERVAL_DEFAULT
                self._attack_right()
            return True
        return False

    def on_mouse_release(self, button: int) -> None:
        """Désactive le maintien au relâchement."""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._mouse_held_left = False
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self._mouse_held_right = False

    def on_mouse_motion(self, x: float, y: float) -> None:
        """Mémorise la position de la souris pour le crosshair."""
        self.mouse_x, self.mouse_y = x, y
