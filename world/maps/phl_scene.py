from __future__ import annotations
import arcade
from assets.param_map import PLAYER_SCALING, KENNY, WINDOW_WIDTH, WINDOW_HEIGHT
from character.enemies.zombie_manager import ZombieManager
from character.ai.kyle_ai import KyleAI
from world.scene.base_scene import BaseScene
from world.loader.map_loader import MapLoader
from ui.menus.death_menu import DeathMenu
from ui.menus.stats_view import StatsView
import utils.paths as paths

_ZOMBIE_SPAWN = (574, 50)

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

        self._death_alpha = 0
        self._death_dir   = 0
        self._death_menu  = DeathMenu()
        self.mouse_x      = WINDOW_WIDTH  // 2
        self.mouse_y      = WINDOW_HEIGHT // 2

    def _setup_zombie_mode(self) -> None:
        """Configure le ZombieManager : obstacles de pathfinding et points de spawn."""
        walls = arcade.SpriteList()
        walls.extend(self.scene["Mur"])
        walls.extend(self.scene["Meuble_H"])
        self._combat_walls = walls

        self.zombie_manager = ZombieManager(self.quest_manager, self.player_sprite)
        self.zombie_manager.setup_walls(walls)
        self.zombie_manager.set_spawn_points([
            (574, 50),    # Entrée cuisine
            (92, 1114),   # Entrée formation
            (2516, 1854), # Entrée wall
        ])

        if hasattr(self, "kyle_ai"):
            self.kyle_ai.init_path(walls)
            if self.zombie_manager.is_active():
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
        """Rendu world-space avec tri de profondeur : layers bas → PNJs debout → zombies → layers hauts → joueur → PNJs en mouvement."""
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
        self.zombie_manager.draw()
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
        """Rendu screen-space : bascule entre le HUD zombie et le HUD normal, puis dessine toujours le fondu de mort, les notifications, le menu et les cutscènes."""
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
        self.cutscene_manager.draw()

    def _draw_zombie_hud(self) -> None:
        """Affiche le compteur de kills, la barre de vie, le panneau d'arme et le crosshair de visée."""
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

        w = self.player_sprite.weapon
        if w is not None:
            cx      = bx - 40
            cy      = by - 14
            cw      = BAR_W + 48
            ch      = 110
            bar_w   = cw - 32

            arcade.draw_lrbt_rectangle_filled(cx, cx + cw, cy - ch, cy, (35, 35, 65, 220))
            arcade.draw_lrbt_rectangle_outline(cx, cx + cw, cy - ch, cy, arcade.color.WHITE, 1)

            arcade.draw_text(w.name, cx + 16, cy - 22,
                             arcade.color.WHITE, 14, bold=True,
                             anchor_y="center", font_name=KENNY)

            dmg_y = cy - 46
            arcade.draw_text("Dégâts :", cx + 16, dmg_y,
                             arcade.color.GRAY, 11, anchor_y="center", font_name=KENNY)
            arcade.draw_text(f"{w.damage_min:.1f}  –  {w.damage_max:.1f}",
                             cx + 95, dmg_y,
                             arcade.color.YELLOW, 12, anchor_y="center", font_name=KENNY)

            bry = cy - 64
            fill_min = max(0.0, min(1.0, w.damage_min / 10.0))
            fill_max = max(0.0, min(1.0, w.damage_max / 10.0))
            arcade.draw_lrbt_rectangle_filled(cx + 16, cx + 16 + bar_w, bry, bry + 8, (50, 50, 70))
            arcade.draw_lrbt_rectangle_filled(cx + 16, cx + 16 + bar_w * fill_max, bry, bry + 8, (180, 60, 60))
            arcade.draw_lrbt_rectangle_filled(cx + 16, cx + 16 + bar_w * fill_min, bry, bry + 8, (220, 100, 60))
            arcade.draw_lrbt_rectangle_outline(cx + 16, cx + 16 + bar_w, bry, bry + 8, arcade.color.WHITE, 1)

            proj_y = cy - 90
            arcade.draw_text("Projectile :", cx + 16, proj_y,
                             arcade.color.GRAY, 11, anchor_y="center", font_name=KENNY)
            r, g, b = w.bullet_color
            sw = 14
            arcade.draw_lrbt_rectangle_filled(cx + 100, cx + 100 + sw, proj_y - sw / 2, proj_y + sw / 2, (r, g, b))
            arcade.draw_lrbt_rectangle_outline(cx + 100, cx + 100 + sw, proj_y - sw / 2, proj_y + sw / 2, arcade.color.WHITE, 1)

        mx, my = self.mouse_x, self.mouse_y
        arcade.draw_line(mx - 12, my, mx + 12, my, arcade.color.RED, 2)
        arcade.draw_line(mx, my - 12, mx, my + 12, arcade.color.RED, 2)
        arcade.draw_circle_outline(mx, my, 7, arcade.color.RED, 1)

    # ---------------------------------------------------------------- update

    def on_update(self, delta_time: float) -> None:
        """Boucle logique : physique, stats, zombies, kills, dégâts joueur et visibilité des PNJs selon l'arc."""
        if self.show_menu:
            return
        self.update_auto_walk()

        self.physics_engine.update()
        self.scene.update(delta_time)
        self.follow_player()
        self.update_notif(delta_time)
        self.character_manager.update_player_stats(delta_time)

        if self._death_dir != 0 or self._death_menu.active:
            self._update_death_fade(delta_time)
            return

        arc_id = self.quest_manager.arc.arc_id if self.quest_manager.arc else None

        zombie_active = self.zombie_manager.is_active()
        kills = self.zombie_manager.update(delta_time)
        for _ in range(kills):
            self.quest_manager.register_kill()

        if hasattr(self, "kyle_ai"):
            kyle_kills = self.kyle_ai.update(delta_time, self._combat_walls, self.zombie_manager.zombies, arc_id == 3)
            for _ in range(kyle_kills):
                self.quest_manager.register_kill()

        self.zombie_manager.check_player_damage(self.player_sprite, delta_time)

        if self.player_sprite.health <= 0:
            self._death_dir = 1

        self.window.set_mouse_visible(not zombie_active)

        for pnj in self.pnj_sprite + self.strategique_sprite:
            pnj.visible = arc_id != 3 or pnj.nom == "Kyle"

    def _update_death_fade(self, delta_time: float) -> None:
        """Anime le fondu noir de mort : monte vers 255 (dir=1) ou descend vers 0 (dir=-1), active le DeathMenu quand l'écran est plein noir."""
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
        """Réinitialise l'état après la mort : kills à 0, PV à 50, téléportation au spawn, reset des zombies."""
        obj = self.quest_manager.get_kill_objective()
        if obj:
            obj.counter = 0
            self.quest_manager.save_progress()
        self.player_sprite.health          = 50
        self.player_sprite.damage_cooldown = 0.0
        self.player_sprite.center_x        = _ZOMBIE_SPAWN[0]
        self.player_sprite.center_y        = _ZOMBIE_SPAWN[1]
        self.zombie_manager.reset()

    # ---------------------------------------------------------------- input

    def on_text(self, text: str) -> None:
        """Redirige la saisie texte vers le menu pause ou le système de dialogue selon l'état actif."""
        if self.show_menu:
            self.menu.on_text(text)
        elif self.is_typing:
            self.dialogue.on_text(text)

    def on_key_press(self, key, modifiers) -> None:
        """Gère les touches selon le mode actif : DeathMenu, combat zombie ou navigation normale (changements de map via ENTER)."""
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
            if key == arcade.key.P and not self.show_menu:
                self.window.show_view(StatsView(self))
            elif key == arcade.key.ESCAPE:
                if self.show_menu and self.menu.has_sub():
                    self.menu.handle_key(key)
                else:
                    self.show_menu = not self.show_menu
                    self.menu.reset()
            elif self.show_menu:
                self.menu.handle_key(key)
            return

        self.input_handler.handle_key_press(key, modifiers)
        if not self.is_typing and not self.cutscene_manager.any_active and key == arcade.key.ENTER:
            if self.current_strategique:
                self.character_manager.save_player()
                self.manager.switch_map("tma")
            elif 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600:
                self.character_manager.save_player()
                self.manager.switch_map("home")

    def on_key_release(self, key, modifiers) -> None:
        """Stoppe le déplacement du joueur à la relâche de la touche."""
        self.input_handler.reset_movement_on_release(key, modifiers)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        """En mode zombie, clic gauche = tir vers la position monde ; sinon délègue à l'input_handler."""
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
        """Mémorise la position de la souris pour positionner le crosshair en mode zombie."""
        self.mouse_x, self.mouse_y = x, y

    def on_resize(self, width: int, height: int) -> None:
        """Recalibre la caméra world-space à la nouvelle taille de fenêtre."""
        super().on_resize(width, height)
        self.camera_sprites.match_window()
