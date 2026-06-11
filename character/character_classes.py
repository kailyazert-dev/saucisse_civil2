from __future__ import annotations
import math
import random
from enum import Enum
from typing import TYPE_CHECKING
import arcade
from assets.param_map import MAP_WIDTH, MAP_HEIGHT, PLAYER_SCALING, MOVEMENT_SPEED
import utils.paths as paths

if TYPE_CHECKING:
    from quests.quest_manager import QuestManager
    from character.character_manager import CharacterManager


def _img(filename: str) -> str:
    return paths.asset(f"assets/images/{filename}")


# ---------------------------------------------------------------------------
class Weapon:
    """Arme attribuable à un Player ou un PNJ."""

    def __init__(self, name: str, damage_min: float, damage_max: float,
                 bullet_color: tuple[int, int, int] = (255, 210, 50)) -> None:
        self.name         = name
        self.damage_min   = damage_min
        self.damage_max   = damage_max
        self.bullet_color = bullet_color

    def get_damage(self) -> float:
        return random.uniform(self.damage_min, self.damage_max)

    def __repr__(self) -> str:
        return f"<Weapon {self.name} [{self.damage_min}-{self.damage_max}]>"


# ---------------------------------------------------------------------------
class Bullet(arcade.SpriteSolidColor):
    """Projectile tiré par un Player ou un PNJ."""

    SPEED    = 10.0
    LIFETIME = 90

    def __init__(self, x: float, y: float, tx: float, ty: float,
                 damage: float = 1.0, color: tuple[int, int, int] = (255, 210, 50)) -> None:
        super().__init__(8, 8, color)
        self.center_x, self.center_y = x, y
        self.damage = damage
        dist = math.hypot(tx - x, ty - y)
        if dist > 0:
            self.vel_x = (tx - x) / dist * self.SPEED
            self.vel_y = (ty - y) / dist * self.SPEED
        else:
            self.vel_x = self.vel_y = 0.0
        self.life = self.LIFETIME

    def step(self) -> None:
        self.center_x += self.vel_x
        self.center_y += self.vel_y
        self.life -= 1


# ---------------------------------------------------------------------------
class Humain:
    def __init__(self,
                 force:        float = 0.1,
                 vitesse:      float = 0.1,
                 endurance:    float = 0.1,
                 mathematique: float = 0.14,
                 logique:      float = 0.14,
                 rpg:          float = 0.1,
                 music:        float = 0.1,
                 langue:       float = 0.1,
                 sociabilite:  float = 0.1,
                 x:            float = 0.0,
                 y:            float = 0.0) -> None:
        self.force           = force
        self.vitesse         = vitesse
        self.endurance       = endurance
        self.mathematique    = mathematique
        self.logique         = logique
        self.rpg             = rpg
        self.music           = music
        self.langue          = langue
        self.sociabilite     = sociabilite
        self.x, self.y       = x, y

    def get_stats_physique(self) -> list[tuple[str, float]]:
        return [("Force", self.force), ("Vitesse", self.vitesse),
                ("Endurance", self.endurance)]

    def get_stats_intellect(self) -> list[tuple[str, float]]:
        return [("Math", self.mathematique), ("Logique", self.logique),
                ("RPG", self.rpg)]

    def get_stats_sociale(self) -> list[tuple[str, float]]:
        return [("Musique", self.music), ("Langue", self.langue),
                ("Sociabilite", self.sociabilite)]


# ---------------------------------------------------------------------------
class PNJState(Enum):
    """États possibles d'un PNJ — machine à états explicite."""
    ASSIS    = "assis"
    ERRANCE  = "errance"
    CHASSE   = "chasse"
    DIALOGUE = "dialogue"   # immobile, face au joueur


