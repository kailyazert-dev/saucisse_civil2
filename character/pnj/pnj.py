from __future__ import annotations
import math
import random
from enum import Enum
import arcade
from assets.param_map import MOVEMENT_SPEED
import utils.paths as paths
from character.character_base import CharacterBase, Humain
from character.equipment.weapon import Weapon
from character.equipment.bullet import Bullet


def _img(filename: str) -> str:
    return paths.asset(f"assets/images/{filename}")


class PNJState(Enum):
    """États possibles d'un PNJ — machine à états explicite."""
    ASSIS    = "assis"
    ERRANCE  = "errance"
    CHASSE   = "chasse"
    DIALOGUE = "dialogue"
    STAND    = "stand"


class PNJ(CharacterBase):
    """Personnage non-joueur avec FSM d'attitude et d'arme."""

    def __init__(self, nom: str, humain: Humain, type: str,
                 image_path: str, scale: float, attitude: str = "assis") -> None:
        super().__init__(nom, humain, image_path, scale)
        self.type       = type
        self.image_path = image_path

        self._state:          PNJState        = PNJState(attitude)
        self._previous_state: PNJState | None = None

        self.speed:           float                = MOVEMENT_SPEED
        self.detect_radius:   float                = 200.0
        self.safety_distance: float                = 90.0
        self._fire_interval:  float                = 1.2
        self._fire_timer:     float                = 0.0
        self._current_target: arcade.Sprite | None = None
        self.bullets:         arcade.SpriteList    = arcade.SpriteList()

        self.center_x, self.center_y = humain.x, humain.y

        self.textures = {
            d: arcade.load_texture(_img(f"player_{d[0]}.png"))
            for d in self._DIRS
        }

        self._wander_dir:    str   = "down"
        self._wander_timer:  float = 0.0
        self._wander_change: float = random.uniform(1.5, 3.5)

    # ---------------------------------------------------------------- FSM

    @property
    def attitude(self) -> str:
        return self._state.value

    @attitude.setter
    def attitude(self, val: str) -> None:
        self._state = PNJState(val)

    def transition_to(self, new_state: PNJState) -> None:
        if new_state == self._state:
            return
        self._previous_state = self._state
        self._state = new_state

    def leave_dialogue(self) -> None:
        if self._state == PNJState.DIALOGUE and self._previous_state is not None:
            self._state = self._previous_state
            self._previous_state = None

    # ---------------------------------------------------------------- public

    def update_ai(self, delta_time: float,
                  walls:   arcade.SpriteList | None = None,
                  zombies: arcade.SpriteList | None = None) -> int:
        """Met à jour le comportement. Retourne le nombre de zombies tués."""
        if self._state == PNJState.DIALOGUE:
            return 0
        if self._state == PNJState.ERRANCE:
            self._wander(delta_time, walls)
        elif self._state == PNJState.CHASSE:
            return self._chasse(delta_time, zombies, walls)
        return 0

    def draw_bullets(self) -> None:
        self.bullets.draw()

    # --------------------------------------------------------------- private

    def _wander(self, dt: float, walls: arcade.SpriteList | None) -> None:
        self._wander_timer += dt
        if self._wander_timer >= self._wander_change:
            self._wander_dir    = random.choice(list(self._DIRS))
            self._wander_change = random.uniform(1.5, 3.5)
            self._wander_timer  = 0.0

        dx, dy = self._DIRS[self._wander_dir]
        ox, oy = self.center_x, self.center_y
        self.center_x += dx * self.speed
        self.center_y += dy * self.speed
        if walls and arcade.check_for_collision_with_list(self, walls):
            self.center_x, self.center_y = ox, oy
            self._wander_dir   = random.choice(list(self._DIRS))
            self._wander_timer = 0.0
        self._animate(self._wander_dir, dt)

    def _chasse(self, dt: float,
                zombies: arcade.SpriteList | None,
                walls:   arcade.SpriteList | None) -> int:
        kills = self._update_bullets(dt, zombies, walls)
        self._current_target = self._nearest_zombie(zombies)

        if self._current_target is None:
            self._wander(dt, walls)
            return kills

        z    = self._current_target
        dx   = z.center_x - self.center_x
        dy   = z.center_y - self.center_y
        dist = math.hypot(dx, dy) or 1.0

        if dist < self.safety_distance:
            nx, ny = dx / dist, dy / dist
            ox, oy = self.center_x, self.center_y
            self.center_x -= nx * self.speed
            self.center_y -= ny * self.speed
            if walls and arcade.check_for_collision_with_list(self, walls):
                self.center_x, self.center_y = ox, oy
            self.face(dx, dy)
            self._animate(self._wander_dir, dt)
        else:
            self.texture = self.textures["down"]

        if self.weapon:
            self._fire_timer += dt
            if self._fire_timer >= self._fire_interval:
                self._fire_timer = 0.0
                self.bullets.append(Bullet(
                    self.center_x, self.center_y,
                    z.center_x, z.center_y,
                    self.weapon.get_damage(),
                    self.weapon.bullet_color,
                ))
        return kills

    def _nearest_zombie(self, zombies: arcade.SpriteList | None) -> arcade.Sprite | None:
        if not zombies:
            return None
        best: arcade.Sprite | None = None
        best_d = self.detect_radius
        for z in zombies:
            d = math.hypot(z.center_x - self.center_x, z.center_y - self.center_y)
            if d < best_d:
                best, best_d = z, d
        return best

    def _update_bullets(self, dt: float,
                        zombies: arcade.SpriteList | None,
                        walls:   arcade.SpriteList | None) -> int:
        for b in [b for b in self.bullets if b.life <= 0]:
            b.remove_from_sprite_lists()
        for b in list(self.bullets):
            b.step()
            if walls and arcade.check_for_collision_with_list(b, walls):
                b.remove_from_sprite_lists()

        kills = 0
        if zombies:
            for b in list(self.bullets):
                hit = arcade.check_for_collision_with_list(b, zombies)
                if hit:
                    b.remove_from_sprite_lists()
                    for z in hit:
                        z.health -= b.damage
                        if z.health <= 0:
                            z.remove_from_sprite_lists()
                            kills += 1
        return kills
