# world/

Représentation du monde de jeu : scènes Arcade, cartes, chargement, objets interactifs et environnement.

## Structure

```
world/
├── scene/          — couche arcade.View (boucle de jeu, caméras, physique)
├── maps/           — implémentations par zone (HOME, PHL, TMA)
├── loader/         — chargement des configs JSON de map (world/configs/)
├── objects/        — objets interactifs (interactables/) et drops ennemis (drops/)
├── environment/    — données d'environnement social d'un lieu
├── zombie_mode.py  — ZombieMode : spawn, tir, dégâts, mort, projectiles ennemis, musique (partagé PHL/Merc) ; rendu délégué à ZombieHUD
└── pathfinding/    — algorithmes de navigation (A*)
```

## Principe

Ce dossier contient tout ce qui est **espace de jeu** (world-space), par opposition à `ui/` (screen-space) et `input/` (saisie clavier/souris).

- Les **scènes** héritent de `arcade.View` et orchestrent le rendu + la physique.
- Les **maps** sont des sous-classes de `BaseScene` — une par zone géographique.
- Les **objets** sont des `arcade.Sprite` placés sur la tilemap et interactifs à l'approche.
- Le **loader** lit les fichiers JSON dans `world/configs/` pour instancier PNJs et objets.

## ZombieMode (`zombie_mode.py`)

Classe partagée entre `PhlScene` et `MercScene`. Encapsule : spawn de zombies, tir joueur, dégâts, projectiles ennemis, musique et fondu de mort.

### Attributs publics notables

| Attribut | Type | Rôle |
|---|---|---|
| `drops` | `SpriteList` | Drops spawmés à la mort de zombies |
| `rocks` | `SpriteList` | Projectiles (pierres) tirés par les `ZombieAugmente` |
| `on_reset` | `callable \| None` | Callback appelé après `_do_death_reset()` (None par défaut) |
| `mouse_x / mouse_y` | `int` | Position curseur, mise à jour par la scène parente |

### Propriétés

| Propriété | Retour | Rôle |
|---|---|---|
| `dying` | `bool` | `True` si le fondu de mort est en cours ou si le `DeathMenu` est actif |
| `zombies` | `SpriteList` | Sprites zombies actifs (délégué à `zombie_manager`) |
| `combat_walls` | `SpriteList` | `_combat_walls` ou `SpriteList` vide si non initialisé |

### Méthodes publiques

| Méthode | Rôle |
|---|---|
| `setup(walls, spawn_points, always_active, zombie_class, player_spawn)` | Initialise le mode : physique, zombies, musique |
| `set_spawn_points(points)` | Change les points de spawn dynamiquement |
| `set_spawn_enabled(enabled)` | Active/désactive le spawn de zombies |
| `set_zombie_class(zombie_class)` | Change dynamiquement la classe de zombie du `ZombieManager` |
| `is_active()` | `True` si le mode zombie est actif (objectif actuel ou `always_active`) |
| `stop_music()` | Arrête la musique zombie (p. ex. au retour à `HomeScene`) |
| `draw_world()` | Rendu world-space (délégué à `ZombieHUD` + `zombie_manager` + `drops`) |
| `draw_hud()` | Rendu HUD screen-space (délégué à `ZombieHUD`) |
| `draw_death_overlay()` | Affiche le fondu/menu de mort indépendamment du mode actif |
| `update(delta_time)` | Mise à jour complète : zombies, tir, projectiles, mort |

### Sous-système projectiles ZombieAugmente

Les `ZombieAugmente` accumulent des `pending_projectiles` lors de leurs attaques à distance.

- `_collect_rocks()` — collecte ces projectiles en attente et crée des `Bullet` dans `self.rocks`.
- `_update_rocks()` — déplace les pierres et gère les collisions avec les murs et le joueur.

### Musique zombie

Fichier : `assets/song/zombie.mp3`. Cache global `_music_cache` partagé entre toutes les instances. Démarrée automatiquement par `_start_music()` à l'activation du mode, arrêtée via `stop_music()`.

## Ajouter une nouvelle map

1. Créer un fichier JSON dans `world/configs/<NOM>.json`
2. Créer un `.tmx` dans `world/tilemaps/`
3. Créer `world/maps/<nom>_scene.py` avec une classe `<Nom>Scene(BaseScene)`
4. Enregistrer la classe dans `_MAPS` de `world/scene/scene_manager.py`
