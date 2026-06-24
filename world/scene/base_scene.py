from __future__ import annotations
import math
import arcade
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, KENNY, MOVEMENT_SPEED
from ui.menus.menu import Menu
from ui.hud.quest_notif import QuestNotif
from ui.cutscene.cutscene_manager import CutsceneManager
from input.input_handler import InputHandler
from ui.hud.interact_ui import InteractUI
from ui.dialogue.dialogue_system import DialogueSystem


class BaseScene(arcade.View):
    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__()
        self.environnement = environnement
        self.tile_map = None
        self.scene = None
        self.physics_engine = None
        self.camera_sprites = arcade.Camera2D()
        self.camera_gui = arcade.Camera2D()
        self.camera_speed = 0.1

        self.character_manager = character_manager
        self.player_sprite = None
        self.pnj_sprite = []
        self.current_pnj = None

        self.objet_sprites = []
        self.current_objet = None
        self.current_collection = None
        self.open_collection = False
        self.current_index_upstat = 0
        self.current_select_upstat = 0
        self.strategique_sprite = []
        self.current_strategique = None

        self.current_input = ""
        self.last_response = ""
        self.is_typing = False
        self.waiting_response = False
        self.current_map_action = None

        self.quest_manager = quest_manager
        self.show_side_bar = False

        self.quest_width  = 80
        self.quest_height = 26
        self.quest_x = 10 + self.quest_width / 2
        self.quest_y = WINDOW_HEIGHT - 10 - self.quest_height / 2

        self.show_menu = False

        self.zombie_mode        = None

        self.auto_walk_active   = False
        self.auto_walk_target   = (0.0, 0.0)
        self.auto_walk_path     = []
        self._on_auto_walk_done = None

        self.input_handler     = InputHandler(self)
        self.interact_ui       = InteractUI(self)
        self.dialogue          = DialogueSystem(self)
        self.menu              = Menu(self)
        self.quest_notif       = QuestNotif()
        self.cutscene_manager  = CutsceneManager(self)
        self.quest_manager._on_progress_save = self.character_manager.save_player

    def set_manager(self, manager) -> None:
        self.manager = manager

    def create_obstacles(self):
        return self.interact_ui.create_obstacles()

    def follow_player(self) -> None:
        position = (self.player_sprite.center_x, self.player_sprite.center_y)
        self.camera_sprites.position = arcade.math.lerp_2d(
            self.camera_sprites.position, position, self.camera_speed
        )

    def get_quests(self) -> None:
        x, y = self.quest_x, self.quest_y
        w, h = self.quest_width, self.quest_height
        bg = (50, 50, 90, 200) if self.show_side_bar else (20, 20, 50, 200)
        arcade.draw_lrbt_rectangle_filled(x - w / 2, x + w / 2, y - h / 2, y + h / 2, bg)
        arcade.draw_lrbt_rectangle_outline(x - w / 2, x + w / 2, y - h / 2, y + h / 2, arcade.color.WHITE, 1)
        arcade.draw_text("Quêtes", x, y, arcade.color.WHITE, 12,
                         anchor_x="center", anchor_y="center", bold=True, font_name=KENNY)

    def update_notif(self, delta_time: float) -> None:
        self.quest_notif.update(delta_time, self.quest_manager.pending_notifications)
        if self.quest_manager._needs_stat_check and self.player_sprite is not None:
            self.quest_manager.check_current_quest_stat_objectives(self.player_sprite)

    def draw_notif(self) -> None:
        self.quest_notif.draw()

    def get_position(self) -> None:
        if self.player_sprite is None:
            return
        x = int(self.player_sprite.center_x)
        y = int(self.player_sprite.center_y)
        arcade.draw_text(f"x: {x}   y: {y}", 10, 10, arcade.color.WHITE, 14, font_name=KENNY)

    def start_auto_walk(self, target_x: float, target_y: float,
                        path: list | None = None) -> None:
        self.auto_walk_target = (target_x, target_y)
        self.auto_walk_path   = list(path) if path else []
        self.auto_walk_active = True

    def update_auto_walk(self) -> None:
        if not self.auto_walk_active or self.player_sprite is None:
            return
        player = self.player_sprite

        if self.auto_walk_path:
            tx, ty = self.auto_walk_path[0]
        else:
            tx, ty = self.auto_walk_target

        dx   = tx - player.center_x
        dy   = ty - player.center_y
        dist = math.hypot(dx, dy)

        if dist <= MOVEMENT_SPEED:
            player.center_x = tx
            player.center_y = ty
            if self.auto_walk_path:
                self.auto_walk_path.pop(0)
                if self.auto_walk_path:
                    return
            player.change_x = 0
            player.change_y = 0
            player.texture  = player.textures[player.direction]
            self.auto_walk_active = False
            if self._on_auto_walk_done is not None:
                cb = self._on_auto_walk_done
                self._on_auto_walk_done = None
                cb()
            return

        nx, ny          = dx / dist, dy / dist
        player.change_x = nx * MOVEMENT_SPEED
        player.change_y = ny * MOVEMENT_SPEED
        if abs(dx) > abs(dy):
            player.direction = "right" if dx > 0 else "left"
        else:
            player.direction = "up" if dy > 0 else "down"

    _STAND_ATTITUDES = {"errance", "stand", "dialogue"}

    def on_draw(self) -> None:
        self.clear()
        self._draw_world()
        self.draw_stat_progress_bar()
        self.camera_gui.use()
        self._draw_hud()

    def _draw_world(self) -> None:
        pass

    def _draw_hud(self) -> None:
        pass

    def _split_pnjs_by_depth(self):
        before = arcade.SpriteList()
        after  = arcade.SpriteList()
        for pnj in self.pnj_sprite:
            if pnj.visible:
                if pnj.attitude in self._STAND_ATTITUDES:
                    before.append(pnj)
                else:
                    after.append(pnj)
        return before, after

    def _update_common(self, delta_time: float) -> bool:
        """Physique + caméra + stats. Retourne False si le menu est ouvert."""
        if self.show_menu:
            return False
        self.update_auto_walk()
        self.physics_engine.update()
        self.scene.update(delta_time)
        self.follow_player()
        self.update_notif(delta_time)
        self.character_manager.update_player_stats(delta_time)
        return True

    def _collect_layer(self, layer_name: str) -> list:
        try:
            return list(self.scene[layer_name])
        except Exception:
            return []

    def on_key_release(self, key, modifiers) -> None:
        self.input_handler.reset_movement_on_release(key, modifiers)

    def on_mouse_release(self, x, y, button, modifiers) -> None:
        if self.zombie_mode:
            self.zombie_mode.on_mouse_release(button)

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        if self.zombie_mode:
            self.zombie_mode.on_mouse_motion(x, y)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.camera_sprites.match_window()

    def draw_stat_progress_bar(self) -> None:
        cm = self.character_manager
        if not cm.up or cm.current_progresseur is None or self.player_sprite is None:
            return

        player  = self.player_sprite
        stat    = cm.stat_to_up
        current = getattr(player.humain, stat, 0.0)
        prog    = cm.current_progresseur
        filled  = max(0.0, min(1.0, (current - prog.stat_min) / max(prog.stat_max - prog.stat_min, 0.001)))
        tick    = min(1.0, cm.time_since_last_up_increase / cm.up_increase_interval)

        BAR_W, BAR_H, TICK_H = 84, 8, 3
        cx      = player.center_x
        bar_bot = player.top + 14

        arcade.draw_lrbt_rectangle_filled(
            cx - BAR_W / 2, cx + BAR_W / 2, bar_bot - TICK_H - 2, bar_bot - 2, (20, 20, 40, 180))
        arcade.draw_lrbt_rectangle_filled(
            cx - BAR_W / 2, cx - BAR_W / 2 + BAR_W * tick, bar_bot - TICK_H - 2, bar_bot - 2, (150, 180, 230, 210))

        arcade.draw_lrbt_rectangle_filled(
            cx - BAR_W / 2, cx + BAR_W / 2, bar_bot, bar_bot + BAR_H, (20, 20, 40, 200))
        arcade.draw_lrbt_rectangle_outline(
            cx - BAR_W / 2, cx + BAR_W / 2, bar_bot, bar_bot + BAR_H, arcade.color.WHITE, 1)
        if filled > 0:
            arcade.draw_lrbt_rectangle_filled(
                cx - BAR_W / 2, cx - BAR_W / 2 + BAR_W * filled, bar_bot, bar_bot + BAR_H, arcade.color.JADE)

        arcade.draw_text(stat.capitalize(), cx, bar_bot + BAR_H + 4,
                         arcade.color.WHITE, 9, anchor_x="center", font_name=KENNY)
