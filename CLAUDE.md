# CLAUDE.md

Ce fichier documente l'architecture du projet pour Claude Code.

## Démarrage rapide

```bash
python main.py          # lancer le jeu
python -m compileall . -q  # vérifier la syntaxe
```

Nécessite un `.env` à la racine avec `REPLICATE_API_TOKEN=<clé>`.

---

## Architecture générale

Trois managers racines initialisés dans `main.py` et injectés en cascade :

```
main.py
  QuestManager          (quests/quest_manager.py)
  CharacterManager      (character/player/player_manager.py)
  SceneManager          (world/scene/scene_manager.py)
    └── fenêtre Arcade 1056×750
          └── BaseScene active (HomeScene | PhlScene | TmaScene | MercScene)
```

---

## Structure des dossiers

### `world/` — espace de jeu (world-space)
Tout ce qui est rendu avec `camera_sprites`.

| Sous-dossier / fichier | Contenu clé |
|---|---|
| `world/scene/` | `BaseScene` (classe mère), `SceneManager`, `LoadingView` |
| `world/maps/` | `HomeScene`, `PhlScene`, `TmaScene` |
| `world/loader/` | `MapLoader` — lit `world/configs/<NOM>.json` et instancie PNJs/objets |
| `world/objects/` | `interactables/` (UpStat, UpStatCollection, MapActionObject, ObjetInteractif) + `drops/` (GoldDrop, HealthDrop) |
| `world/environment/` | `Environnement` — paramètres sociaux d'un lieu |
| `world/zombie_mode.py` | `ZombieMode` — encapsule spawn, tir, dégâts et mort (partagé par PhlScene et MercScene) ; délègue le rendu à `ZombieHUD` |
| `world/pathfinding/` | Réservé — extraction A* prévue |

### `ui/` — interface (screen-space)
Tout ce qui est rendu avec `camera_gui`.

| Sous-dossier | Contenu clé |
|---|---|
| `ui/dialogue/` | `DialogueSystem` (API Replicate), `CutscenePopup` |
| `ui/cutscene/` | `CutsceneManager`, `cutscene_data.py` (textes scriptés) |
| `ui/menus/` | `StatsView`, `Menu` (pause), `DeathMenu` |
| `ui/hud/` | `InteractUI` (popups proximité), `QuestNotif` (notifications), `ZombieHUD` (rendu mode zombie) |
| `ui/effects/` | `ScreenFade` (fondu plein écran) |

### `input/` — saisie clavier/souris
`InputHandler` + `MOVE_KEYS` (AZERTY : Z/Q/S/D).

### `character/` — entités personnages
Voir `character/CLAUDE.md` pour le détail complet.

| Sous-dossier | Contenu clé |
|---|---|
| `character/player/` | `Player`, `CharacterManager`, `AnimationManager` |
| `character/pnj/` | `PNJ` (FSM), `PNJState`, `pnj_loader` |
| `character/enemies/` | `Zombie`, `ZombieAugmente`, `ZombieManager` (SPAWN_INTERVAL=0.8, MAX_ZOMBIES=70) |
| `character/equipment/` | `Weapon`, `Bullet` |
| `character/ai/` | `KyleAI` (FSM + A* pour Kyle dans PHL) |

### `quests/` — système de quêtes
`QuestManager` → `Arc` → `Quest` → `Objective`.  
Définitions : `quests/quests_file/quests.json`.  
Sauvegarde runtime : `save/quests_save.json`.

### `core/` — constantes globales
`core/constants.py` — positions Kyle (`PHL_POSITIONS`), config combat (`COMBAT_CONFIG`).

### `assets/` — ressources statiques
- `assets/param_map.py` — taille fenêtre, vitesse, tile size, police
- `assets/param_humain.py` — profils stat PNJs, system prompts dialogue IA
- `assets/images/` — sprites (joueur, PNJs, objets, armes) ; zombies dans `assets/images/enemies/zombies/` (préfixe `z_aug_` pour `ZombieAugmente`, préfixe `z_1_` pour `Zombie` de base)

### `merc/` — mode arène mercenaire (auto-contenu)
Module autonome pour le mode survie zombie. Contrairement aux autres maps, tout est local au dossier.

| Fichier / Sous-dossier | Contenu clé |
|---|---|
| `merc/merc_scene.py` | `MercScene(BaseScene)` — scène principale, gère rendu + logique + input |
| `merc/configs/MERC.json` | Config map : spawn joueur `[700, 325]`, pas de PNJs ni d'objets |
| `merc/map/PHL_MER.tmx` | Tilemap Tiled chargée par le jeu (tilesets dans `merc/map/tuile/`) |
| `merc/quests/quests.json` | Arc « Mode Mercenaire » : 4 quêtes progressives (30 / 60 / 90 / 110 kills) — sert aussi de fichier de réinitialisation par défaut |
| `merc/configs/zombie.json` | Config des zombies mercenaires : stats, mouvement, drops |
| `merc/configs/shop.json` | Catalogue des distributeurs : sections `soins`, `armes`, `general` |

