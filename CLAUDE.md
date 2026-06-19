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
          └── BaseScene active (HomeScene | PhlScene | TmaScene)
```

---

## Structure des dossiers

### `world/` — espace de jeu (world-space)
Tout ce qui est rendu avec `camera_sprites`.

| Sous-dossier | Contenu clé |
|---|---|
| `world/scene/` | `BaseScene` (classe mère), `SceneManager`, `LoadingView` |
| `world/maps/` | `HomeScene`, `PhlScene`, `TmaScene` |
| `world/loader/` | `MapLoader` — lit les JSON de config et instancie PNJs/objets |
| `world/objects/` | `UpStat`, `UpStatCollection`, `MapActionObject`, `ObjetInteractif` |
| `world/environment/` | `Environnement` — paramètres sociaux d'un lieu |
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

### Système de quêtes
Objectifs de 4 types : `"stat"` (seuil), `"compteur"` (kills), `"talk"` (cutscène), `"map_action"` (objet ENTER).

### Sauvegardes
`save/character_save.json` + `save/quests_save.json` — runtime.  
`save/saves.json` — slots nommés (via menu pause).  
`utils/paths.py` résout les chemins en dev et en build PyInstaller frozen.

---

## Ajouter une nouvelle map

1. `map/map_configs/<NOM>.json` — PNJs, objets, spawns
2. `world/tilemaps/<NOM>.tmx` — tilemap Tiled
3. `world/maps/<nom>_scene.py` — classe `<Nom>Scene(BaseScene)`
4. `world/scene/scene_manager.py` — ajouter dans `_MAPS`

---

## Langue

Tout le texte en jeu, les noms de variables, commentaires et données quêtes/PNJs sont en **français**.
