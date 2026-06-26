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
- État d'interaction : `current_pnj`, `current_objet`, `current_collection`, `open_collection`, `current_index_upstat`, `current_select_upstat`, `current_map_action`, `current_strategique`
- Dialogue : `current_input`, `last_response`, `is_typing`, `waiting_response`
- Sous-systèmes injectés dans `__init__` : `InputHandler`, `InteractUI`, `DialogueSystem`, `Menu`, `QuestNotif`, `CutsceneManager`
- `self.zombie_mode = None` — référence optionnelle au `ZombieMode` actif (PhlScene, MercScene)
- `show_menu`, `show_side_bar` — flags UI
- `auto_walk_active`, `auto_walk_target`, `auto_walk_path`, `_on_auto_walk_done` — déplacement automatique avec chemin
- `start_auto_walk()` / `update_auto_walk()` — déplacement automatique avec chemin
- `draw_stat_progress_bar()` — barre de progression stat au-dessus du joueur (deux couches : barre de remplissage stat + barre de tick d'intervalle)

### Méthodes communes héritées

| Méthode | Rôle |
|---|---|
| `on_draw()` | `clear → _draw_world → draw_stat_progress_bar → camera_gui → _draw_hud` |
| `_draw_world()` | Stub — surchargé par chaque scène |
| `_draw_hud()` | Stub — surchargé par chaque scène |
| `_split_pnjs_by_depth()` | Retourne `(before, after)` SpriteList selon `attitude` ∈ `_STAND_ATTITUDES` |
| `_update_common(dt)` | Physique + caméra + stats. Retourne `False` si menu ouvert |
| `_collect_layer(name)` | `list(self.scene[name])` avec fallback `[]` si couche absente |
| `create_obstacles()` | Délègue à `interact_ui.create_obstacles()` |
| `follow_player()` | Lerp de `camera_sprites.position` vers le joueur (vitesse `camera_speed = 0.1`) |
| `get_quests()` | Dessine le bouton "Quêtes" en screen-space |
| `update_notif(dt)` | Met à jour `quest_notif` et vérifie les objectifs stat en attente |
| `draw_notif()` | Appelle `quest_notif.draw()` |
| `get_position()` | Affiche les coordonnées joueur (x/y) en bas à gauche — utile en debug |
| `set_manager(manager)` | Stocke la référence `SceneManager` dans `self.manager` |
| `on_key_release(key, mod)` | `input_handler.reset_movement_on_release` |
| `on_mouse_release(x, y, btn, mod)` | Délègue `button` à `zombie_mode.on_mouse_release()` si présent |
| `on_mouse_motion(x, y, dx, dy)` | Délègue `(x, y)` à `zombie_mode.on_mouse_motion()` si présent |
| `on_resize(w, h)` | `super + camera_sprites.match_window()` |

`_STAND_ATTITUDES = {"errance", "stand", "dialogue"}` — attitudes qui placent un PNJ devant le joueur.

Les scènes concrètes n'implémentent que `setup()`, `_draw_world()`, `_draw_hud()`, `on_update()` et `on_key_press()`.

## SceneManager

Propriétaire de la fenêtre Arcade. Transitions via `switch_map(map_name)` qui crée une `LoadingView` avant d'appeler `setup()` sur la nouvelle scène.

Attributs : `window`, `quest_manager`, `character_manager`, `last_map` (map précédente), `current_map` (map active), `view` (instance de scène active).

Maps enregistrées dans `_MAPS` (dict module-level) :

| Clé | Classe |
|---|---|
| `"home"` | `HomeScene` |
| `"phl"` | `PhlScene` |
| `"tma"` | `TmaScene` |
| `"merc"` | `MercScene` |

`_load_initial_map()` — charge `HomeScene` au démarrage via une `LoadingView`.

Les scènes concrètes reçoivent une référence `self.manager` via `set_manager()` pour pouvoir appeler `switch_map()`.