`MercScene` crée son propre `QuestManager` local (sauvegarde désactivée) et instancie `ZombieMode(always_active=True)`.

### `map/` — ancienne structure (conservée, inactive)
Les fichiers `map/` originaux sont conservés mais ne sont plus importés.  
Le jeu tourne entièrement depuis `world/`, `ui/`, `input/`.  
Ils peuvent être supprimés après validation complète.

---

## Pipeline de rendu

```
BaseScene.on_draw()             ← défini dans BaseScene, hérité par toutes les scènes
  _draw_world()                 ← world-space, surchargé par chaque scène
    camera_sprites.use()
      tilemap layers
      interact_ui.interact_*()    popups proximité
      zombie_mode.draw_world()    → ZombieHUD.draw_world() : arme + arcs mêlée
                                  → zombie_manager.draw() : sprites zombies + balles
                                  → drops.draw() : objets lâchés à la mort
                                  → rocks.draw() : pierres lancées par ZombieAugmente
  draw_stat_progress_bar()      barre stat au-dessus du joueur
  camera_gui.use()              ← activé dans on_draw() avant _draw_hud()
  _draw_hud()                   ← screen-space, surchargé par chaque scène
      zombie_mode.draw_hud()    → ZombieHUD.draw_hud() : kills + vie + or + armes + crosshair
      dialogue.draw_dialogue_box()
      interact_ui.draw_side_bar()
      get_quests()                bouton Quêtes
      quest_notif.draw()
      menu.draw()
      cutscene_manager.draw()
```

---

## Mécaniques clés

### Progression de stat
`UpStat.utiliser()` → `CharacterManager.start_up(progresseur)` → +0.002 toutes les 2 s → barre au-dessus du joueur. Auto-save toutes les 30 s pendant la progression.

### Dialogue IA
`DialogueSystem` appelle Replicate (gpt-4o-mini) dans un thread daemon. Rate-limit : 3 appels / 30 s. Personnalités dans `assets/param_humain.IbmI_personnage`.

### Cutscènes narratives
`CutsceneManager.try_trigger(pnj)` vérifie arc + quête + objectif `"talk"`. Si conditions remplies, ouvre la `CutscenePopup` correspondante. À la fin, le callback `on_done` complète l'objectif et déclenche l'effet suivant (arme, marche Kyle…).

### Mode Mercenaire (arène zombie)
Activé depuis PhlScene via un objet `ObjetInteractif`. `MercScene.setup()` :
- Instancie un `QuestManager` local (fichiers dans `merc/quests/`, **sauvegarde désactivée**, `quests.json` sert aussi de fichier de réinitialisation par défaut)
- Équipe le joueur avec `Pistolet` (feu) et `Couteau` (blanc)
- Appelle `_setup_zombie_mode()` qui collecte les murs (`Mur`, `Meuble_H`, `step_1_H`, `step_2`, `step_3_H`, `hero_1/2/3`), crée un `PhysicsEngineSimple` et instancie `ZombieMode(always_active=True)`
- `_load_zombie_class()` (méthode statique) lit `merc/configs/zombie.json` et crée dynamiquement `MercZombie(Zombie)` avec les stats/mouvement/drops configurés
- Le spawn est retardé jusqu'à la fin de l'animation `QuestNotif` via deux flags : `_notif_was_active` (détecte le début de la notif) et `_spawn_unlocked` (activé quand `quest_notif.is_idle` redevient vrai)

`on_update()` récupère les kills depuis `ZombieMode` et les pousse dans `quest_manager`. Progression en 4 quêtes avec changements de terrain à chaque passage :

| Quête | Objectif | Spawn zombies | Effet au passage |
|---|---|---|---|
| 1 | 30 kills | 2 points : `(570,80)`, `(575,547)` | Retire `step_1_H`, passe à 3 points |
| 2 | 60 kills | 3 points : `(570,80)`, `(528,1123)`, `(1946,652)` | Retire `step_2`, passe à 3 points |
| 3 | 90 kills | 3 points : `(570,80)`, `(528,1123)`, `(2686,1108)` | Retire `step_3_H`, passe à 4 points |
| 4 | 110 kills | 4 points : `(570,80)`, `(528,1123)`, `(2686,1108)`, `(2517,1846)` | — |

