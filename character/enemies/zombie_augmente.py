from character.enemies.zombie import Zombie


class ZombieAugmente(Zombie):
    _SPRITE_PREFIX  = "enemies/zombies/z_aug"

    MAX_HEALTH      = 6
    DAMAGE          = 4
    VITESSE_ERRANCE = 70.0
    VITESSE_CHASSE  = 160.0
    ACCEL_CHASSE    = 40.0
    RAYON_DETECTION = 280
    RAYON_FUITE     = 550