class PNJ(arcade.Sprite):
    """Personnage non-joueur avec FSM d'attitude et d'arme.

    États (PNJState) :
      ASSIS    — statique, aucun mouvement
      ERRANCE  — déplacement aléatoire avec animation
      CHASSE   — poursuite/tir sur les zombies proches
      DIALOGUE — immobile pendant une conversation
    """

    _DIRS:        dict[str, tuple[int, int]] = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
    _WALK_SWITCH: float                      = 0.15

    def __init__(self, nom: str, humain: Humain, type: str,
                 image_path: str, scale: float, attitude: str = "assis") -> None:
        super().__init__(image_path, scale)
        self.nom        = nom
        self.humain     = humain
        self.type       = type
        self.image_path = image_path

        # FSM
        self._state:          PNJState        = PNJState(attitude)
        self._previous_state: PNJState | None = None

        self.speed:            float              = MOVEMENT_SPEED
        self.weapon:           Weapon | None      = None
        self.detect_radius:    float              = 200.0
        self.safety_distance:  float              = 90.0
        self._fire_interval:   float              = 1.2
        self._fire_timer:      float              = 0.0
        self._current_target:  arcade.Sprite | None = None
        self.bullets:          arcade.SpriteList  = arcade.SpriteList()

        self.center_x, self.center_y = humain.x, humain.y

        self.textures: dict[str, arcade.Texture] = {
            d: arcade.load_texture(_img(f"player_{d[0]}.png"))
            for d in self._DIRS
        }
        self.textures_walk: dict[str, list[arcade.Texture]] | None = None

        self._wander_dir:    str   = "down"
        self._wander_timer:  float = 0.0
        self._wander_change: float = random.uniform(1.5, 3.5)
        self._walk_frame:    int   = 0
        self._walk_timer:    float = 0.0

    # ---------------------------------------------------------------- FSM

    @property
    def attitude(self) -> str:
        """Compatibilité : retourne la valeur string de l'état courant."""
        return self._state.value

    @attitude.setter
    def attitude(self, val: str) -> None:
        """Compatibilité : accepte les strings 'assis', 'errance', etc."""
        self._state = PNJState(val)

    def transition_to(self, new_state: PNJState) -> None:
        """Transition explicite avec mémorisation de l'état précédent."""
        if new_state == self._state:
            return
        self._previous_state = self._state
        self._state = new_state

    def leave_dialogue(self) -> None:
        """Revient à l'état précédant le dialogue."""
        if self._state == PNJState.DIALOGUE and self._previous_state is not None:
            self._state = self._previous_state
            self._previous_state = None

    # ---------------------------------------------------------------- public

    def get_nom(self) -> str:
        return self.nom

    def load_walk_textures(self, prefix: str = "player") -> None:
        self.textures = {
            d: arcade.load_texture(_img(f"{prefix}_{d[0]}.png"))
            for d in self._DIRS
        }
        self.textures_walk = {
            d: [arcade.load_texture(_img(f"{prefix}_{d[0]}1.png")),
                arcade.load_texture(_img(f"{prefix}_{d[0]}2.png"))]
            for d in self._DIRS
        }

    def face(self, dx: float, dy: float) -> None:
        key = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) \
              else ("up" if dy > 0 else "down")
        self.texture = self.textures[key]

    def update_ai(self, delta_time: float,
                  walls:   arcade.SpriteList | None = None,
                  zombies: arcade.SpriteList | None = None) -> int:
        """Met à jour le comportement. Retourne le nombre de zombies tués."""
        if self._state == PNJState.DIALOGUE:
            return 0   # immobile pendant la conversation
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

        z  = self._current_target
        dx = z.center_x - self.center_x
        dy = z.center_y - self.center_y
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

    def _animate(self, direction: str, dt: float) -> None:
        self._walk_timer += dt
        if self._walk_timer >= self._WALK_SWITCH:
            self._walk_frame = 1 - self._walk_frame
            self._walk_timer = 0.0
        if self.textures_walk:
            self.texture = self.textures_walk[direction][self._walk_frame]
        else:
            self.texture = self.textures.get(direction, self.texture)


