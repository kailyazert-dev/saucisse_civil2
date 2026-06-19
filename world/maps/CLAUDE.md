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

- `ZombieManager` : spawn de zombies, tirs, dégâts joueur
- `KyleAI` : FSM de Kyle (sit → stand → walk → chasse → dialogue) — instancié uniquement en arc 3
- `DeathMenu` : menu de mort avec fondu rouge
- Rendu en deux passes : `_draw_world()` puis `_draw_hud()` (caméras différentes)
- Curseur de visée (crosshair) affiché en mode zombie
- Balles de Kyle dessinées via `kyle_ai.sprite.draw_bullets()` dans `_draw_world()`

### Branchement KyleAI dans setup()

```python
# 1. Instanciation (arc 3 seulement — seul arc où Kyle a _standing_tex)
kyle_sprite = next((p for p in self.pnj_sprite if p.nom == "Kyle"), None)
if kyle_sprite is not None and arc_id == 3:
    self.kyle_ai = KyleAI(kyle_sprite, self.quest_manager, self.tile_map)

# 2. Dans _setup_zombie_mode() — après construction des murs :
self._combat_walls = walls          # conservé pour on_update
self.kyle_ai.init_path(walls)       # pré-calcul A*
if self.zombie_manager.is_active(): # rechargement en mode zombie
    self.kyle_ai.start_walk()       # relance la marche avant chasse

# 3. Dans on_update() :
kyle_kills = self.kyle_ai.update(dt, self._combat_walls, self.zombie_manager.zombies, arc_id == 3)
for _ in range(kyle_kills):
    self.quest_manager.register_kill()
```

## HomeScene — spécificités

- Logique de sommeil : `_sleep_available()`, `_near_bed()`, fondu noir
- Transition vers PHL conditionnelle : `_phl_unlocked` (arc ≥ 2)

## TmaScene — spécificités

- Scène la plus simple : pas de combat, navigation quête uniquement
- Transition vers PHL via `current_strategique` (Hotesse)
