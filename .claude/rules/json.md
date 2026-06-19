---
paths:
  - "*.json"
---

## Fichiers JSON du projet

Le projet utilise plusieurs fichiers JSON avec des rôles distincts :

| Fichier | Rôle | Éditable ? |
|---|---|---|
| `world/configs/*.json` | Config d'une map : tilemap, spawns, PNJs, objets | Oui — données de niveau |
| `quests/quests_file/quests.json` | Définitions de toutes les quêtes (Arc → Quest → Objective) | Oui — contenu narratif |
| `save/character_save.json` | Stats du joueur en cours de partie | Non — runtime |
| `save/quests_save.json` | Progression quêtes en cours | Non — runtime |
| `save/saves.json` | Slots de sauvegarde nommés | Non — runtime |

### Format quests.json

```json
[{
  "arc_id": 1,
  "name": "...",
  "quests": [{
    "id": 1,
    "title": "...",
    "objectives": [{
      "name": "...",
      "type": "stat|compteur|talk|map_action",
      "stat_key": "...",
      "validator": 0.5
    }]
  }]
}]
```

Types d'objectif : `"stat"` (seuil de stat), `"compteur"` (kills), `"talk"` (cutscène PNJ), `"map_action"` (objet ENTER).

### Format map_configs

```json
{
  "tilemap": "world/tilemaps/NOM.tmx",
  "player_spawn": { "default": [x, y], "home": [x, y] },
  "pnjs": [{ "nom": "...", "image": "assets/images/...", "x": 0, "y": 0 }],
  "strategiques": [...],
  "objets": [{ "type": "UpStat", "stat": "mathematique", "stat_min": 0, "stat_max": 0.5, ... }]
}
```
