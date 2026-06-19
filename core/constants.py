"""Constantes nommées du projet — remplace les magic numbers dispersés."""
from dataclasses import dataclass


@dataclass(frozen=True)
class _PHLPositions:
    kyle_start_x: float = 694.0
    kyle_start_y: float = 787.0
    kyle_desk_x: float = 690.0
    kyle_desk_y: float = 848.0
    kyle_combat_x: float = 772.0
    kyle_combat_y: float = 236.0
    kyle_auto_walk_x: float = 755.0
    kyle_auto_walk_y: float = 745.0
    zombie_spawn_x: float = 574.0
    zombie_spawn_y: float = 50.0


PHL_POSITIONS = _PHLPositions()


@dataclass(frozen=True)
class _CombatConfig:
    spawn_interval: float = 0.8
    wander_speed: float = 90.0
    chase_speed_max: float = 125.0
    chase_accel: float = 30.0
    chase_radius: float = 220.0
    disengage_radius: float = 450.0
    wander_change_min: float = 2.5
    wander_change_max: float = 4.5
    player_damage: int = 30
    player_knockback: float = 18.0
    zombie_knockback: float = 12.0
    damage_cooldown: float = 1.5


COMBAT = _CombatConfig()
