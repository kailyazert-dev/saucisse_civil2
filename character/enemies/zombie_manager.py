from __future__ import annotations
import math
import random
import arcade
from character.enemies.zombie import Zombie
from character.equipment.weapon import Weapon
from character.equipment.bullet import Bullet

_SPAWN_POINTS = [(574, 50)]


class ZombieManager:
    SPAWN_INTERVAL = 0.8

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
        color  = getattr(weapon, "bullet_color", (255, 210, 50))
        self.bullets.append(Bullet(fx, fy, tx, ty, damage, color))

    def melee_attack(self, player: arcade.Sprite, radius: float, get_damage,
                     attack_angle: float | None = None, half_span: float = 360.0) -> int:
        """Inflige des dégâts aux zombies dans le secteur (rayon + angle). Retourne les kills."""
        kills = 0
        for z in list(self.zombies):
            dist = math.hypot(z.center_x - player.center_x, z.center_y - player.center_y)
            if dist > radius + z.width / 2:
                continue
            if attack_angle is not None and half_span < 180.0:
                zombie_angle = math.degrees(math.atan2(
                    z.center_y - player.center_y, z.center_x - player.center_x))
                diff = abs((zombie_angle - attack_angle + 180) % 360 - 180)
                if diff > half_span:
                    continue
            z.health -= get_damage()
            if z.health <= 0:
                z.remove_from_sprite_lists()
                kills += 1
        return kills

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
                player.center_x  += nx * 18
                player.center_y  += ny * 18
                zombie.center_x  -= nx * 12
                zombie.center_y  -= ny * 12
                player.health = max(0, player.health - zombie.DAMAGE)
                player.damage_cooldown = player.DAMAGE_COOLDOWN
                took_damage = True
            else:
                player.center_x  += nx * 2
                player.center_y  += ny * 2
                zombie.center_x  -= nx * 2
                zombie.center_y  -= ny * 2

        return took_damage

    def update(self, delta_time: float) -> int:
        if not self.is_active():
            for b in list(self.bullets):
                b.remove_from_sprite_lists()
            return 0

        self._timer += delta_time
        obj = self._qm.get_kill_objective()
        remaining = max(0, int(obj.validator) - obj.counter) if obj else 0
        if self._timer >= self.SPAWN_INTERVAL and len(self.zombies) < remaining:
            self.zombies.append(Zombie(*random.choice(self._spawn_points)))
            self._timer = 0.0

        for z in self.zombies:
            z.move(self._player, delta_time, self._walls)

        for b in [b for b in self.bullets if b.life <= 0]:
            b.remove_from_sprite_lists()
        for b in list(self.bullets):
            b.step()
            if self._walls and arcade.check_for_collision_with_list(b, self._walls):
                b.remove_from_sprite_lists()

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

        arcade.draw_lrbt_rectangle_filled(bx, bx + BAR_W, by, by + BAR_H, (40, 10, 10))
        if ratio > 0:
            color = arcade.color.JADE if ratio > 0.6 else arcade.color.ORANGE if ratio > 0.3 else arcade.color.RED
            arcade.draw_lrbt_rectangle_filled(bx, bx + BAR_W * ratio, by, by + BAR_H, color)
        arcade.draw_lrbt_rectangle_outline(bx, bx + BAR_W, by, by + BAR_H, arcade.color.WHITE, 1)
