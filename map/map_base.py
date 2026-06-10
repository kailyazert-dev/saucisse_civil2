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
        self.show_side_bar = False

        self.quest_width = 80
        self.quest_height = 26
        self.quest_x = 10 + self.quest_width / 2
        self.quest_y = WINDOW_HEIGHT - 10 - self.quest_height / 2

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
        text = f"x: {x}   y: {y}"
        arcade.draw_text(text, 10, 10, arcade.color.WHITE, 14, font_name=KENNY)

    def draw_stat_progress_bar(self) -> None:
        cm = self.character_manager
        if not cm.up or cm.current_progresseur is None or self.player_sprite is None:
            return

        player = self.player_sprite
        stat    = cm.stat_to_up
        current = getattr(player.humain, stat, 0.0)
        prog    = cm.current_progresseur
        filled  = max(0.0, min(1.0, (current - prog.stat_min) / max(prog.stat_max - prog.stat_min, 0.001)))
        tick    = min(1.0, cm.time_since_last_up_increase / cm.up_increase_interval)

        BAR_W, BAR_H, TICK_H = 84, 8, 3
        cx      = player.center_x
        bar_bot = player.top + 14

        # Barre de tick (compteur jusqu'au prochain +0.002)
        arcade.draw_lrbt_rectangle_filled(cx - BAR_W / 2, cx + BAR_W / 2, bar_bot - TICK_H - 2, bar_bot - 2, (20, 20, 40, 180))
        arcade.draw_lrbt_rectangle_filled(cx - BAR_W / 2, cx - BAR_W / 2 + BAR_W * tick,        bar_bot - TICK_H - 2, bar_bot - 2, (150, 180, 230, 210))

        # Barre de progression principale
        arcade.draw_lrbt_rectangle_filled(cx - BAR_W / 2, cx + BAR_W / 2, bar_bot, bar_bot + BAR_H, (20, 20, 40, 200))
        arcade.draw_lrbt_rectangle_outline(cx - BAR_W / 2, cx + BAR_W / 2, bar_bot, bar_bot + BAR_H, arcade.color.WHITE, 1)
        if filled > 0:
            arcade.draw_lrbt_rectangle_filled(cx - BAR_W / 2, cx - BAR_W / 2 + BAR_W * filled, bar_bot, bar_bot + BAR_H, arcade.color.JADE)

        # Nom de la stat
        arcade.draw_text(stat.capitalize(), cx, bar_bot + BAR_H + 4, arcade.color.WHITE, 9, anchor_x="center", font_name=KENNY)


