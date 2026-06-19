# character/ai/

Intelligence artificielle des personnages autonomes. Découplée des entités et des scènes.

## Fichiers

| Fichier | Classe | Personnage |
|---|---|---|
| `kyle_ai.py` | `KyleAI` | Kyle dans PHL |

## KyleAI

FSM (machine à états finis) pour Kyle dans la map PHL. Séparée du sprite `PNJ` pour garder les responsabilités isolées.

```python
kyle_ai = KyleAI(kyle_sprite, quest_manager, tile_map)
kyle_ai.init_path(walls)      # pré-calcule le chemin A* si arc 3 quest 1 ou 2 active
kyle_ai.start_walk()          # démarre la marche (appelé par CutsceneManager ou setup au rechargement)
kills = kyle_ai.update(dt, walls, zombies, pnjs_active)  # retourne kills ce tick
```

### États

| État | Condition | Comportement |
|---|---|---|
| `"sit"` | PNJs cachés (avant quête) | Texture assise, immobile |
| `"stand"` | Quête active, avant cutscène | Debout à sa position initiale |
| `"walk"` | Après cutscène Kyle | Suit le chemin A* vers la zone de combat |
| `"chasse"` | `walk_done` + zombies actifs | `PNJ.update_ai()` — poursuite + tir |
| `"dialogue"` | `walk_done` + zombies inactifs + non `end_talked` | Debout, attend l'interaction |

### Pathfinding

Utilise `arcade.AStarBarrierList` + `arcade.astar_calculate_path` avec `grid_size=16`.

Le chemin calculé est mis en cache dans `_path_cache` (variable de module) pour être réutilisé si la map est rechargée. Le cache est invalidé dès que `start_walk()` est appelé.

`_quest_active()` retourne `True` si arc 3 ET (quest 1 **ou** quest 2) est en cours. Cela couvre deux cas :
- **Flux normal** : quest 1 active → chemin calculé avant la cutscène
- **Rechargement en mode zombie** : quest 1 terminée, quest 2 active → chemin recalculé pour que Kyle refasse sa marche avant de passer en chasse

### Hitbox adaptative

- État `"sit"` / `"stand"` / `"walk"` / `"dialogue"` → demi-hitbox supérieure (ne bloque pas le passage)
- État `"chasse"` → hitbox complète (collisions de combat)

## Ajouter une nouvelle IA

Créer `character/ai/<nom>_ai.py` avec une classe autonome qui :
- Reçoit le sprite + les managers nécessaires dans `__init__`
- Expose `update(dt, ...)` qui retourne un int (kills ou 0)
- Ne modifie jamais directement `quest_manager` — retourne des actions que la scène applique
