# merc/

Mode mercenaire — zone de jeu dédiée, accessible depuis l'objet « Mode mercenaire » dans PHL.

## Fichiers

| Fichier / Dossier | Rôle |
|---|---|
| `merc_scene.py` | `MercScene(BaseScene)` — scène principale |
| `configs/MERC.json` | Config map : spawn joueur `[700, 325]`, pas de PNJs ni d'objets |
| `configs/zombie.json` | Stats, mouvement et drops des `MercZombie` |
| `configs/shop.json` | Catalogue des distributeurs : 3 sections (`soins`, `armes`, `general`) |
| `map/PHL_MER.tmx` | Tilemap Tiled chargée par le jeu |
| `map/tuile/` | Tilesets PNG |
| `quests/quests.json` | Arc « Mode Mercenaire » : 4 quêtes (30 / 60 / 90 / 110 kills) — sert aussi de fichier de réinitialisation par défaut |

## Accès

- **Entrée** : objet `ObjetInteractif` nommé `"Mode mercenaire"` dans PHL → touche Entrée → `switch_map("merc")`
- **Sortie** : zone de sortie dans la tilemap MERC → touche Entrée → `switch_map("phl")`

## Workflow tilemap

Édite directement `merc/map/PHL_MER.tmx` dans Tiled — c'est ce fichier qui est chargé par le jeu (référencé dans `merc/configs/MERC.json`).
Les tilesets sont dans `merc/map/tuile/`. Aucune copie nécessaire.

> `world/tilemaps/PHL_MER.tmx` est un fichier orphelin non utilisé par le jeu.

## Setup de la scène

`MercScene.setup()` :
1. Instancie un `QuestManager` local pointant sur `merc/quests/` (`quests.json` est utilisé à la fois comme fichier de définition et comme fichier de réinitialisation par défaut — `merc_quests_default.json` supprimé)
2. Désactive la sauvegarde (`save_progress = lambda: None`) — runtime dans `save/merc_quests_save.json`
3. Équipe le joueur avec `Weapon.from_name("Pistolet")` (feu) et `Weapon.from_name("Couteau")` (blanc)
4. Appelle `_setup_zombie_mode()` qui :
   - Appelle `_load_zombie_class()` pour créer dynamiquement `MercZombie(Zombie)` depuis `configs/zombie.json`
   - Instancie `ZombieMode(always_active=True)` avec `zombie_class=MercZombie` et `player_spawn`
   - Désactive le spawn (`set_spawn_enabled(False)`) — réactivé après la fin de l'animation `QuestNotif`

**Délai de spawn** : `on_update()` surveille `quest_notif.is_idle` — le spawn n'est débloqué qu'une fois la notification initiale terminée (flags `_notif_was_active`, `_spawn_unlocked`).

## Système de quêtes local

| Quête | Objectif | Spawn zombies | Changement de terrain au passage |
|---|---|---|---|
| 1 | 30 kills | 2 points : `(570,80)`, `(575,547)` | Retire physiquement `step_1_H`, passe à 3 points |
| 2 | 60 kills | 3 points : `(570,80)`, `(528,1123)`, `(1946,652)` | Retire physiquement `step_2`, passe à 3 points |
| 3 | 90 kills | 3 points : `(570,80)`, `(528,1123)`, `(2686,1108)` | Retire physiquement `step_3_H`, passe à 4 points |
| 4 | 110 kills | 4 points : `(570,80)`, `(528,1123)`, `(2686,1108)`, `(2517,1846)` | Fin de l'arc |

Les sprites `step_1_H` et `step_2` sont retirés via `sprite.remove_from_sprite_lists()` (pas seulement masqués) pour éviter les collisions résiduelles.

## ZombieMode

`MercScene._setup_zombie_mode()` collecte les murs de tous les layers de collision (`Mur`, `Meuble_H`, `step_1/2/3_H`, `hero_1/2/3`) dans une `walls` SpriteList partagée — bloque joueur **et** zombies. Construit ensuite les `obstacles` (PNJs + stratégiques + objets + walls) pour le `PhysicsEngineSimple`, puis instancie `ZombieMode` (`world/zombie_mode.py`) avec `always_active=True`.

`always_active=True` désactive la vérification d'objectif et rend le combat permanent sans condition de quête.

## Layers tilemap utilisés

| Layer | Rôle |
|---|---|
| `Sol` | Sol rendu en premier |
| `step_1_B`, `step_1_H` | Plateforme niveau 1 (retirée à la quête 2) |
| `step_2` | Plateforme niveau 2 (retirée à la quête 3) |
| `step_3_B`, `step_3_H` | Plateforme niveau 3 (retirée à la quête 4) |
| `Mur`, `Meuble_H`, `Meuble_B`, `Meuble_T` | Obstacles et décors |
| `hero_1`, `hero_2`, `hero_3` | Obstacles joueur **et** zombies (inclus dans `walls`) |
| `Player` | Sprite joueur |

## Pipeline de rendu (MercScene)

`on_draw()` appelle `_draw_world()` puis `_draw_hud()`.

**World-space** (`camera_sprites`) : `Sol` → steps (masqués si retirés) → `Mur/Meuble_B` → PNJs `before` → `zombie_mode.draw_world()` → couches hautes (`Meuble_H`, `Meuble_T`, `hero_*`) → `Player` → PNJs `after`.

**Screen-space** (`camera_gui`) : `zombie_mode.draw_hud()` → position HUD → notifications → menu → cutscenes.
