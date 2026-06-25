from __future__ import annotations
import math
from character.enemies.zombie import Zombie


class ZombieAugmente(Zombie):
    _SPRITE_PREFIX          = "enemies/zombies/z_aug"

    MAX_HEALTH              = 30
    DAMAGE                  = 7
    VITESSE_ERRANCE         = 100.0
    VITESSE_CHASSE          = 160.0
    ACCEL_CHASSE            = 80.0
    RAYON_DETECTION         = 480
    RAYON_FUITE             = 550

    # Paramètres du jet de pierre — surchargeables via JSON
    PROJECTILE_DEGATS       = 2
    PROJECTILE_VITESSE      = 6.0
    PROJECTILE_INTERVALLE   = 2.5
    PROJECTILE_RAYON_TIR    = 400
    PROJECTILE_COULEUR      = (150, 100, 60)

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self._tir_timer          = self.PROJECTILE_INTERVALLE
        self.pending_projectiles: list[tuple[float, float, float, float]] = []

    def move(self, player, dt: float, walls) -> None:
        super().move(player, dt, walls)
        if not self._chasing:
            return
        dist = math.hypot(player.center_x - self.center_x,
                          player.center_y - self.center_y)
        if dist <= self.PROJECTILE_RAYON_TIR:
            self._tir_timer -= dt
            if self._tir_timer <= 0:
                self.pending_projectiles.append((
                    self.center_x, self.center_y,
                    player.center_x, player.center_y,
                ))
                self._tir_timer = self.PROJECTILE_INTERVALLE
