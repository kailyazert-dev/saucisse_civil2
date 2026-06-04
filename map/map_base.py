from __future__ import annotations
import arcade
import os
import threading
import time
from dotenv import load_dotenv
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, MOVEMENT_SPEED, KENNY
from assets.param_humain import IbmI_personnage
import utils.paths as paths

try:
    import replicate as _replicate
    _REPLICATE_AVAILABLE = True
except ImportError:
    _replicate = None
    _REPLICATE_AVAILABLE = False

load_dotenv()
_API_KEY: str = os.getenv("REPLICATE_API_TOKEN", "")

_DIALOGUE_MAX_CHARS = 200  # longueur max d'un message joueur


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
        self.waiting_response = False  # True pendant l'appel API
        self.current_map_action = None

        self.quest_manager = quest_manager
        self.show_quests = False
        self.show_side_bar = False
        self.show_stats = False

        try:
            self.quest_texture = arcade.load_texture(paths.asset("map/map_tmx/bottom1.png"))
        except Exception as e:
            raise RuntimeError(f"Texture requise manquante : 'map/map_tmx/bottom1.png' — {e}") from e

        self.quest_width = self.quest_texture.width * 0.5
        self.quest_height = self.quest_texture.height * 0.5
        self.quest_x = 30 + self.quest_width / 2
        self.quest_y = WINDOW_HEIGHT - 30 - self.quest_height / 2

        self.show_menu = False

        self.keycaps = Keycaps(self)
        self.interact = Interact(self)
        self.talk = Talk(self)
        self.menu = Menu(self)
        self.quest_notif = QuestNotif()

    def set_manager(self, manager) -> None:
        self.manager = manager

    def create_obstacles(self):
        return self.interact.create_obstacles()

    def follow_player(self) -> None:
        position = (self.player_sprite.center_x, self.player_sprite.center_y)
        self.camera_sprites.position = arcade.math.lerp_2d(
            self.camera_sprites.position, position, self.camera_speed
        )

    def get_quests(self) -> None:
        if not self.show_stats and not self.show_quests:
            arcade.draw_texture_rect(
                self.quest_texture,
                arcade.XYWH(30, WINDOW_HEIGHT - 28, self.quest_texture.width, self.quest_texture.height).scale(0.5),
            )
            arcade.draw_text("Quests:", 50, self.height - 40, arcade.color.WHITE, 14, bold=True, font_name=KENNY)

    def update_notif(self, delta_time: float) -> None:
        self.quest_notif.update(delta_time, self.quest_manager.pending_notifications)

    def draw_notif(self) -> None:
        self.quest_notif.draw()

    def get_position(self) -> None:
        if self.player_sprite is None:
            return
        x = int(self.player_sprite.center_x)
        y = int(self.player_sprite.center_y)
        text = f"x: {x}   y: {y}"
        arcade.draw_text(text, 10, 10, arcade.color.WHITE, 14, font_name=KENNY)


