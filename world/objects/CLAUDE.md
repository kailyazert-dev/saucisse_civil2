# world/objects/

Objets placés dans le monde de jeu, organisés en deux familles selon leur mode d'interaction.

## Structure

```
world/objects/
  interactables/       — objets posés sur la map, interactifs au ENTER
    base_object.py     — Objet (classe mère)
    up_stat.py         — UpStat(Objet)
    up_stat_collection.py — UpStatCollection(Objet)
    map_action_object.py  — MapActionObject(Objet)
    interactable.py    — ObjetInteractif(Objet)
    coffre.py          — Coffre(arcade.Sprite)
  drops/               — objets lâchés par les ennemis, ramassage automatique au contact
    base_drop.py       — BaseDrop (classe mère)
    gold_drop.py       — GoldDrop(BaseDrop)
    health_drop.py     — HealthDrop(BaseDrop)
```

## Hiérarchie

```
arcade.Sprite
├── Objet                    (interactables/base_object.py)
│   ├── UpStat               (interactables/up_stat.py)
│   ├── UpStatCollection     (interactables/up_stat_collection.py)
│   ├── MapActionObject      (interactables/map_action_object.py)
│   └── ObjetInteractif      (interactables/interactable.py)
├── Coffre                   (interactables/coffre.py)
└── BaseDrop                 (drops/base_drop.py)
    ├── GoldDrop             (drops/gold_drop.py)
    └── HealthDrop           (drops/health_drop.py)
```

## Famille interactables

Objets placés sur la tilemap, déclenchés par ENTER au contact du joueur.
Gérés par `ui/hud/interact_ui.py` (détection de proximité) et `world/loader/map_loader.py` (instanciation depuis JSON).

### Objet
Classe mère. Expose `interact(player, character_manager, quest_manager)` et `is_available(quest_manager)`.

### UpStat
Augmente `stat_cible` du joueur si `stat_min ≤ valeur_actuelle < stat_max`.
```python
upstat.interact(player, character_manager, quest_manager)  # → character_manager.start_up(self)
```

### UpStatCollection
Conteneur de plusieurs `UpStat` (ex : bibliothèque). Le joueur navigue avec ↑↓ puis confirme avec ENTER.

### MapActionObject
Lié à un objectif `"map_action"` ou `"test"`. Visible seulement si l'objectif est actif.
```python
obj.is_available(quest_manager)  # → True si objectif actif
# À ENTER :
quest_manager.complete_map_action_objective(obj.objective_name)
```

### ObjetInteractif
Popup avec nom uniquement. Aucune mécanique de progression.

### Coffre
Distributeur/boutique. Hérite directement de `arcade.Sprite` (pas de `Objet`). Ouvre un `ShopMenu` au contact du joueur.
- `INTERACTION_DISTANCE = 80` — rayon de détection
- Attributs : `nom` (affiché dans l'UI), `catalogue` (section du shop à afficher)

## Famille drops

Objets spawnés à la mort d'un zombie, ramassés automatiquement au contact joueur.
Gérés par `ZombieMode` (`world/zombie_mode.py`) : spawn dans `update()`, rendu dans `draw_world()`.

### BaseDrop
Classe mère. Expose `ramasser(player)` (abstraite) et la constante `ECHELLE`.

### GoldDrop
Drop d'or. Valeur aléatoire 1–3 (`VALEUR_MIN = 1`, `VALEUR_MAX = 3`). Incrémente `player.gold`.

### HealthDrop
Drop de vie. Restaure 2 PV (`SOIN = 2`), plafonné à `Player.MAX_HEALTH + getattr(player, 'max_health_bonus', 0)` (prend en compte le bonus de vie du joueur).

## Ajouter un objet interactif

1. Créer `world/objects/interactables/mon_objet.py` héritant de `Objet`
2. Ajouter le cas `"MonObjet"` dans `world/loader/map_loader.py` (`_make_objet`)
3. Ajouter la gestion dans `ui/hud/interact_ui.py` (`interact_obj_prg`)

## Ajouter un drop

1. Créer `world/objects/drops/mon_drop.py` héritant de `BaseDrop`
2. Implémenter `ramasser(player)`
3. Ajouter un tirage dans `world/zombie_mode.py` (boucle `morts_ce_frame`)
