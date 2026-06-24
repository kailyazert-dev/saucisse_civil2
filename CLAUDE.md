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
| `world/objects/` | `UpStat`, `UpStatCollection`, `MapActionObject`, `ObjetInteractif` |
| `world/environment/` | `Environnement` — paramètres sociaux d'un lieu |
| `world/zombie_mode.py` | `ZombieMode` — encapsule spawn, tir, dégâts, mort et HUD zombie (partagé par PhlScene et MercScene) |
| `world/pathfinding/` | Réservé — extraction A* prévue |

### `ui/` — interface (screen-space)
Tout ce qui est rendu avec `camera_gui`.

| Sous-dossier | Contenu clé |
|---|---|
| `ui/dialogue/` | `DialogueSystem` (API Replicate), `CutscenePopup` |
| `ui/cutscene/` | `CutsceneManager`, `cutscene_data.py` (textes scriptés) |
| `ui/menus/` | `StatsView`, `Menu` (pause), `DeathMenu` |
| `ui/hud/` | `InteractUI` (popups proximité), `QuestNotif` (notifications) |
| `ui/effects/` | `ScreenFade` (fondu plein écran) |

### `input/` — saisie clavier/souris
`InputHandler` + `MOVE_KEYS` (AZERTY : Z/Q/S/D).

### `character/` — entités personnages
Voir `character/CLAUDE.md` pour le détail complet.

| Sous-dossier | Contenu clé |
|---|---|
| `character/player/` | `Player`, `CharacterManager`, `AnimationManager` |
| `character/pnj/` | `PNJ` (FSM), `PNJState`, `pnj_loader` |
| `character/enemies/` | `Zombie`, `ZombieManager` |
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
- `assets/images/` — sprites (joueur, PNJs, zombies, objets, armes)

### `merc/` — mode arène mercenaire (auto-contenu)
Module autonome pour le mode survie zombie. Contrairement aux autres maps, tout est local au dossier.

| Fichier / Sous-dossier | Contenu clé |
|---|---|
| `merc/merc_scene.py` | `MercScene(BaseScene)` — scène principale, gère rendu + logique + input |
| `merc/configs/MERC.json` | Config map : spawn joueur `[574, 50]`, pas de PNJs ni d'objets |
| `merc/map/PHL_MER.tmx` | Tilemap Tiled (tilesets dans `merc/map/tuile/`) |
| `merc/quests/quests.json` | Arc « Mode Mercenaire » : 3 quêtes progressives (30 / 60 / 90 kills) |
| `merc/quests/merc_quests_default.json` | État initial des quêtes merc (quête 1 uniquement) |

`MercScene` crée son propre `QuestManager` local (sauvegarde désactivée) et instancie `ZombieMode(always_active=True)`.

### `map/` — ancienne structure (conservée, inactive)
Les fichiers `map/` originaux sont conservés mais ne sont plus importés.  
Le jeu tourne entièrement depuis `world/`, `ui/`, `input/`.  
Ils peuvent être supprimés après validation complète.

---

## Pipeline de rendu

```
BaseScene.on_draw()
  camera_sprites.use()          ← world-space
    scene.draw()                  tilemap layers
    interact_ui.interact_*()      popups proximité
    draw_stat_progress_bar()      barre stat au-dessus du joueur
  camera_gui.use()              ← screen-space
    dialogue.draw_dialogue_box()
    interact_ui.draw_side_bar()
    get_quests()                  bouton Quêtes
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
Activé depuis PhlScene via un objet `ObjetInteractif`. `MercScene.setup()` instancie un `QuestManager` local (fichiers dans `merc/quests/`, **sauvegarde désactivée**) et appelle `_setup_zombie_mode()` qui :
- Collecte les murs des layers : `Mur`, `Meuble_H`, `step_1_H`, `step_2`, `step_3_H`
- Crée un `PhysicsEngineSimple` joueur ↔ obstacles
- Instancie `ZombieMode` via `world/zombie_mode.py` avec `always_active=True`

`on_update()` récupère les kills depuis `ZombieMode` et les pousse dans `quest_manager`. Progression en 3 quêtes avec changements de terrain à chaque passage :

| Quête | Objectif | Effet au passage |
|---|---|---|
| 1 → 2 | 30 kills | Retire physiquement `step_1_H`, 3 points de spawn |
| 2 → 3 | 60 kills | Retire physiquement `step_2`, 4 points de spawn |
| 3 | 90 kills | — |

La sauvegarde runtime est dans `save/merc_quests_save.json` (séparé de `save/quests_save.json`).

### ZombieMode (`world/zombie_mode.py`)
Classe partagée entre `PhlScene` et `MercScene`. Encapsule : spawn de zombies, tir joueur, dégâts, fondu de mort, `DeathMenu`, et HUD (compteur kills, barre vie, info arme, crosshair). Paramètre `always_active=True` désactive la vérification d'objectif — utile en MercScene où le combat est permanent.

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