# ---------------------------------------------------------------------------
class Keycaps:
    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view

    def on_mouse_press(self, x: float, y: float, button, modifiers) -> None:
        left = self.game_view.quest_x - self.game_view.quest_width
        right = self.game_view.quest_x + self.game_view.quest_width
        bottom = self.game_view.quest_y - self.game_view.quest_height / 2
        top = self.game_view.quest_y + self.game_view.quest_height
        if left <= x <= right and bottom <= y <= top:
            self.game_view.show_side_bar = not self.game_view.show_side_bar

        if self.game_view.show_stats:
            mini_world_pos = self.game_view.interact.mini_map_camera.unproject((x, y))
            mini_x, mini_y = mini_world_pos.x, mini_world_pos.y
            for tile in self.game_view.interact.choise_stat:
                if tile.left <= mini_x <= tile.right and tile.bottom <= mini_y <= tile.top:
                    self.game_view.interact.sous_box = self.game_view.interact.stat_map.sprite_lists["Stats-base"]
                    return
            for tile in self.game_view.interact.choise_bag:
                if tile.left <= mini_x <= tile.right and tile.bottom <= mini_y <= tile.top:
                    self.game_view.interact.sous_box = self.game_view.interact.stat_map.sprite_lists["Bag-base"]
                    return

    def handle_key_press(self, key, modifiers) -> None:
        if key == arcade.key.ESCAPE:
            self.game_view.show_menu = not self.game_view.show_menu
            self.game_view.menu.selected = 0
            return
        if self.game_view.show_menu:
            self.game_view.menu.handle_key(key)
            return
        self._to_reinit(key)
        if self._handle_movement_keys(key):
            return
        self._to_show_stat(key)
        self._to_show_quests(key)
        self._to_dialogue(key)
        self._up_stat(key)

    def _handle_movement_keys(self, key) -> bool:
        player = self.game_view.player_sprite
        if key == arcade.key.Z:
            player.change_y = MOVEMENT_SPEED
            player.direction = "up"
        elif key == arcade.key.S:
            player.change_y = -MOVEMENT_SPEED
            player.direction = "down"
        elif key == arcade.key.Q:
            player.change_x = -MOVEMENT_SPEED
            player.direction = "left"
        elif key == arcade.key.D:
            player.change_x = MOVEMENT_SPEED
            player.direction = "right"
        else:
            return False
        return True

    def reset_movement_on_release(self, key, modifiers) -> None:
        player = self.game_view.player_sprite
        if key == arcade.key.Z:
            player.change_y = 0
            player.texture = player.textures["up"]
        elif key == arcade.key.S:
            player.change_y = 0
            player.texture = player.textures["down"]
        elif key == arcade.key.Q:
            player.change_x = 0
            player.texture = player.textures["left"]
        elif key == arcade.key.D:
            player.change_x = 0
            player.texture = player.textures["right"]

    def _to_reinit(self, key) -> None:
        is_moving = key in (arcade.key.Z, arcade.key.S, arcade.key.Q, arcade.key.D)
        if not is_moving:
            return
        if self.game_view.is_typing:
            self.game_view.is_typing = False
            self.game_view.last_response = ""
            self.game_view.current_input = ""
            self.game_view.current_pnj = None
        if self.game_view.current_strategique:
            self.game_view.current_strategique = None
        if self.game_view.current_map_action:
            self.game_view.current_map_action = None
        if self.game_view.current_objet:
            self.game_view.current_objet = None
            self.game_view.character_manager.stop_up()
            self.game_view.character_manager.player.reading = False
        if self.game_view.current_collection:
            self.game_view.current_collection = None
            self.game_view.open_collection = False
            self.game_view.character_manager.stop_up()
            self.game_view.character_manager.player.reading = False

    def _up_stat(self, key) -> None:
        if self.game_view.current_map_action and key == arcade.key.ENTER:
            self.game_view.quest_manager.complete_map_action_objective(
                self.game_view.current_map_action.objective_name
            )
            self.game_view.current_map_action = None
            return
        if self.game_view.current_objet and key == arcade.key.ENTER:
            self.game_view.current_objet.utiliser(self.game_view.player_sprite, self.game_view.character_manager)
        elif self.game_view.current_collection:
            if key == arcade.key.ENTER:
                if self.game_view.open_collection:
                    livre = self.game_view.current_collection.upStats[self.game_view.current_index_upstat]
                    self.game_view.character_manager.player.reading = True
                    livre.utiliser(self.game_view.player_sprite, self.game_view.character_manager)
                else:
                    self.game_view.open_collection = True
            elif self.game_view.open_collection:
                nb = len(self.game_view.current_collection.upStats)
                if key == arcade.key.UP:
                    self.game_view.current_index_upstat = (self.game_view.current_index_upstat - 1) % nb
                elif key == arcade.key.DOWN:
                    self.game_view.current_index_upstat = (self.game_view.current_index_upstat + 1) % nb

    def _to_show_stat(self, key) -> None:
        if key == arcade.key.P:
            self.game_view.show_stats = not self.game_view.show_stats

    def _to_show_quests(self, key) -> None:
        if key != arcade.key.O:
            return
        self.game_view.show_quests = not self.game_view.show_quests
        arc = self.game_view.quest_manager.arc
        if arc is None:
            return
        quest = next((q for q in arc.quests if q.status == "ec"), None)
        if quest is None:
            return
        print(quest.title, quest.description, quest.status)
        for obj in quest.objectives:
            print(obj.name, obj.description, obj.status)

    def _to_dialogue(self, key) -> None:
        player = self.game_view.player_sprite
        pnjs = self.game_view.pnj_sprite
        if key == arcade.key.LALT:
            for pnj in pnjs:
                if arcade.get_distance_between_sprites(player, pnj) < 50:
                    dx = player.center_x - pnj.center_x
                    dy = player.center_y - pnj.center_y
                    if abs(dx) > abs(dy):
                        pnj.texture = pnj.textures["right"] if dx > 0 else pnj.textures["left"]
                    else:
                        pnj.texture = pnj.textures["up"] if dy > 0 else pnj.textures["down"]
                    self.game_view.current_pnj = pnj
                    self.game_view.is_typing = True
                    self.game_view.current_input = ""
                    self.game_view.quest_manager.complete_talk_objective(pnj.nom)
                    break
        elif self.game_view.is_typing and key == arcade.key.ENTER:
            if self.game_view.current_pnj and not self.game_view.waiting_response:
                self.game_view.talk.request_response(
                    self.game_view.current_input, self.game_view.current_pnj
                )
            self.game_view.current_input = ""
        elif self.game_view.is_typing and key == arcade.key.BACKSPACE:
            self.game_view.current_input = self.game_view.current_input[:-1]


