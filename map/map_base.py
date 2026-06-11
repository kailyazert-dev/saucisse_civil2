from __future__ import annotations
import arcade
from assets.param_map import WINDOW_HEIGHT, KENNY
from map.ui_menus import Menu, QuestNotif
from map.input_handler import InputHandler
from map.interact_system import InteractUI
from map.dialogue_system import DialogueSystem


class BaseGameView(arcade.View):
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

        self.input_handler = InputHandler(self)
        self.interact_ui   = InteractUI(self)
        self.dialogue      = DialogueSystem(self)
        self.menu          = Menu(self)
        self.quest_notif   = QuestNotif()

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

    def draw_notif(self) -> None:
        self.quest_notif.draw()

    def get_position(self) -> None:
        if self.player_sprite is None:
            return
        x = int(self.player_sprite.center_x)
        y = int(self.player_sprite.center_y)
        arcade.draw_text(f"x: {x}   y: {y}", 10, 10, arcade.color.WHITE, 14, font_name=KENNY)

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

        # Barre de tick (compteur jusqu'au prochain +0.002)
        arcade.draw_lrbt_rectangle_filled(
            cx - BAR_W / 2, cx + BAR_W / 2, bar_bot - TICK_H - 2, bar_bot - 2, (20, 20, 40, 180))
        arcade.draw_lrbt_rectangle_filled(
            cx - BAR_W / 2, cx - BAR_W / 2 + BAR_W * tick, bar_bot - TICK_H - 2, bar_bot - 2, (150, 180, 230, 210))

        # Barre de progression principale
        arcade.draw_lrbt_rectangle_filled(
            cx - BAR_W / 2, cx + BAR_W / 2, bar_bot, bar_bot + BAR_H, (20, 20, 40, 200))
        arcade.draw_lrbt_rectangle_outline(
            cx - BAR_W / 2, cx + BAR_W / 2, bar_bot, bar_bot + BAR_H, arcade.color.WHITE, 1)
        if filled > 0:
            arcade.draw_lrbt_rectangle_filled(
                cx - BAR_W / 2, cx - BAR_W / 2 + BAR_W * filled, bar_bot, bar_bot + BAR_H, arcade.color.JADE)

        arcade.draw_text(stat.capitalize(), cx, bar_bot + BAR_H + 4,
                         arcade.color.WHITE, 9, anchor_x="center", font_name=KENNY)
