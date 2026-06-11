from __future__ import annotations
import math
import random
import arcade
from character.character_classes import Weapon, Bullet  # noqa: F401 (re-exportés)

_SPAWN_POINTS    = [(574, 50)]
_CHASE_RADIUS    = 220   # px — le zombie commence à poursuivre
_CHASE_EXIT      = 450   # px — le zombie reprend son errance (hysteresis)
_WANDER_SPEED    = 58.0  # px/s en mode errance
_CHASE_SPEED_MAX = 86.0  # px/s max en poursuite (< vitesse joueur ~90 px/s)
_CHASE_ACCEL     = 30.0  # px/s² — accélération à l'entrée en poursuite
_WANDER_CHANGE   = (1.5, 3.5)  # intervalle aléatoire de changement de direction


class Zombie(arcade.SpriteSolidColor):
    MAX_HEALTH = 3

    def __init__(self, x: float, y: float):
        super().__init__(22, 30, (40, 110, 40))
        self.center_x = x
        self.center_y = y
        self.health        = self.MAX_HEALTH
        self._chasing      = False
        self._speed        = _WANDER_SPEED
        self._wander_dir   = random.uniform(0, math.pi * 2)
        self._wander_timer = 0.0
        self._wander_next  = random.uniform(*_WANDER_CHANGE)

    def move(self, player: arcade.Sprite, dt: float,
             walls: arcade.SpriteList | None) -> None:
        dist = math.hypot(player.center_x - self.center_x,
                          player.center_y - self.center_y)

        # Transition d'état avec hysteresis
        if dist < _CHASE_RADIUS:
            self._chasing = True
        elif dist > _CHASE_EXIT:
            self._chasing = False

        if self._chasing:
            self._speed = min(_CHASE_SPEED_MAX, self._speed + _CHASE_ACCEL * dt)
            self._chase(player, dt, walls)
        else:
            self._speed = _WANDER_SPEED
            self._wander(dt, walls)

    # ------------------------------------------------------------------ chase
    def _chase(self, player: arcade.Sprite, dt: float,
               walls: arcade.SpriteList | None) -> None:
        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        self._slide(dx / dist, dy / dist, self._speed * dt, walls)

    # ----------------------------------------------------------------- wander
    def _wander(self, dt: float, walls: arcade.SpriteList | None) -> None:
        self._wander_timer += dt
        if self._wander_timer >= self._wander_next:
            self._wander_dir   = random.uniform(0, math.pi * 2)
            self._wander_next  = random.uniform(*_WANDER_CHANGE)
            self._wander_timer = 0.0

        nx = math.cos(self._wander_dir)
        ny = math.sin(self._wander_dir)
        step = _WANDER_SPEED * dt
        ox, oy = self.center_x, self.center_y

        self.center_x = ox + nx * step
        self.center_y = oy + ny * step
        if self.center_y < 28:
            self.center_y = 28
            self._wander_dir = random.uniform(math.pi * 0.1, math.pi * 0.9)
        if walls and arcade.check_for_collision_with_list(self, walls):
            # Bloqué : choisit une nouvelle direction aléatoire
            self.center_x, self.center_y = ox, oy
            self._wander_dir  = random.uniform(0, math.pi * 2)
            self._wander_timer = 0.0

    # ------------------------------------------------------------ wall-slide
    def _slide(self, nx: float, ny: float, step: float,
               walls: arcade.SpriteList | None) -> None:
        ox, oy = self.center_x, self.center_y
        for mx, my in [(nx, ny), (nx, 0), (0, ny)]:
            self.center_x = ox + mx * step
            self.center_y = oy + my * step
            if walls is None or not arcade.check_for_collision_with_list(self, walls):
                return
        self.center_x, self.center_y = ox, oy