# ---------------------------------------------------------------------------
class Interact:
    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view

        try:
            self.stat_map = arcade.load_tilemap(paths.asset("map/map_tmx/stat_box.tmx"), scaling=1)
            self.quest_map = arcade.load_tilemap(paths.asset("map/map_tmx/quests_box.tmx"), scaling=1)
        except Exception as e:
            raise RuntimeError(f"Impossible de charger les UI boxes : {e}") from e

        self.box_stat = arcade.Scene.from_tilemap(self.stat_map)
        self.base = self.stat_map.sprite_lists["Base"]
        self.top = self.stat_map.sprite_lists["Top-base"]
        self.choise_stat = self.stat_map.sprite_lists["Choise_1"]
        self.choise_bag = self.stat_map.sprite_lists["Choise_2"]
        self.sous_box = self.stat_map.sprite_lists["Stats-base"]
        self.box_quest = arcade.Scene.from_tilemap(self.quest_map)
        self.mini_map_camera = arcade.Camera2D()

        try:
            self.box_text = arcade.load_texture(paths.asset("map/map_tmx/use_box.png"))
            self.box_text_t = arcade.load_texture(paths.asset("map/map_tmx/use_box_t.png"))
            self.box_text_c = arcade.load_texture(paths.asset("map/map_tmx/use_box_c.png"))
            self.box_text_b = arcade.load_texture(paths.asset("map/map_tmx/use_box_b.png"))
        except Exception as e:
            raise RuntimeError(f"Texture d'interaction manquante : {e}") from e

    def draw_side_bar(self) -> None:
        if self.game_view.show_stats or self.game_view.show_quests or not self.game_view.show_side_bar:
            return
        arc = self.game_view.quest_manager.arc
        if arc is None:
            return
        quest = next((q for q in arc.quests if q.status == "ec"), None)
        if quest is None:
            return
        y = WINDOW_HEIGHT - 67
        arcade.draw_text(quest.title, 20, y, arcade.color.WHITE, 14, bold=True, font_name=KENNY)
        y -= 20
        for obj in quest.objectives:
            color = arcade.color.JADE if obj.status == "t" else arcade.color.WHITE
            arcade.draw_text(obj.name, 30, y, color, 12, bold=True, font_name=KENNY)
            y -= 20

    def draw_box(self) -> None:
        if self.game_view.show_stats:
            self.base.draw()
            self.top.draw()
            self.choise_stat.draw()
            self.choise_bag.draw()
            self.sous_box.draw()
            arcade.draw_text("Physique", 360, 640, arcade.color.ORANGE, 12, font_name=KENNY)
            arcade.draw_text("Intellect", 360, 592, arcade.color.ORANGE, 12, font_name=KENNY)
            arcade.draw_text("Sociale", 360, 544, arcade.color.ORANGE, 12, font_name=KENNY)
            if self.sous_box == self.stat_map.sprite_lists["Stats-base"]:
                y = 325
                arcade.draw_text("Stats physique", 247, 350, arcade.color.ORANGE, 12, font_name=KENNY)
                for key, value in self.game_view.player_sprite.humain.get_stats_physique():
                    arcade.draw_text(f"{key} : {value}", 247, y, arcade.color.BLACK, 12, font_name=KENNY)
                    y -= 25
                arcade.draw_text("Stats intellect", 447, 350, arcade.color.ORANGE, 12, font_name=KENNY)
                y = 325
                for key, value in self.game_view.player_sprite.humain.get_stats_intellect():
                    arcade.draw_text(f"{key} : {value}", 447, y, arcade.color.BLACK, 12, font_name=KENNY)
                    y -= 25
                arcade.draw_text("Stats sociale", 647, 350, arcade.color.ORANGE, 12, font_name=KENNY)
                y = 325
                for key, value in self.game_view.player_sprite.humain.get_stats_sociale():
                    arcade.draw_text(f"{key} : {value}", 647, y, arcade.color.BLACK, 12, font_name=KENNY)
                    y -= 25
        if self.game_view.show_quests:
            self.box_quest.draw()

    def draw_interact_box(self):
        arcade.get_window().use()
        player = self.game_view.player_sprite
        left = player.center_x + 25
        right = player.center_x + 200
        top = player.center_y - 25
        bottom = player.center_y - 75
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.WHITE)
        return left, top

    def create_obstacles(self):
        obstacles = arcade.SpriteList()
        obstacles.extend(self.game_view.pnj_sprite)
        obstacles.extend(self.game_view.strategique_sprite)
        obstacles.extend(self.game_view.objet_sprites)
        obstacles.extend(self.game_view.scene["Meuble_H"])
        obstacles.extend(self.game_view.scene["Mur"])
        return obstacles

    def get_r_corner_cord(self):
        arcade.get_window().use()
        player = self.game_view.player_sprite
        return player.center_x + 20, player.center_y - 55

    def interact_obj_prg(self) -> None:
        box_width = self.box_text.width - 10
        box_height = self.box_text.height - 40
        player = self.game_view.player_sprite
        qm = self.game_view.quest_manager

        # Passe 1 : MapActionObject — priorité sur les UpStats quand un objectif est actif
        for objet in self.game_view.objet_sprites:
            if type(objet).__name__ != "MapActionObject":
                continue
            if arcade.get_distance_between_sprites(player, objet) >= 68:
                continue
            if not objet.is_available(qm):
                continue
            left, top = self.get_r_corner_cord()
            self.game_view.current_map_action = objet
            arcade.draw_texture_rect(self.box_text, arcade.XYWH(left + box_width / 2, top, box_width, box_height))
            arcade.draw_text(objet.get_name(), left, top - 7, arcade.color.JADE, 12, box_width, "center", font_name=KENNY)
            return  # Un seul objet affiché à la fois

        # Passe 2 : UpStat / UpStatCollection
        for objet in self.game_view.objet_sprites:
            if arcade.get_distance_between_sprites(player, objet) >= 68:
                continue
            left, top = self.get_r_corner_cord()

            if type(objet).__name__ == "UpStat":
                self.game_view.current_objet = objet
                stat_name = objet.stat_cible
                player_level_stat = getattr(player.humain, stat_name)
                arcade.draw_texture_rect(self.box_text, arcade.XYWH(left + box_width / 2, top, box_width, box_height))
                color = (
                    arcade.color.GRAY_BLUE if player_level_stat >= objet.stat_max
                    else arcade.color.RED if player_level_stat < objet.stat_min
                    else arcade.color.JADE
                )
                arcade.draw_text(objet.get_name(), left, top - 7, color, 12, box_width, "center", font_name=KENNY)
                return

            if type(objet).__name__ == "UpStatCollection":
                self.game_view.current_collection = objet
                box_width += 10
                arcade.draw_texture_rect(self.box_text, arcade.XYWH(left + box_width / 2, top, box_width, box_height))
                arcade.draw_text(objet.get_name(), left, top - 7, arcade.color.JADE, 12, box_width, "center", font_name=KENNY)
                if self.game_view.current_collection and self.game_view.open_collection:
                    upstats = objet.get_all_upStats()
                    box_t_height = self.box_text_t.height - 8
                    box_c_height = self.box_text_c.height - 13
                    y_cursor = top - box_height / 2 - 4
                    arcade.draw_texture_rect(self.box_text_t, arcade.XYWH(left + box_width / 2, y_cursor, box_width, box_t_height))
                    y_cursor -= box_c_height / 2 + 3
                    y_pos = y_cursor + box_t_height / 2 - 4
                    for i, upstat in enumerate(upstats):
                        stat_name = upstat.stat_cible
                        player_level_stat = getattr(player.humain, stat_name)
                        color = (
                            arcade.color.GRAY_BLUE if player_level_stat >= upstat.stat_max
                            else arcade.color.RED if player_level_stat < upstat.stat_min
                            else arcade.color.JADE
                        )
                        arcade.draw_texture_rect(self.box_text_c, arcade.XYWH(left + box_width / 2, y_cursor, box_width, box_c_height))
                        prefix = "-> " if i == self.game_view.current_index_upstat else "   "
                        arcade.draw_text(prefix, left + 7, y_pos, arcade.color.BLACK, 10)
                        arcade.draw_text(upstat.get_name(), left + 26, y_pos, color, 10, font_name=KENNY)
                        y_cursor -= box_c_height
                        y_pos -= 35
                    y_cursor += box_c_height / 2
                    arcade.draw_texture_rect(self.box_text_b, arcade.XYWH(left + box_width / 2, y_cursor, box_width, box_t_height))
                return

    def interact_pnj_strateg(self) -> None:
        player = self.game_view.player_sprite
        for strategique in self.game_view.strategique_sprite:
            if arcade.get_distance_between_sprites(player, strategique) < 50:
                self.game_view.current_strategique = strategique
                arcade.draw_text("RALT : Aller à PHL", strategique.center_x - 90, strategique.center_y - 50, arcade.color.LIGHT_GREEN, 14, font_name=KENNY)
                arcade.draw_text(strategique.get_nom(), strategique.center_x - 40, strategique.center_y + 40, arcade.color.ALLOY_ORANGE, 14, font_name=KENNY)
                break

    def interact_pnj(self) -> None:
        player = self.game_view.player_sprite
        for pnj in self.game_view.pnj_sprite:
            if arcade.get_distance_between_sprites(player, pnj) < 50:
                left, top = self.draw_interact_box()
                arcade.draw_text(pnj.get_nom(), left + 15, top - 20, arcade.color.ORANGE, 14, font_name=KENNY)
                arcade.draw_text("LALT : Discuter", left + 15, top - 40, arcade.color.LIGHT_GREEN, 14, font_name=KENNY)
        if self.game_view.is_typing and self.game_view.current_pnj:
            self.game_view.talk.draw_dialogue_box()


