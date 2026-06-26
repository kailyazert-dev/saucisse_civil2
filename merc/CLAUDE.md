# merc/

Mode mercenaire — zone de jeu dédiée, accessible depuis l'objet « Mode mercenaire » dans PHL.

## Fichiers

| Fichier / Dossier | Rôle |
|---|---|
| `merc_scene.py` | `MercScene(BaseScene)` — scène principale |
| `configs/MERC.json` | Config map : spawn joueur `[700, 325]`, pas de PNJs ni d'objets |
| `configs/zombie.json` | Stats/mouvement/drops par quête (`quetes`) et configs boss (`boss`) |
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
4. Charge `shop.json` et instancie `ShopMenu` + la liste `_coffres` depuis les objets interactifs de la map
5. Appelle `_setup_zombie_mode()` qui :
   - Appelle `_load_zombie_classes()` (statique) pour créer une sous-classe `MercZombie1`…`MercZombie4` par quête depuis la clé `quetes` de `configs/zombie.json`
   - Appelle `_load_boss_classes()` (statique) pour créer une sous-classe `BossZombie1`…`BossZombie4` par quête depuis la clé `boss` de `configs/zombie.json` ; chaque boss hérite de `ZombieAugmente`
   - Instancie `ZombieMode(always_active=True)` avec `zombie_class=_zombie_classes[0]` et `player_spawn`
   - Désactive le spawn (`set_spawn_enabled(False)`) — réactivé après la fin de l'animation `QuestNotif`

**Délai de spawn** : `on_update()` surveille `quest_notif.is_idle` — le spawn n'est débloqué qu'une fois la notification initiale terminée (flags `_notif_was_active`, `_spawn_unlocked`).

## Structure de zombie.json

Deux clés de premier niveau :