class ZombieManager:
    SPAWN_INTERVAL = 2.5
    MAX_ZOMBIES    = 12

    def __init__(self, quest_manager, player_sprite: arcade.Sprite):
        self._qm           = quest_manager
        self._player       = player_sprite
        self.zombies       = arcade.SpriteList()
        self.bullets       = arcade.SpriteList()
        self._timer        = 0.0
        self._walls: arcade.SpriteList | None = None
        self._spawn_points = list(_SPAWN_POINTS)

    def setup_walls(self, wall_sprites: arcade.SpriteList) -> None:
        self._walls = wall_sprites

    def set_spawn_points(self, points: list) -> None:
        self._spawn_points = points

    def reset(self) -> None:
        for z in list(self.zombies):
            z.remove_from_sprite_lists()
        for b in list(self.bullets):
            b.remove_from_sprite_lists()
        self._timer = 0.0

    def is_active(self) -> bool:
        return self._qm.get_kill_objective() is not None

    def fire(self, fx: float, fy: float, tx: float, ty: float,
             weapon: Weapon | None = None) -> None:
        damage = weapon.get_damage() if weapon else 1.0
        color  = weapon.bullet_color if weapon else (255, 210, 50)
        self.bullets.append(Bullet(fx, fy, tx, ty, damage, color))

    def check_player_damage(self, player, delta_time: float) -> bool:
        """Gère dégâts + knockback. Retourne True si dégâts appliqués."""
        if player.damage_cooldown > 0:
            player.damage_cooldown -= delta_time

        hit = arcade.check_for_collision_with_list(player, self.zombies)
        if not hit:
            return False

        took_damage = False
        for zombie in hit:
            dx = player.center_x - zombie.center_x
            dy = player.center_y - zombie.center_y
            dist = math.hypot(dx, dy) or 1.0
            nx, ny = dx / dist, dy / dist

            if player.damage_cooldown <= 0:
                # Knockback fort au moment du dégât
                player.center_x  += nx * 18
                player.center_y  += ny * 18
                zombie.center_x  -= nx * 12
                zombie.center_y  -= ny * 12
                player.health = max(0, player.health - 30)
                player.damage_cooldown = 1.5
                took_damage = True
            else:
                # Séparation douce chaque frame pour éviter l'overlap
                player.center_x  += nx * 2
                player.center_y  += ny * 2
                zombie.center_x  -= nx * 2
                zombie.center_y  -= ny * 2

        return took_damage

    def update(self, delta_time: float) -> int:
        if not self.is_active():
            return 0

        # Spawn
        self._timer += delta_time
        if self._timer >= self.SPAWN_INTERVAL and len(self.zombies) < self.MAX_ZOMBIES:
            self.zombies.append(Zombie(*random.choice(self._spawn_points)))
            self._timer = 0.0

        # Mouvement
        for z in self.zombies:
            z.move(self._player, delta_time, self._walls)

        # Balles — déplacement + suppression si mur/meuble touché ou vie expirée
        for b in [b for b in self.bullets if b.life <= 0]:
            b.remove_from_sprite_lists()
        for b in list(self.bullets):
            b.step()
            if self._walls and arcade.check_for_collision_with_list(b, self._walls):
                b.remove_from_sprite_lists()

        # Collisions balle → zombie
        kills = 0
        for b in list(self.bullets):
            hit = arcade.check_for_collision_with_list(b, self.zombies)
            if hit:
                b.remove_from_sprite_lists()
                for z in hit:
                    z.health -= b.damage
                    if z.health <= 0:
                        z.remove_from_sprite_lists()
                        kills += 1
        return kills

    def draw(self) -> None:
        self.zombies.draw()
        self.bullets.draw()
        for z in self.zombies:
            self._draw_health_bar(z)

    @staticmethod
    def _draw_health_bar(z: Zombie) -> None:
        BAR_W, BAR_H = z.width, 4
        bx = z.center_x - BAR_W / 2
        by = z.top + 4
        ratio = max(0.0, z.health / Zombie.MAX_HEALTH)

        # Fond sombre
        arcade.draw_lrbt_rectangle_filled(bx, bx + BAR_W, by, by + BAR_H, (40, 10, 10))
        # Portion remplie
        if ratio > 0:
            if ratio > 0.6:
                color = arcade.color.JADE
            elif ratio > 0.3:
                color = arcade.color.ORANGE
            else:
                color = arcade.color.RED
            arcade.draw_lrbt_rectangle_filled(bx, bx + BAR_W * ratio, by, by + BAR_H, color)
        # Bordure
        arcade.draw_lrbt_rectangle_outline(bx, bx + BAR_W, by, by + BAR_H, arcade.color.WHITE, 1)