La sauvegarde runtime est dans `save/merc_quests_save.json` (séparé de `save/quests_save.json`).

### ZombieMode (`world/zombie_mode.py`)
Classe partagée entre `PhlScene` et `MercScene`. Encapsule : spawn de zombies, tir joueur, dégâts, fondu de mort et `DeathMenu`. Délègue tout le rendu à `ZombieHUD` (`ui/hud/zombie_hud.py`) via `self._hud`. Paramètre `always_active=True` désactive la vérification d'objectif — utile en MercScene où le combat est permanent.

Attributs notables :
- `self.drops` — `SpriteList` des drops spawmés à la mort de zombies
- `self.rocks` — `SpriteList` des pierres lancées par les `ZombieAugmente` ; géré par `_collect_rocks()` et `_update_rocks()`
- `self.on_reset` — callback optionnel (défaut `None`) appelé dans `_do_death_reset()` ; permet à `MercScene` d'être notifiée d'un reset

Méthodes notables :
- `set_spawn_enabled(bool)` — active/désactive le spawn de zombies
- `set_spawn_points(list)` — change les points de spawn dynamiquement
- `set_zombie_class(zombie_class)` — change la classe de zombie après setup (modifie `zombie_manager._zombie_class`)
- `draw_death_overlay()` — dessine le fondu de mort et le menu de mort, appelable indépendamment de `is_active()`
- `setup(walls, spawn_points, always_active, zombie_class, player_spawn)` — signature étendue : accepte une sous-classe de `Zombie` et la position de respawn joueur

### ZombieAugmente (`character/enemies/zombie_augmente.py`)
Sous-classe de `Zombie` avec sprites préfixés `z_aug_`. Stats renforcées par rapport au zombie de base :

| Attribut | ZombieAugmente | Zombie (défaut) |
|---|---|---|
| `MAX_HEALTH` | 30 | — |
| `DAMAGE` | 7 | — |
| `VITESSE_ERRANCE` | 100.0 | 90 |
| `VITESSE_CHASSE` | 160.0 | — |
| `ACCEL_CHASSE` | 80.0 | 30 |
| `RAYON_DETECTION` | 480 | 220 |
| `RAYON_FUITE` | 550 | 450 |

Tir périodique (surcharge de `move()`) : lance un projectile (`Bullet` avec `size=10`, couleur `(150,100,60)`, dégâts 2, vitesse 6.0) si en mode chasse et dans `RAYON_TIR=400`, toutes les `PROJECTILE_INTERVALLE=2.5` secondes. Les projectiles sont collectés dans `ZombieMode.rocks`.

### ZombieHUD (`ui/hud/zombie_hud.py`)
Responsable unique du rendu visuel du mode zombie. Interface en colonne verticale côté droit : kills → barre vie → or (avec icône pièce) → arme feu → arme blanche. Accède à `ZombieMode` via `self._zm`.

Constantes de layout : `_PANEL_RIGHT`, `_PANEL_W`, `_PANEL_LEFT`, `_BAR_X`, `_BAR_Y`, `_ICON_SIZE`.

Méthodes internes :
- `_draw_player_firearm()` — sprite arme à feu orienté vers le curseur
- `_draw_melee_arcs()` — animation de frappe arc mêlée
- `_draw_stats()` — kills + barre vie + or + armes
- `_draw_weapon_compact(w, cy, label, icon_size)` — ligne compacte icône + nom + dégâts (remplace l'ancienne `_draw_weapon_card`)
- `_draw_crosshair()` — viseur rouge

### Système de quêtes
Objectifs de 4 types : `"stat"` (seuil), `"compteur"` (kills), `"talk"` (cutscène), `"map_action"` (objet ENTER).

### Sauvegardes
`save/character_save.json` + `save/quests_save.json` — runtime.  
`save/saves.json` — slots nommés (via menu pause).  
`utils/paths.py` résout les chemins en dev et en build PyInstaller frozen.

---

## Ajouter une nouvelle map

**Pattern standard** (HomeScene, PhlScene, TmaScene) :
1. `world/configs/<NOM>.json` — PNJs, objets, spawns
2. `world/tilemaps/<NOM>.tmx` — tilemap Tiled
3. `world/maps/<nom>_scene.py` — classe `<Nom>Scene(BaseScene)`
4. `world/scene/scene_manager.py` — ajouter dans `_MAPS`

**Pattern auto-contenu** (MercScene) : tout dans un dossier `<nom>/` à la racine avec ses propres `configs/`, `map/`, et `quests/`. Utile pour les modes de jeu isolés qui ne partagent pas les quêtes globales.

---

## Langue

Tout le texte en jeu, les noms de variables, commentaires et données quêtes/PNJs sont en **français**.