- `quetes` — tableau de 4 objets (un par quête), chacun avec `stats` (`max_sante`, `degats`), `mouvement` et `drops`
- `boss` — tableau de 4 objets boss, chacun avec `stats`, `mouvement`, `projectile` (`degats`, `vitesse`, `intervalle`, `rayon_tir`, `couleur`) et `spawn` (coordonnées d'apparition)

## Structure de shop.json

Trois sections (`soins`, `armes`, `general`), chacune étant un tableau d'items. Types d'items possibles :

| Type | Effet | Champs spécifiques |
|---|---|---|
| `soin` | Restaure des points de vie | `valeur` |
| `upgrade_arme` | Augmente les dégâts d'une arme | `slot` (`"feu"` ou `"blanc"`), `valeur` |
| `upgrade_perso` | Augmente la vie maximum | `valeur` |
| `arme` | Remplace l'arme dans un slot | `arme_id`, `slot` |

## Système de quêtes local

| Quête | Objectif | Spawn zombies | Classe zombie | Changement de terrain au passage |
|---|---|---|---|---|
| 1 | 30 kills | 2 points : `(570,80)`, `(575,547)` | `MercZombie1` | Retire physiquement `step_1_H`, passe à 3 points |
| 2 | 60 kills | 3 points : `(570,80)`, `(528,1123)`, `(1946,652)` | `MercZombie2` | Retire physiquement `step_2`, passe à 3 points |
| 3 | 90 kills | 3 points : `(570,80)`, `(528,1123)`, `(2686,1108)` | `MercZombie3` | Retire physiquement `step_3_B` et `step_3_H`, passe à 3 points |
| 4 | 110 kills | 3 points : `(570,80)`, `(528,1123)`, `(2517,1846)` | `MercZombie4` | Fin de l'arc |

La classe zombie active est mise à jour dynamiquement à chaque transition via `zombie_mode.set_zombie_class(self._zombie_classes[quest_id - 1])`.

Les sprites `step_1_H`, `step_2`, `step_3_B` et `step_3_H` sont tous retirés via `sprite.remove_from_sprite_lists()` (pas seulement masqués) — ce qui les retire de toutes leurs listes (scene, `_walls`, `_obstacles`) pour éviter les collisions résiduelles.

## Système de boss

À chaque fin de quête, quand l'objectif atteint `counter >= validator - 1`, `_trigger_boss_phase()` est appelé :

1. Bloque le spawn normal (`set_spawn_enabled(False)`)
2. Instancie le boss de la quête courante (`BossZombie1`…`BossZombie4`) à son point de spawn configuré
3. Positionne `_boss_phase = True` et garde une référence dans `_boss_sprite`

Quand le boss meurt (plus dans `zombie_manager.zombies`) : `register_kill()` est appelé pour comptabiliser le kill final, le spawn normal est réactivé et `_boss_phase` repasse à `False`.

## Distributeurs (Coffre / ShopMenu)

Les coffres sont instanciés par `MapLoader` depuis la config map (type `Coffre`). La scène les regroupe dans `_coffres` et `_coffres_sl`.

**Interaction** :
- `on_update()` calcule la distance joueur–coffre par `math.hypot` ; si `<= Coffre.INTERACTION_DISTANCE`, `_near_coffre` est défini
- Touche `E` ou `RETURN` près d'un coffre : ouvre `ShopMenu` avec les items de la section `coffre.catalogue` du shop.json
- Si `ShopMenu` est actif, toutes les touches sont redirigées vers `_shop_menu.handle_key()`

## ZombieMode

`MercScene._setup_zombie_mode()` collecte les murs de tous les layers de collision (`Mur`, `Meuble_H`, `step_1_H`, `step_2`, `step_3_H`, `hero_1/2/3`) dans `_walls` — bloque joueur **et** zombies. Construit `_obstacles` (PNJs + stratégiques + objets + walls) pour le `PhysicsEngineSimple`, puis instancie `ZombieMode` (`world/zombie_mode.py`) avec `always_active=True`.

`always_active=True` désactive la vérification d'objectif et rend le combat permanent sans condition de quête.

## Reset (_merc_reset)

Callback assigné à `zombie_mode.on_reset`, appelé après la mort du joueur. Restaure l'état initial complet :

- Réinsère `step_1_H` dans `_walls`, `_obstacles` et la scene (si `_hide_steps`)
- Réinsère `step_2` dans `_walls`, `_obstacles` et la scene (si `_hide_step2`)
- Réinsère `step_3_B` dans la scene uniquement et `step_3_H` dans `_walls`, `_obstacles` et la scene (si `_hide_step3`)
- Remet les armes par défaut (`Pistolet` + `Couteau`)
- Appelle `quest_manager.reset()`, remet les spawn points à `_QUEST1_SPAWNS`
- Remet la zombie class à `_zombie_classes[0]`, désactive le spawn
- Remet tous les flags à zéro : `_boss_phase`, `_boss_sprite`, `_spawn_unlocked`, `_notif_was_active`, `_active_quest_id`
- Ferme le `_shop_menu` et remet `_near_coffre` à `None`

## Layers tilemap utilisés

| Layer | Rôle |
|---|---|
| `Sol` | Sol rendu en premier |
| `step_1_B`, `step_1_H` | Plateforme niveau 1 (retirée à la quête 2) |
| `step_2` | Plateforme niveau 2 (retirée à la quête 3) |
| `step_3_B`, `step_3_H` | Plateforme niveau 3 (retirée à la quête 4) |
| `Mur`, `Meuble_H`, `Meuble_B`, `Meuble_T` | Obstacles et décors |
| `hero_1`, `hero_2`, `hero_3` | Obstacles joueur **et** zombies (inclus dans `_walls`) |
| `Player` | Sprite joueur |

## Pipeline de rendu (MercScene)

`on_draw()` appelle `_draw_world()` puis `_draw_hud()`.

**World-space** (`camera_sprites`) : `Sol` → steps (sautés si retirés) → `Mur/Meuble_B` → PNJs `before` → `zombie_mode.draw_world()` → couches hautes (`Meuble_H`, `Meuble_T`, `hero_*`) → `_coffres_sl.draw()` → `scene["Player"].draw()` → PNJs `after`.

**Screen-space** (`camera_gui`) : `zombie_mode.draw_hud()` → position HUD → notifications → menu → cutscenes → hint `[ E ] Ouvrir le distributeur` (si `_near_coffre` et shop inactif) → `_shop_menu.draw(player_sprite)`.
