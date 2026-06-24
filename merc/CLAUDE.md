# merc/

Mode mercenaire — zone de jeu dédiée, accessible depuis l'objet « Mode mercenaire » dans PHL.

## Fichiers

| Fichier / Dossier | Rôle |
|---|---|
| `merc_scene.py` | `MercScene(BaseScene)` — scène principale |
| `configs/MERC.json` | Config map : spawn `[574, 50]`, pas de PNJs ni d'objets |
| `map/PHL_MER.tmx` | Tilemap Tiled (source + fichier chargé par le jeu) |
| `map/tuile/` | Tilesets PNG |
| `quests/quests.json` | Arc « Mode Mercenaire » : 3 quêtes (30 / 60 / 90 kills) |
| `quests/merc_quests_default.json` | État initial des quêtes (quête 1 uniquement, utilisé à la réinitialisation) |

## Accès

- **Entrée** : objet `ObjetInteractif` nommé `"Mode mercenaire"` dans PHL → touche Entrée → `switch_map("merc")`
- **Sortie** : zone de sortie dans la tilemap MERC → touche Entrée → `switch_map("phl")`

## Workflow tilemap

Édite directement `merc/map/PHL_MER.tmx` dans Tiled — c'est ce fichier qui est chargé par le jeu.
Les tilesets sont dans `merc/map/tuile/`. Aucune copie nécessaire.

## Système de quêtes local

`MercScene.setup()` instancie un `QuestManager` local pointant sur `merc/quests/`.
La sauvegarde est **désactivée** (`save_progress = lambda: None`) — le fichier runtime est `save/merc_quests_save.json`.

| Quête | Objectif | Changement de terrain au passage |
|---|---|---|
| 1 | 30 kills | Retire physiquement `step_1_H`, passe à 3 points de spawn |
| 2 | 60 kills | Retire physiquement `step_2`, passe à 4 points de spawn |
| 3 | 90 kills | Fin de l'arc |

Les sprites `step_1_H` et `step_2` sont retirés via `sprite.remove_from_sprite_lists()` (pas seulement masqués) pour éviter les collisions résiduelles.

## ZombieMode

`MercScene._setup_zombie_mode()` instancie `ZombieMode` (`world/zombie_mode.py`) avec `always_active=True`.
Cela désactive la vérification d'objectif et rend le combat permanent sans condition de quête.

Points de spawn initiaux : `[(575, 547)]` — élargi à 3 puis 4 points aux quêtes 2 et 3.

## Layers tilemap utilisés

| Layer | Rôle |
|---|---|
| `Sol` | Sol rendu en premier |
| `step_1_B`, `step_1_H` | Plateforme niveau 1 (retirée à la quête 2) |
| `step_2` | Plateforme niveau 2 (retirée à la quête 3) |
| `step_3_B`, `step_3_H` | Plateforme niveau 3 (permanente) |
| `Mur`, `Meuble_H`, `Meuble_B`, `Meuble_T` | Obstacles et décors |
| `hero_1`, `hero_2`, `hero_3` | Obstacles supplémentaires (inclus dans physics) |
| `Player` | Sprite joueur |