# ---------------------------------------------------------------------------
class Keycaps:
    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view

    def on_mouse_press(self, x: float, y: float, button, modifiers) -> None:
        qx, qy = self.game_view.quest_x, self.game_view.quest_y
        qw, qh = self.game_view.quest_width / 2, self.game_view.quest_height / 2
        if qx - qw <= x <= qx + qw and qy - qh <= y <= qy + qh:
            self.game_view.show_side_bar = not self.game_view.show_side_bar


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
            self.game_view.window.show_view(StatsView(self.game_view))

    def _to_dialogue(self, key) -> None:
        player = self.game_view.player_sprite
        pnjs = self.game_view.pnj_sprite
        if key == arcade.key.LALT:
            for pnj in pnjs:
                if arcade.get_distance_between_sprites(player, pnj) < 70:
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
    _BOX_W    = 260
    _BOX_H    = 50
    _BOX_T_H  = 28
    _BOX_C_H  = 43
    _POP_BG   = (15, 15, 40, 215)
    _HINT_COL = (150, 180, 230)

    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view

    def draw_side_bar(self) -> None:
        if not self.game_view.show_side_bar:
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
        pass

    def draw_interact_box(self):
        arcade.get_window().use()
        player = self.game_view.player_sprite
        left  = player.center_x + 25
        top   = player.center_y - 25
        w, h  = self._BOX_W - 10, self._BOX_H
        self._draw_popup(left, top, w, h)
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

    def _draw_popup(self, left: float, top: float, w: float, h: float) -> None:
        arcade.draw_lrbt_rectangle_filled(left, left + w, top - h, top, self._POP_BG)
        arcade.draw_lrbt_rectangle_outline(left, left + w, top - h, top, arcade.color.WHITE, 1)

    def _draw_box_rect(self, cx: float, cy: float, w: float, h: float) -> None:
        self._draw_popup(cx - w / 2, cy + h / 2, w, h)

    def interact_obj_prg(self) -> None:
        box_width = self._BOX_W - 10
        box_height = self._BOX_H - 10
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
            cx = left + box_width / 2
            self._draw_box_rect(cx, top, box_width, box_height)
            arcade.draw_text(objet.get_name(), cx, top + 9, arcade.color.JADE, 13, anchor_x="center", anchor_y="center", font_name=KENNY)
            arcade.draw_text("[Entrée]", cx, top - 9, self._HINT_COL, 11, anchor_x="center", anchor_y="center", font_name=KENNY)
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
                cx = left + box_width / 2
                self._draw_box_rect(cx, top, box_width, box_height)
                color = (
                    arcade.color.GRAY_BLUE if player_level_stat >= objet.stat_max
                    else arcade.color.RED if player_level_stat < objet.stat_min
                    else arcade.color.JADE
                )
                at_max = player_level_stat >= objet.stat_max
                hint       = "Niveau max atteint" if at_max else "[Entrée]"
                hint_color = arcade.color.GRAY_BLUE if at_max else self._HINT_COL
                arcade.draw_text(objet.get_name(), cx, top + 9, color, 13, anchor_x="center", anchor_y="center", font_name=KENNY)
                arcade.draw_text(hint, cx, top - 9, hint_color, 11, anchor_x="center", anchor_y="center", font_name=KENNY)
                return

            if type(objet).__name__ == "UpStatCollection":
                self.game_view.current_collection = objet
                box_width += 10
                cx = left + box_width / 2

                if not self.game_view.open_collection:
                    self._draw_box_rect(cx, top, box_width, box_height)
                    arcade.draw_text(objet.get_name(), cx, top + 9, arcade.color.JADE, 13, anchor_x="center", anchor_y="center", font_name=KENNY)
                    arcade.draw_text("[Entrée]", cx, top - 9, self._HINT_COL, 11, anchor_x="center", anchor_y="center", font_name=KENNY)
                else:
                    upstats = objet.get_all_upStats()
                    HEADER_H = 30
                    ITEM_H   = 28
                    FOOTER_H = 36
                    total_h  = HEADER_H + ITEM_H * len(upstats) + FOOTER_H
                    bx       = cx - box_width / 2
                    b_top    = top + box_height / 2
                    b_bot    = b_top - total_h

                    arcade.draw_lrbt_rectangle_filled(bx, bx + box_width, b_bot, b_top, self._POP_BG)
                    arcade.draw_lrbt_rectangle_outline(bx, bx + box_width, b_bot, b_top, arcade.color.WHITE, 1)

                    header_cy = b_top - HEADER_H / 2
                    arcade.draw_text(objet.get_name(), cx, header_cy, arcade.color.JADE, 13, anchor_x="center", anchor_y="center", font_name=KENNY)

                    sep1 = b_top - HEADER_H
                    arcade.draw_line(bx + 4, sep1, bx + box_width - 4, sep1, arcade.color.WHITE, 1)

                    for i, upstat in enumerate(upstats):
                        stat_name = upstat.stat_cible
                        player_level_stat = getattr(player.humain, stat_name)
                        color = (
                            arcade.color.GRAY_BLUE if player_level_stat >= upstat.stat_max
                            else arcade.color.RED if player_level_stat < upstat.stat_min
                            else arcade.color.JADE
                        )
                        item_cy = sep1 - ITEM_H / 2 - i * ITEM_H
                        if i == self.game_view.current_index_upstat:
                            arcade.draw_lrbt_rectangle_filled(bx + 1, bx + box_width - 1, item_cy - ITEM_H / 2, item_cy + ITEM_H / 2, (50, 50, 90))
                        label = f"> {upstat.get_name()}" if i == self.game_view.current_index_upstat else upstat.get_name()
                        arcade.draw_text(label, cx, item_cy, color, 11, anchor_x="center", anchor_y="center", font_name=KENNY)

                    sep2 = sep1 - ITEM_H * len(upstats)
                    arcade.draw_line(bx + 4, sep2, bx + box_width - 4, sep2, arcade.color.WHITE, 1)

                    sel = upstats[self.game_view.current_index_upstat]
                    sel_stat_val = getattr(player.humain, sel.stat_cible)
                    sel_at_max   = sel_stat_val >= sel.stat_max

                    footer_cy = sep2 - FOOTER_H / 2
                    arcade.draw_text("↑ ↓   Naviguer", cx, footer_cy + 9, self._HINT_COL, 10, anchor_x="center", anchor_y="center", font_name=KENNY)
                    if sel_at_max:
                        arcade.draw_text("Niveau max atteint", cx, footer_cy - 9, arcade.color.GRAY_BLUE, 10, anchor_x="center", anchor_y="center", font_name=KENNY)
                    else:
                        arcade.draw_text("[Entrée]   Utiliser", cx, footer_cy - 9, self._HINT_COL, 10, anchor_x="center", anchor_y="center", font_name=KENNY)
                return

    def interact_pnj_strateg(self) -> None:
        player = self.game_view.player_sprite
        for strategique in self.game_view.strategique_sprite:
            dist = getattr(strategique, "interaction_distance", 50)
            if arcade.get_distance_between_sprites(player, strategique) < dist:
                self.game_view.current_strategique = strategique
                w, h = self._BOX_W - 10, self._BOX_H
                left = strategique.center_x - w / 2
                top  = strategique.center_y + 60
                self._draw_popup(left, top, w, h)
                cx, cy = left + w / 2, top - h / 2
                arcade.draw_text(strategique.get_nom(), cx, cy + 9, arcade.color.ORANGE, 13, anchor_x="center", anchor_y="center", font_name=KENNY)
                arcade.draw_text("RALT : Aller à PHL", cx, cy - 9, self._HINT_COL, 11, anchor_x="center", anchor_y="center", font_name=KENNY)
                break

    def interact_pnj(self) -> None:
        player = self.game_view.player_sprite
        for pnj in self.game_view.pnj_sprite:
            if arcade.get_distance_between_sprites(player, pnj) < 70:
                left, top = self.draw_interact_box()
                cx, cy = left + (self._BOX_W - 10) / 2, top - self._BOX_H / 2
                arcade.draw_text(pnj.get_nom(), cx, cy + 9, arcade.color.ORANGE, 13, anchor_x="center", anchor_y="center", font_name=KENNY)
                arcade.draw_text("LALT : Discuter", cx, cy - 9, self._HINT_COL, 11, anchor_x="center", anchor_y="center", font_name=KENNY)


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
        if not (self.game_view.is_typing or self.game_view.last_response):
            return

        PAD       = 16
        BOX_H     = 180
        SEP_H     = 36   # hauteur de la zone joueur
        RESP_H    = BOX_H - SEP_H
        BG        = (15, 15, 40, 230)
        HINT_COL  = (150, 180, 230)
        text_w    = WINDOW_WIDTH - 2 * PAD - 2 * PAD

        # Coordonnées GUI (ancrées en bas de l'écran)
        box_l = PAD
        box_r = WINDOW_WIDTH - PAD
        box_b = PAD
        box_t = PAD + BOX_H
        sep_y = box_b + SEP_H

        # Fond principal
        arcade.draw_lrbt_rectangle_filled(box_l, box_r, box_b, box_t, BG)
        arcade.draw_lrbt_rectangle_outline(box_l, box_r, box_b, box_t, arcade.color.WHITE, 1)
        # Séparateur horizontal
        arcade.draw_line(box_l + 4, sep_y, box_r - 4, sep_y, arcade.color.WHITE, 1)

        # ── Zone joueur (bas) ──────────────────────────────────────────────
        player_nom = self.game_view.player_sprite.nom
        cursor = "_" if not self.game_view.waiting_response else ""
        input_text = f"{player_nom} : {self.game_view.current_input}{cursor}"
        arcade.draw_text(input_text, box_l + PAD, sep_y - SEP_H / 2,
                         arcade.color.WHITE, 13,
                         anchor_y="center", font_name=KENNY,
                         width=int(text_w), multiline=False)
        arcade.draw_text("[Entrée] Envoyer", box_r - PAD, box_b + 10,
                         HINT_COL, 10, anchor_x="right", font_name=KENNY)

        # ── Zone PNJ (haut) ────────────────────────────────────────────────
        pnj = self.game_view.current_pnj
        if pnj:
            arcade.draw_text(pnj.nom, box_l + PAD, box_t - 14,
                             arcade.color.ORANGE, 13, bold=True,
                             anchor_y="center", font_name=KENNY)
        if self.game_view.waiting_response:
            arcade.draw_text("...", box_l + PAD, sep_y + RESP_H / 2,
                             HINT_COL, 14, anchor_y="center", font_name=KENNY)
        elif self.game_view.last_response and pnj:
            resp_t = arcade.Text(self.game_view.last_response,
                                 box_l + PAD, box_t - 28,
                                 arcade.color.WHITE, 13,
                                 font_name=KENNY,
                                 width=int(text_w),
                                 multiline=True,
                                 anchor_y="top")
            resp_t.draw()

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
class StatsView(arcade.View):
    _TABS = ["Stats", "Quêtes"]

    def __init__(self, game_view: BaseGameView, tab: int = 0):
        super().__init__()
        self._game_view = game_view
        self._tab = tab

    def on_draw(self):
        self.clear()
        pad = 50
        cx = WINDOW_WIDTH / 2

        arcade.draw_lrbt_rectangle_filled(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, (10, 10, 30, 255))
        arcade.draw_lrbt_rectangle_filled(pad, WINDOW_WIDTH - pad, pad, WINDOW_HEIGHT - pad, (25, 25, 50, 255))
        arcade.draw_lrbt_rectangle_outline(pad, WINDOW_WIDTH - pad, pad, WINDOW_HEIGHT - pad, arcade.color.WHITE, 2)

        player = self._game_view.player_sprite
        if player is None:
            return

        arcade.draw_text(player.nom, cx, WINDOW_HEIGHT - 90,
                         arcade.color.ORANGE, 18, anchor_x="center", font_name=KENNY)

        # Onglets
        tab_w, tab_h, tab_gap = 150, 34, 8
        total_tabs_w = len(self._TABS) * tab_w + (len(self._TABS) - 1) * tab_gap
        tab_start_x = cx - total_tabs_w / 2
        tab_bottom = WINDOW_HEIGHT - 148
        for i, name in enumerate(self._TABS):
            tx = tab_start_x + i * (tab_w + tab_gap)
            bg = (55, 55, 100) if i == self._tab else (30, 30, 60)
            arcade.draw_lrbt_rectangle_filled(tx, tx + tab_w, tab_bottom, tab_bottom + tab_h, bg)
            border = arcade.color.WHITE if i == self._tab else arcade.color.GRAY
            arcade.draw_lrbt_rectangle_outline(tx, tx + tab_w, tab_bottom, tab_bottom + tab_h, border, 1)
            color = arcade.color.WHITE if i == self._tab else arcade.color.GRAY
            arcade.draw_text(name, tx + tab_w / 2, tab_bottom + tab_h / 2,
                             color, 14, anchor_x="center", anchor_y="center",
                             bold=(i == self._tab), font_name=KENNY)

        sep_y = tab_bottom - 8
        arcade.draw_line(pad + 20, sep_y, WINDOW_WIDTH - pad - 20, sep_y, arcade.color.WHITE, 1)

        if self._tab == 0:
            self._draw_stats(player, sep_y - 20)
        else:
            self._draw_quests(sep_y - 20)

        arcade.draw_text("[← →] Changer d'onglet    [P] ou [Echap]  —  Fermer",
                         cx, pad + 16, arcade.color.GRAY, 12, anchor_x="center", font_name=KENNY)

    def _draw_stats(self, player, top_y: float):
        pad = 50
        col_w = (WINDOW_WIDTH - 2 * pad) / 3
        sections = [
            ("Physique",  player.humain.get_stats_physique()),
            ("Intellect", player.humain.get_stats_intellect()),
            ("Sociale",   player.humain.get_stats_sociale()),
        ]
        for i, (title, stats) in enumerate(sections):
            col_cx = pad + col_w * i + col_w / 2
            arcade.draw_text(title, col_cx, top_y,
                             arcade.color.ORANGE, 16, anchor_x="center", bold=True, font_name=KENNY)
            y = top_y - 50
            for name, value in stats:
                bar_x = col_cx - 80
                bar_w, bar_h = 160, 14
                filled = int(bar_w * min(float(value), 1.0))
                arcade.draw_lrbt_rectangle_filled(bar_x, bar_x + bar_w, y, y + bar_h, (60, 60, 80))
                arcade.draw_lrbt_rectangle_filled(bar_x, bar_x + filled, y, y + bar_h, arcade.color.JADE)
                arcade.draw_text(name, bar_x, y + 18, arcade.color.WHITE, 13, font_name=KENNY)
                arcade.draw_text(f"{float(value):.2f}", bar_x + bar_w + 8, y + 2, arcade.color.WHITE, 11, font_name=KENNY)
                y -= 70

    def _draw_quests(self, top_y: float):
        pad = 50
        cx = WINDOW_WIDTH / 2
        text_w = WINDOW_WIDTH - 2 * pad - 40

        arc = self._game_view.quest_manager.arc
        if arc is None:
            arcade.draw_text("Aucune quête disponible.", cx, top_y - 40,
                             arcade.color.GRAY, 14, anchor_x="center", font_name=KENNY)
            return
        quest = next((q for q in arc.quests if q.status == "ec"), None)
        if quest is None:
            arcade.draw_text("Aucune quête en cours.", cx, top_y - 40,
                             arcade.color.GRAY, 14, anchor_x="center", font_name=KENNY)
            return

        arcade.draw_text(quest.title, pad + 20, top_y,
                         arcade.color.WHITE, 16, bold=True, font_name=KENNY)

        desc = arcade.Text(quest.description, pad + 20, top_y - 26,
                           arcade.color.GRAY, 12, font_name=KENNY,
                           width=text_w, multiline=True, anchor_y="top")
        desc.draw()
        y = top_y - 26 - desc.content_height - 16

        arcade.draw_text("Objectifs :", pad + 20, y, arcade.color.ORANGE, 14, bold=True, font_name=KENNY)
        y -= 28
        for obj in quest.objectives:
            done = obj.status == "t"
            color = arcade.color.JADE if done else arcade.color.WHITE
            prefix = "[x]" if done else "[ ]"

            name_t = arcade.Text(f"{prefix}  {obj.name}", pad + 30, y,
                                 color, 13, font_name=KENNY,
                                 width=text_w - 10, multiline=True, anchor_y="top")
            name_t.draw()
            y -= name_t.content_height + 4

            if obj.description:
                sub_t = arcade.Text(obj.description, pad + 60, y,
                                    arcade.color.GRAY, 11, font_name=KENNY,
                                    width=text_w - 40, multiline=True, anchor_y="top")
                sub_t.draw()
                y -= sub_t.content_height + 6

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.P, arcade.key.ESCAPE):
            self.window.show_view(self._game_view)
        elif key == arcade.key.RIGHT:
            self._tab = (self._tab + 1) % len(self._TABS)
        elif key == arcade.key.LEFT:
            self._tab = (self._tab - 1) % len(self._TABS)


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
