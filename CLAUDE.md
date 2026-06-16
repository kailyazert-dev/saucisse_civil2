# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
pip install -r requirements.txt
python main.py
```

Requires a `.env` file with `REPLICATE_API_TOKEN=your_key` (see `.env.example`). The Replicate API drives NPC dialogue generation.

No automated tests exist — all testing is manual.

## Architecture

Three managers are initialized in `main.py` and passed down through the system:

- **`QuestManager`** (`quests/quest_manager.py`) — loads quest definitions from `quests/quests_file/quests.json`, tracks Arc → Quest → Objective progression, saves to `save/quests_save.json`
- **`CharacterManager`** (`character/character_manager.py`) — owns the player sprite, manages the 9 stats (force, vitesse, endurance, mathematique, logique, rpg, music, langue, sociabilite), auto-saves to `save/character_save.json` every 30 seconds on change
- **`MapManager`** (`map/map_manager.py`) — creates the Arcade window (1056×750), handles map transitions with a loading screen, delegates each frame to the active `BaseGameView` subclass

### Map System

Each location is a subclass of `BaseGameView` (`map/map_base.py`) which runs the Arcade game loop (`on_draw`, `on_update`, `on_key_press`, `on_mouse_press`). The three maps are `HOME`, `PHL`, and `TMA` in `map/map_classes/`. Adding a new map requires:
1. A JSON config in `map/map_configs/<NAME>.json` (NPCs, objects, positions)
2. A `.tmx` tilemap in `map/map_tmx/`
3. A `BaseGameView` subclass in `map/map_classes/<NAME>.py`

NPCs and interactable objects are loaded from the JSON config by `map/map_loader.py`.

### Input

AZERTY layout: **Z/Q/S/D** to move, **ENTER** to interact/confirm, **ESCAPE** to cancel/close. `InputHandler` (`map/input_handler.py`) holds the set of currently-pressed keys and delegates actions to the relevant system.

### Stat Progression

Interactable objects implement `UpStat` or `UpStatCollection` (in `map/map_classes/objet.py`). When the player presses ENTER on one, `CharacterManager.start_up(progresseur)` begins incrementing the stat by +0.002 every 2 seconds, shown as a progress bar above the player.

### NPC Dialogue

`DialogueSystem` (`map/dialogue_system.py`) calls the Replicate API in a background thread (rate-limited to 3 calls / 30 s). NPC personalities come from `assets/param_humain.py`. Cutscene dialogue for key characters (Kyle, Sylvain, etc.) is handled by `ui_quests_dialogue.py` and drives quest objective completion.

### Rendering Pipeline

Two cameras are used: `camera_sprites` (world space — tilemap, sprites, interaction boxes) and `camera_gui` (screen space — menus, dialogue box, quest notifications, stat bar). Quest notifications are queued by `QuestManager` and consumed by `ui_quests_notif.py`.

### Save Files

All runtime saves live in `save/`. `utils/paths.py` resolves paths for both dev mode and PyInstaller frozen builds. `saves.json` holds named save slots; `checkpoint_*.json` files are automatic checkpoints.

## Key Constants

`assets/param_map.py` — window size, movement speed, tile size, camera constants.  
`assets/param_humain.py` — NPC stat profiles and system prompts for dialogue.

## Language

All in-game text, variable names, comments, and quest/NPC data are in **French**.
