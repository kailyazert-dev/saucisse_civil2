# world/objects/

Tous les objets interactifs placés dans le monde de jeu. Unified depuis `map/map_classes/objet.py` et `map/map_objects/objet_interactif.py`.

## Hiérarchie

```
arcade.Sprite
└── Objet                    (base_object.py)   — base avec image + scale
    ├── UpStat               (up_stat.py)        — augmente une stat
    └── MapActionObject      (map_action_object.py) — complète un objectif

arcade.Sprite
└── UpStatCollection         (up_stat_collection.py) — liste de UpStat (bibliothèque)
└── ObjetInteractif          (interactable.py)   — popup info uniquement, pas de mécanique
```

## Comportements

### UpStat
Augmente `stat_cible` du joueur si `stat_min ≤ valeur_actuelle < stat_max`.
```python
upstat.utiliser(player, character_manager)  # déclenche character_manager.start_up(self)
```

### UpStatCollection
Conteneur de plusieurs `UpStat` (ex : bibliothèque avec plusieurs livres).
Le joueur navigue dans la liste avec ↑↓, puis confirme avec ENTER.

### MapActionObject
Objet lié à un objectif de type `"map_action"` ou `"test"`.
N'est visible (popup) que si l'objectif est actif dans la quête en cours.
```python
obj.is_available(quest_manager)  # → True si objectif actif
```
À ENTER : `quest_manager.complete_map_action_objective(obj.objective_name)`

### ObjetInteractif
Affiche uniquement un popup avec son nom. Aucune mécanique de progression.
Utilisé pour des points d'intérêt informatifs.

## Ajouter un nouveau type d'objet

1. Créer `world/objects/mon_objet.py` avec une classe héritant de `Objet` ou `arcade.Sprite`
2. Ajouter le cas `"MonObjet"` dans `world/loader/map_loader.py` (`_make_objet`)
3. Ajouter la gestion dans `ui/hud/interact_ui.py` (`interact_obj_prg`)
