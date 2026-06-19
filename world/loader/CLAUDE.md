# world/loader/

Chargement des configurations JSON de map et instanciation des entités.

## Fichiers

| Fichier | Classe | Rôle |
|---|---|---|
| `map_loader.py` | `MapLoader` | Lit `world/configs/<NOM>.json` et peuple la scène |

## MapLoader

```python
loader = MapLoader("PHL")            # lit map/map_configs/PHL.json
loader.get_tilemap_path()            # → chemin du .tmx
loader.get_player_spawn(from_map)    # → (x, y) selon la map source
loader.load_pnjs(game_view)          # crée les PNJ et les ajoute à game_view
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
  "pnjs": [{ "nom": "Sylvain", "image": "...", "x": 0, "y": 0 }],
  "strategiques": [{ "nom": "Hotesse", ... }],
  "objets": [{ "type": "UpStat", "stat": "mathematique", ... }]
}
```

## Types d'objets supportés

| `type` JSON | Classe Python |
|---|---|
| `"UpStat"` | `world.objects.up_stat.UpStat` |
| `"UpStatCollection"` | `world.objects.up_stat_collection.UpStatCollection` |
| `"MapActionObject"` | `world.objects.map_action_object.MapActionObject` |
| `"ObjetInteractif"` | `world.objects.interactable.ObjetInteractif` |
