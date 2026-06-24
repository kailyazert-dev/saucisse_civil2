# world/

Représentation du monde de jeu : scènes Arcade, cartes, chargement, objets interactifs et environnement.

## Structure

```
world/
├── scene/          — couche arcade.View (boucle de jeu, caméras, physique)
├── maps/           — implémentations par zone (HOME, PHL, TMA)
├── loader/         — chargement des configs JSON de map (world/configs/)
├── objects/        — objets interactifs placés dans le monde
├── environment/    — données d'environnement social d'un lieu
├── zombie_mode.py  — ZombieMode : spawn, tir, dégâts, mort (partagé PHL/Merc) ; rendu délégué à ZombieHUD
└── pathfinding/    — algorithmes de navigation (A*)
```

## Principe

Ce dossier contient tout ce qui est **espace de jeu** (world-space), par opposition à `ui/` (screen-space) et `input/` (saisie clavier/souris).

- Les **scènes** héritent de `arcade.View` et orchestrent le rendu + la physique.
- Les **maps** sont des sous-classes de `BaseScene` — une par zone géographique.
- Les **objets** sont des `arcade.Sprite` placés sur la tilemap et interactifs à l'approche.
- Le **loader** lit les fichiers JSON dans `world/configs/` pour instancier PNJs et objets.

## Ajouter une nouvelle map

1. Créer un fichier JSON dans `world/configs/<NOM>.json`
2. Créer un `.tmx` dans `world/tilemaps/`
3. Créer `world/maps/<nom>_scene.py` avec une classe `<Nom>Scene(BaseScene)`
4. Enregistrer la classe dans `_MAPS` de `world/scene/scene_manager.py`
