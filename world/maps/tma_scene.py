from __future__ import annotations
import arcade
from world.scene.base_scene import BaseScene
from world.loader.map_loader import MapLoader
import utils.paths as paths


class TmaScene(BaseScene):

    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__(environnement, quest_manager, character_manager)

    def setup(self, last_map: str | None) -> None:
        arc_id = self.quest_manager.arc.arc_id if self.quest_manager.arc else None
        loader = MapLoader("TMA", arc_id=arc_id)

        try:
            self.tile_map = arcade.load_tilemap(paths.asset(loader.get_tilemap_path()), scaling=1.0)
        except Exception as e:
            raise RuntimeError(f"Impossible de charger la carte TMA : {e}") from e

        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.character_manager.set_map_bounds(
            self.tile_map.width * self.tile_map.tile_width,
            self.tile_map.height * self.tile_map.tile_height,
        )

        self.player_sprite = self.character_manager.player
        spawn = self.character_manager.consume_pending_spawn()
        self.player_sprite.center_x, self.player_sprite.center_y = spawn if spawn else loader.get_player_spawn(last_map)
        self.scene.add_sprite("Player", self.player_sprite)

        loader.load_pnjs(self)
        loader.load_strategiques(self)
        loader.load_objets(self)

        obstacles = self.interact_ui.create_obstacles()
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, obstacles)

    # ---------------------------------------------------------------- draw

    def on_draw(self) -> None:
        self.clear()
        self.camera_sprites.use()
        self.scene.draw()
        self.interact_ui.interact_obj_prg()
        self.interact_ui.interact_pnj_strateg()
        self.interact_ui.interact_pnj()
        self.draw_stat_progress_bar()
        self.camera_gui.use()
        self.dialogue.draw_dialogue_box()
        self.interact_ui.draw_box()
        self.get_quests()
        self.interact_ui.draw_side_bar()
        self.get_position()
        self.draw_notif()
        self.menu.draw()
        self.cutscene_manager.draw()

    # ---------------------------------------------------------------- update

    def on_update(self, delta_time: float) -> None:
        if self.show_menu:
            return
        self.update_auto_walk()
        self.physics_engine.update()
        self.scene.update(delta_time)
        self.follow_player()
        self.update_notif(delta_time)

    # ---------------------------------------------------------------- input

    def on_text(self, text: str) -> None:
        if self.show_menu:
            self.menu.on_text(text)
        elif self.is_typing:
            self.dialogue.on_text(text)

    def on_key_press(self, key, modifiers) -> None:
        self.input_handler.handle_key_press(key, modifiers)
        if self.current_strategique and not self.is_typing and not self.cutscene_manager.any_active and key == arcade.key.ENTER:
            self.character_manager.save_player()
            self.manager.switch_map("phl")

    def on_key_release(self, key, modifiers) -> None:
        self.input_handler.reset_movement_on_release(key, modifiers)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        self.input_handler.on_mouse_press(x, y, button, modifiers)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.camera_sprites.match_window()
