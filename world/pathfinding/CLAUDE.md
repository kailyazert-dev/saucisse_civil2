# world/pathfinding/

Algorithmes de navigation pour les entités autonomes.

## État actuel

Dossier réservé. Le calcul A* est actuellement intégré dans `character/ai/kyle_ai.py` via `_calc_astar()`, qui utilise l'API Arcade :

```python
arcade.AStarBarrierList(moving_sprite, blocking_sprites, grid_size=16, ...)
arcade.astar_calculate_path(start, end, barrier, diagonal_movement=True)
```

## Prochaine étape

Extraire la logique A* dans un module réutilisable :

```python
# world/pathfinding/astar.py (à créer)
def calc_path(start, end, walls, tile_map, grid_size=16) -> list[tuple]:
    """Calcule un chemin A* entre start et end en évitant walls."""
    ...
```

Permettrait à n'importe quelle entité (PNJ errant, zombie boss, etc.) d'utiliser le pathfinding sans dupliquer le code.