# ---------------------------------------------------------------------------
class Talk:
    _MAX_CALLS = 3
    _PERIOD = 30.0  # 3 messages max par 30 secondes

    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view
        self._rate_calls: list[float] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ public

    def on_text(self, text: str) -> None:
        if self.game_view.is_typing and not self.game_view.waiting_response:
            if len(self.game_view.current_input) < _DIALOGUE_MAX_CHARS:
                self.game_view.current_input += text

    def request_response(self, message: str, pnj) -> None:
        """Lance l'appel API dans un thread séparé pour ne pas bloquer le jeu."""
        if self.game_view.waiting_response:
            return
        if self._is_rate_limited():
            self.game_view.last_response = "Je parle trop souvent. Attends un moment..."
            return
        clean = message.strip()
        if not clean:
            return
        self.game_view.waiting_response = True
        thread = threading.Thread(target=self._fetch_response, args=(clean, pnj), daemon=True)
        thread.start()

    def draw_dialogue_box(self) -> None:
        arcade.get_window().use()
        if not (self.game_view.is_typing or self.game_view.last_response):
            return
        margin = 15
        dialog_w = WINDOW_WIDTH - 2 * margin
        left = self.game_view.player_sprite.center_x - WINDOW_WIDTH // 2 + margin
        right = self.game_view.player_sprite.center_x + WINDOW_WIDTH // 2 - margin
        top = self.game_view.player_sprite.center_y - 100
        bottom = self.game_view.player_sprite.center_y - WINDOW_HEIGHT // 2 - 10
        arcade.draw_lrbt_rectangle_filled(left - margin, right + margin, bottom, top, arcade.color.WHITE)

        if self.game_view.is_typing:
            arcade.draw_text(
                f"{self.game_view.player_sprite.nom} : {self.game_view.current_input}",
                left, top - margin - 15,
                arcade.color.BLACK, 14,
                width=int(dialog_w), multiline=True,
            )

        if self.game_view.waiting_response:
            arcade.draw_text("...", left, top - margin - 45, arcade.color.GRAY, 14)
        elif self.game_view.last_response and self.game_view.current_pnj:
            arcade.draw_text(
                f"{self.game_view.current_pnj.nom} : {self.game_view.last_response}",
                left, top - margin - 45,
                arcade.color.LIGHT_GREEN, 14,
                width=int(dialog_w), multiline=True,
            )

    # ------------------------------------------------------------------ private

    def _is_rate_limited(self) -> bool:
        now = time.monotonic()
        with self._lock:
            self._rate_calls = [t for t in self._rate_calls if now - t < self._PERIOD]
            if len(self._rate_calls) >= self._MAX_CALLS:
                return True
            self._rate_calls.append(now)
            return False

    def _fetch_response(self, message: str, pnj) -> None:
        try:
            response = self._call_api(message, pnj)
        except Exception as e:
            print(f"[Talk] Erreur API : {e}")
            response = "Désolé, je suis occupé en ce moment..."
        self.game_view.last_response = response
        self.game_view.waiting_response = False

    def _call_api(self, message: str, pnj) -> str:
        if not _REPLICATE_AVAILABLE:
            return "[module replicate non installé]"
        if not _API_KEY:
            return "[clé API REPLICATE_API_TOKEN manquante dans .env]"

        os.environ["REPLICATE_API_TOKEN"] = _API_KEY
        nom = pnj.nom
        if nom in IbmI_personnage.personnages:
            d = IbmI_personnage.personnages[nom]
            system_prompt = (
                f"Tu es {d['nom']}, un personnage {d.get('type', 'mystérieux')}.\n"
                f"Ton métier est {d.get('metier', 'inconnu')}.\n"
                f"Tu as une personnalité {d.get('personnalite', 'mystérieuse')}.\n"
                f"Tes hobbies sont {d.get('hobbie', 'inconnus')}.\n"
                f"Réponds en 1-2 phrases, sans émoji."
            )
        else:
            system_prompt = "Tu es un personnage mystérieux. Reste vague et bref."

        full_prompt = f"{system_prompt}\nJoueur: {message}\n{nom}:"
        output = _replicate.run(
            "openai/gpt-4o-mini",
            input={"prompt": full_prompt, "max_new_tokens": 250, "temperature": 0.7},
        )
        return "".join(output)


