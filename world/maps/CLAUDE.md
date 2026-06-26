# world/maps/

Implémentations concrètes des zones de jeu. Chaque fichier est une sous-classe de `BaseScene`.

## Fichiers

| Fichier | Classe | Zone |
|---|---|---|
| `home_scene.py` | `HomeScene` | Appartement du joueur |
| `phl_scene.py` | `PhlScene` | Bureaux PHL — zone de combat zombies |
| `tma_scene.py` | `TmaScene` | Bureaux TMA — zone quête Guy |

## Pattern commun

Chaque scène implémente :

```python
class XxxScene(BaseScene):
    def setup(self, last_map):       # charge tilemap, player, PNJs, objets, physics
    def on_draw(self):               # rendu world puis gui
    def on_update(self, delta_time): # physique, IA, notifications
    def on_key_press(key, mod):      # délègue à input_handler + logique locale
    def on_key_release(key, mod):    # délègue à input_handler
    def on_mouse_press(x, y, ...):   # délègue à input_handler
    def on_text(text):               # dialogue ou menu
```

## PhlScene — spécificités

- `ZombieMode` (`self.zombie_mode`) : spawn de zombies, tirs, dégâts joueur — fondu et overlay de mort gérés en interne par `ZombieMode`
- `KyleAI` : FSM de Kyle (sit → stand → walk → chasse → dialogue) — instancié uniquement en arc 3
- Rendu en deux passes : `_draw_world()` puis `_draw_hud()` (caméras différentes)
- Curseur de visée (crosshair) affiché en mode zombie via `ZombieHUD`
- Balles de Kyle dessinées via `kyle_ai.sprite.draw_bullets()` dans `_draw_world()`
- Transition vers le mode mercenaire via l'objet `'Mode mercenaire'` dans `on_key_press()` → `switch_map('merc')`
- Visibilité des PNJs en arc 3 : seul Kyle reste visible (`pnj.visible = arc_id != 3 or pnj.nom == "Kyle"`)
- Pointeur souris masqué en mode zombie actif : `self.window.set_mouse_visible(not self.zombie_mode.is_active())`

### Attributs propres à PhlScene

| Attribut | Type | Rôle |
|---|---|---|
| `_physics_obstacles` | `SpriteList` | Obstacles du `PhysicsEngineSimple`, stocké en attribut pour modification dynamique |
| `_kyle_removed_from_obstacles` | `bool` | Flag indiquant si le sprite de Kyle a été retiré des obstacles |
| `kyle_ai` | `KyleAI` | Instance de l'IA de Kyle (créée uniquement en arc 3, accédée via `hasattr`) |

### Branchement KyleAI dans setup()

```python
# 1. Instanciation (arc 3 seulement — seul arc où Kyle a _standing_tex)
kyle_sprite = next((p for p in self.pnj_sprite if p.nom == "Kyle"), None)
if kyle_sprite is not None and arc_id == 3:
    self.kyle_ai = KyleAI(kyle_sprite, self.quest_manager, self.tile_map)

# 2. Obstacles stockés en attribut (pas une variable locale)
self._physics_obstacles = self.interact_ui.create_obstacles()
self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self._physics_obstacles)

# 3. Dans _setup_zombie_mode() — après construction des murs :
self.kyle_ai.init_path(walls)        # pré-calcul A*
if self.zombie_mode.is_active():     # rechargement en mode zombie
    self.kyle_ai.start_walk()        # relance la marche avant chasse
```

### Toggle Kyle dans les obstacles (on_update)

Quand le mode zombie s'active, le sprite de Kyle est retiré de `_physics_obstacles` pour que le joueur puisse le traverser (utile en mode chasse). Il est réajouté quand le mode zombie se désactive.

```python
if self.zombie_mode.is_active() and not getattr(self, "_kyle_removed_from_obstacles", False):
    self._kyle_removed_from_obstacles = True
    if hasattr(self, "kyle_ai"):
        try:
            self._physics_obstacles.remove(self.kyle_ai.sprite)
        except Exception:
            pass
elif getattr(self, "_kyle_removed_from_obstacles", False) and not self.zombie_mode.is_active():
    self._kyle_removed_from_obstacles = False
    if hasattr(self, "kyle_ai"):
        try:
            self._physics_obstacles.append(self.kyle_ai.sprite)
        except Exception:
            pass
```

### Rendu _draw_world() — tri de profondeur

```
Sol / Mur / Meuble_B
PNJs derrière le joueur (split par profondeur)
zombie_mode.draw_world()          # arme, arcs mêlée, zombies, drops
Meuble_H / Meuble_T / Livre / OrdiRPG / PcTest / Objets
PNJs stratégiques visibles
joueur
balles de Kyle (kyle_ai.sprite.draw_bullets())
PNJs devant le joueur

-- uniquement si zombie_mode.is_active() == False --
interact_ui.interact_obj_prg()
interact_ui.interact_pnj_strateg()
interact_ui.interact_pnj()
box sortie (Maison) si joueur en zone de sortie
```

### Rendu _draw_hud()

```
if zombie_mode.is_active():
    zombie_mode.draw_hud()          # HUD kills/vie/or/armes/crosshair
else:
    dialogue.draw_dialogue_box()
    interact_ui.draw_box()
    get_quests()
    interact_ui.draw_side_bar()
    zombie_mode.draw_death_overlay()  # fondu/menu si mort en suspens

get_position()
draw_notif()
menu.draw()
cutscene_manager.draw()
```

## HomeScene — spécificités

- Logique de sommeil : `_sleep_objective()`, `_sleep_available()`, `_near_bed()`, fondu noir animé (`_fade_alpha`, `_fade_dir`)
- `_phl_unlocked` : propriété (`@property`) — `True` si `arc_id >= 2` ou si plus d'arc (jeu terminé)
- Transition vers PHL : zone de sortie à `center_y ∈ [975, 980]` et `center_x ∈ [735, 755]`, conditionnelle à `_phl_unlocked`
- La touche Entrée en zone de lit lance le fondu d'endormissement (`_fade_dir = 1`) qui complète l'objectif `map_action` de type `"lit"` et sauvegarde

## TmaScene — spécificités

- Scène la plus simple : pas de combat, navigation quête uniquement
- `on_draw()` inclut `cutscene_manager.draw()` (p. ex. pour les cutscènes de l'arc Guy)
- Transition vers PHL via `current_strategique` : Entrée quand `current_strategique` est défini et aucune cutscène active → `switch_map("phl")`
- `on_update()` n'appelle pas `character_manager.update_player_stats()` (pas de progression de stat en TMA)
