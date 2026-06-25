from __future__ import annotations
import json
import math
import os
import arcade
from assets.param_map import WINDOW_WIDTH, KENNY
from world.scene.base_scene import BaseScene
from world.loader.map_loader import MapLoader
from world.zombie_mode import ZombieMode
from world.objects.interactables.coffre import Coffre
from quests.quest_manager import QuestManager
from character.equipment.weapon import Weapon
from character.enemies.zombie import Zombie
from ui.menus.shop_menu import ShopMenu
import utils.paths as paths

_ZOMBIE_CONFIG_PATH = os.path.join(paths.get_project_root(), "merc", "configs", "zombie.json")
_SHOP_CONFIG_PATH   = os.path.join(paths.get_project_root(), "merc", "configs", "shop.json")

_MERC_QUESTS_DIR = os.path.join(paths.get_project_root(), "merc", "quests")
_QUEST1_SPAWNS   = [(570, 80), (575, 547)]
_QUEST2_SPAWNS   = [(570, 80), (528, 1123), (1946, 652)]
_QUEST3_SPAWNS   = [(570, 80), (528, 1123), (2686, 1108)]
_QUEST4_SPAWNS   = [(570, 80), (528, 1123), (2517, 1846)]


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
            quests_default_file=os.path.join(_MERC_QUESTS_DIR, "quests.json"),
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
        self._player_spawn = spawn if spawn else loader.get_player_spawn(last_map)
        self.player_sprite.center_x, self.player_sprite.center_y = self._player_spawn
        self.scene.add_sprite("Player", self.player_sprite)

        loader.load_pnjs(self)
        loader.load_strategiques(self)
        loader.load_objets(self)

        self._hide_steps = False
        self._hide_step2 = False
        self._hide_step3 = False
        self._active_quest_id = None

        self._coffres    = [o for o in self.objet_sprites if isinstance(o, Coffre)]
        self._coffres_sl = arcade.SpriteList()
        for c in self._coffres:
            self._coffres_sl.append(c)
        self._shop_data  = self._load_shop_data()
        self._shop_menu  = ShopMenu()
        self._near_coffre = None

        self._setup_zombie_mode()

    @staticmethod
    def _load_shop_data() -> dict:
        with open(_SHOP_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _load_zombie_classes() -> list[type]:
        """Lit merc/configs/zombie.json et retourne une sous-classe de Zombie par quête."""
        with open(_ZOMBIE_CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)

        from world.objects.drops.gold_drop import GoldDrop
        from world.objects.drops.health_drop import HealthDrop
        drop_map = {"GoldDrop": GoldDrop, "HealthDrop": HealthDrop}

        classes = []
        for i, quete in enumerate(cfg.get("quetes", [{}]), start=1):
            stats = quete.get("stats", {})
            mouv  = quete.get("mouvement", {})
            drops = [
                (drop_map[d["type"]], d["chance"])
                for d in quete.get("drops", [])
                if d["type"] in drop_map
            ]
            MercZombie = type(f"MercZombie{i}", (Zombie,), {
                "MAX_HEALTH":      stats.get("max_sante",          Zombie.MAX_HEALTH),
                "DAMAGE":          stats.get("degats",             Zombie.DAMAGE),
                "VITESSE_ERRANCE": mouv.get("vitesse_errance",     Zombie.VITESSE_ERRANCE),
                "VITESSE_CHASSE":  mouv.get("vitesse_chasse_max",  Zombie.VITESSE_CHASSE),
                "ACCEL_CHASSE":    mouv.get("acceleration_chasse", Zombie.ACCEL_CHASSE),
                "RAYON_DETECTION": mouv.get("rayon_detection",     Zombie.RAYON_DETECTION),
                "RAYON_FUITE":     mouv.get("rayon_fuite",         Zombie.RAYON_FUITE),
                "CHANGEMENT_DIR":  tuple(mouv.get("changement_direction", list(Zombie.CHANGEMENT_DIR))),
                "_DROPS":          drops or None,
            })
            classes.append(MercZombie)
        return classes

    def _setup_zombie_mode(self) -> None:
        """Construit les murs de combat, la physique et initialise ZombieMode (toujours actif)."""
        self._walls = arcade.SpriteList()
        for layer in ("Mur", "Meuble_H", "step_1_H", "step_2", "step_3_H",
                      "hero_1", "hero_2", "hero_3"):
            self._walls.extend(self._collect_layer(layer))
        self._step1_sprites   = self._collect_layer("step_1_H")
        self._step2_sprites   = self._collect_layer("step_2")
        self._step3_B_sprites = self._collect_layer("step_3_B")
        self._step3_H_sprites = self._collect_layer("step_3_H")
        self._step3_sprites   = self._step3_B_sprites + self._step3_H_sprites

        self._obstacles = arcade.SpriteList()
        self._obstacles.extend(self.pnj_sprite)
        self._obstacles.extend(self.strategique_sprite)
        self._obstacles.extend(self.objet_sprites)
        self._obstacles.extend(self._walls)
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self._obstacles)

        self._zombie_classes = self._load_zombie_classes()
        self.zombie_mode = ZombieMode(self)
        self.zombie_mode.setup(self._walls, _QUEST1_SPAWNS, always_active=True,
                               zombie_class=self._zombie_classes[0],
                               player_spawn=self._player_spawn)
        self.zombie_mode.on_reset  = self._merc_reset
        self.zombie_mode.set_spawn_enabled(False)
        self._notif_was_active = False
        self._spawn_unlocked   = False

    def _merc_reset(self) -> None:
        """Réinitialisation complète après mort : terrain, quêtes, spawn et boutique."""
        if self._hide_steps:
            for sprite in self._step1_sprites:
                self._walls.append(sprite)
                self._obstacles.append(sprite)
                try: self.scene["step_1_H"].append(sprite)
                except Exception: pass
            self._hide_steps = False

        if self._hide_step2:
            for sprite in self._step2_sprites:
                self._walls.append(sprite)
                self._obstacles.append(sprite)
                try: self.scene["step_2"].append(sprite)
                except Exception: pass
            self._hide_step2 = False

        if self._hide_step3:
            for sprite in self._step3_B_sprites:
                try: self.scene["step_3_B"].append(sprite)
                except Exception: pass
            for sprite in self._step3_H_sprites:
                self._walls.append(sprite)
                self._obstacles.append(sprite)
                try: self.scene["step_3_H"].append(sprite)
                except Exception: pass
            self._hide_step3 = False

        self.player_sprite.weapon_feu   = Weapon.from_name("Pistolet")
        self.player_sprite.weapon_blanc = Weapon.from_name("Couteau")

        self.quest_manager.reset()
        self.zombie_mode.set_spawn_points(_QUEST1_SPAWNS)
        self.zombie_mode.set_zombie_class(self._zombie_classes[0])
        self.zombie_mode.set_spawn_enabled(False)
        self._active_quest_id  = None
        self._spawn_unlocked   = False
        self._notif_was_active = False
        self._shop_menu.close()
        self._near_coffre = None

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

        self._coffres_sl.draw()
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
        if self._near_coffre and not self._shop_menu.active:
            arcade.draw_text("[ E ]  Ouvrir le distributeur",
                             WINDOW_WIDTH / 2, 55,
                             arcade.color.YELLOW, 14,
                             anchor_x="center", bold=True, font_name=KENNY)
        self._shop_menu.draw(self.player_sprite)

    # ---------------------------------------------------------------- update

    def on_update(self, delta_time: float) -> None:
        """Boucle logique : physique, caméra, stats, zombies et mort."""
        if not self._update_common(delta_time):
            return

        if not self._spawn_unlocked:
            if not self.quest_notif.is_idle:
                self._notif_was_active = True
            elif self._notif_was_active:
                self.zombie_mode.set_spawn_enabled(True)
                self._spawn_unlocked = True

        if self._shop_menu.active:
            self._shop_menu.update(delta_time)

        self._near_coffre = None
        if not self._shop_menu.active:
            px, py = self.player_sprite.center_x, self.player_sprite.center_y
            for coffre in self._coffres:
                if math.hypot(coffre.center_x - px, coffre.center_y - py) <= Coffre.INTERACTION_DISTANCE:
                    self._near_coffre = coffre
                    break

        kills = self.zombie_mode.update(delta_time)
        for _ in range(kills):
            self.quest_manager.register_kill()

        quest_id = self._get_active_quest_id()
        if quest_id != self._active_quest_id:
            self._active_quest_id = quest_id
            if quest_id is not None and 1 <= quest_id <= len(self._zombie_classes):
                self.zombie_mode.set_zombie_class(self._zombie_classes[quest_id - 1])
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
        if self._shop_menu.active:
            self._shop_menu.handle_key(key, self.player_sprite)
            return
        if self._near_coffre and key in (arcade.key.E, arcade.key.RETURN):
            items = self._shop_data.get(self._near_coffre.catalogue, [])
            self._shop_menu.open(items)
            return
        self.zombie_mode.on_key_press(key)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        """Clic gauche = tir immédiat + activation du tir continu."""
        self.zombie_mode.on_mouse_press(x, y, button)