# ---------------------------------------------------------------------------
class Menu:
    _OPTIONS = ["Reprendre", "Sauvegarder", "Réinitialiser", "Quitter"]
    _W = 320
    _H = 290

    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view
        self.selected = 0

    def draw(self) -> None:
        if not self.game_view.show_menu:
            return
        cx = WINDOW_WIDTH / 2
        cy = WINDOW_HEIGHT / 2
        arcade.draw_lrbt_rectangle_filled(
            cx - self._W / 2, cx + self._W / 2,
            cy - self._H / 2, cy + self._H / 2,
            (15, 15, 15, 210),
        )
        arcade.draw_lrbt_rectangle_outline(
            cx - self._W / 2, cx + self._W / 2,
            cy - self._H / 2, cy + self._H / 2,
            arcade.color.WHITE, 2,
        )
        arcade.draw_text("MENU", cx, cy + self._H / 2 - 35,
                         arcade.color.WHITE, 22, anchor_x="center", bold=True, font_name=KENNY)
        for i, opt in enumerate(self._OPTIONS):
            color = arcade.color.YELLOW if i == self.selected else arcade.color.WHITE
            arcade.draw_text(opt, cx, cy + 50 - i * 55,
                             color, 17, anchor_x="center", font_name=KENNY)

    def handle_key(self, key) -> None:
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self._OPTIONS)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self._OPTIONS)
        elif key == arcade.key.ENTER:
            self._confirm()

    def _confirm(self) -> None:
        opt = self._OPTIONS[self.selected]
        if opt == "Reprendre":
            self.game_view.show_menu = False
        elif opt == "Sauvegarder":
            self.game_view.character_manager.save_player()
            self.game_view.quest_manager.save_progress()
        elif opt == "Réinitialiser":
            self.game_view.character_manager.reset()
            self.game_view.quest_manager.reset()
            self.game_view.show_menu = False
            self.game_view.manager.switch_map("home")
        elif opt == "Quitter":
            arcade.exit()


