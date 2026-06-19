# world/scene/

Couche de base du moteur de jeu : gestion de la boucle Arcade, des caméras et des transitions de map.

## Fichiers

| Fichier | Classe | Rôle |
|---|---|---|
| `base_scene.py` | `BaseScene(arcade.View)` | Classe mère de toutes les scènes |
| `scene_manager.py` | `SceneManager` | Crée la fenêtre, gère les transitions entre maps |
| `loading_view.py` | `LoadingView(arcade.View)` | Affiche "Chargement..." pendant un frame |

## BaseScene

God-class allégée : elle fournit à toutes les scènes :
- `camera_sprites` (world-space) + `camera_gui` (screen-space)
- `physics_engine`, `scene`, `tile_map`
- Listes de sprites : `pnj_sprite`, `strategique_sprite`, `objet_sprites`
- État d'interaction : `current_pnj`, `current_objet`, `current_collection`, `current_map_action`
- Sous-systèmes injectés dans `__init__` : `InputHandler`, `InteractUI`, `DialogueSystem`, `Menu`, `QuestNotif`, `CutsceneManager`
- `start_auto_walk()` / `update_auto_walk()` — déplacement automatique avec chemin
- `draw_stat_progress_bar()` — barre de progression stat au-dessus du joueur

Les scènes concrètes (`HomeScene`, `PhlScene`, `TmaScene`) n'implémentent que `setup()`, `on_draw()`, `on_update()` et les handlers d'input.

## SceneManager

Propriétaire de la fenêtre Arcade. Transitions via `switch_map(map_name)` qui crée une `LoadingView` avant d'appeler `setup()` sur la nouvelle scène.

Les scènes concrètes reçoivent une référence `self.manager` via `set_manager()` pour pouvoir appeler `switch_map()`.