# ---------------------------------------------------------------------------
class Player(arcade.Sprite):
    def __init__(self, humain: Humain, nom: str, image_file: str,
                 quest_manager: QuestManager, character_manager: CharacterManager,
                 scale: float = PLAYER_SCALING) -> None:
        super().__init__(image_file, scale)
        self.humain            = humain
        self.nom               = nom
        self.reading           = False
        self.quest_manager     = quest_manager
        self.character_manager = character_manager
        self.health:           int          = 50
        self.damage_cooldown:  float        = 0.0
        self.weapon:           Weapon | None = None

        self.direction = "down"
        self.textures: dict[str, arcade.Texture] = {
            "up":    arcade.load_texture(_img("player_u.png")),
            "down":  arcade.load_texture(_img("player_d.png")),
            "left":  arcade.load_texture(_img("player_l.png")),
            "right": arcade.load_texture(_img("player_r.png")),
            "read":  arcade.load_texture(_img("player_read1.png")),
        }
        self.textures_up:    list[arcade.Texture] = [arcade.load_texture(_img("player_u1.png")),
                                                      arcade.load_texture(_img("player_u2.png"))]
        self.textures_down:  list[arcade.Texture] = [arcade.load_texture(_img("player_d1.png")),
                                                      arcade.load_texture(_img("player_d2.png"))]
        self.textures_left:  list[arcade.Texture] = [arcade.load_texture(_img("player_l1.png")),
                                                      arcade.load_texture(_img("player_l2.png"))]
        self.textures_right: list[arcade.Texture] = [arcade.load_texture(_img("player_r1.png")),
                                                      arcade.load_texture(_img("player_r2.png"))]
        self.textures_read:  list[arcade.Texture] = [
            arcade.load_texture(_img("player_read1.png")),
            arcade.load_texture(_img("player_read1.png")),
            arcade.load_texture(_img("player_read2.png")),
            arcade.load_texture(_img("player_read3.png")),
            arcade.load_texture(_img("player_read4.png")),
            arcade.load_texture(_img("player_read1.png")),
            arcade.load_texture(_img("player_read1.png")),
        ]
        self.walk_texture_index:              int   = 0
        self.read_texture_index:              int   = 0
        self.time_since_last_texture_change:  float = 0.0
        self.walking_texture_switch_interval: float = 0.2
        self.reading_texture_switch_interval: float = 0.5

    def update(self, delta_time: float = 1 / 60) -> None:
        self.character_manager.update_player_stats(delta_time)
        self.character_manager.animation.update(delta_time)


# ---------------------------------------------------------------------------
class AnimationManager:
    def __init__(self, character_manager: CharacterManager) -> None:
        self.manager = character_manager

    def update(self, delta_time: float = 1 / 60) -> None:
        player = self.manager.player
        if player is None:
            return

        player.center_x += player.change_x
        player.center_y += player.change_y
        super(Player, player).update(delta_time)

        if player.left < 0:
            player.left = 0
        elif player.right > MAP_WIDTH - 1:
            player.right = MAP_WIDTH - 1
        if player.bottom < 0:
            player.bottom = 0
        elif player.top > MAP_HEIGHT - 1:
            player.top = MAP_HEIGHT - 1

        if player.reading:
            player.time_since_last_texture_change += delta_time
            if player.time_since_last_texture_change >= player.reading_texture_switch_interval:
                self._toggle_read_texture(player)
                player.time_since_last_texture_change = 0.0
        elif player.change_x != 0 or player.change_y != 0:
            player.time_since_last_texture_change += delta_time
            if player.time_since_last_texture_change >= player.walking_texture_switch_interval:
                self._toggle_walk_texture(player)
                player.time_since_last_texture_change = 0.0
        else:
            player.texture = player.textures[player.direction]

    def _toggle_walk_texture(self, player: Player) -> None:
        player.walk_texture_index = 1 - player.walk_texture_index
        direction_map: dict[str, list[arcade.Texture]] = {
            "up":    player.textures_up,
            "down":  player.textures_down,
            "left":  player.textures_left,
            "right": player.textures_right,
        }
        textures = direction_map.get(player.direction, player.textures_down)
        player.texture = textures[player.walk_texture_index]

    def _toggle_read_texture(self, player: Player) -> None:
        player.read_texture_index = (player.read_texture_index + 1) % len(player.textures_read)
        player.texture = player.textures_read[player.read_texture_index]