# ---------------------------------------------------------------------------
class QuestNotif:
    _FADE_IN = 0.35
    _HOLD = 2.2
    _FADE_OUT = 0.55

    def __init__(self):
        self._queue: list[dict] = []
        self._current_text = ""
        self._current_type = ""
        self._state = "idle"
        self._timer = 0.0
        self._alpha = 0

    def update(self, delta_time: float, pending: list) -> None:
        while pending:
            self._queue.append(pending.pop(0))

        if self._state == "idle":
            if self._queue:
                n = self._queue.pop(0)
                self._current_text = n["text"]
                self._current_type = n["type"]
                self._state = "fade_in"
                self._timer = 0.0
                self._alpha = 0
            return

        self._timer += delta_time

        if self._state == "fade_in":
            self._alpha = min(255, int(255 * self._timer / self._FADE_IN))
            if self._timer >= self._FADE_IN:
                self._alpha = 255
                self._state = "hold"
                self._timer = 0.0
        elif self._state == "hold":
            if self._timer >= self._HOLD:
                self._state = "fade_out"
                self._timer = 0.0
        elif self._state == "fade_out":
            self._alpha = max(0, int(255 * (1.0 - self._timer / self._FADE_OUT)))
            if self._timer >= self._FADE_OUT:
                self._alpha = 0
                self._state = "idle"
                self._timer = 0.0

    def draw(self) -> None:
        if self._state == "idle" or self._alpha == 0:
            return

        cx = WINDOW_WIDTH / 2
        cy = WINDOW_HEIGHT * 0.68

        if self._current_type == "quest":
            r, g, b = 255, 172, 28   # ALLOY_ORANGE
            size = 24
        else:
            r, g, b = 0, 168, 107    # JADE
            size = 19

        bg_alpha = int(self._alpha * 0.72)
        pad_x, pad_y = 28, 14
        arcade.draw_lrbt_rectangle_filled(
            cx - 220, cx + 220,
            cy - pad_y, cy + size + pad_y,
            (0, 0, 0, bg_alpha),
        )
        arcade.draw_text(
            self._current_text,
            cx, cy + size / 2,
            (r, g, b, self._alpha),
            size,
            anchor_x="center",
            anchor_y="center",
            bold=True,
            font_name=KENNY,
        )
