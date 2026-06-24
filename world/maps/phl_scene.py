from __future__ import annotations
import arcade
from assets.param_map import KENNY, WINDOW_WIDTH, WINDOW_HEIGHT
from character.ai.kyle_ai import KyleAI
from world.scene.base_scene import BaseScene
from world.loader.map_loader import MapLoader
from world.zombie_mode import ZombieMode
import utils.paths as paths


class PhlScene(BaseScene):

    def __init__(self, environnement, quest_manager, character_manager):
        """Initialise PhlScene en déléguant entièrement à BaseScene."""
        super().__init__(environnement, quest_manager, character_manager)

    # ---------------------------------------------------------------- setup

    def setup(self, last_map: str | None) -> None:
        """Charge la tilemap PHL, positionne le joueur, instancie PNJs/objets, physique et zombies."""
        arc_id = self.quest_manager.arc.arc_id if self.quest_manager.arc else None
        loader = MapLoader("PHL", arc_id=arc_id)

        try:
            self.tile_map = arcade.load_tilemap(paths.asset(loader.get_tilemap_path()), scaling=1.0)
        except Exception as e:
            raise RuntimeError(f"Impossible de charger la carte PHL : {e}") from e

        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        self.player_sprite = self.character_manager.player
        spawn = self.character_manager.consume_pending_spawn()
        self.player_sprite.center_x, self.player_sprite.center_y = spawn if spawn else loader.get_player_spawn(last_map)
        self.scene.add_sprite("Player", self.player_sprite)

        self.behind_player = arcade.SpriteList()
        loader.load_pnjs(self, behind_player=self.behind_player)
        loader.load_strategiques(self)
        loader.load_objets(self)

        kyle_sprite = next((p for p in self.pnj_sprite if p.nom == "Kyle"), None)
        if kyle_sprite is not None and arc_id == 3:
            self.kyle_ai = KyleAI(kyle_sprite, self.quest_manager, self.tile_map)

        obstacles = self.interact_ui.create_obstacles()
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, obstacles)

        self._setup_zombie_mode()

    def _setup_zombie_mode(self) -> None:
        """Construit les murs de combat et initialise ZombieMode et KyleAI."""
        walls = arcade.SpriteList()
        walls.extend(self.scene["Mur"])
        walls.extend(self.scene["Meuble_H"])

        self.zombie_mode = ZombieMode(self)
        self.zombie_mode.setup(walls, [
            (574, 50),
            (92, 1114),
            (2516, 1854),
        ])

        if hasattr(self, "kyle_ai"):
            self.kyle_ai.init_path(walls)
            if self.zombie_mode.is_active():
                self.kyle_ai.start_walk()

    # ---------------------------------------------------------------- draw

    def on_draw(self) -> None:
        """Efface l'écran puis enchaîne le rendu world-space et le rendu GUI."""
        self.clear()
        self._draw_world()
        self.draw_stat_progress_bar()
        self.camera_gui.use()
        self._draw_hud()

    _STAND_ATTITUDES = {"errance", "stand", "dialogue"}

    def _draw_world(self) -> None:
        """Rendu world-space avec tri de profondeur : layers bas → PNJs → zombies → layers hauts → joueur."""
        self.camera_sprites.use()
        for layer in ("Sol", "Mur", "Meuble_B"):
            self.scene[layer].draw()

        before = arcade.SpriteList()
        after  = arcade.SpriteList()
        for pnj in self.pnj_sprite:
            if pnj.visible:
                if pnj.attitude in self._STAND_ATTITUDES:
                    before.append(pnj)
                else:
                    after.append(pnj)

        before.draw()
        self.zombie_mode.draw_world()
        for layer in ("Meuble_H", "Meuble_T", "Livre", "OrdiRPG", "PcTest", "Objets"):
            try:
                self.scene[layer].draw()
            except Exception:
                pass
        strat_visible = arcade.SpriteList()
        for pnj in self.strategique_sprite:
            if pnj.visible:
                strat_visible.append(pnj)
        strat_visible.draw()
        self.scene["Player"].draw()
        after.draw()
        if hasattr(self, "kyle_ai"):
            self.kyle_ai.sprite.draw_bullets()

        before.clear()
        after.clear()

        if not self.zombie_mode.is_active():
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
        """Rendu screen-space : bascule HUD zombie / HUD normal, puis mort, notifs, menu, cutscènes."""
        if self.zombie_mode.is_active():
            self.zombie_mode.draw_hud()
        else:
            self.dialogue.draw_dialogue_box()
            self.interact_ui.draw_box()
            self.get_quests()
            self.interact_ui.draw_side_bar()
            self.zombie_mode.draw_death_overlay()

        self.get_position()
        self.draw_notif()
        self.menu.draw()
        self.cutscene_manager.draw()

    # ---------------------------------------------------------------- update

    def on_update(self, delta_time: float) -> None:
        """Boucle logique : physique, stats, zombies, kills, mort et visibilité PNJs."""
        if self.show_menu:
            return
        self.update_auto_walk()
        self.physics_engine.update()
        self.scene.update(delta_time)
        self.follow_player()
        self.update_notif(delta_time)
        self.character_manager.update_player_stats(delta_time)

        arc_id = self.quest_manager.arc.arc_id if self.quest_manager.arc else None

        kills = self.zombie_mode.update(delta_time)
        for _ in range(kills):
            self.quest_manager.register_kill()

        if self.zombie_mode.dying:
            return

        if hasattr(self, "kyle_ai"):
            kyle_kills = self.kyle_ai.update(
                delta_time, self.zombie_mode.combat_walls,
                self.zombie_mode.zombies, arc_id == 3)
            for _ in range(kyle_kills):
                self.quest_manager.register_kill()

        self.window.set_mouse_visible(not self.zombie_mode.is_active())

        for pnj in self.pnj_sprite + self.strategique_sprite:
            pnj.visible = arc_id != 3 or pnj.nom == "Kyle"

    # ---------------------------------------------------------------- input

    def on_text(self, text: str) -> None:
        """Redirige la saisie texte vers le menu pause ou le système de dialogue."""
        if self.show_menu:
            self.menu.on_text(text)
        elif self.is_typing:
            self.dialogue.on_text(text)

    def on_key_press(self, key, modifiers) -> None:
        """Gère les touches : mode zombie en priorité, puis navigation normale."""
        if self.zombie_mode.on_key_press(key):
            return

        self.input_handler.handle_key_press(key, modifiers)
        if not self.is_typing and not self.cutscene_manager.any_active and key == arcade.key.ENTER:
            if self.current_strategique:
                self.character_manager.save_player()
                self.manager.switch_map("tma")
            elif self.current_objet and self.current_objet.name == "Mode mercenaire":
                self.character_manager.save_player()
                self.manager.switch_map("merc")
            elif 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600:
                self.character_manager.save_player()
                self.manager.switch_map("home")

    def on_key_release(self, key, modifiers) -> None:
        """Stoppe le déplacement du joueur à la relâche de la touche."""
        self.input_handler.reset_movement_on_release(key, modifiers)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        """Mode zombie : tir ; sinon délègue à l'input_handler."""
        if self.zombie_mode.on_mouse_press(x, y, button):
            return
        self.input_handler.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers) -> None:
        """Désactive le tir continu au relâchement du bouton gauche."""
        self.zombie_mode.on_mouse_release(button)

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        """Mémorise la position de la souris pour le crosshair."""
        self.zombie_mode.on_mouse_motion(x, y)

    def on_resize(self, width: int, height: int) -> None:
        """Recalibre la caméra world-space à la nouvelle taille de fenêtre."""
        super().on_resize(width, height)
        self.camera_sprites.match_window()
