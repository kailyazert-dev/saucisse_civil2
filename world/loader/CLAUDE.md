# world/loader/

Chargement des configurations JSON de map et instanciation des entités.

## Fichiers

| Fichier | Classe | Rôle |
|---|---|---|
| `map_loader.py` | `MapLoader` | Lit `world/configs/<NOM>.json` et peuple la scène |

## MapLoader

```python
loader = MapLoader("PHL")                              # lit world/configs/PHL.json
loader = MapLoader("MERC", config_path="merc/configs/MERC.json")  # chemin custom
loader.get_tilemap_path()            # → chemin du .tmx
loader.get_player_spawn(from_map)    # → (x, y) selon la map source
loader.load_pnjs(game_view, behind_player)  # crée les PNJ et les ajoute à game_view
loader.load_strategiques(game_view)  # crée les PNJ stratégiques
loader.load_objets(game_view)        # crée les objets interactifs
```

## Format JSON des configs

```json
{
  "tilemap": "world/tilemaps/PHL.tmx",
  "player_spawn": {
    "default": [72, 72],
    "tma": [2792, 1848],
    "home": [574, 50]
  },
  "base": {
    "pnjs": [{ "nom": "Sylvain", "image": "...", "x": 0, "y": 0 }],
    "strategiques": [{ "nom": "Hotesse", "image": "...", "x": 0, "y": 0 }],
    "objets": [{ "type": "UpStat", "stat": "mathematique", ... }]
  },
  "arc_1": {
    "pnjs": [...],
    "objets": [...]
  },
  "arc_2": { ... }
}
```

`"base"` est toujours chargé. Les sections `arc_1` … `arc_N` remplacent `base` selon l'arc actif — si `arc_id` est fourni et que la section correspondante existe, elle est utilisée à la place de `base` (pas de fusion cumulative). Rétro-compatible : si `"base"` est absent, lit `pnjs`/`objets` à la racine.

## Types d'objets supportés

| `type` JSON | Classe Python |
|---|---|
| `"UpStat"` | `world.objects.interactables.up_stat.UpStat` |
| `"UpStatCollection"` | `world.objects.interactables.up_stat_collection.UpStatCollection` |
| `"MapActionObject"` | `world.objects.interactables.map_action_object.MapActionObject` |
| `"ObjetInteractif"` | `world.objects.interactables.interactable.ObjetInteractif` |
| `"Coffre"` | `world.objects.interactables.coffre.Coffre` (import dynamique) |

Le type `"Coffre"` accepte une clé optionnelle `"catalogue"` (défaut `"general"`) qui désigne la section du shop à afficher.

## Propriétés PNJ supportées dans le JSON

| Clé | Effet |
|---|---|
| `"walk_textures"` | Charge les textures de marche (préfixe, ex : `"assets/images/kyle"`) |
| `"sitting_image"` | Remplace les 4 textures par une texture assise fixe |
| `"hitbox": "upper_half"` | Réduit la hitbox à la moitié supérieure (PNJ derrière comptoir) |
| `"speed"` | Vitesse de déplacement |
| `"fire_interval"` | Intervalle de tir (secondes) |
| `"weapon"` | Arme : chaîne `"nom"` (via `Weapon.from_name()`) ou dict `{name, damage_min, damage_max, bullet_color, fire_interval}` |
| `"scale"` | Facteur d'échelle du sprite (défaut : `PLAYER_SCALING` = 0.85) |
| `"behind_player"` | Ajoute à la liste `behind_player` pour le rendu en dessous du joueur |
| `"scene_layer"` | Ajoute le sprite à ce layer de la scène Arcade |
| `"interaction_distance"` | Distance d'interaction (px) — défaut 60 pour PNJ, 50 pour stratégiques |

## Signature complète de load_pnjs

```python
def load_pnjs(self, game_view: BaseScene,
              behind_player: arcade.SpriteList | None = None) -> None
```

Le paramètre `behind_player` est optionnel. Quand il est fourni, les PNJs dont le JSON contient `"behind_player": true` y sont également ajoutés (rendu sous le joueur).
