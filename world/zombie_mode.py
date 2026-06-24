from __future__ import annotations
import math
import random
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT
from character.enemies.zombie_manager import ZombieManager
from character.player.player import Player
from ui.menus.death_menu import DeathMenu
from ui.hud.zombie_hud import ZombieHUD
from ui.menus.stats_view import StatsView
from character.enemies.zombie import Zombie
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
        self.drops       = arcade.SpriteList()
        self._hud        = ZombieHUD(self)

    # ---------------------------------------------------------------- setup

    def set_spawn_points(self, points: list) -> None:
        if self.zombie_manager:
            self.zombie_manager.set_spawn_points(points)

    def set_spawn_enabled(self, enabled: bool) -> None:
        if self.zombie_manager:
            self.zombie_manager.spawn_enabled = enabled

    def set_zombie_class(self, zombie_class: type) -> None:
        if self.zombie_manager:
            self.zombie_manager._zombie_class = zombie_class

    def setup(self, walls: arcade.SpriteList, spawn_points: list,
              always_active: bool = False, zombie_class: type | None = None,
              player_spawn: tuple[float, float] | None = None) -> None:
        """Configure le ZombieManager, le DeathMenu, les points de spawn et la musique."""
        self._combat_walls = walls
        self._zombie_spawn = player_spawn or (spawn_points[0] if spawn_points else (574, 50))
        self._death_menu   = DeathMenu()

        scene = self._scene
        self.zombie_manager = ZombieManager(scene.quest_manager, scene.player_sprite,
                                            zombie_class=zombie_class)
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
            self.zombie_manager.morts_ce_frame.clear()
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

        for pos in self.zombie_manager.morts_ce_frame:
            self.drops.extend(Zombie.loot(*pos))

        player = self._scene.player_sprite
        self.zombie_manager.check_player_damage(player, delta_time)

        for drop in arcade.check_for_collision_with_list(player, self.drops):
            drop.ramasser(player)
            drop.remove_from_sprite_lists()

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
        player.gold            = 0
        player.center_x, player.center_y = self._zombie_spawn
        self.zombie_manager.reset()
        for drop in list(self.drops):
            drop.remove_from_sprite_lists()

    # ---------------------------------------------------------------- draw

    def draw_world(self) -> None:
        """Dessine arme, animation de frappe, zombies et drops (world-space, caméra déjà activée)."""
        self._hud.draw_world()
        self.zombie_manager.draw()
        self.drops.draw()

    def draw_hud(self) -> None:
        """HUD zombie complet : indicateurs, overlay de mort et menu de mort."""
        self._hud.draw_hud()
        self.draw_death_overlay()

    def draw_death_overlay(self) -> None:
        """Fondu et menu de mort uniquement. Peut être appelé indépendamment de is_active()."""
        if self._death_alpha > 0:
            arcade.draw_lrbt_rectangle_filled(
                0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, (0, 0, 0, self._death_alpha))
        if self._death_menu:
            self._death_menu.draw()

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
        """Clic gauche : délègue à weapon_feu.use(), balle depuis le bout du canon."""
        scene  = self._scene
        player = scene.player_sprite
        weapon = player.weapon_feu
        if weapon is None:
            return
        world     = scene.camera_sprites.unproject((self.mouse_x, self.mouse_y))
        angle_rad = math.atan2(world.y - player.center_y, world.x - player.center_x)
        texture   = weapon.get_texture()
        size      = weapon.sprite_size or (max(texture.width, texture.height) if texture else 0)
        offset    = player.width / 2 + player.width / 3 + size / 2
        spawn_x   = player.center_x + offset * math.cos(angle_rad)
        spawn_y   = player.center_y + offset * math.sin(angle_rad)
        weapon.use(player, self.zombie_manager, world.x, world.y,
                   spawn_x=spawn_x, spawn_y=spawn_y)

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
