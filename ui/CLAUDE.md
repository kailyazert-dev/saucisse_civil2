# ui/

Tout ce qui est affiché en **screen-space** (coordonnées fenêtre, caméra GUI). S'oppose à `world/` qui est en world-space.

## Structure

```
ui/
├── dialogue/   — boîte de dialogue IA (NPC) + popup cutscène
├── cutscene/   — gestionnaire de cutscènes narratives + données de dialogue
├── menus/      — menus fullscreen (stats, pause, mort)
├── hud/        — éléments HUD permanents (interaction, notifications)
└── effects/    — effets visuels plein écran (fondu)
```

## Principe

Chaque composant UI :
- Reçoit une référence à `game_view` (ou `quest_manager`) pour lire l'état
- N'écrit **jamais** directement l'état du jeu — il délègue à `quest_manager`, `character_manager`, ou `input_handler`
- Expose une méthode `draw()` appelée depuis `on_draw()` de la scène, **après** `camera_gui.use()`

## Flux de rendu

```
BaseScene.on_draw()
  └── camera_gui.use()
        ├── dialogue.draw_dialogue_box()
        ├── interact_ui.draw_box() + draw_side_bar()
        ├── get_quests()             ← inline dans BaseScene
        ├── quest_notif.draw()
        ├── menu.draw()
        └── cutscene_manager.draw()
```
