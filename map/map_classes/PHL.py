from __future__ import annotations
import arcade
from assets.param_map import PLAYER_SCALING, KENNY, WINDOW_WIDTH, WINDOW_HEIGHT
from character.character_classes import PNJ, Weapon
from map.map_base import BaseGameView
from map.map_loader import MapLoader, humain_from_data
from map.zombie_manager import ZombieManager
from map.ui_menus import DeathMenu
import utils.paths as paths

_ZOMBIE_SPAWN = (574, 50)  # position "home" dans PHL.json


# ---------------------------------------------------------------------------
class GameView(BaseGameView):

    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__(environnement, quest_manager, character_manager)

    # ---------------------------------------------------------------- setup

    def setup(self, last_map: str | None) -> None:
        loader = MapLoader("PHL")

        try:
            self.tile_map = arcade.load_tilemap(paths.asset(loader.get_tilemap_path()), scaling=1.0)
        except Exception as e:
            raise RuntimeError(f"Impossible de charger la carte PHL : {e}") from e

        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        self.player_sprite = self.character_manager.player
        self.player_sprite.center_x, self.player_sprite.center_y = loader.get_player_spawn(last_map)
        self.scene.add_sprite("Player", self.player_sprite)

        self.behind_player = arcade.SpriteList()
        loader.load_pnjs(self, behind_player=self.behind_player)
        loader.load_strategiques(self)
        loader.load_objets(self)
        self._setup_kyle()

        obstacles = self.interact_ui.create_obstacles()
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, obstacles)

        self._setup_zombie_mode()

        self._death_alpha = 0
        self._death_dir   = 0
        self._death_menu  = DeathMenu()
        self.mouse_x      = WINDOW_WIDTH  // 2
        self.mouse_y      = WINDOW_HEIGHT // 2

    def _setup_kyle(self) -> None:
        sitting_g = arcade.load_texture(paths.asset("assets/images/personnage_b_assit_g.png"))
        kyle = PNJ("Kyle", humain_from_data("Kyle"), "Male",
                   paths.asset("assets/images/personnage_b_assit_g.png"), PLAYER_SCALING,
                   attitude="assis")
        kyle.center_x = 690
        kyle.center_y = 848
        kyle.load_walk_textures("player")
        kyle._stand_textures = dict(kyle.textures)
        kyle._standing_tex   = kyle.textures["down"]
        kyle._sitting_tex    = sitting_g
        kyle.textures = {d: sitting_g for d in ("up", "down", "left", "right")}
        kyle.texture  = sitting_g
        kyle.speed    = 2.2
        kyle.weapon   = Weapon("TaMère", damage_min=2.0, damage_max=2.5,
                               bullet_color=(50, 130, 255))
        self.pnj_sprite.append(kyle)
        self.scene.add_sprite("Pnj", kyle)
        self.kyle_sprite = kyle

    def _setup_zombie_mode(self) -> None:
        walls = arcade.SpriteList()
        walls.extend(self.scene["Mur"])
        walls.extend(self.scene["Meuble_H"])

        self.zombie_manager = ZombieManager(self.quest_manager, self.player_sprite)
        self.zombie_manager.setup_walls(walls)
        self.zombie_manager.set_spawn_points([_ZOMBIE_SPAWN])
        self.player_sprite.weapon = Weapon("Pistolet", damage_min=1.0, damage_max=1.5)
        self._kyle_walls = walls

    # ---------------------------------------------------------------- draw

    def on_draw(self) -> None:
        self.clear()
        self._draw_world()
        self.draw_stat_progress_bar()
        self.camera_gui.use()
        self._draw_hud()

    def _draw_world(self) -> None:
        self.camera_sprites.use()
        for layer in ("Sol", "Mur", "Meuble_B"):
            self.scene[layer].draw()
        self.behind_player.draw()
        self.zombie_manager.draw()
        for layer in ("Meuble_H", "Meuble_T", "Livre", "OrdiRPG", "PcTest"):
            self.scene[layer].draw()
        self.scene["Player"].draw()
        self.scene["Pnj"].draw()
        self.kyle_sprite.draw_bullets()

        if not self.zombie_manager.is_active():
            self.interact_ui.interact_obj_prg()
            self.interact_ui.interact_pnj_strateg()
            self.interact_ui.interact_pnj()
            if 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600:
                left, top = self.interact_ui.draw_interact_box()
                cx = left + (self.interact_ui._BOX_W - 10) / 2
                cy = top - self.interact_ui._BOX_H / 2
                arcade.draw_text("Sortie", cx, cy + 9, arcade.color.ORANGE, 13,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)
                arcade.draw_text("[Entrée] Maison", cx, cy - 9, self.interact_ui._HINT_COL, 11,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)

    def _draw_hud(self) -> None:
        if self.zombie_manager.is_active():
            self._draw_zombie_hud()
        else:
            self.dialogue.draw_dialogue_box()
            self.interact_ui.draw_box()
            self.get_quests()
            self.interact_ui.draw_side_bar()

        if self._death_alpha > 0:
            arcade.draw_lrbt_rectangle_filled(
                0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, (0, 0, 0, self._death_alpha))
        self._death_menu.draw()
        self.get_position()
        self.draw_notif()
        self.menu.draw()

    def _draw_zombie_hud(self) -> None:
        obj = self.quest_manager.get_kill_objective()
        if obj:
            arcade.draw_text(f"Zombies : {obj.counter} / {int(obj.validator)}",
                             WINDOW_WIDTH / 2, WINDOW_HEIGHT - 40,
                             arcade.color.RED, 20, anchor_x="center",
                             bold=True, font_name=KENNY)
        BAR_W, BAR_H = 200, 16
        bx    = WINDOW_WIDTH - BAR_W - 20
        by    = WINDOW_HEIGHT - 70
        ratio = max(0.0, self.player_sprite.health / 50)
        bar_color = (arcade.color.JADE   if ratio > 0.5
                     else arcade.color.ORANGE if ratio > 0.25
                     else arcade.color.RED)
        arcade.draw_text("Vie", bx - 40, by + BAR_H / 2,
                         arcade.color.WHITE, 12, anchor_y="center", font_name=KENNY)
        arcade.draw_lrbt_rectangle_filled(bx, bx + BAR_W, by, by + BAR_H, (60, 10, 10))
        if ratio > 0:
            arcade.draw_lrbt_rectangle_filled(bx, bx + BAR_W * ratio, by, by + BAR_H, bar_color)
        arcade.draw_lrbt_rectangle_outline(bx, bx + BAR_W, by, by + BAR_H, arcade.color.WHITE, 1)
        arcade.draw_text(f"{self.player_sprite.health} / 50",
                         bx + BAR_W + 8, by + BAR_H / 2,
                         arcade.color.WHITE, 12, anchor_y="center", font_name=KENNY)
        mx, my = self.mouse_x, self.mouse_y
        arcade.draw_line(mx - 12, my, mx + 12, my, arcade.color.RED, 2)
        arcade.draw_line(mx, my - 12, mx, my + 12, arcade.color.RED, 2)
        arcade.draw_circle_outline(mx, my, 7, arcade.color.RED, 1)

    # --------------------------------------------------------------- update

    def on_update(self, delta_time: float) -> None:
        self.physics_engine.update()
        self.scene.update(delta_time)
        self.follow_player()
        self.update_notif(delta_time)
        self.character_manager.update_player_stats(delta_time)

        if self._death_dir != 0 or self._death_menu.active:
            self._update_death_fade(delta_time)
            return

        zombie_active = self.zombie_manager.is_active()
        kills = self.zombie_manager.update(delta_time)
        for _ in range(kills):
            self.quest_manager.register_kill()
        self.zombie_manager.check_player_damage(self.player_sprite, delta_time)

        if self.player_sprite.health <= 0:
            self._death_dir = 1

        self.window.set_mouse_visible(not zombie_active)
        self._update_kyle(delta_time)

        hide_pnjs = self._pnjs_should_hide()
        for pnj in self.pnj_sprite + self.strategique_sprite:
            pnj.visible = not hide_pnjs or pnj is self.kyle_sprite

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

    def _kyle_state(self) -> str:
        if not self._pnjs_should_hide():
            return "sit"
        if self.zombie_manager.is_active():
            return "chasse"
        return "stand"

    def _update_kyle(self, dt: float) -> None:
        k     = self.kyle_sprite
        state = self._kyle_state()

        if state == "stand":
            k.attitude = "assis"
            k.texture  = k._standing_tex
            k.center_x = 694
            k.center_y = 787
        elif state == "chasse":
            if k.attitude != "chasse":
                k.attitude = "chasse"
                k.textures = k._stand_textures
            kills = k.update_ai(dt, walls=self._kyle_walls,
                                 zombies=self.zombie_manager.zombies)
            for _ in range(kills):
                self.quest_manager.register_kill()
        else:
            k.attitude = "assis"
            k.texture  = k._sitting_tex

    def _pnjs_should_hide(self) -> bool:
        arc = self.quest_manager.arc
        if arc is None:
            return False
        return any(q.title == "Aller au taf." for q in arc.quests)

    def _do_death_reset(self) -> None:
        obj = self.quest_manager.get_kill_objective()
        if obj:
            obj.counter = 0
            self.quest_manager.save_progress()
        self.player_sprite.health          = 50
        self.player_sprite.damage_cooldown = 0.0
        self.player_sprite.center_x        = _ZOMBIE_SPAWN[0]
        self.player_sprite.center_y        = _ZOMBIE_SPAWN[1]
        self.zombie_manager.reset()

    # --------------------------------------------------------- input

    def on_text(self, text: str) -> None:
        if self.is_typing:
            self.dialogue.on_text(text)

    def on_key_press(self, key, modifiers) -> None:
        if self._death_menu.active:
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
                self.character_manager.save_player()
                self.manager.switch_map("home")
            return

        if self.zombie_manager.is_active():
            self.input_handler._handle_movement_keys(key)
            if key == arcade.key.ESCAPE:
                self.show_menu = not self.show_menu
                self.menu.selected = 0
            elif self.show_menu:
                self.menu.handle_key(key)
            return

        self.input_handler.handle_key_press(key, modifiers)
        if not self.is_typing and key == arcade.key.ENTER:
            if self.current_strategique:
                self.character_manager.save_player()
                self.manager.switch_map("tma")
            elif 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600:
                self.character_manager.save_player()
                self.manager.switch_map("home")

    def on_key_release(self, key, modifiers) -> None:
        self.input_handler.reset_movement_on_release(key, modifiers)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        if self.zombie_manager.is_active() and button == arcade.MOUSE_BUTTON_LEFT:
            world = self.camera_sprites.unproject((x, y))
            self.zombie_manager.fire(
                self.player_sprite.center_x, self.player_sprite.center_y,
                world.x, world.y,
                weapon=self.player_sprite.weapon,
            )
            return
        self.input_handler.on_mouse_press(x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        self.mouse_x, self.mouse_y = x, y

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.camera_sprites.match_window()
