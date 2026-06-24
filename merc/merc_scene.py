from __future__ import annotations
import os
import arcade
from world.scene.base_scene import BaseScene
from world.loader.map_loader import MapLoader
from world.zombie_mode import ZombieMode
from quests.quest_manager import QuestManager
from character.equipment.weapon import Weapon
import utils.paths as paths

_MERC_QUESTS_DIR = os.path.join(paths.get_project_root(), "merc", "quests")
_QUEST1_SPAWNS   = [(570, 80), (575, 547)]
_QUEST2_SPAWNS   = [(570, 80), (528, 1123), (1946, 652)]
_QUEST3_SPAWNS   = [(570, 80), (528, 1123), (2686, 1108)]
_QUEST4_SPAWNS   = [(570, 80), (528, 1123), (2686, 1108), (2517, 1846)]


class MercScene(BaseScene):

    def __init__(self, environnement, quest_manager, character_manager):
        """Initialise MercScene en déléguant entièrement à BaseScene."""
        super().__init__(environnement, quest_manager, character_manager)

    # ---------------------------------------------------------------- setup

    def setup(self, last_map: str | None) -> None:
        """Charge la tilemap MERC, positionne le joueur, instancie PNJs/objets, physique et zombies."""
        self.quest_manager = QuestManager(
            quest_file=os.path.join(_MERC_QUESTS_DIR, "quests.json"),
            quests_save_file="merc_quests_save.json",
            quests_default_file=os.path.join(_MERC_QUESTS_DIR, "merc_quests_default.json"),
        )
        self.quest_manager.save_progress = lambda: None
        arc_id = self.quest_manager.arc.arc_id if self.quest_manager.arc else None
        loader = MapLoader("MERC", arc_id=arc_id, config_path="merc/configs/MERC.json")

        try:
            self.tile_map = arcade.load_tilemap(paths.asset(loader.get_tilemap_path()), scaling=1.0)
        except Exception as e:
            raise RuntimeError(f"Impossible de charger la carte MERC : {e}") from e

        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        self.player_sprite = self.character_manager.player
        self.player_sprite.weapon_feu   = Weapon.from_name("Pistolet")
        self.player_sprite.weapon_blanc = Weapon.from_name("Couteau")
        spawn = self.character_manager.consume_pending_spawn()
        self.player_sprite.center_x, self.player_sprite.center_y = spawn if spawn else loader.get_player_spawn(last_map)
        self.scene.add_sprite("Player", self.player_sprite)

        loader.load_pnjs(self)
        loader.load_strategiques(self)
        loader.load_objets(self)

        self._hide_steps = False
        self._hide_step2 = False
        self._hide_step3 = False
        self._active_quest_id = None
        self._setup_zombie_mode()

    def _setup_zombie_mode(self) -> None:
        """Construit les murs de combat, la physique et initialise ZombieMode (toujours actif)."""
        walls = arcade.SpriteList()
        for layer in ("Mur", "Meuble_H", "step_1_H", "step_2", "step_3_H",
                      "hero_1", "hero_2", "hero_3"):
            walls.extend(self._collect_layer(layer))
        self._step1_sprites = self._collect_layer("step_1_H")
        self._step2_sprites = self._collect_layer("step_2")
        self._step3_sprites = self._collect_layer("step_3_B") + self._collect_layer("step_3_H")

        obstacles = arcade.SpriteList()
        obstacles.extend(self.pnj_sprite)
        obstacles.extend(self.strategique_sprite)
        obstacles.extend(self.objet_sprites)
        obstacles.extend(walls)
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, obstacles)

        self.zombie_mode = ZombieMode(self)
        self.zombie_mode.setup(walls, _QUEST1_SPAWNS, always_active=True)

    def _get_active_quest_id(self) -> int | None:
        if self.quest_manager.arc is None:
            return None
        for quest in self.quest_manager.arc.quests:
            if quest.status == "ec":
                return quest.id
        return None

    # ---------------------------------------------------------------- draw

    def _draw_world(self) -> None:
        """Rendu world-space : Sol/steps/Mur/Meuble_B → PNJs → zombies → couches hautes → joueur."""
        self.camera_sprites.use()
        for layer in ("Sol", "step_1_B", "step_1_H", "step_2", "step_3_B", "step_3_H", "Mur", "Meuble_B"):
            if self._hide_steps and layer in {"step_1_B", "step_1_H"}:
                continue
            if self._hide_step2 and layer == "step_2":
                continue
            if self._hide_step3 and layer in {"step_3_B", "step_3_H"}:
                continue
            try:
                self.scene[layer].draw()
            except Exception:
                pass

        before, after = self._split_pnjs_by_depth()
        before.draw()
        self.zombie_mode.draw_world()

        for layer in ("Meuble_H", "Meuble_T", "hero_1", "hero_2", "hero_3"):
            try:
                self.scene[layer].draw()
            except Exception:
                pass

        self.scene["Player"].draw()
        after.draw()

        before.clear()
        after.clear()

    def _draw_hud(self) -> None:
        """Rendu screen-space : HUD zombie (toujours actif), notifs et menu."""
        self.zombie_mode.draw_hud()
        self.get_position()
        self.draw_notif()
        self.menu.draw()
        self.cutscene_manager.draw()

    # ---------------------------------------------------------------- update

    def on_update(self, delta_time: float) -> None:
        """Boucle logique : physique, caméra, stats, zombies et mort."""
        if not self._update_common(delta_time):
            return

        kills = self.zombie_mode.update(delta_time)
        for _ in range(kills):
            self.quest_manager.register_kill()

        quest_id = self._get_active_quest_id()
        if quest_id != self._active_quest_id:
            self._active_quest_id = quest_id
            if quest_id == 2:
                self.zombie_mode.set_spawn_points(_QUEST2_SPAWNS)
                if not self._hide_steps:
                    self._hide_steps = True
                    for sprite in self._step1_sprites:
                        sprite.remove_from_sprite_lists()
            elif quest_id == 3:
                self.zombie_mode.set_spawn_points(_QUEST3_SPAWNS)
                if not self._hide_step2:
                    self._hide_step2 = True
                    for sprite in self._step2_sprites:
                        sprite.remove_from_sprite_lists()
            elif quest_id == 4:
                self.zombie_mode.set_spawn_points(_QUEST4_SPAWNS)
                if not self._hide_step3:
                    self._hide_step3 = True
                    for sprite in self._step3_sprites:
                        sprite.remove_from_sprite_lists()

        self.window.set_mouse_visible(False)

    # ---------------------------------------------------------------- input

    def on_text(self, text: str) -> None:
        """Redirige la saisie texte vers le menu pause."""
        if self.show_menu:
            self.menu.on_text(text)

    def on_key_press(self, key, modifiers) -> None:
        """Délègue entièrement au mode zombie (toujours actif)."""
        self.zombie_mode.on_key_press(key)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        """Clic gauche = tir immédiat + activation du tir continu."""
        self.zombie_mode.on_mouse_press(x, y, button)

