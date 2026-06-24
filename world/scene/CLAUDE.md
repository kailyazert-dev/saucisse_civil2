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
- `self.zombie_mode = None` — référence optionnelle au `ZombieMode` actif (PhlScene, MercScene)
- `start_auto_walk()` / `update_auto_walk()` — déplacement automatique avec chemin
- `draw_stat_progress_bar()` — barre de progression stat au-dessus du joueur

### Méthodes communes héritées

| Méthode | Rôle |
|---|---|
| `on_draw()` | `clear → _draw_world → draw_stat_progress_bar → camera_gui → _draw_hud` |
| `_draw_world()` | Stub — surchargé par chaque scène |
| `_draw_hud()` | Stub — surchargé par chaque scène |
| `_split_pnjs_by_depth()` | Retourne `(before, after)` SpriteList selon `attitude` ∈ `_STAND_ATTITUDES` |
| `_update_common(dt)` | Physique + caméra + stats. Retourne `False` si menu ouvert |
| `_collect_layer(name)` | `list(self.scene[name])` avec fallback `[]` si couche absente |
| `on_key_release(key, mod)` | `input_handler.reset_movement_on_release` |
| `on_mouse_release(x, y, btn, mod)` | Délègue à `zombie_mode` si présent |
| `on_mouse_motion(x, y, dx, dy)` | Délègue à `zombie_mode` si présent |
| `on_resize(w, h)` | `super + camera_sprites.match_window()` |

`_STAND_ATTITUDES = {"errance", "stand", "dialogue"}` — attitudes qui placent un PNJ devant le joueur.

Les scènes concrètes n'implémentent que `setup()`, `_draw_world()`, `_draw_hud()`, `on_update()` et `on_key_press()`.

## SceneManager

Propriétaire de la fenêtre Arcade. Transitions via `switch_map(map_name)` qui crée une `LoadingView` avant d'appeler `setup()` sur la nouvelle scène.

Les scènes concrètes reçoivent une référence `self.manager` via `set_manager()` pour pouvoir appeler `switch_map()`.
