# character/

Ce dossier contient toutes les classes de personnages du jeu ainsi que leur équipement.

## Structure

```
character/
├── character_base.py       — classe mère commune + Humain
├── player/
│   ├── player.py           — classe Player (joueur)
│   └── player_manager.py   — CharacterManager + AnimationManager
├── pnj/
│   ├── pnj.py              — classe PNJ + PNJState
│   └── pnj_loader.py       — humain_from_data()
├── enemies/
│   ├── zombie.py            — classe Zombie
│   └── zombie_manager.py    — ZombieManager
└── equipment/
    ├── weapon.py            — Weapon (arme équipable)
    └── bullet.py            — Bullet (projectile)
```

## Hiérarchie d'héritage

```
arcade.Sprite
└── CharacterBase          (character_base.py)
    ├── Player             (player/player.py)
    ├── PNJ                (pnj/pnj.py)
    └── Zombie             (enemies/zombie.py)
```

## character_base.py

Définit `Humain` et `CharacterBase`. Ré-exporte `Weapon` et `Bullet` depuis `equipment/` pour la compatibilité des imports.

- **`Humain`** — 9 stats (force, vitesse, endurance, mathematique, logique, rpg, music, langue, sociabilite) + position (x, y)
- **`CharacterBase`** — classe mère avec les propriétés communes à tous les personnages :
  - `nom`, `humain`, `direction`, `health`, `damage_cooldown`, `weapon`
  - `textures` (dict idle), `textures_walk` (dict listes frames)
  - `face(dx, dy)` — oriente le sprite
  - `load_walk_textures(prefix)` — charge les textures depuis `assets/images/<prefix>_<d>.png`
  - `_animate(direction, dt)` — alterne les frames de marche

## equipment/

Objets équipables par n'importe quel personnage (Player, PNJ, Zombie).
Pour ajouter un nouveau type d'équipement, créer un fichier dans ce dossier.

- **`weapon.py` — `Weapon`** : arme avec `damage_min`, `damage_max`, `bullet_color`, `get_damage()`
- **`bullet.py` — `Bullet`** : projectile `arcade.SpriteSolidColor` avec `vel_x/y`, `damage`, `life`, `step()`

## player/

### player.py — Player

Joueur contrôlé par le clavier (AZERTY : Z/Q/S/D).

Propriétés spécifiques : `reading`, `quest_manager`, `character_manager`, `textures_read`, timers d'animation.

`Player.update()` délègue à `character_manager.update_player_stats()` et `character_manager.animation.update()`.

### player_manager.py — CharacterManager

Propriétaire du sprite joueur. Responsabilités :
- Chargement et sauvegarde JSON (`save/character_save.json`)
- Slots de sauvegarde nommés (`save/saves.json`)
- Incrémentation de stats via `start_up(progresseur)` / `stop_up()`
- Auto-save toutes les 30 s pendant la progression active

**AnimationManager** — gère l'animation du joueur (marche, lecture) et les limites de la map.

## pnj/

### pnj.py — PNJ + PNJState

PNJ avec machine à états (FSM) :

| État | Comportement |
|------|-------------|
| `ASSIS` | Statique |
| `ERRANCE` | Déplacement aléatoire animé |
| `CHASSE` | Poursuite + tir sur les zombies proches |
| `DIALOGUE` | Immobile, face au joueur |
| `STAND` | Debout immobile |

`update_ai(dt, walls, zombies)` retourne le nombre de zombies tués.

### pnj_loader.py — humain_from_data

`humain_from_data(nom)` construit un `Humain` depuis `assets/param_humain.py`.
Utilisé par `map/map_loader.py` et `map/map_classes/PHL.py`.

## enemies/

### zombie.py — Zombie

Ennemi avec deux comportements :
- **Errance** : déplacement en angle aléatoire (coordonnées polaires)
- **Chasse** : poursuite du joueur avec accélération, wall-slide

Transition errance → chasse à 220 px, retour à 450 px (hysteresis).
`_WALK_SWITCH = 0.2` (plus lent que les autres personnages).

### zombie_manager.py — ZombieManager

Gère le spawn, le mouvement, les balles joueur→zombie et les dégâts zombie→joueur.
Actif uniquement quand `quest_manager.get_kill_objective()` retourne un objectif.
