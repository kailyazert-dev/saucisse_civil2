"""IA et machine à états de Kyle — extrait de PHL.py.

Avant : 6 méthodes + variable globale + 5 attributs d'instance dans PHL.py (80 lignes).
Après : classe autonome, testable, sans couplage à PHL.
"""
from __future__ import annotations
import math
import arcade
from character.pnj.pnj import PNJ
from core.constants import PHL_POSITIONS

# Cache A* inter-sessions (invalidé une fois la marche démarrée)
_path_cache: list | None = None


class KyleAI:
    """FSM pour Kyle dans la map PHL."""

    def __init__(self, sprite: PNJ, quest_manager, tile_map: arcade.TileMap):
        global _path_cache
        self.sprite       = sprite
        self._qm          = quest_manager
        self._tile_map    = tile_map

        self.walk_active  = False
        self.walk_done    = False
        self.end_talked   = False
        self._full_hitbox = False
        self._walk_path:  list = []
        self._path_cache: list | None = list(_path_cache) if _path_cache is not None else None

        self._init_hitbox()

    def init_path(self, walls: arcade.SpriteList) -> None:
        """Pré-calcule le chemin A* si la quête Kyle est active."""
        global _path_cache
        if not self._quest_active():
            return
        if self._path_cache is None:
            if _path_cache is not None:
                self._path_cache = list(_path_cache)
            else:
                self._path_cache = self._calc_astar(walls)
                _path_cache = list(self._path_cache)

    def start_walk(self) -> None:
        """Démarre la marche de Kyle vers la zone de combat."""
        global _path_cache
        self._walk_path  = list(self._path_cache or [])
        self.walk_active = True
        _path_cache      = None

    def update(self, dt: float, walls: arcade.SpriteList,
               zombies: arcade.SpriteList | None, pnjs_active: bool) -> int:
        """Met à jour Kyle. Retourne le nombre de zombies tués ce tick."""
        state = self._get_state(zombies, pnjs_active)
        self._update_hitbox(state)
        return self._run_state(state, dt, walls, zombies)

    # ---------------------------------------------------------------- private

    def _quest_active(self) -> bool:
        qm = self._qm
        if qm.arc is None or qm.arc.arc_id != 3:
            return False
        return any(q.id in (1, 2) and q.status == "ec" for q in qm.arc.quests)

    def _get_state(self, zombies, pnjs_active: bool) -> str:
        if not pnjs_active:
            return "sit"
        if self.walk_active:
            return "walk"
        if self.walk_done and self._qm.get_kill_objective() is not None:
            return "chasse"
        if self.walk_done:
            return "dialogue"
        return "stand"

    def _init_hitbox(self) -> None:
        k = self.sprite
        tex = k._standing_tex
        tw, th = tex.width / 2, tex.height / 2
        k.hit_box = arcade.hitbox.RotatableHitBox(
            [(-tw, 0), (tw, 0), (tw, th), (-tw, th)],
            position=k.position, angle=k.angle,
        )

    def _update_hitbox(self, state: str) -> None:
        k = self.sprite
        tw = k._standing_tex.width / 2
        th = k._standing_tex.height / 2
        if state == "chasse" and not self._full_hitbox:
            k.hit_box = arcade.hitbox.RotatableHitBox(
                [(-tw, -th), (tw, -th), (tw, th), (-tw, th)],
                position=k.position, angle=k.angle,
            )
            self._full_hitbox = True
        elif state != "chasse" and self._full_hitbox:
            k.hit_box = arcade.hitbox.RotatableHitBox(
                [(-tw, 0), (tw, 0), (tw, th), (-tw, th)],
                position=k.position, angle=k.angle,
            )
            self._full_hitbox = False

    def _run_state(self, state: str, dt: float,
                   walls: arcade.SpriteList, zombies) -> int:
        k = self.sprite
        if state == "sit":
            k.attitude = "assis"
            k.texture  = k._sitting_tex
            return 0
        if state == "stand":
            k.attitude = "stand"
            k.texture  = k._standing_tex
            k.center_x = PHL_POSITIONS.kyle_start_x
            k.center_y = PHL_POSITIONS.kyle_start_y
            return 0
        if state == "walk":
            return self._run_walk(k, dt)
        if state == "chasse":
            k.attitude = "chasse"
            k.textures = k._stand_textures
            return k.update_ai(dt, walls=walls, zombies=zombies)
        if state == "dialogue":
            k.attitude = "dialogue"
            k.texture  = k._standing_tex
            return 0
        return 0

    def _run_walk(self, k: PNJ, dt: float) -> int:
        if k.attitude != "chasse":
            k.attitude = "chasse"
        path = self._walk_path
        if not path:
            k.change_x = k.change_y = 0
            self.walk_active = False
            self.walk_done   = True
            return 0

        tx, ty = path[0]
        dx = tx - k.center_x
        dy = ty - k.center_y
        dist = math.hypot(dx, dy)
        if dist <= k.speed:
            k.center_x, k.center_y = tx, ty
            path.pop(0)
            k.change_x = k.change_y = 0
            if not path:
                self.walk_active = False
                self.walk_done   = True
                return 0
            tx, ty = path[0]
            dx = tx - k.center_x
            dy = ty - k.center_y
            dist = math.hypot(dx, dy)

        if dist > 0:
            nx, ny      = dx / dist, dy / dist
            k.center_x += nx * k.speed
            k.center_y += ny * k.speed
            k.change_x  = nx * k.speed
            k.change_y  = ny * k.speed
            k.direction = (
                ("right" if dx > 0 else "left") if abs(dx) > abs(dy)
                else ("up" if dy > 0 else "down")
            )
            k._animate(k.direction, dt)
        return 0

    def _calc_astar(self, walls: arcade.SpriteList) -> list:
        tm = self._tile_map
        map_w = int(tm.width  * tm.tile_width)
        map_h = int(tm.height * tm.tile_height)
        dummy = arcade.SpriteSolidColor(1, 1, arcade.color.WHITE)
        dummy.center_x = PHL_POSITIONS.kyle_start_x
        dummy.center_y = PHL_POSITIONS.kyle_start_y
        barrier = arcade.AStarBarrierList(
            moving_sprite=dummy,
            blocking_sprites=walls,
            grid_size=16,
            left=0, right=map_w,
            bottom=0, top=map_h,
        )
        path = arcade.astar_calculate_path(
            (PHL_POSITIONS.kyle_start_x, PHL_POSITIONS.kyle_start_y),
            (PHL_POSITIONS.kyle_combat_x, PHL_POSITIONS.kyle_combat_y),
            barrier,
            diagonal_movement=True,
        )
        return list(path) if path else [
            (PHL_POSITIONS.kyle_combat_x, PHL_POSITIONS.kyle_combat_y)
        ]
